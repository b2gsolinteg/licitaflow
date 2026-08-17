import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


os.environ["LICITANEXO_DB_BACKEND"] = "sqlite"


class MiniDB:
    def __init__(self, path):
        self.path = str(path)
        self.analyses = []

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def list_quote_items(self, company_id, opportunity_id):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM opportunity_quote_items WHERE company_id=? AND opportunity_id=? ORDER BY lot_number",
                (company_id, opportunity_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_analyses(self, company_id, opportunity_id):
        return list(self.analyses)

    def list_checklist(self, company_id, opportunity_id):
        return []


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        return FakeResponse(self.payload)


class RC311FeatureTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = MiniDB(Path(self.tempdir.name) / "rc311.db")
        with self.db.connect() as conn:
            conn.executescript("""
                CREATE TABLE companies(id TEXT PRIMARY KEY, name TEXT NOT NULL);
                CREATE TABLE opportunities(
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL, agency TEXT NOT NULL DEFAULT '',
                    pncp_control_number TEXT, FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE opportunity_quote_items(
                    id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, company_id TEXT NOT NULL,
                    description TEXT NOT NULL, quantity REAL NOT NULL DEFAULT 1,
                    unit_cost REAL NOT NULL DEFAULT 0, freight REAL NOT NULL DEFAULT 0,
                    taxes REAL NOT NULL DEFAULT 0, other_costs REAL NOT NULL DEFAULT 0,
                    sale_price REAL NOT NULL DEFAULT 0, supplier TEXT NOT NULL DEFAULT '',
                    lot_number TEXT NOT NULL DEFAULT '', edital_price REAL NOT NULL DEFAULT 0,
                    commission REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id),
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                INSERT INTO companies(id,name) VALUES ('company-1','Empresa');
                INSERT INTO opportunities(id,company_id,agency,pncp_control_number)
                VALUES ('opp-1','company-1','Órgão','12345678000199-1-42/2026');
            """)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_pncp_items_are_normalized_and_imported_without_duplicates(self):
        from src.pncp_items import fetch_contract_items, import_contract_items

        session = FakeSession({
            "itens": [{
                "numeroItem": 1,
                "descricao": "Papel A4",
                "quantidade": 100,
                "unidadeMedida": "resma",
                "valorUnitarioEstimado": 32.50,
                "valorTotal": 3250,
                "orcamentoSigiloso": False,
            }],
            "totalPaginas": 1,
        })
        items = fetch_contract_items("12345678000199-1-42/2026", session=session)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["number"], "1")
        self.assertEqual(items[0]["unit_measure"], "resma")
        self.assertAlmostEqual(items[0]["unit_price"], 32.50)

        first = import_contract_items(
            self.db, "company-1", "opp-1", "12345678000199-1-42/2026", items
        )
        second = import_contract_items(
            self.db, "company-1", "opp-1", "12345678000199-1-42/2026", items
        )
        self.assertEqual(first["imported"], 1)
        self.assertEqual(second["skipped"], 1)
        row = self.db.list_quote_items("company-1", "opp-1")[0]
        self.assertEqual(row["source_kind"], "pncp")
        self.assertEqual(row["unit_measure"], "resma")
        self.assertAlmostEqual(float(row["edital_price"]), 32.50)
        self.assertEqual(float(row["sale_price"]), 0.0)

    def test_supplier_is_saved_company_wide_and_quotes_are_grouped(self):
        from src.pricing import add_supplier, ensure_sqlite_pricing_schema
        from src.supplier_directory import (
            ensure_company_supplier,
            list_company_suppliers,
            list_opportunity_supplier_quotes,
        )

        ensure_sqlite_pricing_schema(self.db)
        with self.db.connect() as conn:
            conn.execute("""
                INSERT INTO opportunity_quote_items(
                    id,opportunity_id,company_id,description,quantity,sale_price,lot_number,edital_price
                ) VALUES ('q-1','opp-1','company-1','Papel A4',100,27.90,'1',32.00)
            """)
        supplier_id = ensure_company_supplier(
            self.db, "company-1", "Distribuidora ABC", phone="11999999999"
        )
        same_id = ensure_company_supplier(self.db, "company-1", "distribuidora abc")
        self.assertEqual(supplier_id, same_id)
        self.assertEqual(len(list_company_suppliers(self.db, "company-1")), 1)

        add_supplier(self.db, "company-1", "q-1", "Distribuidora ABC", 20.85, 0.40)
        grouped = list_opportunity_supplier_quotes(self.db, "company-1", "opp-1")
        self.assertEqual(len(grouped["q-1"]), 1)
        self.assertEqual(grouped["q-1"][0]["supplier_name"], "Distribuidora ABC")

    def test_journey_persists_custom_steps_and_auto_completes_pricing(self):
        from src.journey import (
            add_custom_step,
            journey_progress,
            list_journey_steps,
            sync_automatic_completion,
        )

        with self.db.connect() as conn:
            conn.execute("""
                INSERT INTO opportunity_quote_items(
                    id,opportunity_id,company_id,description,quantity,unit_cost,sale_price,supplier,lot_number,edital_price
                ) VALUES ('q-2','opp-1','company-1','Toner',10,50,80,'Fornecedor X','2',90)
            """)
        self.db.analyses = [{"id": "analysis-1"}]
        custom_id = add_custom_step(self.db, "company-1", "opp-1", "Separar amostra")
        self.assertTrue(custom_id)
        status = sync_automatic_completion(self.db, "company-1", "opp-1")
        self.assertTrue(status["analysis"])
        self.assertTrue(status["suppliers"])
        self.assertTrue(status["pricing"])
        steps = list_journey_steps(self.db, "company-1", "opp-1")
        done_keys = {row["step_key"] for row in steps if int(row["is_done"])}
        self.assertTrue({"analysis", "suppliers", "pricing"}.issubset(done_keys))
        self.assertGreater(journey_progress(steps)["percent"], 0)


if __name__ == "__main__":
    unittest.main()
