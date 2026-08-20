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
        self.assertIn("Início", app)
        self.assertIn("Por site de disputa", app)

    def test_sidebar_and_main_content_preserve_premium_typographic_hierarchy(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn("font-weight:650 !important", app)
        self.assertIn('[data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3{color:#172B3A !important;font-weight:700 !important', src)
        self.assertNotIn('[data-testid="stMain"] *{font-weight:400 !important;}', src)

    def test_em_destaque_replaces_top50_label(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("Em destaque", app)
        self.assertNotIn('"🏆 Top 50"', app)

    def test_version_is_rc319(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.17"', cfg)


if __name__ == "__main__":
    unittest.main()
