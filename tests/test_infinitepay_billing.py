import os
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("LICITANEXO_DB_BACKEND", "sqlite")

from src.billing import BillingError, BillingService, InfinitePayGateway


class FakeInfinitePayGateway(InfinitePayGateway):
    def __init__(self):
        super().__init__(
            handle="b2g-solinteg",
            public_url="http://127.0.0.1:8501",
            timeout=1,
        )
        self.calls = []
        self.payment_response = {
            "success": True,
            "paid": True,
            "amount": 2990,
            "paid_amount": 2990,
            "installments": 1,
            "capture_method": "pix",
        }

    def _request(self, path, payload):
        self.calls.append((path, payload))
        if path == "/links":
            return {"url": "https://checkout.infinitepay.invalid/teste"}
        if path == "/payment_check":
            return dict(self.payment_response)
        raise AssertionError(path)


class InfinitePayBillingTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.path = Path(handle.name)
        self.gateway = FakeInfinitePayGateway()
        self.billing = BillingService(self.path, gateway=self.gateway)
        with self.billing.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS companies(
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'Essencial',
                    subscription_status TEXT NOT NULL DEFAULT 'trialing',
                    subscription_ends_at TEXT
                )
                """
            )
            connection.execute(
                "INSERT INTO companies(id,name) VALUES ('c1','Empresa Teste')"
            )

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_checkout_uses_official_price_and_handle(self):
        checkout = self.billing.create_checkout(
            "c1", "financeiro@example.com", "monthly"
        )
        path, payload = self.gateway.calls[0]
        self.assertEqual(path, "/links")
        self.assertEqual(payload["handle"], "b2g-solinteg")
        self.assertEqual(payload["items"][0]["price"], 2990)
        self.assertEqual(payload["order_nsu"], checkout["order_nsu"])
        self.assertIn("billing_return=infinitepay", payload["redirect_url"])
        self.assertEqual(checkout["provider"], "infinitepay")

    def test_payment_check_activates_only_after_server_validation(self):
        checkout = self.billing.create_checkout(
            "c1", "financeiro@example.com", "monthly"
        )
        self.billing.capture_infinitepay_return(
            checkout["order_nsu"],
            "txn-123",
            "slug-123",
            "https://comprovante.invalid/123",
            "pix",
        )
        result = self.billing.sync_checkout(checkout["id"])
        self.assertTrue(result["paid"])
        self.assertEqual(result["local_status"], "active")

        path, payload = self.gateway.calls[-1]
        self.assertEqual(path, "/payment_check")
        self.assertEqual(payload["handle"], "b2g-solinteg")
        self.assertEqual(payload["order_nsu"], checkout["order_nsu"])
        self.assertEqual(payload["transaction_nsu"], "txn-123")
        self.assertEqual(payload["slug"], "slug-123")

        with self.billing.connect() as connection:
            company = connection.execute(
                "SELECT subscription_status,subscription_ends_at FROM companies WHERE id='c1'"
            ).fetchone()
        self.assertEqual(company["subscription_status"], "active")
        self.assertTrue(company["subscription_ends_at"])

    def test_amount_mismatch_never_unlocks_account(self):
        checkout = self.billing.create_checkout(
            "c1", "financeiro@example.com", "monthly"
        )
        self.billing.capture_infinitepay_return(
            checkout["order_nsu"], "txn-456", "slug-456"
        )
        self.gateway.payment_response["amount"] = 100

        with self.assertRaises(BillingError):
            self.billing.sync_checkout(checkout["id"])

        with self.billing.connect() as connection:
            company = connection.execute(
                "SELECT subscription_status FROM companies WHERE id='c1'"
            ).fetchone()
            checkout_row = connection.execute(
                "SELECT local_status FROM billing_checkouts WHERE id=?",
                (checkout["id"],),
            ).fetchone()
        self.assertEqual(company["subscription_status"], "trialing")
        self.assertEqual(checkout_row["local_status"], "pending")


if __name__ == "__main__":
    unittest.main()
