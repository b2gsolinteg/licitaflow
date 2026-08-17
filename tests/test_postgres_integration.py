import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

POSTGRES_TEST = os.getenv("LICITANEXO_TEST_POSTGRES", "0").strip() == "1"


@unittest.skipUnless(POSTGRES_TEST, "PostgreSQL integration test disabled")
class PostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg

        cls.schema = os.getenv("LICITANEXO_DB_SCHEMA", "licitanexo_ci")
        connection = psycopg.connect(
            host=os.getenv("LICITANEXO_PGHOST", "127.0.0.1"),
            port=int(os.getenv("LICITANEXO_PGPORT", "5432")),
            dbname=os.getenv("LICITANEXO_PGDATABASE", "postgres"),
            user=os.getenv("LICITANEXO_PGUSER", "postgres"),
            password=os.getenv("LICITANEXO_PGPASSWORD", "postgres"),
            sslmode=os.getenv("LICITANEXO_PGSSLMODE", "disable"),
        )
        with connection.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE')
            cursor.execute(f'CREATE SCHEMA "{cls.schema}"')
            cursor.execute(f'SET search_path TO "{cls.schema}", public')
            statements = [
                """
                CREATE TABLE companies(
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'Essencial',
                    subscription_status TEXT NOT NULL DEFAULT 'trialing',
                    trial_started_at TEXT,
                    trial_ends_at TEXT,
                    subscription_ends_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE users(
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT 'owner',
                    terms_accepted_at TEXT,
                    privacy_accepted_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TEXT
                )
                """,
                """
                CREATE TABLE assisted_requests(
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    urgency TEXT NOT NULL DEFAULT 'Normal',
                    status TEXT NOT NULL DEFAULT 'Recebida',
                    admin_notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE security_events(
                    id BIGSERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    subject TEXT NOT NULL DEFAULT '',
                    ip_hash TEXT NOT NULL DEFAULT '',
                    success INTEGER NOT NULL DEFAULT 0,
                    details TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE security_rate_limits(
                    bucket TEXT PRIMARY KEY,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    window_started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    blocked_until TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE security_sessions(
                    token_hash TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL DEFAULT '',
                    user_id TEXT NOT NULL DEFAULT '',
                    issued_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT
                )
                """,
                """
                CREATE TABLE security_backup_audit(
                    id BIGSERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    size_bytes BIGINT NOT NULL,
                    integrity_status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE usage_settings(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE usage_company_limits(
                    company_id TEXT PRIMARY KEY,
                    analysis_monthly_limit INTEGER,
                    estimated_analysis_cost_cents DOUBLE PRECISION,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE usage_events(
                    id BIGSERIAL PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    user_id TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL,
                    units INTEGER NOT NULL DEFAULT 1,
                    estimated_cost_cents DOUBLE PRECISION NOT NULL DEFAULT 0,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE commercial_subscriptions(
                    company_id TEXT PRIMARY KEY,
                    plan_code TEXT NOT NULL DEFAULT 'ESSENTIAL',
                    status TEXT NOT NULL DEFAULT 'trialing',
                    trial_started_at TEXT,
                    trial_ends_at TEXT,
                    current_period_start TEXT,
                    current_period_end TEXT,
                    billing_cycle TEXT NOT NULL DEFAULT 'monthly',
                    payment_method TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE billing_checkouts(
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    payer_email TEXT NOT NULL,
                    plan_code TEXT NOT NULL DEFAULT 'ESSENTIAL',
                    billing_cycle TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    provider TEXT NOT NULL DEFAULT 'mercadopago',
                    provider_id TEXT NOT NULL DEFAULT '',
                    provider_status TEXT NOT NULL DEFAULT 'created',
                    local_status TEXT NOT NULL DEFAULT 'pending',
                    init_point TEXT NOT NULL DEFAULT '',
                    external_reference TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE billing_events(
                    id BIGSERIAL PRIMARY KEY,
                    checkout_id TEXT NOT NULL DEFAULT '',
                    company_id TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL,
                    provider_status TEXT NOT NULL DEFAULT '',
                    details TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
            ]
            statements.extend([
                """
                CREATE TABLE opportunities(
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    pncp_control_number TEXT, agency TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT '',
                    modality TEXT NOT NULL DEFAULT '', published_at TEXT, opening_at TEXT, closing_at TEXT,
                    object TEXT NOT NULL DEFAULT '', estimated_value DOUBLE PRECISION,
                    source_url TEXT NOT NULL DEFAULT '', srp INTEGER NOT NULL DEFAULT 0,
                    source_name TEXT NOT NULL DEFAULT 'PNCP', source_channel TEXT NOT NULL DEFAULT 'PNCP',
                    stage TEXT NOT NULL DEFAULT 'Oportunidade',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE opportunity_quote_items(
                    id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, company_id TEXT NOT NULL,
                    description TEXT NOT NULL, quantity DOUBLE PRECISION NOT NULL DEFAULT 1,
                    unit_cost DOUBLE PRECISION NOT NULL DEFAULT 0, freight DOUBLE PRECISION NOT NULL DEFAULT 0,
                    taxes DOUBLE PRECISION NOT NULL DEFAULT 0, other_costs DOUBLE PRECISION NOT NULL DEFAULT 0,
                    sale_price DOUBLE PRECISION NOT NULL DEFAULT 0, supplier TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
            ])
            for statement in statements:
                cursor.execute(statement)
            cursor.execute(
                "INSERT INTO companies(id,name) VALUES ('c1','Empresa CI')"
            )
            cursor.execute(
                "INSERT INTO users(id,company_id,name,email,role) VALUES ('u1','c1','Cliente CI','ci@example.com','owner')"
            )
        connection.commit()
        connection.close()

        from src.db_migrations import run_postgres_migrations

        result = run_postgres_migrations(ROOT)
        if result.get("pending"):
            raise AssertionError(f"Pending migrations: {result['pending']}")

    def test_migration_converts_critical_timestamp_columns(self):
        from src.db_runtime import connect_runtime

        expected = {
            ("security_events", "created_at"),
            ("security_rate_limits", "window_started_at"),
            ("security_sessions", "expires_at"),
            ("usage_events", "created_at"),
            ("billing_checkouts", "created_at"),
            ("assisted_request_messages", "created_at"),
        }
        with connect_runtime(ROOT / "data" / "ci.db") as connection:
            rows = connection.execute(
                """
                SELECT table_name,column_name,data_type
                FROM information_schema.columns
                WHERE table_schema=?
                """,
                (self.schema,),
            ).fetchall()
        types = {
            (row["table_name"], row["column_name"]): row["data_type"]
            for row in rows
        }
        for key in expected:
            self.assertEqual(types.get(key), "timestamp with time zone", key)

    def test_company_intelligence_schema_is_available(self):
        from src.db_runtime import connect_runtime

        with connect_runtime(ROOT / "data" / "ci.db") as connection:
            rows = connection.execute(
                """
                SELECT table_name,column_name,data_type
                FROM information_schema.columns
                WHERE table_schema=? AND table_name IN (
                    'company_profiles','company_document_uploads','opportunity_item_suppliers'
                )
                """,
                (self.schema,),
            ).fetchall()
        columns = {(row["table_name"], row["column_name"]): row["data_type"] for row in rows}
        self.assertIn(("company_profiles", "excluded_keywords"), columns)
        self.assertIn(("company_profiles", "profile_search_enabled"), columns)
        self.assertEqual(columns.get(("company_document_uploads", "created_at")), "timestamp with time zone")
        self.assertEqual(columns.get(("opportunity_item_suppliers", "created_at")), "timestamp with time zone")

    def test_migrations_are_idempotent(self):
        from src.db_migrations import run_postgres_migrations

        result = run_postgres_migrations(ROOT)
        self.assertEqual(result["applied_now"], [])
        self.assertEqual(result["pending"], [])

    def test_security_session_and_rate_limit_roundtrip(self):
        from src.security_rc25 import SecurityService, SessionExpiredError

        security = SecurityService(ROOT / "data" / "ci.db", ROOT)
        token = security.create_session("c1", "u1")
        self.assertTrue(security.validate_session(token))
        security.register_attempt("login", "ci@example.com", "127.0.0.1", success=False)
        security.register_attempt("login", "ci@example.com", "127.0.0.1", success=True)
        metrics = security.metrics()
        self.assertGreaterEqual(metrics["active_sessions"], 1)
        security.revoke_session(token)
        with self.assertRaises(SessionExpiredError):
            security.validate_session(token)

    def test_usage_month_boundary_uses_native_parameters(self):
        from src.usage import UsageService

        usage = UsageService(ROOT / "data" / "ci.db")
        usage.record_analysis("c1", "u1", "edital.pdf", pages=12)
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=70)
        with usage.connect() as connection:
            connection.execute(
                """
                INSERT INTO usage_events(
                    company_id,user_id,event_type,units,estimated_cost_cents,metadata,created_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    "c1",
                    "u1",
                    "analysis",
                    9,
                    0,
                    "{}",
                    old_timestamp,
                ),
            )
        month = usage.month_usage("c1", "analysis")
        self.assertEqual(month["units"], 1)
        self.assertTrue(usage.analysis_status("c1")["allowed"])

    def test_billing_updates_subscription_atomically(self):
        from src.billing import BillingService

        provider_id = "mp-" + uuid.uuid4().hex

        class Gateway:
            configured = True

            def create_subscription(self, payer_email, company_id, cycle, external_reference):
                return {
                    "id": provider_id,
                    "init_point": "https://example.invalid/checkout",
                    "status": "pending",
                }

            def get_subscription(self, current_provider_id):
                self_outer.assertEqual(current_provider_id, provider_id)
                return {"status": "authorized", "next_payment_date": ""}

            def cancel_subscription(self, current_provider_id):
                self_outer.assertEqual(current_provider_id, provider_id)
                return {"status": "canceled"}

        self_outer = self
        billing = BillingService(ROOT / "data" / "ci.db", gateway=Gateway())
        checkout = billing.create_checkout("c1", "financeiro@example.com", "monthly")
        result = billing.sync_checkout(checkout["id"])
        self.assertEqual(result["local_status"], "active")
        with billing.connect() as connection:
            company = connection.execute(
                "SELECT subscription_status,subscription_ends_at FROM companies WHERE id=?",
                ("c1",),
            ).fetchone()
        self.assertEqual(company["subscription_status"], "active")
        self.assertIsNotNone(company["subscription_ends_at"])


if __name__ == "__main__":
    unittest.main()
