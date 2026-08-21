from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3118ReferenceShellContracts(unittest.TestCase):
    def test_reference_topbar_and_sidebar_are_not_empty(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("/* RC31.18 exact reference shell */", app)
        self.assertIn("ln-app-topbar-menu", app)
        self.assertIn("ln-app-topbar-account", app)
        self.assertIn("ln-sidebar-brand", app)
        self.assertIn("left:240px !important", app)

    def test_sidebar_matches_compact_reference_geometry(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("width:240px !important", app)
        self.assertIn("min-height:2.45rem !important", app)
        self.assertIn("position:fixed !important;left:12px !important;bottom:12px", app)
        self.assertIn("--ref-green:#20BF63", app)

    def test_discovery_cards_are_white_and_blue(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn("/* RC31.18 exact discovery cards */", src)
        self.assertIn("background:#2D5FE8 !important", src)
        self.assertIn('type="primary", width="stretch"', src)
        self.assertIn(':has(.ln-state-name) [data-testid="stImage"]{display:none !important;}', src)


if __name__ == "__main__":
    unittest.main()
