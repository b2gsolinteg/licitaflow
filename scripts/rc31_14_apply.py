from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: esperado 1 ocorrência, encontrado {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


essential = ROOT / "src" / "essential_discovery.py"
config = ROOT / "src" / "config.py"
test_premium = ROOT / "tests" / "test_rc31_13_premium_ui.py"
test_discovery = ROOT / "tests" / "test_rc31_9_simple_discovery.py"
test_density = ROOT / "tests" / "test_rc31_14_density.py"

source = essential.read_text(encoding="utf-8")
marker = "/* RC31.14 density polish */"
if marker in source:
    raise SystemExit("RC31.14 já foi aplicada")

anchor = "        @media(max-width:900px){.ln-info-grid,.ln-meta-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.ln-item-row{grid-template-columns:38px minmax(0,1fr)}.ln-item-qty,.ln-item-price{text-align:left;grid-column:2}.ln-discovery-title{font-size:1.72rem}}"

density_css = r'''        /* RC31.14 density polish */
        header[data-testid="stHeader"]{height:44px !important;min-height:44px !important;box-shadow:0 1px 8px rgba(7,29,48,.08) !important;}
        [data-testid="stMain"]{background:#F3F6F9 !important;}
        [data-testid="stMain"] .block-container{max-width:900px !important;padding-top:.78rem !important;padding-bottom:1.8rem !important;}
        [data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:240px !important;min-width:240px !important;max-width:240px !important;}
        [data-testid="stSidebar"] > div:first-child{padding-bottom:.7rem !important;}
        [data-testid="stSidebar"] [data-testid="stImage"] img{max-width:154px !important;width:154px !important;margin:.08rem auto 0 !important;}
        [data-testid="stSidebar"] .stButton button{min-height:2.85rem !important;border-radius:10px !important;padding:.24rem .42rem !important;gap:.55rem !important;font-size:.84rem !important;font-weight:650 !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{flex:0 0 2.15rem !important;width:2.15rem !important;height:2.15rem !important;border-radius:9px !important;font-size:1.08rem !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#F3F8F7 !important;border-color:#DCEAE7 !important;box-shadow:inset 3px 0 0 #13877F !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{margin-top:.46rem !important;margin-bottom:.08rem !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.64rem !important;letter-spacing:.09em !important;}
        [data-testid="stSidebar"] div[style*="background:#F6F9FA"]{padding:.52rem .6rem !important;margin:.1rem 0 .52rem !important;border-radius:10px !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px !important;border-color:#E7EBEF !important;box-shadow:0 4px 14px rgba(30,52,69,.05) !important;}
        [data-testid="stMain"] [data-testid="stForm"]{border-radius:12px !important;padding:.78rem .82rem .72rem !important;box-shadow:0 4px 14px rgba(30,52,69,.04) !important;}
        .ln-page-kicker{padding:.18rem .48rem !important;font-size:.61rem !important;margin-bottom:.38rem !important;}
        .ln-discovery-title{font-size:1.62rem !important;line-height:1.1 !important;margin:0 0 .18rem !important;letter-spacing:-.02em !important;}
        .ln-discovery-sub{font-size:.88rem !important;line-height:1.42 !important;margin:0 0 .7rem !important;max-width:48rem !important;}
        .ln-home-count{font-size:1.34rem !important;margin:.08rem 0 .55rem !important;}
        .ln-home-value{padding:.66rem .78rem !important;margin:.4rem 0 .72rem !important;border-radius:11px !important;font-size:.84rem !important;line-height:1.42 !important;}
        .ln-home-section{font-size:.66rem !important;margin:.72rem 0 .36rem !important;}
        .ln-shortcut-copy{min-height:1.72rem !important;font-size:.71rem !important;line-height:1.3 !important;margin:0 0 .35rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-copy){border-radius:11px !important;box-shadow:0 3px 10px rgba(30,52,69,.035) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-copy) > div{padding:.62rem .68rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name){border:1px solid #E7EBEF !important;border-radius:12px !important;box-shadow:0 5px 15px rgba(30,52,69,.055) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) > div{padding:.66rem .72rem .7rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) [data-testid="stImage"] img{width:42px !important;max-width:42px !important;}
        [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.ln-state-name){gap:.68rem !important;}
        .ln-state-name{font-size:.93rem !important;margin:.2rem 0 0 !important;}
        .ln-state-code{font-size:.7rem !important;}
        .ln-state-count{font-size:1.48rem !important;margin:.48rem 0 .02rem !important;}
        .ln-state-label{font-size:.7rem !important;margin-bottom:.4rem !important;}
        .ln-state-grid-title{font-size:.66rem !important;margin:.62rem 0 .36rem !important;}
        [data-testid="stMain"] .block-container .stButton button,[data-testid="stMain"] .block-container .stDownloadButton button{min-height:2.3rem !important;border-radius:9px !important;font-size:.82rem !important;}
        [data-testid="stMain"] .block-container div[class*="st-key-state_"] button{min-height:2.25rem !important;}
        [data-testid="stMain"] .block-container .stButton button[kind="primary"] p,[data-testid="stMain"] .block-container .stButton button[kind="primary"] span{color:#FFFFFF !important;}
        .ln-info-grid{gap:.48rem !important;margin:.14rem 0 .65rem !important;}
        .ln-info-box,.ln-meta-box{padding:.6rem .64rem !important;min-height:70px !important;border-radius:10px !important;}
        .ln-reference{font-size:1rem !important;margin:.35rem 0 .55rem !important;}
        @media(max-width:900px){[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:230px !important;min-width:230px !important;max-width:230px !important;}[data-testid="stMain"] .block-container{max-width:100% !important;padding:.68rem .72rem 1.4rem !important;}.ln-discovery-title{font-size:1.45rem !important;}}
'''

if source.count(anchor) != 1:
    raise SystemExit("âncora CSS da RC31.13 não encontrada")
essential.write_text(source.replace(anchor, density_css + anchor, 1), encoding="utf-8")

replace_once(config, 'APP_VERSION = "1.0 Essential RC31.13"', 'APP_VERSION = "1.0 Essential RC31.14"')
replace_once(test_premium, 'APP_VERSION = "1.0 Essential RC31.13"', 'APP_VERSION = "1.0 Essential RC31.14"')
replace_once(test_discovery, 'APP_VERSION = "1.0 Essential RC31.13"', 'APP_VERSION = "1.0 Essential RC31.14"')

test_density.write_text('''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass Rc3114DensityContracts(unittest.TestCase):\n    def test_version_is_rc3114(self):\n        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")\n        self.assertIn('APP_VERSION = "1.0 Essential RC31.14"', cfg)\n\n    def test_density_layer_is_single_and_compact(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertEqual(src.count("/* RC31.14 density polish */"), 1)\n        self.assertIn('max-width:900px !important', src)\n        self.assertIn('width:240px !important', src)\n        self.assertIn('height:44px !important', src)\n        self.assertIn('min-height:2.85rem !important', src)\n\n    def test_state_cards_are_compact_without_removing_flags(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn(':has(.ln-state-name)', src)\n        self.assertIn('width:42px !important', src)\n        self.assertIn('font-size:1.48rem !important', src)\n        self.assertIn('min-height:2.25rem !important', src)\n        self.assertIn('FLAGS_DIR / f"{state.lower()}.svg"', src)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

print("RC31.14 density polish materializada nos arquivos reais")
