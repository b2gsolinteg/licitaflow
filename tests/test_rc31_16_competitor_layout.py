from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3116CompetitorLayoutContracts(unittest.TestCase):
    def test_version_tracks_current_reference_release(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.20"', cfg)

    def test_global_shell_is_compact_and_reference_aligned(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("/* RC31.16 competitor-inspired global shell */", app)
        self.assertEqual(app.count("/* RC31.18 exact reference shell */"), 1)
        self.assertIn('background:var(--ref-navy) !important', app)
        self.assertIn('width:240px !important', app)
        self.assertIn('max-width:860px !important', app)
        self.assertIn('--ref-blue:#2D5FE8', app)

    def test_discovery_cards_use_blue_ctas_and_compact_grid(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("/* RC31.18 exact discovery cards */"), 1)
        self.assertIn(':has(.ln-modality-name)', src)
        self.assertIn('background:#2D5FE8 !important', src)
        self.assertIn('"Ver licitações"', src)
        self.assertNotIn('"Ver oportunidades"', src)
        self.assertIn('for start_index in range(0, len(counts), 3):', src)

    def test_existing_navigation_and_search_logic_are_preserved(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        for label in ("Buscar licitações", "Por Estado", "Por Cidade", "Por Modalidade", "Por site de disputa"):
            self.assertIn(label, app)
        self.assertIn('st.session_state["essential_search_criteria"]', src)
        self.assertIn('st.session_state["_navigation_request"] = "Buscar licitações"', src)


if __name__ == "__main__":
    unittest.main()
