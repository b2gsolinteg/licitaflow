from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3120LayoutPolishContracts(unittest.TestCase):
    def test_version(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.20"', cfg)

    def test_logout_is_returned_to_sidebar_flow(self):
        src = (ROOT / "src" / "ui_polish_rc31_20.py").read_text(encoding="utf-8")
        self.assertIn("/* RC31.20 viewport polish */", src)
        self.assertIn('.st-key-sidebar_logout{', src)
        self.assertIn('position:relative !important', src)
        self.assertIn('width:100% !important', src)
        self.assertIn('bottom:auto !important', src)

    def test_notebook_sidebar_is_compact_without_losing_readability(self):
        src = (ROOT / "src" / "ui_polish_rc31_20.py").read_text(encoding="utf-8")
        self.assertIn('min-height:2.76rem !important', src)
        self.assertIn('@media(max-height:820px)', src)
        self.assertIn('font-size:.90rem !important', src)
        self.assertIn('width:2.08rem !important', src)

    def test_home_logo_gap_is_scoped_to_existing_logo_marker(self):
        src = (ROOT / "src" / "ui_polish_rc31_20.py").read_text(encoding="utf-8")
        self.assertIn('.ln-home-color-logo', src)
        self.assertIn(':has(.ln-home-color-logo)', src)
        self.assertIn('max-height:62px !important', src)
        self.assertIn('object-position:left center !important', src)

    def test_polish_is_loaded_before_logger_cache_short_circuit(self):
        src = (ROOT / "src" / "logging_setup.py").read_text(encoding="utf-8")
        self.assertIn('def _install_visual_polish()', src)
        self.assertIn('from .ui_polish_rc31_20 import install_rc31_20_polish', src)
        self.assertLess(src.index('_install_visual_polish()'), src.index('if logger.handlers:'))


if __name__ == "__main__":
    unittest.main()
