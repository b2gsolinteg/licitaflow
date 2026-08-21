from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
DISCOVERY = ROOT / "src" / "essential_discovery.py"
CONFIG = ROOT / "src" / "config.py"
TESTS = ROOT / "tests"


def insert_before_style_end(text: str, marker: str, block: str) -> str:
    if block.strip() in text:
        return text
    pos = text.find(marker)
    if pos < 0:
        raise RuntimeError(f"marker not found: {marker}")
    end = text.find("</style>", pos)
    if end < 0:
        raise RuntimeError(f"style end not found after: {marker}")
    return text[:end] + block + "\n        " + text[end:]


app = APP.read_text(encoding="utf-8")
app_css = r'''
        /* RC31.19 navigation density */
        :root{--rc19-sidebar:276px;}
        @media(min-width:901px){
            [data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:var(--rc19-sidebar) !important;min-width:var(--rc19-sidebar) !important;max-width:var(--rc19-sidebar) !important;}
        }
        .ln-app-topbar{left:var(--rc19-sidebar) !important;}
        [data-testid="stSidebar"] > div:first-child{padding:60px 12px 78px !important;}
        .ln-sidebar-brand{width:var(--rc19-sidebar) !important;padding:0 16px !important;}
        .ln-sidebar-brand img{max-width:150px !important;max-height:32px !important;}
        [data-testid="stSidebar"] .stCaption p{font-size:.72rem !important;font-weight:750 !important;letter-spacing:.08em !important;color:#91A0B3 !important;text-transform:uppercase !important;}
        [data-testid="stSidebar"] .stButton{margin:0 0 .24rem !important;}
        [data-testid="stSidebar"] .stButton button{min-height:3.12rem !important;padding:.28rem .5rem !important;gap:.72rem !important;font-size:.96rem !important;font-weight:650 !important;text-align:left !important;justify-content:flex-start !important;}
        [data-testid="stSidebar"] .stButton button p{font-size:.96rem !important;font-weight:650 !important;line-height:1.18 !important;text-align:left !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{flex:0 0 2.25rem !important;width:2.25rem !important;height:2.25rem !important;border-radius:10px !important;font-size:1.08rem !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#EEF9F5 !important;box-shadow:inset 3px 0 0 #18A77B !important;color:#10253F !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"] [data-testid="stIconMaterial"]{background:#DDF5EA !important;color:#10865F !important;}
        .ln-home-color-logo{margin:0 0 .7rem !important;}
        @media(max-width:900px){.ln-app-topbar{left:0 !important;}.ln-sidebar-brand{width:225px !important;}[data-testid="stSidebar"] .stButton button,[data-testid="stSidebar"] .stButton button p{font-size:.9rem !important;}}
'''
app = insert_before_style_end(app, "/* RC31.18 exact reference shell */", app_css)

home_route_old = '    if page == "Início":\n        essential_home_page(db, user)'
home_route_new = '''    if page == "Início":
        if LOGO_PATH.exists():
            st.markdown('<div class="ln-home-color-logo">', unsafe_allow_html=True)
            st.image(str(LOGO_PATH), width=190)
            st.markdown('</div>', unsafe_allow_html=True)
        essential_home_page(db, user)'''
if home_route_old in app:
    app = app.replace(home_route_old, home_route_new, 1)
elif 'class="ln-home-color-logo"' not in app:
    raise RuntimeError("home route anchor not found")
APP.write_text(app, encoding="utf-8")

src = DISCOVERY.read_text(encoding="utf-8")
discovery_css = r'''
        /* RC31.19 richer discovery home */
        [data-testid="stMain"] .block-container{max-width:980px !important;}
        .ln-back-row{margin:-.1rem 0 .45rem !important;}
        .ln-shortcut-figure{height:92px !important;border-radius:11px !important;margin:0 0 .58rem !important;display:flex !important;align-items:center !important;justify-content:center !important;overflow:hidden !important;}
        .ln-shortcut-figure svg{width:100% !important;height:100% !important;display:block !important;}
        .ln-shortcut-state{background:linear-gradient(135deg,#E6F1FF,#F7FBFF) !important;}
        .ln-shortcut-city{background:linear-gradient(135deg,#E8F8F4,#F7FCFA) !important;}
        .ln-shortcut-modality{background:linear-gradient(135deg,#F0EAFE,#FBF9FF) !important;}
        .ln-shortcut-site{background:linear-gradient(135deg,#EAF1FF,#F8FAFF) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-figure){background:#FFFFFF !important;border:0 !important;border-radius:11px !important;box-shadow:0 3px 11px rgba(18,40,72,.085) !important;min-height:215px !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-figure) > div{padding:.62rem !important;}
        .ln-shortcut-copy{min-height:2.7rem !important;font-size:.72rem !important;line-height:1.34 !important;color:#65758A !important;margin:.05rem 0 .48rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-figure) .stButton button{background:#2D5FE8 !important;color:#FFFFFF !important;border:1px solid #2D5FE8 !important;border-radius:7px !important;min-height:2.35rem !important;font-size:.76rem !important;font-weight:700 !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-figure) .stButton button *{color:#FFFFFF !important;}
        @media(max-width:900px){[data-testid="stMain"] .block-container{max-width:100% !important;}.ln-shortcut-figure{height:78px !important;}}
'''
src = insert_before_style_end(src, "/* RC31.18 exact discovery cards */", discovery_css)

helper_anchor = 'def _page_header(kicker: str, title: str, subtitle: str) -> None:'
helper = r'''
def _render_back_button(key: str) -> None:
    st.markdown('<div class="ln-back-row">', unsafe_allow_html=True)
    if st.button("Voltar", icon=":material/arrow_back:", key=f"discovery_back_{key}"):
        st.session_state["_navigation_request"] = "Início"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def _shortcut_illustration(target: str) -> str:
    figures = {
        "Por Estado": '''<div class="ln-shortcut-figure ln-shortcut-state"><svg viewBox="0 0 240 92" xmlns="http://www.w3.org/2000/svg"><rect width="240" height="92" rx="12" fill="#EAF3FF"/><path d="M56 15l22 7 16-4 18 14 18 4 2 16-13 9-8 18-17-4-9 9-15-11-18-1-8-17 8-12-4-13z" fill="#63A4FF"/><circle cx="78" cy="43" r="4" fill="#fff"/><circle cx="99" cy="61" r="4" fill="#fff"/><circle cx="64" cy="59" r="4" fill="#fff"/><rect x="149" y="26" width="62" height="8" rx="4" fill="#9EC7FF"/><rect x="149" y="43" width="48" height="8" rx="4" fill="#BED9FF"/><rect x="149" y="60" width="56" height="8" rx="4" fill="#BED9FF"/></svg></div>''',
        "Por Cidade": '''<div class="ln-shortcut-figure ln-shortcut-city"><svg viewBox="0 0 240 92" xmlns="http://www.w3.org/2000/svg"><rect width="240" height="92" rx="12" fill="#ECF9F5"/><path d="M42 73h156" stroke="#A9DCCC" stroke-width="5" stroke-linecap="round"/><rect x="59" y="42" width="30" height="31" rx="3" fill="#6DC7AB"/><rect x="96" y="28" width="37" height="45" rx="3" fill="#3BA986"/><rect x="141" y="37" width="34" height="36" rx="3" fill="#83D4BA"/><path d="M116 15c8 0 14 6 14 14 0 11-14 24-14 24s-14-13-14-24c0-8 6-14 14-14z" fill="#2467E8"/><circle cx="116" cy="29" r="5" fill="#fff"/></svg></div>''',
        "Por Modalidade": '''<div class="ln-shortcut-figure ln-shortcut-modality"><svg viewBox="0 0 240 92" xmlns="http://www.w3.org/2000/svg"><rect width="240" height="92" rx="12" fill="#F4EEFF"/><rect x="50" y="19" width="58" height="57" rx="6" fill="#fff" stroke="#D9CAF9"/><rect x="61" y="31" width="34" height="6" rx="3" fill="#B79BEF"/><rect x="61" y="44" width="25" height="6" rx="3" fill="#D0BEF5"/><rect x="61" y="57" width="30" height="6" rx="3" fill="#D0BEF5"/><g transform="rotate(-32 157 47)"><rect x="148" y="27" width="42" height="13" rx="5" fill="#6D4DE3"/><rect x="145" y="42" width="48" height="10" rx="5" fill="#8A6CF0"/><rect x="164" y="51" width="9" height="29" rx="4" fill="#5D42C8"/></g><rect x="138" y="75" width="50" height="7" rx="3" fill="#A98FF0"/></svg></div>''',
        "Por site de disputa": '''<div class="ln-shortcut-figure ln-shortcut-site"><svg viewBox="0 0 240 92" xmlns="http://www.w3.org/2000/svg"><rect width="240" height="92" rx="12" fill="#EDF3FF"/><rect x="55" y="18" width="130" height="58" rx="7" fill="#174B9E"/><rect x="62" y="25" width="116" height="43" rx="3" fill="#fff"/><circle cx="120" cy="46" r="15" fill="none" stroke="#2D5FE8" stroke-width="4"/><path d="M105 46h30M120 31c-6 7-6 23 0 30M120 31c6 7 6 23 0 30" stroke="#2D5FE8" stroke-width="3" fill="none"/><rect x="91" y="77" width="58" height="5" rx="2.5" fill="#7EA7EA"/></svg></div>''',
    }
    return figures.get(target, "")


'''
if '_shortcut_illustration(target: str)' not in src:
    idx = src.find(helper_anchor)
    if idx < 0:
        raise RuntimeError("page header anchor not found")
    src = src[:idx] + helper + src[idx:]

for fn in (
    "portal_page", "search_page", "state_page", "city_page", "modality_page",
    "advanced_search_page", "top50_page", "my_list_page", "preferences_page", "radar_page",
):
    pattern = rf'(def {fn}\([^\n]*\) -> None:\n    _apply_styles\(\)\n)'
    replacement = rf'\1    _render_back_button("{fn}")\n'
    src, count = re.subn(pattern, replacement, src, count=1)
    if count == 0 and f'_render_back_button("{fn}")' not in src:
        raise RuntimeError(f"function anchor not found: {fn}")

shortcut_anchor = '''        with col.container(border=True):
            st.markdown(f'<div class="ln-shortcut-copy">{description}</div>', unsafe_allow_html=True)
            if st.button(label, icon=icon, key=f"home_{target}", width="stretch"):'''
shortcut_replacement = '''        with col.container(border=True):
            st.markdown(_shortcut_illustration(target), unsafe_allow_html=True)
            st.markdown(f'<div class="ln-shortcut-copy">{description}</div>', unsafe_allow_html=True)
            if st.button(label, icon=icon, key=f"home_{target}", type="primary", width="stretch"):'''
if shortcut_anchor in src:
    src = src.replace(shortcut_anchor, shortcut_replacement, 1)
elif 'st.markdown(_shortcut_illustration(target)' not in src:
    raise RuntimeError("home shortcut anchor not found")

DISCOVERY.write_text(src, encoding="utf-8")

config = CONFIG.read_text(encoding="utf-8")
config = re.sub(r'APP_VERSION = "1\.0 Essential RC31\.\d+"', 'APP_VERSION = "1.0 Essential RC31.19"', config, count=1)
CONFIG.write_text(config, encoding="utf-8")

for path in TESTS.glob("test_*.py"):
    text = path.read_text(encoding="utf-8")
    updated = text.replace('APP_VERSION = "1.0 Essential RC31.18"', 'APP_VERSION = "1.0 Essential RC31.19"')
    if updated != text:
        path.write_text(updated, encoding="utf-8")

contract = TESTS / "test_rc31_19_navigation_density.py"
contract.write_text('''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass Rc3119NavigationDensityContracts(unittest.TestCase):\n    def test_version(self):\n        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")\n        self.assertIn('APP_VERSION = "1.0 Essential RC31.19"', cfg)\n\n    def test_sidebar_is_wider_and_readable(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn("/* RC31.19 navigation density */", app)\n        self.assertIn("--rc19-sidebar:276px", app)\n        self.assertIn("font-size:.96rem !important", app)\n        self.assertIn("ln-home-color-logo", app)\n\n    def test_internal_pages_have_back_navigation(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('st.button("Voltar", icon=":material/arrow_back:"', src)\n        for fn in ("portal_page", "search_page", "state_page", "city_page", "modality_page", "advanced_search_page"):\n            self.assertIn(f'_render_back_button("{fn}")', src)\n\n    def test_home_shortcuts_have_visual_figures(self):\n        src = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn("ln-shortcut-state", src)\n        self.assertIn("ln-shortcut-city", src)\n        self.assertIn("ln-shortcut-modality", src)\n        self.assertIn("ln-shortcut-site", src)\n        self.assertIn("_shortcut_illustration(target)", src)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

print("RC31.19 aplicada: navegação, sidebar, logo Home e atalhos ilustrados")
