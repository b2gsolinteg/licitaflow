from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Rc3114DensityContracts(unittest.TestCase):
    def test_version_is_rc3114(self):
        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.14"', cfg)

    def test_density_layer_is_single_and_compact(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("/* RC31.14 density polish */"), 1)
        self.assertIn('max-width:900px !important', src)
        self.assertIn('width:240px !important', src)
        self.assertIn('height:44px !important', src)
        self.assertIn('min-height:2.85rem !important', src)

    def test_state_cards_are_compact_without_removing_flags(self):
        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn(':has(.ln-state-name)', src)
        self.assertIn('width:42px !important', src)
        self.assertIn('font-size:1.48rem !important', src)
        self.assertIn('min-height:2.25rem !important', src)
        self.assertIn('FLAGS_DIR / f"{state.lower()}.svg"', src)


if __name__ == "__main__":
    unittest.main()
