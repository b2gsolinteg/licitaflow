from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3116CompetitorLayoutContracts(unittest.TestCase):
    def test_version_is_rc3116(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.16"', cfg)

    def test_global_shell_is_compact_and_consistent_on_all_pages(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertEqual(app.count("/* RC31.16 competitor-inspired global shell */"), 1)
        self.assertIn('background:var(--ln16-navy) !important', app)
        self.assertIn('width:240px !important', app)
        self.assertIn('max-width:1040px !important', app)
        self.assertIn('--ln16-blue:#2563EB', app)
        self.assertIn('[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button', app)

    def test_discovery_grids_use_rectangular_cards_and_blue_ctas(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("/* RC31.16 discovery grid */"), 1)
        self.assertIn(':has(.ln-modality-name)', src)
        self.assertIn('div[class*="st-key-modality_"] button', src)
        self.assertIn('background:#2563EB !important', src)
        self.assertIn('"Ver licitações"', src)
        self.assertNotIn('"Ver oportunidades"', src)
        self.assertIn('for start_index in range(0, len(counts), 3):', src)

    def test_existing_navigation_and_search_logic_are_preserved(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('"Buscar licitações"', app)
        self.assertIn('"Por Estado"', app)
        self.assertIn('"Por Cidade"', app)
        self.assertIn('"Por Modalidade"', app)
        self.assertIn('"Por site de disputa"', app)
        self.assertIn('st.session_state["essential_search_criteria"]', src)
        self.assertIn('st.session_state["_navigation_request"] = "Buscar licitações"', src)

    def test_release_is_materialized_without_one_time_generator(self):
        self.assertFalse((ROOT / "scripts" / "rc31_16_apply.py").exists())
        self.assertFalse((ROOT / ".github" / "workflows" / "rc31-16-materialize.yml").exists())


if __name__ == "__main__":
    unittest.main()
