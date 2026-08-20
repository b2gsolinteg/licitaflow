import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTGRES_TEST = os.getenv("LICITANEXO_TEST_POSTGRES", "0").strip() == "1"


@unittest.skipUnless(POSTGRES_TEST, "PostgreSQL integration test disabled")
class PostgresMeiDiscoveryTests(unittest.TestCase):
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
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{cls.schema}"')
            cursor.execute(f'SET search_path TO "{cls.schema}", public')
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS global_pncp_catalog (
                    id TEXT PRIMARY KEY,
                    pncp_control_number TEXT NOT NULL UNIQUE,
                    agency TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT '',
                    modality TEXT NOT NULL DEFAULT '',
                    published_at TIMESTAMPTZ,
                    opening_at TIMESTAMPTZ,
                    closing_at TIMESTAMPTZ,
                    object TEXT NOT NULL DEFAULT '',
                    estimated_value DOUBLE PRECISION,
                    source_url TEXT NOT NULL DEFAULT '',
                    srp INTEGER NOT NULL DEFAULT 0,
                    source_name TEXT NOT NULL DEFAULT 'PNCP',
                    source_channel TEXT NOT NULL DEFAULT 'PNCP',
                    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute("DELETE FROM global_pncp_catalog WHERE id LIKE 'mei-pg-%'")
            now = datetime.now(timezone.utc)
            cursor.execute(
                """
                INSERT INTO global_pncp_catalog(
                    id,pncp_control_number,agency,city,state,modality,published_at,
                    opening_at,closing_at,object,estimated_value,source_url,srp,
                    source_name,source_channel
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    "mei-pg-1",
                    "12345678000199-1-901/2026",
                    "Prefeitura de Curitiba",
                    "Curitiba",
                    "PR",
                    "Pregão eletrônico",
                    now,
                    now + timedelta(days=2),
                    now + timedelta(days=4),
                    "Aquisição de materiais de artesanato e barbante",
                    18500.0,
                    "https://www.gov.br/compras/",
                    0,
                    "Compras.gov",
                    "PNCP",
                ),
            )
        connection.commit()
        connection.close()

    def test_region_city_and_blank_keyword_work_with_native_timestamps(self):
        from src.database import Database
        from src.mei_catalog import MeiCatalogService

        service = MeiCatalogService(Database(ROOT / "data" / "mei-ci.db"))
        rows = service.search(region="Sul", city="Curitiba", keyword="", limit=20)
        selected = [row for row in rows if row.get("id") == "mei-pg-1"]
        self.assertEqual(1, len(selected))
        self.assertEqual("Compras.gov", selected[0]["portal"])
        self.assertEqual("Gratuito", selected[0]["portal_access"])


if __name__ == "__main__":
    unittest.main()
