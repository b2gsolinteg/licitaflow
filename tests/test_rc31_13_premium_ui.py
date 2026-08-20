from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PremiumUiContracts(unittest.TestCase):
    def test_version(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.14"', cfg)

    def test_sidebar_has_large_pastel_icon_tiles_and_sections(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('width:2.75rem !important', app)
        self.assertIn('min-height:3.55rem !important', app)
        self.assertIn('_nav_group("MINHA CONTA", account_pages, "account")', app)
        self.assertIn('"Radar de licitações": ":material/radar:"', app)
        self.assertIn('"Minha lista": ":material/bookmark:"', app)

    def test_internal_app_uses_depth_and_strong_typography(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('background:#F4F7FA !important', src)
        self.assertIn('font-weight:750 !important', src)
        self.assertIn('box-shadow:0 5px 18px', src)
        self.assertIn('background:#0E7C75 !important', src)

    def test_material_icons_keep_streamlit_font_and_primary_button_contrast(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertNotIn('[data-testid="stMain"] *{font-family:', src)
        self.assertIn('[data-testid="stMain"]{background:#F4F7FA !important;font-family:Inter', src)
        self.assertIn('.block-container .stButton button[kind="primary"] *', src)
        self.assertIn('.block-container .stDownloadButton button[kind="primary"] *', src)
        self.assertNotIn('[data-testid="stMain"] button[kind="primary"]{', src)

    def test_state_page_uses_real_flags_and_large_counts(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('FLAGS_DIR / f"{state.lower()}.svg"', src)
        self.assertIn('class="ln-state-count"', src)
        self.assertIn('"Ver oportunidades", icon=":material/arrow_forward:"', src)
        self.assertIn('for start_index in range(0, len(BRAZIL_STATES), 3):', src)

    def test_page_kickers_create_hierarchy(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('def _page_header', src)
        self.assertIn('"EXPLORAR LICITAÇÕES"', src)
        self.assertIn('"ENCONTRE OPORTUNIDADES"', src)
        self.assertIn('"ORGANIZE SUAS OPORTUNIDADES"', src)


if __name__ == "__main__":
    unittest.main()
