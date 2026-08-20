from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
DISCOVERY = ROOT / "src" / "essential_discovery.py"
CONFIG = ROOT / "src" / "config.py"
TESTS = ROOT / "tests"

GLOBAL_MARKER = "/* RC31.16 competitor-inspired global shell */"
DISCOVERY_MARKER = "/* RC31.16 discovery grid */"


def insert_before_style_end(path: Path, function_name: str, marker: str, css: str) -> None:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        raise SystemExit(f"{path}: {marker} já aplicado")
    start = text.find(f"def {function_name}(")
    if start < 0:
        raise SystemExit(f"{path}: função {function_name} não encontrada")
    next_def = text.find("\ndef ", start + 5)
    if next_def < 0:
        next_def = len(text)
    segment = text[start:next_def]
    style_end = segment.rfind("        </style>")
    if style_end < 0:
        raise SystemExit(f"{path}: fechamento </style> não encontrado em {function_name}")
    absolute = start + style_end
    text = text[:absolute] + css + "\n" + text[absolute:]
    path.write_text(text, encoding="utf-8")


global_css = r'''        /* RC31.16 competitor-inspired global shell */
        :root{--ln16-navy:#0B1F38;--ln16-blue:#2563EB;--ln16-blue-hover:#1D4ED8;--ln16-bg:#F1F4F8;--ln16-card:#FFFFFF;--ln16-border:#E1E7EE;--ln16-text:#17212B;--ln16-muted:#667485;}
        header[data-testid="stHeader"]{display:block !important;height:48px !important;min-height:48px !important;background:var(--ln16-navy) !important;border-bottom:0 !important;box-shadow:0 2px 7px rgba(11,31,56,.10) !important;}
        [data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none !important;}
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--ln16-bg) !important;color:var(--ln16-text) !important;}
        [data-testid="stIconMaterial"],.material-symbols-rounded,.material-symbols-outlined{font-family:"Material Symbols Rounded","Material Symbols Outlined" !important;}
        .block-container{max-width:1040px !important;padding:1.05rem 1.35rem 2.2rem !important;}
        [data-testid="stMain"] h1{font-size:1.72rem !important;line-height:1.15 !important;letter-spacing:-.025em !important;color:#111C28 !important;font-weight:750 !important;}
        [data-testid="stMain"] h2{font-size:1.28rem !important;line-height:1.2 !important;color:#17212B !important;font-weight:730 !important;}
        [data-testid="stMain"] h3{font-size:1.02rem !important;color:#17212B !important;font-weight:700 !important;}
        [data-testid="stMain"] p,[data-testid="stMain"] label p,[data-testid="stMain"] .stCaption p{color:var(--ln16-muted) !important;}
        [data-testid="stSidebar"]{background:#FFFFFF !important;border-right:1px solid #E2E8EE !important;box-shadow:2px 0 14px rgba(25,39,52,.035) !important;}
        @media(min-width:901px){[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:240px !important;min-width:240px !important;max-width:240px !important;}}
        [data-testid="stSidebar"] > div:first-child{overflow-y:auto !important;overflow-x:hidden !important;max-height:100vh !important;padding-bottom:.75rem !important;}
        [data-testid="stSidebar"] [data-testid="stImage"] img{width:142px !important;max-width:142px !important;margin:.18rem auto .05rem !important;display:block !important;}
        [data-testid="stSidebar"] .stButton button{width:100% !important;min-height:2.7rem !important;justify-content:flex-start !important;background:transparent !important;color:#243342 !important;border:1px solid transparent !important;border-radius:9px !important;box-shadow:none !important;padding:.25rem .45rem !important;gap:.55rem !important;font-size:.84rem !important;font-weight:650 !important;transition:background .15s ease,border-color .15s ease !important;}
        [data-testid="stSidebar"] .stButton button:hover{background:#F6F8FA !important;border-color:#E6EBF0 !important;transform:none !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#F1F7F6 !important;color:#0D5F5A !important;border-color:#D8EAE7 !important;box-shadow:inset 3px 0 0 #16877F !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{display:inline-flex !important;align-items:center !important;justify-content:center !important;flex:0 0 2.05rem !important;width:2.05rem !important;height:2.05rem !important;border-radius:9px !important;background:#F2F5F7 !important;color:#58717F !important;font-size:1.03rem !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_0 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_1 [data-testid="stIconMaterial"]{background:#E4F4EE !important;color:#248466 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_2 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_3 [data-testid="stIconMaterial"]{background:#E7EFFB !important;color:#3E70B7 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_4 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_5 [data-testid="stIconMaterial"]{background:#EEE9F8 !important;color:#765BA0 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_6 [data-testid="stIconMaterial"]{background:#FFF2CF !important;color:#A87822 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_7 [data-testid="stIconMaterial"]{background:#FBE8E8 !important;color:#A85C5C !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{margin-top:.62rem !important;margin-bottom:.1rem !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.61rem !important;font-weight:780 !important;letter-spacing:.10em !important;text-transform:uppercase !important;color:#95A2AF !important;}
        div[data-testid="stVerticalBlockBorderWrapper"],div[data-testid="stMetric"]{background:var(--ln16-card) !important;border:1px solid var(--ln16-border) !important;border-radius:12px !important;box-shadow:0 3px 10px rgba(25,42,62,.055) !important;}
        [data-testid="stForm"]{background:#FFFFFF !important;border:1px solid var(--ln16-border) !important;border-radius:12px !important;padding:.85rem .9rem .8rem !important;box-shadow:0 3px 10px rgba(25,42,62,.04) !important;}
        [data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"] > div,textarea{background:#FFFFFF !important;color:#263544 !important;border-color:#D8E0E8 !important;border-radius:8px !important;box-shadow:none !important;}
        input,textarea{background:#FFFFFF !important;color:#263544 !important;-webkit-text-fill-color:#263544 !important;}
        [data-testid="stMain"] .stButton>button,[data-testid="stMain"] .stDownloadButton>button{min-height:2.3rem !important;background:#FFFFFF !important;color:#263544 !important;border:1px solid #CFD8E2 !important;border-radius:8px !important;box-shadow:none !important;font-size:.82rem !important;font-weight:650 !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"],[data-testid="stMain"] .stDownloadButton>button[kind="primary"],[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button{background:var(--ln16-blue) !important;color:#FFFFFF !important;border-color:var(--ln16-blue) !important;box-shadow:0 2px 5px rgba(37,99,235,.20) !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"] *,[data-testid="stMain"] .stDownloadButton>button[kind="primary"] *,[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"]:hover,[data-testid="stMain"] .stDownloadButton>button[kind="primary"]:hover,[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button:hover{background:var(--ln16-blue-hover) !important;border-color:var(--ln16-blue-hover) !important;}
        [data-testid="stTabs"] [data-baseweb="tab-list"]{gap:.2rem !important;border-bottom:1px solid #E1E7EE !important;}
        [data-testid="stTabs"] button{font-size:.82rem !important;font-weight:650 !important;}
        [data-testid="stExpander"]{background:#FFFFFF !important;border:1px solid var(--ln16-border) !important;border-radius:10px !important;}
        [data-testid="stAlert"]{border-radius:10px !important;}
        [data-testid="stDataFrame"],[data-testid="stTable"]{background:#FFFFFF !important;border-radius:10px !important;overflow:hidden !important;}
        hr{border-color:#E5EAF0 !important;}
        @media(max-width:900px){header[data-testid="stHeader"]{height:42px !important;min-height:42px !important;}[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:230px !important;min-width:230px !important;max-width:230px !important;}.block-container{max-width:100% !important;padding:.8rem .72rem 1.6rem !important;}}
'''

discovery_css = r'''        /* RC31.16 discovery grid */
        header[data-testid="stHeader"]{height:48px !important;min-height:48px !important;background:#0B1F38 !important;border-bottom:0 !important;box-shadow:0 2px 7px rgba(11,31,56,.10) !important;}
        [data-testid="stMain"]{background:#F1F4F8 !important;}
        [data-testid="stMain"] .block-container{max-width:1040px !important;padding-top:1rem !important;padding-bottom:2rem !important;}
        .ln-page-kicker{display:inline-flex !important;background:#E4F7E9 !important;color:#20844E !important;border:1px solid #CDEBD5 !important;border-radius:999px !important;padding:.18rem .48rem !important;font-size:.59rem !important;font-weight:780 !important;letter-spacing:.06em !important;margin-bottom:.38rem !important;}
        .ln-discovery-title{font-size:1.58rem !important;line-height:1.12 !important;margin:0 0 .22rem !important;color:#111C28 !important;font-weight:760 !important;letter-spacing:-.022em !important;}
        .ln-discovery-sub{font-size:.84rem !important;line-height:1.42 !important;color:#627286 !important;margin:0 0 .75rem !important;max-width:52rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{background:#FFFFFF !important;border:1px solid #E1E7EE !important;border-radius:12px !important;box-shadow:0 3px 10px rgba(25,42,62,.055) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] > div{padding:.7rem .75rem !important;}
        [data-testid="stMain"] [data-testid="stForm"]{background:#FFFFFF !important;border:1px solid #E1E7EE !important;border-radius:12px !important;padding:.8rem .85rem .75rem !important;box-shadow:0 3px 10px rgba(25,42,62,.04) !important;}
        .ln-home-count{font-size:1.42rem !important;color:#0B3A72 !important;margin:.12rem 0 .6rem !important;font-weight:760 !important;}
        .ln-home-value{background:#FFFFFF !important;border:1px solid #E1E7EE !important;border-left:3px solid #1A9A89 !important;border-radius:10px !important;padding:.7rem .8rem !important;margin:.48rem 0 .75rem !important;color:#566679 !important;font-size:.82rem !important;line-height:1.42 !important;box-shadow:0 2px 7px rgba(25,42,62,.035) !important;}
        .ln-home-section,.ln-state-grid-title{font-size:.62rem !important;color:#7C8A99 !important;font-weight:780 !important;letter-spacing:.08em !important;text-transform:uppercase !important;margin:.72rem 0 .38rem !important;}
        .ln-shortcut-copy{min-height:1.62rem !important;font-size:.71rem !important;line-height:1.3 !important;color:#6F7E8E !important;margin:0 0 .36rem !important;}
        .ln-state-name,.ln-modality-name,.ln-portal-name{font-size:.91rem !important;line-height:1.2 !important;color:#111C28 !important;font-weight:760 !important;margin:.04rem 0 .12rem !important;}
        .ln-state-code{font-size:.72rem !important;color:#738295 !important;font-weight:650 !important;}
        .ln-state-count,.ln-card-count{font-size:1.55rem !important;color:#0B3A72 !important;font-weight:780 !important;line-height:1 !important;margin:.58rem 0 .08rem !important;}
        .ln-state-label,.ln-card-caption{font-size:.72rem !important;color:#718095 !important;margin-bottom:.55rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name),[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-modality-name),[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-portal-name){border-radius:11px !important;box-shadow:0 3px 9px rgba(21,39,61,.06) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) [data-testid="stImage"] img{width:34px !important;max-width:34px !important;}
        [data-testid="stMain"] div[class*="st-key-state_"] button,[data-testid="stMain"] div[class*="st-key-modality_"] button,[data-testid="stMain"] div[class*="st-key-portal_"] button{min-height:2.28rem !important;background:#2563EB !important;color:#FFFFFF !important;border:1px solid #2563EB !important;border-radius:8px !important;box-shadow:0 2px 5px rgba(37,99,235,.18) !important;font-size:.79rem !important;font-weight:720 !important;}
        [data-testid="stMain"] div[class*="st-key-state_"] button *,[data-testid="stMain"] div[class*="st-key-modality_"] button *,[data-testid="stMain"] div[class*="st-key-portal_"] button *{color:#FFFFFF !important;}
        [data-testid="stMain"] div[class*="st-key-state_"] button:hover,[data-testid="stMain"] div[class*="st-key-modality_"] button:hover,[data-testid="stMain"] div[class*="st-key-portal_"] button:hover{background:#1D4ED8 !important;border-color:#1D4ED8 !important;}
        .ln-reference{font-size:1rem !important;color:#17212B !important;margin:.34rem 0 .54rem !important;font-weight:720 !important;}
        .ln-info-grid{gap:.48rem !important;margin:.14rem 0 .65rem !important;}
        .ln-info-box,.ln-meta-box{background:#F8FAFC !important;border:1px solid #E3E9F0 !important;border-radius:9px !important;padding:.58rem .62rem !important;min-height:68px !important;}
        .ln-info-label,.ln-meta-label{font-size:.62rem !important;color:#7B8998 !important;}
        .ln-info-value,.ln-meta-value{font-size:.82rem !important;color:#263544 !important;}
        .ln-items-box{background:#F8FAFC !important;border-color:#E3E9F0 !important;border-radius:9px !important;padding:.65rem .7rem !important;}
        @media(max-width:900px){[data-testid="stMain"] .block-container{max-width:100% !important;padding:.78rem .7rem 1.5rem !important;}.ln-discovery-title{font-size:1.42rem !important;}.ln-info-grid,.ln-meta-grid{grid-template-columns:repeat(2,minmax(0,1fr)) !important;}}
'''

insert_before_style_end(APP, "apply_brand", GLOBAL_MARKER, global_css)
insert_before_style_end(DISCOVERY, "_apply_styles", DISCOVERY_MARKER, discovery_css)

config = CONFIG.read_text(encoding="utf-8")
if 'APP_VERSION = "1.0 Essential RC31.15"' not in config:
    raise SystemExit("config.py não está em RC31.15")
CONFIG.write_text(config.replace('APP_VERSION = "1.0 Essential RC31.15"', 'APP_VERSION = "1.0 Essential RC31.16"', 1), encoding="utf-8")

discovery = DISCOVERY.read_text(encoding="utf-8")
if discovery.count('"Ver oportunidades", icon=":material/arrow_forward:"') < 3:
    raise SystemExit("CTAs esperados de Estado/Modalidade/Portal não encontrados")
discovery = discovery.replace('"Ver oportunidades", icon=":material/arrow_forward:"', '"Ver licitações"')
DISCOVERY.write_text(discovery, encoding="utf-8")

for path in TESTS.glob("test_*.py"):
    text = path.read_text(encoding="utf-8")
    updated = text.replace('APP_VERSION = "1.0 Essential RC31.15"', 'APP_VERSION = "1.0 Essential RC31.16"')
    if path.name == "test_rc31_13_premium_ui.py":
        updated = updated.replace(
            'self.assertIn(\'"Ver oportunidades", icon=":material/arrow_forward:"\', src)',
            'self.assertIn(\'"Ver licitações"\', src)\n        self.assertNotIn(\'"Ver oportunidades"\', src)',
        )
    if updated != text:
        path.write_text(updated, encoding="utf-8")

new_test = TESTS / "test_rc31_16_competitor_layout.py"
new_test.write_text('''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass Rc3116CompetitorLayoutContracts(unittest.TestCase):\n    def test_version_is_rc3116(self):\n        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")\n        self.assertIn('APP_VERSION = "1.0 Essential RC31.16"', cfg)\n\n    def test_global_shell_is_compact_and_consistent_on_all_pages(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertEqual(app.count("/* RC31.16 competitor-inspired global shell */"), 1)\n        self.assertIn('background:var(--ln16-navy) !important', app)\n        self.assertIn('width:240px !important', app)\n        self.assertIn('max-width:1040px !important', app)\n        self.assertIn('--ln16-blue:#2563EB', app)\n        self.assertIn('[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button', app)\n\n    def test_discovery_grids_use_rectangular_cards_and_blue_ctas(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertEqual(src.count("/* RC31.16 discovery grid */"), 1)\n        self.assertIn(':has(.ln-modality-name)', src)\n        self.assertIn('div[class*="st-key-modality_"] button', src)\n        self.assertIn('background:#2563EB !important', src)\n        self.assertIn('"Ver licitações"', src)\n        self.assertNotIn('"Ver oportunidades"', src)\n        self.assertIn('for start_index in range(0, len(counts), 3):', src)\n\n    def test_existing_navigation_and_search_logic_are_preserved(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('"Buscar licitações"', app)\n        self.assertIn('"Por Estado"', app)\n        self.assertIn('"Por Cidade"', app)\n        self.assertIn('"Por Modalidade"', app)\n        self.assertIn('"Por site de disputa"', app)\n        self.assertIn('st.session_state["essential_search_criteria"]', src)\n        self.assertIn('st.session_state["_navigation_request"] = "Buscar licitações"', src)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

print("RC31.16 aplicada: layout global alinhado e lógica preservada")
