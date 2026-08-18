from pathlib import Path
import tempfile
import unittest

from src.database import Database
from src.sources import portal_access_info

ROOT = Path(__file__).resolve().parents[1]


class CleanEssentialContracts(unittest.TestCase):
    def test_light_theme_has_no_gold_or_dark_background(self):
        theme = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('backgroundColor = "#FFFFFF"', theme)
        self.assertIn('secondaryBackgroundColor = "#F4F7F9"', theme)
        self.assertNotIn("#C99A2E", theme)
        self.assertNotIn("#081321", theme)

    def test_beginner_navigation_hides_future_modules(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('work_pages = ["❤️ Minha lista", "📅 Calendário"]', app)
        self.assertIn('elif page == "📅 Calendário"', app)

    def test_search_can_filter_dispute_site(self):
        discovery = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn("Site da disputa", discovery)
        self.assertIn("Todos os sites", discovery)
        self.assertIn("PORTAL_SEARCH_TERMS", discovery)
        self.assertIn("portal_terms=PORTAL_SEARCH_TERMS.get(portal)", discovery)

    def test_all_state_flags_are_bundled(self):
        states = "ac al ap am ba ce df es go ma mt ms mg pa pb pr pe pi rj rn rs ro rr sc sp se to".split()
        for state in states:
            self.assertTrue((ROOT / "assets" / "state_flags" / f"{state}.svg").exists(), state)

    def test_unknown_portal_uses_simple_text(self):
        info = portal_access_info("Não identificado")
        self.assertEqual(info["label"], "Não identificado")
        self.assertEqual(info["detail"], "Consultar edital.")

    def test_calendar_only_includes_participation_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "licitaflow.db")
            user = db.register("Empresa", "Pessoa", "pessoa@example.com", "SenhaForte123!")
            company_id = user["company_id"]
            oid = db.add_manual_opportunity(company_id, "Órgão", "Objeto", certame_at="2099-01-10T09:00")
            self.assertEqual(db.essential_certame_calendar(company_id, "2099-01-01"), [])
            db.update_details(company_id, oid, decision="Participar", certame_at="2099-01-10T09:00")
            rows = db.essential_certame_calendar(company_id, "2099-01-01")
            self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
