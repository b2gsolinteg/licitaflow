from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESSENTIAL = ROOT / "src" / "essential_discovery.py"
CONFIG = ROOT / "src" / "config.py"
TESTS = ROOT / "tests"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: esperado 1 ocorrência, encontrado {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


source = ESSENTIAL.read_text(encoding="utf-8")
if "/* RC31.15 visual balance */" in source:
    raise SystemExit("RC31.15 já foi aplicada")

replace_once(
    ESSENTIAL,
    '        /* RC31.14 density polish */',
    '        /* RC31.15 visual balance */',
)
replace_once(
    ESSENTIAL,
    '        header[data-testid="stHeader"]{height:44px !important;min-height:44px !important;box-shadow:0 1px 8px rgba(7,29,48,.08) !important;}',
    '        header[data-testid="stHeader"]{height:36px !important;min-height:36px !important;background:#FFFFFF !important;border-bottom:1px solid #E6EBEF !important;box-shadow:none !important;}',
)
replace_once(
    ESSENTIAL,
    '        [data-testid="stMain"] .block-container{max-width:900px !important;padding-top:.78rem !important;padding-bottom:1.8rem !important;}',
    '        [data-testid="stMain"] .block-container{max-width:980px !important;padding-top:.82rem !important;padding-bottom:1.8rem !important;}',
)
replace_once(
    ESSENTIAL,
    '        .ln-discovery-title{font-size:1.62rem !important;line-height:1.1 !important;margin:0 0 .18rem !important;letter-spacing:-.02em !important;}',
    '        .ln-discovery-title{font-size:1.68rem !important;line-height:1.1 !important;margin:0 0 .2rem !important;letter-spacing:-.022em !important;}',
)
replace_once(
    ESSENTIAL,
    '        .ln-shortcut-copy{min-height:1.72rem !important;font-size:.71rem !important;line-height:1.3 !important;margin:0 0 .35rem !important;}',
    '        .ln-shortcut-copy{min-height:1.72rem !important;font-size:.73rem !important;line-height:1.34 !important;margin:0 0 .38rem !important;}',
)
replace_once(
    ESSENTIAL,
    '        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-copy){border-radius:11px !important;box-shadow:0 3px 10px rgba(30,52,69,.035) !important;}',
    '        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-copy){background:#FFFFFF !important;border-color:#E1E8EC !important;border-radius:11px !important;box-shadow:0 4px 12px rgba(30,52,69,.05) !important;}',
)

anchor = '        [data-testid="stMain"] .block-container .stButton button[kind="primary"] p,[data-testid="stMain"] .block-container .stButton button[kind="primary"] span{color:#FFFFFF !important;}'
addition = anchor + '''\n        [data-testid="stMain"] .block-container div[data-testid="stFormSubmitButton"] button{background:#0E8B82 !important;color:#FFFFFF !important;border:1px solid #0E8B82 !important;border-radius:9px !important;box-shadow:0 4px 10px rgba(14,139,130,.16) !important;font-weight:700 !important;}\n        [data-testid="stMain"] .block-container div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF !important;}\n        [data-testid="stMain"] .block-container div[data-testid="stFormSubmitButton"] button:hover{background:#0A746D !important;border-color:#0A746D !important;}\n        [data-testid="stMain"] .block-container div[data-testid="stFormSubmitButton"] button:focus{box-shadow:0 0 0 3px rgba(14,139,130,.14) !important;}'''
replace_once(ESSENTIAL, anchor, addition)

replace_once(CONFIG, 'APP_VERSION = "1.0 Essential RC31.14"', 'APP_VERSION = "1.0 Essential RC31.15"')

for test_path in TESTS.glob("test_*.py"):
    text = test_path.read_text(encoding="utf-8")
    updated = text.replace('APP_VERSION = "1.0 Essential RC31.14"', 'APP_VERSION = "1.0 Essential RC31.15"')
    if updated != text:
        test_path.write_text(updated, encoding="utf-8")

old_density_test = TESTS / "test_rc31_14_density.py"
if old_density_test.exists():
    old_density_test.unlink()

(TESTS / "test_rc31_15_visual_balance.py").write_text(
    '''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass Rc3115VisualBalanceContracts(unittest.TestCase):\n    def test_version_is_rc3115(self):\n        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")\n        self.assertIn('APP_VERSION = "1.0 Essential RC31.15"', cfg)\n\n    def test_visual_balance_reduces_empty_chrome_and_recovers_width(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertEqual(src.count("/* RC31.15 visual balance */"), 1)\n        self.assertIn('height:36px !important', src)\n        self.assertIn('background:#FFFFFF !important;border-bottom:1px solid #E6EBEF', src)\n        self.assertIn('max-width:980px !important', src)\n        self.assertNotIn('/* RC31.14 density polish */', src)\n\n    def test_primary_form_cta_is_explicit_and_high_contrast(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('div[data-testid="stFormSubmitButton"] button{background:#0E8B82', src)\n        self.assertIn('div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF', src)\n        self.assertIn('background:#0A746D !important', src)\n\n    def test_state_density_and_material_icons_remain_preserved(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('width:42px !important', src)\n        self.assertIn('min-height:2.25rem !important', src)\n        self.assertNotIn('[data-testid="stMain"] *{font-family:', src)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
    encoding="utf-8",
)

print("RC31.15 visual balance materializada nos arquivos reais")
