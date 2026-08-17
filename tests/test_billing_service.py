import os
import tempfile
import unittest
import uuid
from pathlib import Path


os.environ.setdefault("LICITANEXO_DB_BACKEND", "sqlite")

from src.billing import BillingService


class FakeGateway:
    configured = True

    def __init__(self):
        self.provider_id = "mp-" + uuid.uuid4().hex
        self.status = "pending"

    def create_subscription(self, payer_email, company_id, cycle, external_reference):
        return {
            "id": self.provider_id,
            "init_point": "https://example.invalid/checkout",
            "status": self.status,
        }

    def get_subscription(self, provider_id):
        assert provider_id == self.provider_id
        return {"status": self.status, "next_payment_date": ""}

    def cancel_subscription(self, provider_id):
        assert provider_id == self.provider_id
        self.status = "canceled"
        return {"status": self.status}


class BillingServiceTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.path = Path(handle.name)
        self.gateway = FakeGateway()
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

    def test_authorized_checkout_activates_company(self):
        checkout = self.billing.create_checkout(
            "c1", "financeiro@example.com", "monthly"
        )
        self.gateway.status = "authorized"
        result = self.billing.sync_checkout(checkout["id"])
        self.assertEqual(result["local_status"], "active")
        with self.billing.connect() as connection:
            company = connection.execute(
                "SELECT plan,subscription_status,subscription_ends_at FROM companies WHERE id='c1'"
            ).fetchone()
        self.assertEqual(company["plan"], "Essential")
        self.assertEqual(company["subscription_status"], "active")
        self.assertTrue(company["subscription_ends_at"])

    def test_provider_lookup_reuses_checkout(self):
        checkout = self.billing.create_checkout(
            "c1", "financeiro@example.com", "quarterly"
        )
        self.gateway.status = "authorized"
        result = self.billing.sync_provider_subscription(self.gateway.provider_id)
        self.assertEqual(result["local_status"], "active")
        rows = self.billing.list_company("c1")
        self.assertEqual(rows[0]["id"], checkout["id"])

    def test_cancel_marks_subscription_canceled(self):
        checkout = self.billing.create_checkout(
            "c1", "financeiro@example.com", "monthly"
        )
        self.billing.cancel(checkout["id"])
        with self.billing.connect() as connection:
            company = connection.execute(
                "SELECT subscription_status FROM companies WHERE id='c1'"
            ).fetchone()
        self.assertEqual(company["subscription_status"], "canceled")


if __name__ == "__main__":
    unittest.main()
