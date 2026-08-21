from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3119NavigationDensityContracts(unittest.TestCase):
    def test_version(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.19"', cfg)

    def test_sidebar_is_wider_and_readable(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("/* RC31.19 navigation density */", app)
        self.assertIn("--rc19-sidebar:276px", app)
        self.assertIn("font-size:.96rem !important", app)
        self.assertIn("ln-home-color-logo", app)

    def test_internal_pages_have_back_navigation(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('st.button("Voltar", icon=":material/arrow_back:"', src)
        for fn in ("portal_page", "search_page", "state_page", "city_page", "modality_page", "advanced_search_page"):
            self.assertIn(f'_render_back_button("{fn}")', src)

    def test_home_shortcuts_have_visual_figures(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn("ln-shortcut-state", src)
        self.assertIn("ln-shortcut-city", src)
        self.assertIn("ln-shortcut-modality", src)
        self.assertIn("ln-shortcut-site", src)
        self.assertIn("_shortcut_illustration(target)", src)


if __name__ == "__main__":
    unittest.main()
