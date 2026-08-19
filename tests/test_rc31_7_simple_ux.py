from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SimpleUxContracts(unittest.TestCase):
    def test_discovery_uses_plain_language(self):
        text = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn("editais abertos para participação", text)
        self.assertIn("O que o governo quer comprar ou contratar", text)
        self.assertIn("Onde participar", text)
        self.assertNotIn("sem score e sem exigir CNAE", text)

    def test_state_buttons_are_readable(self):
        text = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('div[class*="st-key-state_"] button', text)
        self.assertIn("background:#FFFFFF !important;color:#293746 !important", text)
        self.assertIn("STATE_NAMES", text)
        self.assertIn("editais abertos", text)

    def test_sidebar_override_is_compact_and_selected_item_is_light(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("width:250px !important", app)
        self.assertIn("min-height:2.25rem !important", app)
        self.assertIn("background:#F0F4F5 !important", app)
        self.assertIn("max-width:190px !important", app)


if __name__ == "__main__":
    unittest.main()
