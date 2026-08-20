from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3115VisualBalanceContracts(unittest.TestCase):
    def test_version_is_rc3115(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.15"', cfg)

    def test_visual_balance_reduces_empty_chrome_and_recovers_width(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("/* RC31.15 visual balance */"), 1)
        self.assertIn('height:36px !important', src)
        self.assertIn('background:#FFFFFF !important;border-bottom:1px solid #E6EBEF', src)
        self.assertIn('max-width:980px !important', src)
        self.assertNotIn('/* RC31.14 density polish */', src)

    def test_primary_form_cta_is_explicit_and_high_contrast(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('div[data-testid="stFormSubmitButton"] button{background:#0E8B82', src)
        self.assertIn('div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF', src)
        self.assertIn('background:#0A746D !important', src)

    def test_state_density_and_material_icons_remain_preserved(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('width:42px !important', src)
        self.assertIn('min-height:2.25rem !important', src)
        self.assertNotIn('[data-testid="stMain"] *{font-family:', src)


if __name__ == "__main__":
    unittest.main()
