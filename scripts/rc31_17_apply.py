from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
DISCOVERY = ROOT / "src" / "essential_discovery.py"
CONFIG = ROOT / "src" / "config.py"
TESTS = ROOT / "tests"


def replace_style_tail(path: Path, function_name: str, marker: str, css: str) -> None:
    text = path.read_text(encoding="utf-8")
    fn = text.find(f"def {function_name}(")
    if fn < 0:
        raise SystemExit(f"{path}: função {function_name} não encontrada")
    next_fn = text.find("\ndef ", fn + 5)
    if next_fn < 0:
        next_fn = len(text)
    marker_pos = text.find(marker, fn, next_fn)
    if marker_pos < 0:
        raise SystemExit(f"{path}: marcador {marker!r} não encontrado")
    style_end = text.find("        </style>", marker_pos, next_fn)
    if style_end < 0:
        raise SystemExit(f"{path}: fechamento </style> não encontrado")
    text = text[:marker_pos] + css + "\n" + text[style_end:]
    path.write_text(text, encoding="utf-8")


APP_CSS = r'''/* RC31.17 faithful reference shell */
        :root{--ln17-navy:#0A1E36;--ln17-blue:#2E5FEA;--ln17-blue-hover:#244FD0;--ln17-bg:#F1F4F8;--ln17-card:#FFFFFF;--ln17-border:#E6EBF1;--ln17-text:#17212B;--ln17-muted:#667485;}
        html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{font-family:"Poppins","Inter","Segoe UI",Arial,sans-serif !important;color:var(--ln17-text) !important;}
        header[data-testid="stHeader"]{display:block !important;height:48px !important;min-height:48px !important;background:var(--ln17-navy) !important;border:0 !important;box-shadow:0 2px 7px rgba(10,30,54,.12) !important;}
        [data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none !important;}
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--ln17-bg) !important;}
        [data-testid="stIconMaterial"],.material-symbols-rounded,.material-symbols-outlined{font-family:"Material Symbols Rounded","Material Symbols Outlined" !important;}
        .block-container{max-width:860px !important;padding:1.05rem 1rem 2rem !important;}
        [data-testid="stMain"] h1{font-size:1.28rem !important;line-height:1.2 !important;letter-spacing:-.018em !important;color:#111827 !important;font-weight:700 !important;}
        [data-testid="stMain"] h2{font-size:1.05rem !important;line-height:1.25 !important;color:#111827 !important;font-weight:700 !important;}
        [data-testid="stMain"] h3{font-size:.94rem !important;color:#111827 !important;font-weight:650 !important;}
        [data-testid="stMain"] p,[data-testid="stMain"] label p,[data-testid="stMain"] .stCaption p{color:var(--ln17-muted) !important;font-size:.79rem !important;}
        [data-testid="stSidebar"]{background:#FFFFFF !important;border-right:1px solid #E4E9EF !important;box-shadow:none !important;}
        @media(min-width:901px){[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:240px !important;min-width:240px !important;max-width:240px !important;}}
        [data-testid="stSidebar"] > div:first-child{overflow-y:auto !important;overflow-x:hidden !important;max-height:100vh !important;padding-bottom:.55rem !important;}
        [data-testid="stSidebar"] [data-testid="stImage"] img{width:128px !important;max-width:128px !important;margin:.05rem auto 0 !important;display:block !important;}
        [data-testid="stSidebar"] .stButton button{width:100% !important;min-height:2.48rem !important;justify-content:flex-start !important;background:transparent !important;color:#1F2937 !important;border:0 !important;border-radius:8px !important;box-shadow:none !important;padding:.18rem .34rem !important;gap:.48rem !important;font-size:.79rem !important;font-weight:600 !important;transition:background .12s ease !important;}
        [data-testid="stSidebar"] .stButton button:hover{background:#F6F8FA !important;border:0 !important;transform:none !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:transparent !important;color:#111827 !important;border:0 !important;box-shadow:none !important;font-weight:700 !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{display:inline-flex !important;align-items:center !important;justify-content:center !important;flex:0 0 1.92rem !important;width:1.92rem !important;height:1.92rem !important;border-radius:9px !important;background:#F1F4F7 !important;color:#5B6D7E !important;font-size:.98rem !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"] [data-testid="stIconMaterial"]{background:#DDF8E6 !important;color:#25A65A !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_0 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_1 [data-testid="stIconMaterial"]{background:#DDF8E6 !important;color:#25A65A !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_2 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_3 [data-testid="stIconMaterial"]{background:#E4EEFF !important;color:#3D73DF !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_4 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_5 [data-testid="stIconMaterial"]{background:#EFE8FF !important;color:#8158C9 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_6 [data-testid="stIconMaterial"]{background:#FFF2CF !important;color:#D68B1E !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_7 [data-testid="stIconMaterial"]{background:#FFE7E7 !important;color:#C65A65 !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{margin-top:.46rem !important;margin-bottom:.04rem !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.58rem !important;font-weight:700 !important;letter-spacing:.10em !important;text-transform:uppercase !important;color:#98A4B1 !important;}
        [data-testid="stSidebar"] div[style*="background:#F6F9FA"]{padding:.45rem .55rem !important;margin:.08rem 0 .42rem !important;border-radius:9px !important;}
        div[data-testid="stVerticalBlockBorderWrapper"],div[data-testid="stMetric"]{background:var(--ln17-card) !important;border:1px solid var(--ln17-border) !important;border-radius:11px !important;box-shadow:0 4px 11px rgba(22,39,60,.055) !important;}
        [data-testid="stForm"]{background:#FFFFFF !important;border:1px solid var(--ln17-border) !important;border-radius:11px !important;padding:.72rem .78rem .68rem !important;box-shadow:0 4px 11px rgba(22,39,60,.045) !important;}
        [data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"] > div,textarea{background:#FFFFFF !important;color:#263544 !important;border-color:#DCE3EA !important;border-radius:7px !important;box-shadow:none !important;}
        input,textarea{background:#FFFFFF !important;color:#263544 !important;-webkit-text-fill-color:#263544 !important;font-size:.8rem !important;}
        [data-testid="stMain"] .stButton>button,[data-testid="stMain"] .stDownloadButton>button{min-height:2.25rem !important;background:#FFFFFF !important;color:#263544 !important;border:1px solid #D7DFE8 !important;border-radius:7px !important;box-shadow:none !important;font-size:.78rem !important;font-weight:600 !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"],[data-testid="stMain"] .stDownloadButton>button[kind="primary"],[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button{background:var(--ln17-blue) !important;color:#FFFFFF !important;border-color:var(--ln17-blue) !important;box-shadow:0 2px 5px rgba(46,95,234,.20) !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"] *,[data-testid="stMain"] .stDownloadButton>button[kind="primary"] *,[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"]:hover,[data-testid="stMain"] .stDownloadButton>button[kind="primary"]:hover,[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button:hover{background:var(--ln17-blue-hover) !important;border-color:var(--ln17-blue-hover) !important;}
        [data-testid="stTabs"] [data-baseweb="tab-list"]{gap:.18rem !important;border-bottom:1px solid #E3E8EF !important;}
        [data-testid="stTabs"] button{font-size:.78rem !important;font-weight:600 !important;}
        [data-testid="stExpander"]{background:#FFFFFF !important;border:1px solid var(--ln17-border) !important;border-radius:9px !important;}
        [data-testid="stAlert"]{border-radius:9px !important;}
        [data-testid="stDataFrame"],[data-testid="stTable"]{background:#FFFFFF !important;border-radius:9px !important;overflow:hidden !important;}
        hr{border-color:#E5EAF0 !important;}
        @media(max-width:900px){header[data-testid="stHeader"]{height:44px !important;min-height:44px !important;}[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:225px !important;min-width:225px !important;max-width:225px !important;}.block-container{max-width:100% !important;padding:.75rem .65rem 1.5rem !important;}}
'''

DISCOVERY_CSS = r'''        /* RC31.17 faithful discovery layout */
        header[data-testid="stHeader"]{height:48px !important;min-height:48px !important;background:#0A1E36 !important;border:0 !important;box-shadow:0 2px 7px rgba(10,30,54,.12) !important;}
        [data-testid="stMain"]{background:#F1F4F8 !important;}
        [data-testid="stMain"] .block-container{max-width:860px !important;padding-top:1.05rem !important;padding-bottom:1.8rem !important;}
        .ln-page-kicker{display:inline-flex !important;background:#DCFCE7 !important;color:#218A4B !important;border:1px solid #C7F0D3 !important;border-radius:999px !important;padding:.14rem .42rem !important;font-size:.54rem !important;font-weight:700 !important;letter-spacing:.055em !important;margin-bottom:.34rem !important;}
        .ln-discovery-title{font-size:1.22rem !important;line-height:1.18 !important;margin:0 0 .18rem !important;color:#111827 !important;font-weight:700 !important;letter-spacing:-.015em !important;}
        .ln-discovery-sub{font-size:.77rem !important;line-height:1.42 !important;color:#657386 !important;margin:0 0 .68rem !important;max-width:49rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{background:#FFFFFF !important;border:1px solid #E6EBF1 !important;border-radius:11px !important;box-shadow:0 4px 11px rgba(22,39,60,.055) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] > div{padding:.62rem .68rem !important;}
        [data-testid="stMain"] [data-testid="stForm"]{background:#FFFFFF !important;border:1px solid #E6EBF1 !important;border-radius:11px !important;padding:.7rem .76rem .66rem !important;box-shadow:0 4px 11px rgba(22,39,60,.045) !important;}
        [data-testid="stMain"] div[data-testid="stFormSubmitButton"] button{background:#2E5FEA !important;color:#FFFFFF !important;border:1px solid #2E5FEA !important;border-radius:7px !important;box-shadow:0 2px 5px rgba(46,95,234,.20) !important;font-size:.78rem !important;font-weight:650 !important;min-height:2.28rem !important;}
        [data-testid="stMain"] div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF !important;}
        [data-testid="stMain"] div[data-testid="stFormSubmitButton"] button:hover{background:#244FD0 !important;border-color:#244FD0 !important;}
        .ln-home-count{font-size:1.28rem !important;color:#0B3A72 !important;margin:.1rem 0 .52rem !important;font-weight:700 !important;}
        .ln-home-value{background:#FFFFFF !important;border:1px solid #E6EBF1 !important;border-left:3px solid #28A889 !important;border-radius:9px !important;padding:.6rem .7rem !important;margin:.4rem 0 .68rem !important;color:#566679 !important;font-size:.76rem !important;line-height:1.4 !important;box-shadow:0 3px 9px rgba(22,39,60,.035) !important;}
        .ln-home-section,.ln-state-grid-title{font-size:.58rem !important;color:#7C8998 !important;font-weight:700 !important;letter-spacing:.08em !important;text-transform:uppercase !important;margin:.66rem 0 .32rem !important;}
        .ln-shortcut-copy{min-height:1.45rem !important;font-size:.67rem !important;line-height:1.3 !important;color:#6F7D8D !important;margin:0 0 .3rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-copy){border-radius:9px !important;box-shadow:none !important;}
        .ln-state-name,.ln-modality-name,.ln-portal-name{font-size:.82rem !important;line-height:1.2 !important;color:#111827 !important;font-weight:700 !important;margin:.02rem 0 .08rem !important;}
        .ln-state-code{font-size:.66rem !important;color:#748296 !important;font-weight:600 !important;}
        .ln-state-count,.ln-card-count{font-size:1.42rem !important;color:#0B3A72 !important;font-weight:700 !important;line-height:1 !important;margin:.48rem 0 .04rem !important;}
        .ln-state-label,.ln-card-caption{font-size:.67rem !important;color:#718095 !important;margin-bottom:.48rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name),[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-modality-name),[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-portal-name){border:0 !important;border-radius:10px !important;box-shadow:0 4px 12px rgba(18,36,58,.075) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) [data-testid="stImage"]{display:none !important;}
        [data-testid="stMain"] div[class*="st-key-state_"] button,[data-testid="stMain"] div[class*="st-key-modality_"] button,[data-testid="stMain"] div[class*="st-key-portal_"] button{min-height:2.18rem !important;background:#2E5FEA !important;color:#FFFFFF !important;border:1px solid #2E5FEA !important;border-radius:7px !important;box-shadow:0 2px 5px rgba(46,95,234,.18) !important;font-size:.73rem !important;font-weight:650 !important;}
        [data-testid="stMain"] div[class*="st-key-state_"] button *,[data-testid="stMain"] div[class*="st-key-modality_"] button *,[data-testid="stMain"] div[class*="st-key-portal_"] button *{color:#FFFFFF !important;}
        [data-testid="stMain"] div[class*="st-key-state_"] button:hover,[data-testid="stMain"] div[class*="st-key-modality_"] button:hover,[data-testid="stMain"] div[class*="st-key-portal_"] button:hover{background:#244FD0 !important;border-color:#244FD0 !important;}
        .ln-reference{font-size:.92rem !important;color:#17212B !important;margin:.28rem 0 .45rem !important;font-weight:650 !important;}
        .ln-info-grid{gap:.42rem !important;margin:.12rem 0 .56rem !important;}
        .ln-info-box,.ln-meta-box{background:#F8FAFC !important;border:1px solid #E6EBF1 !important;border-radius:8px !important;padding:.5rem .55rem !important;min-height:62px !important;}
        .ln-info-label,.ln-meta-label{font-size:.57rem !important;color:#7B8797 !important;}
        .ln-info-value,.ln-meta-value{font-size:.74rem !important;color:#263544 !important;}
        .ln-info-extra,.ln-meta-help{font-size:.62rem !important;color:#778596 !important;}
        .ln-items-box{border-radius:8px !important;padding:.58rem .62rem !important;margin:.5rem 0 !important;}
        .ln-item-row{grid-template-columns:42px minmax(0,1fr) 108px 112px !important;gap:.38rem !important;padding:.36rem .04rem !important;}
        .ln-item-desc{font-size:.7rem !important}.ln-item-number,.ln-item-qty,.ln-item-price{font-size:.64rem !important;}
        @media(max-width:900px){[data-testid="stMain"] .block-container{max-width:100% !important;padding:.75rem .65rem 1.5rem !important;}.ln-discovery-title{font-size:1.12rem !important;}.ln-info-grid{grid-template-columns:repeat(2,minmax(0,1fr)) !important;}}
'''

replace_style_tail(APP, "apply_brand", "/* RC31.16 competitor-inspired global shell */", APP_CSS)
replace_style_tail(DISCOVERY, "_apply_styles", "/* RC31.15 visual balance */", DISCOVERY_CSS)

cfg = CONFIG.read_text(encoding="utf-8")
if 'APP_VERSION = "1.0 Essential RC31.16"' not in cfg:
    raise SystemExit("config.py não está em RC31.16")
CONFIG.write_text(cfg.replace('APP_VERSION = "1.0 Essential RC31.16"', 'APP_VERSION = "1.0 Essential RC31.17"', 1), encoding="utf-8")

for path in TESTS.glob("test_*.py"):
    text = path.read_text(encoding="utf-8")
    text = text.replace('APP_VERSION = "1.0 Essential RC31.16"', 'APP_VERSION = "1.0 Essential RC31.17"')
    path.write_text(text, encoding="utf-8")

(TESTS / "test_rc31_15_visual_balance.py").write_text('''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass Rc3115VisualBalanceContracts(unittest.TestCase):\n    def test_version_tracks_current_rc31_release(self):\n        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")\n        self.assertIn('APP_VERSION = "1.0 Essential RC31.17"', cfg)\n\n    def test_legacy_balance_block_is_replaced_by_single_faithful_layer(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertNotIn("/* RC31.15 visual balance */", src)\n        self.assertNotIn("/* RC31.16 discovery grid */", src)\n        self.assertEqual(src.count("/* RC31.17 faithful discovery layout */"), 1)\n        self.assertIn('max-width:860px !important', src)\n\n    def test_primary_form_cta_is_blue_and_high_contrast(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('div[data-testid="stFormSubmitButton"] button{background:#2E5FEA', src)\n        self.assertIn('button *{color:#FFFFFF !important', src)\n\n    def test_material_icons_keep_streamlit_font(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertNotIn('[data-testid="stMain"] *{font-family:', src)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

(TESTS / "test_rc31_16_competitor_layout.py").write_text('''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass Rc3116CompetitorLayoutContracts(unittest.TestCase):\n    def test_version_tracks_rc3117(self):\n        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")\n        self.assertIn('APP_VERSION = "1.0 Essential RC31.17"', cfg)\n\n    def test_global_shell_is_compact_and_reference_aligned(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertNotIn("/* RC31.16 competitor-inspired global shell */", app)\n        self.assertEqual(app.count("/* RC31.17 faithful reference shell */"), 1)\n        self.assertIn('background:var(--ln17-navy) !important', app)\n        self.assertIn('width:240px !important', app)\n        self.assertIn('max-width:860px !important', app)\n        self.assertIn('--ln17-blue:#2E5FEA', app)\n\n    def test_discovery_cards_use_blue_ctas_and_compact_grid(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertEqual(src.count("/* RC31.17 faithful discovery layout */"), 1)\n        self.assertIn(':has(.ln-modality-name)', src)\n        self.assertIn('div[class*="st-key-modality_"] button', src)\n        self.assertIn('background:#2E5FEA !important', src)\n        self.assertIn('"Ver licitações"', src)\n        self.assertNotIn('"Ver oportunidades"', src)\n        self.assertIn('for start_index in range(0, len(counts), 3):', src)\n\n    def test_existing_navigation_and_search_logic_are_preserved(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        for label in ("Buscar licitações", "Por Estado", "Por Cidade", "Por Modalidade", "Por site de disputa"):\n            self.assertIn(label, app)\n        self.assertIn('st.session_state["essential_search_criteria"]', src)\n        self.assertIn('st.session_state["_navigation_request"] = "Buscar licitações"', src)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

(TESTS / "test_rc31_17_faithful_layout.py").write_text('''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass Rc3117FaithfulLayoutContracts(unittest.TestCase):\n    def test_home_and_discovery_share_reference_width(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('.block-container{max-width:860px !important', app)\n        self.assertIn('.block-container{max-width:860px !important', src)\n\n    def test_sidebar_is_compact_without_selected_row_pill(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn('min-height:2.48rem !important', app)\n        self.assertIn('button[kind="primary"]{background:transparent !important', app)\n        self.assertIn('width:1.92rem !important', app)\n\n    def test_cards_are_white_compact_and_ctas_blue(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('border:0 !important;border-radius:10px', src)\n        self.assertIn('background:#2E5FEA !important', src)\n        self.assertIn('font-size:1.42rem !important', src)\n\n    def test_old_teal_form_override_is_removed(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        tail = src.split("/* RC31.17 faithful discovery layout */", 1)[1]\n        self.assertNotIn('background:#0E8B82', tail)\n        self.assertNotIn('background:#0A746D', tail)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

print("RC31.17 aplicada: layout fiel, camada conflitante removida e lógica preservada")
