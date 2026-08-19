from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SimpleDiscoveryContracts(unittest.TestCase):
    def test_card_uses_agency_instead_of_raw_pncp_control_as_heading(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn("reference = agency", src)
        self.assertNotIn('reference = control or "Contratação pública"', src)

    def test_home_and_portal_discovery_are_available(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("def home_page", src)
        self.assertIn("def portal_page", src)
        self.assertIn("🏠 Início", app)
        self.assertIn("🌐 Por site de disputa", app)

    def test_sidebar_menu_is_bold_but_main_content_stays_light(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('[data-testid="stSidebar"] .stButton button{font-weight:600 !important;}', src)
        self.assertIn('[data-testid="stMain"] *{font-weight:400 !important;}', src)

    def test_em_destaque_replaces_top50_label(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("🔥 Em destaque", app)
        self.assertNotIn('"🏆 Top 50"', app)

    def test_version_is_rc319(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.9"', cfg)


if __name__ == "__main__":
    unittest.main()
