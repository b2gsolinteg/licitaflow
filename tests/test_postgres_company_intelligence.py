import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

POSTGRES_TEST = os.getenv("LICITANEXO_TEST_POSTGRES", "0").strip() == "1"


@unittest.skipUnless(POSTGRES_TEST, "PostgreSQL integration test disabled")
class PostgresCompanyIntelligenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg

        cls.original_schema = os.getenv("LICITANEXO_DB_SCHEMA", "licitanexo_ci")
        cls.schema = f"{cls.original_schema}_company"
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
            cursor.execute("INSERT INTO companies(id,name) VALUES ('company-rc31','Empresa RC31')")
            cursor.execute(
                "INSERT INTO users(id,company_id,name,email) VALUES ('user-rc31','company-rc31','Cliente','rc31@example.com')"
            )
            cursor.execute("""
                INSERT INTO opportunities(id,company_id,pncp_control_number,agency,state,object,estimated_value)
                VALUES ('opp-rc31','company-rc31','RC31-TEST','Prefeitura','SP','Aquisição de papel A4',3200)
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

    def test_profile_roundtrip_and_rank_in_postgres(self):
        from src.company_intelligence import get_extended_profile, rank_opportunities, save_extended_profile
        from src.database import Database

        db = Database(ROOT / "data" / "ci-company.db")
        save_extended_profile(
            db,
            "company-rc31",
            offerings="papel A4, toner, material de escritório",
            procurement_interests="material de expediente",
            interest_keywords="papel A4, papelaria",
            service_states="SP, PR",
            excluded_keywords="obra pesada",
            profile_search_enabled=True,
        )
        profile = get_extended_profile(db, "company-rc31")
        self.assertIn("papel A4", profile["offerings"])
        self.assertEqual(int(profile["profile_search_enabled"]), 1)
        ranked = rank_opportunities([
            {"id": "a", "object": "Compra de papel A4 para expediente", "state": "SP"},
            {"id": "b", "object": "Obra pesada de pavimentação", "state": "SP"},
        ], profile)
        self.assertEqual(ranked[0]["id"], "a")
        self.assertGreater(ranked[0]["_match_score"], 0)
        self.assertEqual(next(row for row in ranked if row["id"] == "b")["_match_score"], 0)

    def test_multiple_supplier_roundtrip_in_postgres(self):
        from src.database import Database
        from src.pricing import add_supplier, item_financials, list_suppliers, select_supplier

        db = Database(ROOT / "data" / "ci-company.db")
        db.add_quote_item(
            "company-rc31", "opp-rc31", "Papel A4", 100,
            0, 0, 0, 0, 27.90, "", lot_number="1", edital_price=32.00, commission=0,
        )
        item = db.list_quote_items("company-rc31", "opp-rc31")[0]
        supplier_a = add_supplier(db, "company-rc31", item["id"], "Fornecedor A", 21.40, 0.50)
        supplier_b = add_supplier(db, "company-rc31", item["id"], "Fornecedor B", 20.85, 0.40)
        suppliers = list_suppliers(db, "company-rc31", item["id"])
        self.assertEqual(len(suppliers), 2)
        self.assertTrue(next(row for row in suppliers if row["id"] == supplier_a)["is_selected"])
        select_supplier(db, "company-rc31", item["id"], supplier_b)
        refreshed = db.list_quote_items("company-rc31", "opp-rc31")[0]
        self.assertEqual(refreshed["supplier"], "Fornecedor B")
        self.assertAlmostEqual(float(refreshed["unit_cost"]), 20.85, places=2)
        self.assertGreater(item_financials(refreshed)["profit"], 0)


if __name__ == "__main__":
    unittest.main()
