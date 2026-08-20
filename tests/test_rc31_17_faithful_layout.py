from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3117FaithfulLayoutContracts(unittest.TestCase):
    """Contratos finais da camada visual fiel RC31.17."""

    def test_home_and_discovery_share_reference_width(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('.block-container{max-width:860px !important', app)
        self.assertIn('.block-container{max-width:860px !important', src)

    def test_sidebar_is_compact_without_selected_row_pill(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('min-height:2.48rem !important', app)
        self.assertIn('button[kind="primary"]{background:transparent !important', app)
        self.assertIn('width:1.92rem !important', app)

    def test_cards_are_white_compact_and_ctas_blue(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('border:0 !important;border-radius:10px', src)
        self.assertIn('background:#2E5FEA !important', src)
        self.assertIn('font-size:1.42rem !important', src)

    def test_old_teal_form_override_is_removed(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        tail = src.split("/* RC31.17 faithful discovery layout */", 1)[1]
        self.assertNotIn('background:#0E8B82', tail)
        self.assertNotIn('background:#0A746D', tail)


if __name__ == "__main__":
    unittest.main()
