from pathlib import Path
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
CONFIG = ROOT / "src" / "config.py"
TESTS = ROOT / "tests"
SOURCE_LOGO = ROOT / "assets" / "licitanexo-logo.png"
TIGHT_LOGO = ROOT / "assets" / "licitanexo-logo-tight.png"


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


if SOURCE_LOGO.exists():
    image = Image.open(SOURCE_LOGO).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        left, top, right, bottom = bbox
        pad_x, pad_y = 8, 6
        left = max(0, left - pad_x)
        top = max(0, top - pad_y)
        right = min(image.width, right + pad_x)
        bottom = min(image.height, bottom + pad_y)
        image.crop((left, top, right, bottom)).save(TIGHT_LOGO)

app = APP.read_text(encoding="utf-8")
app_css = r'''
        /* RC31.20 viewport polish */
        [data-testid="stSidebar"] > div:first-child{padding:56px 12px 18px !important;}
        [data-testid="stSidebar"] .stButton{margin:0 0 .16rem !important;}
        [data-testid="stSidebar"] .stButton button{min-height:2.82rem !important;padding:.22rem .48rem !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout{position:relative !important;left:auto !important;bottom:auto !important;width:100% !important;z-index:auto !important;margin:.72rem 0 .1rem !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout button{min-height:2.55rem !important;font-size:.82rem !important;border-radius:8px !important;}
        .ln-home-color-logo{display:flex !important;align-items:center !important;min-height:54px !important;height:54px !important;margin:0 0 .28rem !important;overflow:hidden !important;}
        .ln-home-color-logo img{display:block !important;width:190px !important;max-width:190px !important;height:auto !important;margin:0 !important;object-fit:contain !important;}
        @media(max-height:820px) and (min-width:901px){
            [data-testid="stSidebar"] .stButton button{min-height:2.64rem !important;}
            [data-testid="stSidebar"] .stButton button p{font-size:.92rem !important;}
            [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{width:2.05rem !important;height:2.05rem !important;flex-basis:2.05rem !important;}
        }
'''
app = insert_before_style_end(app, "/* RC31.19 navigation density */", app_css)

if 'HOME_LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo-tight.png"' not in app:
    app = app.replace(
        'LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo.png"\n',
        'LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo.png"\nHOME_LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo-tight.png"\n',
        1,
    )

old_home = '''    if page == "Início":
        if LOGO_PATH.exists():
            st.markdown('<div class="ln-home-color-logo">', unsafe_allow_html=True)
            st.image(str(LOGO_PATH), width=190)
            st.markdown('</div>', unsafe_allow_html=True)
        essential_home_page(db, user)'''
new_home = '''    if page == "Início":
        home_logo = HOME_LOGO_PATH if HOME_LOGO_PATH.exists() else LOGO_PATH
        if home_logo.exists():
            logo_data = base64.b64encode(home_logo.read_bytes()).decode("ascii")
            st.markdown(
                f'<div class="ln-home-color-logo"><img src="data:image/png;base64,{logo_data}" alt="LicitaNexo"></div>',
                unsafe_allow_html=True,
            )
        essential_home_page(db, user)'''
if old_home in app:
    app = app.replace(old_home, new_home, 1)
elif 'home_logo = HOME_LOGO_PATH if HOME_LOGO_PATH.exists() else LOGO_PATH' not in app:
    raise RuntimeError("RC31.19 home logo anchor not found")
APP.write_text(app, encoding="utf-8")

config = CONFIG.read_text(encoding="utf-8")
config = re.sub(r'APP_VERSION = "1\.0 Essential RC31\.\d+"', 'APP_VERSION = "1.0 Essential RC31.20"', config, count=1)
CONFIG.write_text(config, encoding="utf-8")

for path in TESTS.glob("test_*.py"):
    text = path.read_text(encoding="utf-8")
    updated = text.replace('APP_VERSION = "1.0 Essential RC31.19"', 'APP_VERSION = "1.0 Essential RC31.20"')
    if updated != text:
        path.write_text(updated, encoding="utf-8")

contract = TESTS / "test_rc31_20_layout_polish.py"
contract.write_text(
    '''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass Rc3120LayoutPolishContracts(unittest.TestCase):\n    def test_version(self):\n        cfg = (ROOT / "src" / "config.py").read_text(encoding="utf-8")\n        self.assertIn('APP_VERSION = "1.0 Essential RC31.20"', cfg)\n\n    def test_logout_does_not_overlay_navigation(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn("/* RC31.20 viewport polish */", app)\n        self.assertIn(".st-key-sidebar_logout{position:relative !important", app)\n        self.assertIn("min-height:2.82rem !important", app)\n\n    def test_home_uses_tight_logo_asset(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn("HOME_LOGO_PATH", app)\n        self.assertIn("ln-home-color-logo", app)\n        self.assertIn("data:image/png;base64", app)\n        self.assertTrue((ROOT / "assets" / "licitanexo-logo-tight.png").exists())\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
    encoding="utf-8",
)

print("RC31.20 applied")
