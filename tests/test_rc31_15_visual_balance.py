from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3115VisualBalanceContracts(unittest.TestCase):
    def test_version_tracks_current_rc31_release(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.19"', cfg)

    def test_legacy_balance_blocks_are_replaced_by_single_reference_layer(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertNotIn("/* RC31.15 visual balance */", src)
        self.assertNotIn("/* RC31.16 discovery grid */", src)
        self.assertNotIn("/* RC31.17 faithful discovery layout */", src)
        self.assertEqual(src.count("/* RC31.18 exact discovery cards */"), 1)
        self.assertIn('max-width:860px !important', src)

    def test_primary_form_cta_is_blue_and_high_contrast(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('div[data-testid="stFormSubmitButton"] button{background:#2D5FE8', src)
        self.assertIn('button *{color:#FFFFFF !important', src)

    def test_material_icons_keep_streamlit_font(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertNotIn('[data-testid="stMain"] *{font-family:', src)


if __name__ == "__main__":
    unittest.main()
