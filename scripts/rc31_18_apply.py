from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
DISCOVERY = ROOT / "src" / "essential_discovery.py"
CONFIG = ROOT / "src" / "config.py"
TESTS = ROOT / "tests"

APP_MARKER = "/* RC31.18 exact reference shell */"
DISCOVERY_MARKER = "/* RC31.18 exact discovery cards */"


def replace_tail_style(path: Path, old_marker: str, new_block: str) -> None:
    text = path.read_text(encoding="utf-8")
    if APP_MARKER in text or DISCOVERY_MARKER in text:
        raise SystemExit(f"{path}: RC31.18 já aplicada")
    start = text.find(old_marker)
    if start < 0:
        raise SystemExit(f"{path}: marcador antigo não encontrado: {old_marker}")
    end = text.find("\n\n        </style>", start)
    if end < 0:
        raise SystemExit(f"{path}: fim do bloco style não encontrado")
    text = text[:start] + new_block.rstrip() + text[end:]
    path.write_text(text, encoding="utf-8")


app_css = r'''/* RC31.18 exact reference shell */
        :root{--ref-navy:#0A1D34;--ref-blue:#2D5FE8;--ref-blue-hover:#244FCB;--ref-green:#20BF63;--ref-bg:#F1F4F8;--ref-card:#FFFFFF;--ref-border:#E5EAF0;--ref-text:#142033;--ref-muted:#65758A;}
        html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{font-family:"Poppins","Inter","Segoe UI",Arial,sans-serif !important;color:var(--ref-text) !important;}
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--ref-bg) !important;}
        header[data-testid="stHeader"]{display:block !important;height:48px !important;min-height:48px !important;background:var(--ref-navy) !important;border:0 !important;box-shadow:0 2px 8px rgba(10,29,52,.14) !important;z-index:999990 !important;}
        [data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none !important;}
        .ln-app-topbar{position:fixed !important;top:0 !important;left:240px !important;right:0 !important;height:48px !important;z-index:999999 !important;display:flex !important;align-items:center !important;justify-content:space-between !important;padding:0 16px 0 18px !important;pointer-events:none !important;color:#FFFFFF !important;}
        .ln-app-topbar-menu{font-size:1.25rem !important;line-height:1 !important;color:#FFFFFF !important;font-weight:400 !important;letter-spacing:-.08em !important;}
        .ln-app-topbar-account{display:inline-flex !important;align-items:center !important;min-height:29px !important;padding:0 13px !important;border:1px solid rgba(255,255,255,.22) !important;border-radius:999px !important;background:rgba(255,255,255,.08) !important;color:#FFFFFF !important;font-size:.72rem !important;font-weight:650 !important;}
        [data-testid="stIconMaterial"],.material-symbols-rounded,.material-symbols-outlined{font-family:"Material Symbols Rounded","Material Symbols Outlined" !important;}
        .block-container{max-width:860px !important;padding:1rem .75rem 2rem !important;}
        [data-testid="stMain"] h1{font-size:1.28rem !important;line-height:1.18 !important;color:#111827 !important;font-weight:700 !important;letter-spacing:-.018em !important;}
        [data-testid="stMain"] h2{font-size:1.05rem !important;line-height:1.22 !important;color:#111827 !important;font-weight:700 !important;}
        [data-testid="stMain"] h3{font-size:.92rem !important;color:#111827 !important;font-weight:700 !important;}
        [data-testid="stMain"] p,[data-testid="stMain"] label p,[data-testid="stMain"] .stCaption p{font-size:.77rem !important;color:var(--ref-muted) !important;}
        [data-testid="stSidebar"]{background:#FFFFFF !important;border-right:1px solid #E3E8EE !important;box-shadow:none !important;z-index:999995 !important;}
        @media(min-width:901px){[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:240px !important;min-width:240px !important;max-width:240px !important;}}
        [data-testid="stSidebar"] > div:first-child{overflow-y:auto !important;overflow-x:hidden !important;max-height:100vh !important;padding:58px 12px 62px !important;}
        .ln-sidebar-brand{position:fixed !important;top:0 !important;left:0 !important;width:240px !important;height:48px !important;z-index:999999 !important;background:var(--ref-navy) !important;display:flex !important;align-items:center !important;padding:0 12px !important;border-right:1px solid rgba(255,255,255,.08) !important;}
        .ln-sidebar-brand img{display:block !important;width:auto !important;max-width:112px !important;max-height:28px !important;filter:brightness(0) invert(1) !important;object-fit:contain !important;}
        .ln-sidebar-brand-text{color:#FFFFFF !important;font-size:.91rem !important;font-weight:750 !important;letter-spacing:-.02em !important;}
        [data-testid="stSidebar"] .stButton{margin:0 0 .16rem !important;}
        [data-testid="stSidebar"] .stButton button{width:100% !important;min-height:2.45rem !important;justify-content:flex-start !important;background:transparent !important;color:#172033 !important;border:0 !important;border-radius:7px !important;box-shadow:none !important;padding:.16rem .2rem !important;gap:.52rem !important;font-size:.77rem !important;font-weight:600 !important;transition:background .12s ease !important;}
        [data-testid="stSidebar"] .stButton button:hover{background:#F6F8FA !important;border:0 !important;transform:none !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:transparent !important;color:#111827 !important;border:0 !important;box-shadow:none !important;font-weight:700 !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{display:inline-flex !important;align-items:center !important;justify-content:center !important;flex:0 0 2rem !important;width:2rem !important;height:2rem !important;border-radius:9px !important;background:#F2F4F7 !important;color:#66788B !important;font-size:1rem !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"] [data-testid="stIconMaterial"]{background:#DDF8E6 !important;color:#21A95A !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_0 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_1 [data-testid="stIconMaterial"]{background:#DDF8E6 !important;color:#24A95A !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_2 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_3 [data-testid="stIconMaterial"]{background:#E3EDFF !important;color:#3974E1 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_4 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_5 [data-testid="stIconMaterial"]{background:#EFE7FF !important;color:#845CCB !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_6 [data-testid="stIconMaterial"]{background:#FFF1CB !important;color:#DB8E19 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_7 [data-testid="stIconMaterial"]{background:#FFE6E8 !important;color:#C55E68 !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{margin:.48rem 0 .12rem !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.55rem !important;font-weight:750 !important;letter-spacing:.10em !important;text-transform:uppercase !important;color:#97A4B3 !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout{position:fixed !important;left:12px !important;bottom:12px !important;width:216px !important;z-index:999999 !important;margin:0 !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout button{min-height:2.25rem !important;justify-content:center !important;background:var(--ref-green) !important;color:#FFFFFF !important;border:0 !important;border-radius:8px !important;font-size:.75rem !important;font-weight:700 !important;box-shadow:none !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout button *{color:#FFFFFF !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout [data-testid="stIconMaterial"]{display:none !important;}
        div[data-testid="stVerticalBlockBorderWrapper"],div[data-testid="stMetric"]{background:#FFFFFF !important;border:1px solid var(--ref-border) !important;border-radius:10px !important;box-shadow:0 3px 10px rgba(20,38,60,.05) !important;}
        [data-testid="stForm"]{background:#FFFFFF !important;border:1px solid var(--ref-border) !important;border-radius:10px !important;padding:.7rem .75rem .65rem !important;box-shadow:0 3px 10px rgba(20,38,60,.045) !important;}
        [data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"] > div,textarea{background:#FFFFFF !important;color:#263544 !important;border-color:#DCE3EA !important;border-radius:7px !important;box-shadow:none !important;}
        input,textarea{background:#FFFFFF !important;color:#263544 !important;-webkit-text-fill-color:#263544 !important;font-size:.78rem !important;}
        [data-testid="stMain"] .stButton>button,[data-testid="stMain"] .stDownloadButton>button{min-height:2.2rem !important;background:#FFFFFF !important;color:#263544 !important;border:1px solid #D8E0E8 !important;border-radius:7px !important;box-shadow:none !important;font-size:.75rem !important;font-weight:650 !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"],[data-testid="stMain"] .stDownloadButton>button[kind="primary"],[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button{background:var(--ref-blue) !important;color:#FFFFFF !important;border-color:var(--ref-blue) !important;box-shadow:0 2px 5px rgba(45,95,232,.18) !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"] *,[data-testid="stMain"] .stDownloadButton>button[kind="primary"] *,[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"]:hover,[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button:hover{background:var(--ref-blue-hover) !important;border-color:var(--ref-blue-hover) !important;}
        [data-testid="stTabs"] [data-baseweb="tab-list"]{gap:.18rem !important;border-bottom:1px solid #E3E8EF !important;}
        [data-testid="stTabs"] button{font-size:.76rem !important;font-weight:650 !important;}
        [data-testid="stExpander"]{background:#FFFFFF !important;border:1px solid var(--ref-border) !important;border-radius:9px !important;}
        [data-testid="stAlert"]{border-radius:9px !important;}
        [data-testid="stDataFrame"],[data-testid="stTable"]{background:#FFFFFF !important;border-radius:9px !important;overflow:hidden !important;}
        @media(max-width:900px){header[data-testid="stHeader"]{height:44px !important;min-height:44px !important;}.ln-app-topbar{left:0 !important;height:44px !important;}.ln-sidebar-brand{height:44px !important;}[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:225px !important;min-width:225px !important;max-width:225px !important;}.block-container{max-width:100% !important;padding:.72rem .6rem 1.5rem !important;}}
'''


discovery_css = r'''/* RC31.18 exact discovery cards */
        header[data-testid="stHeader"]{height:48px !important;min-height:48px !important;background:#0A1D34 !important;}
        [data-testid="stMain"]{background:#F1F4F8 !important;}
        [data-testid="stMain"] .block-container{max-width:860px !important;padding-top:1rem !important;padding-bottom:1.8rem !important;}
        .ln-page-kicker{display:inline-flex !important;background:#DCFCE7 !important;color:#218A4B !important;border:1px solid #C7F0D3 !important;border-radius:999px !important;padding:.13rem .4rem !important;font-size:.53rem !important;font-weight:750 !important;letter-spacing:.055em !important;margin-bottom:.34rem !important;}
        .ln-discovery-title{font-size:1.2rem !important;line-height:1.18 !important;margin:0 0 .16rem !important;color:#111827 !important;font-weight:700 !important;letter-spacing:-.015em !important;}
        .ln-discovery-sub{font-size:.75rem !important;line-height:1.4 !important;color:#657386 !important;margin:0 0 .68rem !important;max-width:49rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{background:#FFFFFF !important;border:1px solid #E6EBF1 !important;border-radius:10px !important;box-shadow:0 3px 10px rgba(20,38,60,.05) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] > div{background:#FFFFFF !important;padding:.62rem .68rem !important;border-radius:10px !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name),[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-modality-name),[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-portal-name){background:#FFFFFF !important;border:0 !important;border-radius:10px !important;box-shadow:0 3px 10px rgba(19,38,61,.09) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) > div,[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-modality-name) > div,[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-portal-name) > div{background:#FFFFFF !important;padding:.62rem .7rem .68rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) [data-testid="stImage"]{display:none !important;}
        .ln-state-name,.ln-modality-name,.ln-portal-name{font-size:.8rem !important;line-height:1.18 !important;color:#111827 !important;font-weight:700 !important;margin:0 0 .08rem !important;}
        .ln-state-code{font-size:.65rem !important;color:#738195 !important;font-weight:600 !important;margin-left:.18rem !important;}
        .ln-state-count,.ln-card-count{font-size:1.42rem !important;color:#0B3A72 !important;font-weight:750 !important;line-height:1 !important;margin:.45rem 0 .06rem !important;}
        .ln-state-label,.ln-card-caption{font-size:.66rem !important;color:#718095 !important;margin-bottom:.5rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) .stButton button,[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-modality-name) .stButton button,[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-portal-name) .stButton button{min-height:2.15rem !important;background:#2D5FE8 !important;color:#FFFFFF !important;border:1px solid #2D5FE8 !important;border-radius:7px !important;box-shadow:0 2px 5px rgba(45,95,232,.18) !important;font-size:.72rem !important;font-weight:700 !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) .stButton button *,[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-modality-name) .stButton button *,[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-portal-name) .stButton button *{color:#FFFFFF !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) .stButton button:hover,[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-modality-name) .stButton button:hover,[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-portal-name) .stButton button:hover{background:#244FCB !important;border-color:#244FCB !important;}
        [data-testid="stMain"] div[data-testid="stFormSubmitButton"] button{background:#2D5FE8 !important;color:#FFFFFF !important;border:1px solid #2D5FE8 !important;border-radius:7px !important;box-shadow:0 2px 5px rgba(45,95,232,.18) !important;min-height:2.2rem !important;font-size:.75rem !important;font-weight:700 !important;}
        [data-testid="stMain"] div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF !important;}
        .ln-home-count{font-size:1.26rem !important;color:#0B3A72 !important;margin:.1rem 0 .5rem !important;font-weight:700 !important;}
        .ln-home-value{background:#FFFFFF !important;border:1px solid #E6EBF1 !important;border-left:3px solid #28A889 !important;border-radius:9px !important;padding:.58rem .68rem !important;margin:.4rem 0 .65rem !important;color:#566679 !important;font-size:.74rem !important;line-height:1.4 !important;box-shadow:0 3px 9px rgba(22,39,60,.035) !important;}
        .ln-home-section,.ln-state-grid-title{font-size:.56rem !important;color:#7C8998 !important;font-weight:750 !important;letter-spacing:.08em !important;text-transform:uppercase !important;margin:.62rem 0 .3rem !important;}
        .ln-shortcut-copy{min-height:1.35rem !important;font-size:.65rem !important;line-height:1.28 !important;color:#6F7D8D !important;margin:0 0 .28rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-copy){border-radius:9px !important;box-shadow:none !important;}
        .ln-reference{font-size:.9rem !important;color:#17212B !important;margin:.28rem 0 .44rem !important;font-weight:650 !important;}
        .ln-info-grid{gap:.4rem !important;margin:.12rem 0 .54rem !important;}
        .ln-info-box,.ln-meta-box{background:#F8FAFC !important;border:1px solid #E6EBF1 !important;border-radius:8px !important;padding:.48rem .54rem !important;min-height:60px !important;}
        @media(max-width:900px){[data-testid="stMain"] .block-container{max-width:100% !important;padding:.72rem .6rem 1.5rem !important;}.ln-discovery-title{font-size:1.1rem !important;}.ln-info-grid{grid-template-columns:repeat(2,minmax(0,1fr)) !important;}}
'''

replace_tail_style(APP, "/* RC31.17 faithful reference shell */", app_css)
replace_tail_style(DISCOVERY, "/* RC31.17 faithful discovery layout */", discovery_css)

app = APP.read_text(encoding="utf-8")
old_sidebar = '''    admin_section = None\n    with st.sidebar:\n        if LOGO_PATH.exists():\n            st.image(str(LOGO_PATH), width="stretch")\n        else:\n            st.markdown("## LicitaNexo")\n        st.markdown(f'<div style="color:#293746">LicitaNexo · {APP_VERSION}</div>', unsafe_allow_html=True)\n        st.markdown('<div style="color:#718096;font-size:.80rem;margin-bottom:.7rem">B2G SaaS · Business to Growth</div>', unsafe_allow_html=True)\n        st.markdown(\n            f'<div style="background:#F6F9FA;border:1px solid #E0E8ED;border-radius:14px;padding:.72rem .78rem;margin:.25rem 0 .8rem">'\n            f'<div style="font-weight:650;color:#172B3A">{_greeting(user)}</div>'\n            f'<div style="font-size:.76rem;color:#718096">{escape(str(user.get("name") or user.get("email") or "Minha conta"))}</div></div>',\n            unsafe_allow_html=True,\n        )\n'''
new_sidebar = '''    admin_section = None\n    account_label = escape(str(user.get("name") or user.get("email") or "Minha conta").split()[0])\n    st.markdown(\n        f'<div class="ln-app-topbar"><span class="ln-app-topbar-menu">☰</span>'\n        f'<span class="ln-app-topbar-account">{account_label}</span></div>',\n        unsafe_allow_html=True,\n    )\n    with st.sidebar:\n        if LOGO_PATH.exists():\n            logo_data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")\n            st.markdown(\n                f'<div class="ln-sidebar-brand"><img src="data:image/png;base64,{logo_data}" alt="LicitaNexo"></div>',\n                unsafe_allow_html=True,\n            )\n        else:\n            st.markdown('<div class="ln-sidebar-brand"><span class="ln-sidebar-brand-text">LicitaNexo</span></div>', unsafe_allow_html=True)\n'''
if old_sidebar not in app:
    raise SystemExit("app.py: bloco visual inicial da sidebar não encontrado")
app = app.replace(old_sidebar, new_sidebar, 1)
APP.write_text(app, encoding="utf-8")

discovery = DISCOVERY.read_text(encoding="utf-8")
discovery = discovery.replace("background:#0E7C75 !important", "background:#2D5FE8 !important")
discovery = discovery.replace("border:1px solid #0E7C75 !important", "border:1px solid #2D5FE8 !important")
discovery = discovery.replace("rgba(14,124,117,.12)", "rgba(45,95,232,.18)")
discovery = discovery.replace("background:#0A655F !important", "background:#244FCB !important")
discovery = discovery.replace("border-color:#0A655F !important", "border-color:#244FCB !important")
discovery = discovery.replace('if st.button("Ver licitações", key=f"modality_{label}", width="stretch"):', 'if st.button("Ver licitações", key=f"modality_{label}", type="primary", width="stretch"):')
discovery = discovery.replace('if st.button("Ver licitações", key=f"portal_{portal_name}", width="stretch"):', 'if st.button("Ver licitações", key=f"portal_{portal_name}", type="primary", width="stretch"):')
DISCOVERY.write_text(discovery, encoding="utf-8")

cfg = CONFIG.read_text(encoding="utf-8")
cfg = cfg.replace('APP_VERSION = "1.0 Essential RC31.17"', 'APP_VERSION = "1.0 Essential RC31.18"')
CONFIG.write_text(cfg, encoding="utf-8")

for path in TESTS.glob("test_*.py"):
    text = path.read_text(encoding="utf-8")
    changed = text.replace('APP_VERSION = "1.0 Essential RC31.17"', 'APP_VERSION = "1.0 Essential RC31.18"')
    if changed != text:
        path.write_text(changed, encoding="utf-8")

(TESTS / "test_rc31_18_reference_shell.py").write_text('''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\nclass Rc3118ReferenceShellContracts(unittest.TestCase):\n    def test_reference_topbar_and_sidebar_are_not_empty(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn("/* RC31.18 exact reference shell */", app)\n        self.assertIn("ln-app-topbar-menu", app)\n        self.assertIn("ln-app-topbar-account", app)\n        self.assertIn("ln-sidebar-brand", app)\n\n    def test_sidebar_matches_compact_reference_geometry(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn("width:240px !important", app)\n        self.assertIn("min-height:2.45rem !important", app)\n        self.assertIn("position:fixed !important;left:12px !important;bottom:12px", app)\n\n    def test_discovery_cards_are_white_and_blue(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn("/* RC31.18 exact discovery cards */", src)\n        self.assertIn("background:#2D5FE8 !important", src)\n        self.assertIn('type="primary", width="stretch"', src)\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

print("RC31.18 aplicada: shell e cards alinhados à referência visual")
