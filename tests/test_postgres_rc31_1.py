import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

POSTGRES_TEST = os.getenv("LICITANEXO_TEST_POSTGRES", "0").strip() == "1"


@unittest.skipUnless(POSTGRES_TEST, "PostgreSQL integration test disabled")
class PostgresRC311Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg

        cls.original_schema = os.getenv("LICITANEXO_DB_SCHEMA", "licitanexo_ci")
        cls.schema = f"{cls.original_schema}_rc311"
        os.environ["LICITANEXO_DB_SCHEMA"] = cls.schema
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
            for statement in (
                """
                CREATE TABLE companies(
                    id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    cnpj TEXT NOT NULL DEFAULT '', plan TEXT NOT NULL DEFAULT 'Essencial',
                    subscription_status TEXT NOT NULL DEFAULT 'trialing',
                    trial_started_at TEXT, trial_ends_at TEXT, subscription_ends_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE users(
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL DEFAULT '', role TEXT NOT NULL DEFAULT 'owner',
                    terms_accepted_at TEXT, privacy_accepted_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, last_login_at TEXT
                )
                """,
                """
                CREATE TABLE assisted_requests(
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    request_type TEXT NOT NULL, title TEXT NOT NULL, details TEXT NOT NULL DEFAULT '',
                    urgency TEXT NOT NULL DEFAULT 'Normal', status TEXT NOT NULL DEFAULT 'Recebida',
                    admin_notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE opportunities(
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    pncp_control_number TEXT, agency TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT '',
                    modality TEXT NOT NULL DEFAULT '', published_at TEXT, opening_at TEXT, closing_at TEXT,
                    object TEXT NOT NULL DEFAULT '', estimated_value DOUBLE PRECISION,
                    source_url TEXT NOT NULL DEFAULT '', srp INTEGER NOT NULL DEFAULT 0,
                    source_name TEXT NOT NULL DEFAULT 'PNCP', source_channel TEXT NOT NULL DEFAULT 'PNCP',
                    stage TEXT NOT NULL DEFAULT 'Nova oportunidade',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
            ):
                cursor.execute(statement)
            cursor.execute("INSERT INTO companies(id,name) VALUES ('company-rc311','Empresa RC311')")
            cursor.execute(
                "INSERT INTO users(id,company_id,name,email) VALUES ('user-rc311','company-rc311','Cliente','rc311@example.com')"
            )
            cursor.execute("""
                INSERT INTO opportunities(id,company_id,pncp_control_number,agency,state,object,estimated_value)
                VALUES ('opp-rc311','company-rc311','12345678000199-1-42/2026','Prefeitura','SP','Aquisição de papel A4',3250)
            """)
        connection.commit()
        connection.close()

        from src.db_migrations import run_postgres_migrations
        result = run_postgres_migrations(ROOT)
        if result.get("pending"):
            raise AssertionError(f"Pending migrations: {result['pending']}")

    @classmethod
    def tearDownClass(cls):
        os.environ["LICITANEXO_DB_SCHEMA"] = cls.original_schema

    def test_supplier_directory_journey_and_pncp_item_roundtrip(self):
        from src.database import Database
        from src.journey import add_custom_step, list_journey_steps, set_step_done
        from src.pncp_items import import_contract_items
        from src.supplier_directory import ensure_company_supplier, list_company_suppliers

        db = Database(ROOT / "data" / "ci-rc311.db")
        supplier_id = ensure_company_supplier(
            db, "company-rc311", "Fornecedor Permanente",
            phone="11999999999", payment_terms="28 dias", default_lead_time_days=5,
        )
        suppliers = list_company_suppliers(db, "company-rc311")
        self.assertEqual(suppliers[0]["id"], supplier_id)
        self.assertEqual(suppliers[0]["payment_terms"], "28 dias")

        imported = import_contract_items(
            db,
            "company-rc311",
            "opp-rc311",
            "12345678000199-1-42/2026",
            [{
                "number": "1",
                "description": "Papel A4",
                "quantity": 100,
                "unit_measure": "resma",
                "unit_price": 32.50,
                "confidential": False,
                "source_reference": "pncp:12345678000199-1-42/2026:1",
            }],
        )
        self.assertEqual(imported["imported"], 1)
        item = db.list_quote_items("company-rc311", "opp-rc311")[0]
        self.assertEqual(item["source_kind"], "pncp")
        self.assertEqual(item["unit_measure"], "resma")
        self.assertAlmostEqual(float(item["edital_price"]), 32.50)

        custom_id = add_custom_step(db, "company-rc311", "opp-rc311", "Separar amostra")
        set_step_done(db, "company-rc311", "opp-rc311", custom_id, True)
        steps = list_journey_steps(db, "company-rc311", "opp-rc311")
        custom = next(row for row in steps if row["id"] == custom_id)
        self.assertEqual(int(custom["is_done"]), 1)

        with db.connect() as conn:
            columns = {
                row["column_name"]
                for row in conn.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema=? AND table_name='opportunity_quote_items'
                """, (self.schema,)).fetchall()
            }
        self.assertTrue({"unit_measure", "source_kind", "source_reference"}.issubset(columns))


if __name__ == "__main__":
    unittest.main()
