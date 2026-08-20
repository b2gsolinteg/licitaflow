import tempfile
import unittest
from pathlib import Path

from src.database import Database
from src.sources import portal_access_info


class EssentialDiscoveryContractsTest(unittest.TestCase):
    def test_portal_access_is_beginner_friendly_and_conservative(self):
        self.assertEqual(portal_access_info("Compras.gov")["status"], "free")
        self.assertEqual(portal_access_info("BLL Compras")["status"], "may_charge")
        self.assertEqual(portal_access_info("Não identificado")["status"], "unknown")

    def test_catalog_can_filter_city_and_group_open_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "licitaflow.db")
            with db.connect() as conn:
                conn.executemany(
                    """
                    INSERT INTO global_pncp_catalog(
                        id, pncp_control_number, agency, city, state, modality,
                        closing_at, object, estimated_value, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        ("1", "00000000000001-1-1/2026", "Órgão A", "Londrina", "PR", "Pregão eletrônico", "2099-08-20T10:00:00", "Papel", 1000, "https://example.com/a"),
                        ("2", "00000000000002-1-2/2026", "Órgão B", "Curitiba", "PR", "Dispensa de licitação", "2099-08-21T10:00:00", "Caneta", 2000, "https://example.com/b"),
                        ("3", "00000000000003-1-3/2026", "Órgão C", "Londrina", "PR", "Pregão eletrônico", "2000-01-01T10:00:00", "Pasta", 3000, "https://example.com/c"),
                    ],
                )
            rows = db.list_global_catalog(cities=["londrina"], closing_from="2026-08-18", limit=50)
            self.assertEqual([row["id"] for row in rows], ["1"])
            states = db.global_catalog_group_counts("state", closing_from="2026-08-18")
            pr = next(row for row in states if row["label"] == "PR")
            self.assertEqual(pr["total"], 2)
            quality = db.global_catalog_quality_stats()
            self.assertEqual(quality["total"], 3)
            self.assertEqual(quality["future_deadline"], 2)

    def test_ui_contracts_remove_score_and_cnae_from_beginner_flow(self):
        discovery = Path("src/essential_discovery.py").read_text(encoding="utf-8")
        company = Path("src/company_ui.py").read_text(encoding="utf-8")
        app = Path("app.py").read_text(encoding="utf-8")
        config = Path("src/config.py").read_text(encoding="utf-8")

        self.assertNotIn("_match_score", discovery)
        self.assertNotIn("profile_search_ready", discovery)
        self.assertNotIn("CNAEs / atividades formais", company)
        self.assertNotIn("Como o Radar usa meu perfil", company)
        self.assertIn("Minha lista", app)
        self.assertIn("Por Estado", app)
        self.assertIn("Radar de licitações", app)
        self.assertIn('APP_VERSION = "1.0 Essential RC31.13"', config)


if __name__ == "__main__":
    unittest.main()
