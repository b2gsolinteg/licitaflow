from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor ausente: {label}")
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# app.py · design system global, sidebar e login
# -----------------------------------------------------------------------------
p = Path("app.py")
s = p.read_text(encoding="utf-8")

start = s.index("def apply_brand():")
end = s.index("\n\ndef brand_header", start)
apply_brand = r'''def apply_brand():
    st.markdown("""
        <style>
        :root{--ln-navy:#0B2944;--ln-teal:#0E7C75;--ln-teal-dark:#0A655F;--ln-bg:#F4F7FA;--ln-card:#FFFFFF;--ln-text:#172B3A;--ln-muted:#667786;--ln-border:#DEE6EC;}
        html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{font-family:Inter,"Segoe UI",Arial,sans-serif !important;color:var(--ln-text) !important;}
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--ln-bg) !important;}
        header[data-testid="stHeader"]{display:block !important;background:var(--ln-navy) !important;height:58px !important;border-bottom:1px solid rgba(255,255,255,.08) !important;box-shadow:0 1px 10px rgba(7,29,48,.10) !important;}
        [data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none !important;}
        [data-testid="stSidebar"]{background:#FFFFFF !important;border-right:1px solid #E2E8EE !important;box-shadow:2px 0 14px rgba(25,39,52,.035) !important;}
        [data-testid="stSidebar"] *{color:#223544 !important;}
        [data-testid="stSidebar"] > div:first-child{overflow-y:auto !important;overflow-x:hidden !important;max-height:100vh !important;padding-bottom:1rem !important;}
        @media(min-width:901px){[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:276px !important;min-width:276px !important;max-width:276px !important;}}
        [data-testid="stSidebar"] .stButton button{width:100% !important;min-height:3.55rem !important;justify-content:flex-start !important;background:transparent !important;color:#223544 !important;border:1px solid transparent !important;border-radius:13px !important;box-shadow:none !important;padding:.38rem .55rem !important;gap:.72rem !important;font-size:.91rem !important;font-weight:650 !important;transition:background .15s ease,border-color .15s ease,transform .15s ease !important;}
        [data-testid="stSidebar"] .stButton button:hover{background:#F7F9FB !important;border-color:#E7ECF0 !important;transform:translateX(1px);}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#F1F7F6 !important;color:#0D5F5A !important;border-color:#D6E8E5 !important;box-shadow:inset 3px 0 0 #16877F !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{display:inline-flex !important;align-items:center !important;justify-content:center !important;flex:0 0 2.75rem !important;width:2.75rem !important;height:2.75rem !important;border-radius:13px !important;background:#F2F5F7 !important;color:#58717F !important;font-size:1.35rem !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_0 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_1 [data-testid="stIconMaterial"]{background:#E4F4EE !important;color:#248466 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_2 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_3 [data-testid="stIconMaterial"]{background:#E7EFFB !important;color:#3E70B7 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_4 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_5 [data-testid="stIconMaterial"]{background:#EEE9F8 !important;color:#765BA0 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_6 [data-testid="stIconMaterial"]{background:#FFF2CF !important;color:#A87822 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_7 [data-testid="stIconMaterial"]{background:#FBE8E8 !important;color:#A85C5C !important;}
        [data-testid="stSidebar"] .st-key-nav_work_0 [data-testid="stIconMaterial"]{background:#F5E7F0 !important;color:#93627D !important;}
        [data-testid="stSidebar"] .st-key-nav_work_1 [data-testid="stIconMaterial"]{background:#E7F3F5 !important;color:#357F88 !important;}
        [data-testid="stSidebar"] .st-key-nav_account_0 [data-testid="stIconMaterial"]{background:#E8F1FB !important;color:#4478B4 !important;}
        [data-testid="stSidebar"] .st-key-nav_account_1 [data-testid="stIconMaterial"]{background:#E9F4E5 !important;color:#5F8A4B !important;}
        [data-testid="stSidebar"] .st-key-nav_account_2 [data-testid="stIconMaterial"]{background:#FFF0E1 !important;color:#A66D35 !important;}
        [data-testid="stSidebar"] .st-key-nav_account_3 [data-testid="stIconMaterial"]{background:#E9EFF7 !important;color:#526F94 !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{margin-top:.8rem !important;margin-bottom:.18rem !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.70rem !important;font-weight:750 !important;letter-spacing:.10em !important;text-transform:uppercase !important;color:#8A9AA8 !important;}
        [data-testid="stSidebar"] [data-testid="stImage"] img{max-width:188px !important;width:188px !important;margin:.35rem auto .1rem !important;display:block !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout button{justify-content:center !important;min-height:2.8rem !important;background:#F7F9FB !important;border:1px solid #E1E8ED !important;color:#536675 !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout [data-testid="stIconMaterial"]{background:transparent !important;width:auto !important;height:auto !important;flex:0 0 auto !important;border-radius:0 !important;color:#6E7F8C !important;}
        .block-container{padding-top:1.5rem !important;padding-bottom:2.6rem !important;max-width:1220px !important;}
        div[data-testid="stVerticalBlockBorderWrapper"],div[data-testid="stMetric"]{background:#FFFFFF !important;border:1px solid #DEE6EC !important;border-radius:16px !important;box-shadow:0 4px 16px rgba(31,52,69,.045) !important;}
        [data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"] > div,textarea{background:#FFFFFF !important;color:#243746 !important;border-color:#CCD7DF !important;border-radius:11px !important;box-shadow:none !important;}
        input,textarea{background:#FFFFFF !important;color:#243746 !important;-webkit-text-fill-color:#243746 !important;}
        .stButton>button,.stDownloadButton>button{background:#FFFFFF !important;color:#263947 !important;border:1px solid #CCD7DF !important;border-radius:11px !important;box-shadow:none !important;font-weight:600 !important;}
        .stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:var(--ln-teal) !important;color:#FFFFFF !important;border-color:var(--ln-teal) !important;box-shadow:0 3px 8px rgba(14,124,117,.13) !important;}
        .stButton>button[kind="primary"]:hover,.stDownloadButton>button[kind="primary"]:hover{background:var(--ln-teal-dark) !important;border-color:var(--ln-teal-dark) !important;}
        .brand-mark{font-size:2.1rem;color:#293746;line-height:1}.brand-mark span{color:#5F858A}.brand-tagline{color:#667786;margin-top:.45rem;margin-bottom:1.4rem}
        @media(max-width:900px){header[data-testid="stHeader"]{height:50px !important;}.block-container{padding-top:.9rem !important;padding-left:.8rem !important;padding-right:.8rem !important;}.stButton button,.stDownloadButton button{min-height:2.65rem;}}
        </style>
    """, unsafe_allow_html=True)
'''
s = s[:start] + apply_brand.rstrip() + s[end:]

# Sidebar account card: stronger hierarchy, still restrained.
s = s.replace(
    'f\'<div style="background:#F7F9FC;border:1px solid #E3E8EF;border-radius:12px;padding:.65rem .72rem;margin-bottom:.75rem">\'\n            f\'<div style="font-weight:400;color:#172033">{_greeting(user)}</div>\'',
    'f\'<div style="background:#F6F9FA;border:1px solid #E0E8ED;border-radius:14px;padding:.72rem .78rem;margin:.25rem 0 .8rem">\'\n            f\'<div style="font-weight:650;color:#172B3A">{_greeting(user)}</div>\'',
)
s = s.replace('_nav_group("CONTA", account_pages, "account")', '_nav_group("MINHA CONTA", account_pages, "account")')
s = s.replace('"Radar de licitações": ":material/notifications_active:"', '"Radar de licitações": ":material/radar:"')
s = s.replace('"Minha lista": ":material/bookmarks:"', '"Minha lista": ":material/bookmark:"')

# Login: same visual language as the internal product, with more hierarchy and trust.
s = replace_once(
    s,
    'html, body, [data-testid="stAppViewContainer"], .stApp {margin:0 !important;padding:0 !important;background:#FFFFFF !important;min-height:100vh !important;color:#293746 !important;overflow:auto !important;}',
    'html, body, [data-testid="stAppViewContainer"], .stApp {margin:0 !important;padding:0 !important;background:#F4F7FA !important;min-height:100vh !important;color:#172B3A !important;overflow:auto !important;font-family:Inter,"Segoe UI",Arial,sans-serif !important;}',
    "login background",
)
s = replace_once(
    s,
    '.block-container{max-width:1120px !important;width:100% !important;margin:0 auto !important;padding:4rem 2rem !important;}',
    '.block-container{max-width:1180px !important;width:100% !important;margin:0 auto !important;padding:3.4rem 2rem !important;}',
    "login container",
)
s = replace_once(
    s,
    'div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{background:#FFFFFF !important;padding:0 !important;}',
    'div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{background:transparent !important;padding:0 !important;}',
    "login columns",
)
s = replace_once(
    s,
    '.ln-login-intro{color:#293746;font-size:1.9rem;line-height:1.22;margin:.8rem 0 .65rem;}',
    '.ln-login-eyebrow{display:inline-flex;align-items:center;background:#E5F4EF;color:#23715D;border:1px solid #CDE8DE;border-radius:999px;padding:.28rem .58rem;font-size:.70rem;font-weight:750 !important;letter-spacing:.07em;margin:.75rem 0 .7rem}.ln-login-intro{color:#152B3B;font-size:2.2rem;line-height:1.14;margin:.2rem 0 .75rem;font-weight:750 !important;letter-spacing:-.025em;}',
    "login hierarchy",
)
s = replace_once(
    s,
    '.st-key-auth_card{width:100% !important;max-width:560px !important;margin:0 auto !important;padding:1.25rem 1.35rem 1.35rem !important;background:#FFFFFF !important;border:1px solid #DCE3E8 !important;border-radius:14px !important;box-shadow:none !important;}',
    '.st-key-auth_card{width:100% !important;max-width:560px !important;margin:0 auto !important;padding:1.45rem 1.55rem 1.55rem !important;background:#FFFFFF !important;border:1px solid #DCE5EB !important;border-radius:18px !important;box-shadow:0 18px 45px rgba(25,45,61,.08) !important;}',
    "login card",
)
s = replace_once(
    s,
    '.ln-auth-nav a.active{color:#293746 !important;border-color:#AFC5C8 !important;background:#EDF3F4 !important;}',
    '.ln-auth-nav a.active{color:#0C625D !important;border-color:#B7D8D4 !important;background:#EDF7F5 !important;font-weight:650 !important;}',
    "login nav active",
)
s = replace_once(
    s,
    '.st-key-auth_card .stFormSubmitButton button{min-height:3rem !important;border-radius:9px !important;background:#EAF2F3 !important;color:#293746 !important;border:1px solid #ADC6C9 !important;box-shadow:none !important;font-size:.94rem !important;}',
    '.st-key-auth_card .stFormSubmitButton button{min-height:3.15rem !important;border-radius:11px !important;background:#0E7C75 !important;color:#FFFFFF !important;border:1px solid #0E7C75 !important;box-shadow:0 4px 12px rgba(14,124,117,.14) !important;font-size:.95rem !important;font-weight:650 !important;}',
    "login primary button",
)
s = replace_once(
    s,
    '        st.markdown(\'<div class="ln-login-intro">Encontre oportunidades para vender ao governo.</div>\', unsafe_allow_html=True)',
    '        st.markdown(\'<div class="ln-login-eyebrow">LICITANEXO ESSENTIAL</div>\', unsafe_allow_html=True)\n        st.markdown(\'<div class="ln-login-intro">Encontre oportunidades para vender ao governo.</div>\', unsafe_allow_html=True)',
    "login eyebrow",
)

p.write_text(s, encoding="utf-8")


# -----------------------------------------------------------------------------
# src/essential_discovery.py · visual premium e páginas de descoberta
# -----------------------------------------------------------------------------
p = Path("src/essential_discovery.py")
s = p.read_text(encoding="utf-8")

start = s.index("def _apply_styles() -> None:")
end = s.index("\n\n@st.cache_data", start)
styles_and_header = r'''def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stMain"]{background:#F4F7FA !important;}
        [data-testid="stMain"] .block-container{max-width:1180px !important;padding-top:1.35rem !important;}
        [data-testid="stMain"] *{font-family:Inter,"Segoe UI",Arial,sans-serif !important;}
        [data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3{color:#172B3A !important;font-weight:700 !important;letter-spacing:-.015em !important;}
        [data-testid="stMain"] p,[data-testid="stMain"] label p,[data-testid="stMain"] .stCaption p{color:#526675 !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{background:#FFFFFF !important;border:1px solid #DEE6EC !important;border-radius:16px !important;box-shadow:0 5px 18px rgba(30,52,69,.055) !important;}
        [data-testid="stMain"] [data-testid="stForm"]{background:#FFFFFF !important;border:1px solid #DEE6EC !important;border-radius:16px !important;padding:1rem 1rem .9rem !important;box-shadow:0 5px 18px rgba(30,52,69,.045) !important;}
        .ln-page-kicker{display:inline-flex;align-items:center;background:#E4F4EE;color:#23715D;border:1px solid #CDE8DE;border-radius:999px;padding:.25rem .58rem;font-size:.68rem;font-weight:750 !important;letter-spacing:.07em;text-transform:uppercase;margin:0 0 .55rem;}
        .ln-discovery-title{font-size:2.05rem;font-weight:750 !important;letter-spacing:-.025em;margin:.02rem 0 .28rem;color:#172B3A;line-height:1.12}
        .ln-discovery-sub{color:#667786;font-size:.96rem;margin:0 0 1.15rem;line-height:1.5;max-width:58rem}
        .ln-modality-badge{display:inline-block;background:#EDF3F8;color:#4D687B;border:1px solid #D9E4EC;border-radius:999px;padding:.24rem .62rem;font-size:.69rem;font-weight:650 !important;text-transform:uppercase;letter-spacing:.045em}
        .ln-reference{font-size:1.12rem;color:#172B3A;margin:.48rem 0 .75rem;font-weight:700 !important;line-height:1.32}
        .ln-info-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.62rem;margin:.2rem 0 .9rem}
        .ln-info-box,.ln-meta-box{background:#F8FAFB;border:1px solid #E3E9EE;border-radius:12px;padding:.75rem .8rem;min-height:82px}
        .ln-info-label,.ln-meta-label{font-size:.67rem;color:#7B8B98;text-transform:uppercase;letter-spacing:.055em;margin-bottom:.32rem;font-weight:700 !important}
        .ln-info-value,.ln-meta-value{color:#263947;font-size:.9rem;line-height:1.3;font-weight:600 !important}
        .ln-info-extra,.ln-meta-help{color:#71808D;font-size:.70rem;margin-top:.34rem;line-height:1.32}
        .ln-object-label{font-size:.69rem;color:#6F808E;text-transform:uppercase;letter-spacing:.055em;margin:.38rem 0 .2rem;font-weight:700 !important}
        .ln-meta-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.62rem;margin:.7rem 0}
        .ln-meta-link{color:#0D6F69;text-decoration:none;border-bottom:1px solid #B4D3D0;font-weight:650 !important}
        .ln-items-box{background:#F8FAFB;border:1px solid #E1E8ED;border-radius:13px;padding:.78rem .82rem;margin:.72rem 0}
        .ln-items-title{color:#172B3A;font-size:.88rem;margin-bottom:.44rem;font-weight:700 !important}
        .ln-item-row{display:grid;grid-template-columns:48px minmax(0,1fr) 130px 132px;gap:.5rem;align-items:start;padding:.45rem .08rem;border-top:1px solid #E8EDF1;color:#344452}
        .ln-item-row:first-of-type{border-top:0}.ln-item-number,.ln-item-qty,.ln-item-price{font-size:.74rem;line-height:1.32;color:#667786}.ln-item-desc{font-size:.79rem;line-height:1.34;color:#293C49}.ln-item-qty,.ln-item-price{text-align:right}.ln-items-note{font-size:.72rem;color:#71808D;margin-top:.35rem}
        [data-testid="stMain"] .stButton button,[data-testid="stMain"] .stDownloadButton button{background:#FFFFFF !important;color:#263947 !important;border:1px solid #CBD7DF !important;border-radius:11px !important;box-shadow:none !important;font-weight:600 !important;}
        [data-testid="stMain"] .stButton button[kind="primary"],[data-testid="stMain"] button[kind="primary"]{background:#0E7C75 !important;color:#FFFFFF !important;border:1px solid #0E7C75 !important;box-shadow:0 4px 10px rgba(14,124,117,.12) !important;}
        [data-testid="stMain"] .stButton button:hover{border-color:#9FB3C0 !important;}
        [data-testid="stMain"] .stButton button[kind="primary"]:hover{background:#0A655F !important;border-color:#0A655F !important;}
        .ln-home-count{font-size:1.52rem;color:#0B4160;margin:.2rem 0 .85rem;font-weight:700 !important;}
        .ln-home-value{background:#FFFFFF;border:1px solid #DCE7EA;border-left:4px solid #55A89F;border-radius:14px;padding:.85rem 1rem;margin:.65rem 0 1rem;color:#4F6573;font-size:.9rem;line-height:1.48;box-shadow:0 4px 14px rgba(30,52,69,.035)}
        .ln-home-section{font-size:.72rem;color:#7A8A97;margin:1rem 0 .5rem;font-weight:750 !important;letter-spacing:.08em;text-transform:uppercase}
        .ln-shortcut-copy{min-height:2.25rem;color:#71808D;font-size:.76rem;line-height:1.38;margin:.05rem 0 .55rem;}
        .ln-state-name{font-size:1.02rem;color:#172B3A;font-weight:700 !important;margin:.42rem 0 0}.ln-state-code{font-size:.78rem;color:#7A8B98;margin-left:.25rem;font-weight:600 !important}.ln-state-count{font-size:1.85rem;color:#0B4B76;font-weight:750 !important;line-height:1.05;margin:.9rem 0 .05rem}.ln-state-label{font-size:.78rem;color:#748592;margin-bottom:.65rem}.ln-state-card-note{font-size:.70rem;color:#8A99A5;margin-top:.2rem}.ln-state-grid-title{font-size:.73rem;color:#788995;font-weight:750 !important;letter-spacing:.08em;text-transform:uppercase;margin:.95rem 0 .48rem}
        .ln-portal-name,.ln-modality-name{font-size:1rem;color:#172B3A;font-weight:700 !important;margin-bottom:.2rem}.ln-card-count{font-size:1.55rem;color:#0B4B76;font-weight:750 !important;margin:.55rem 0 .08rem;line-height:1}.ln-card-caption{font-size:.76rem;color:#748592;margin-bottom:.65rem}
        [data-testid="stMain"] div[class*="st-key-state_"] button{min-height:2.7rem !important;}
        @media(max-width:900px){.ln-info-grid,.ln-meta-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.ln-item-row{grid-template-columns:38px minmax(0,1fr)}.ln-item-qty,.ln-item-price{text-align:left;grid-column:2}.ln-discovery-title{font-size:1.72rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="ln-page-kicker">{escape(kicker)}</div>'
        f'<div class="ln-discovery-title">{escape(title)}</div>'
        f'<div class="ln-discovery-sub">{escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )
'''
s = s[:start] + styles_and_header.rstrip() + s[end:]

# Home rewritten to make the first screen feel dense, useful and premium.
start = s.index("def home_page(db, user: dict) -> None:")
end = s.index("\n\ndef portal_page", start)
home = r'''def home_page(db, user: dict) -> None:
    _apply_styles()
    counts = db.global_catalog_group_counts("state", closing_from=date.today().isoformat())
    open_total = sum(int(row.get("total") or 0) for row in counts)

    _page_header(
        "COMECE POR AQUI",
        "Descubra o que o governo está comprando.",
        "Você não precisa adivinhar o que vender. Pesquise editais de todo o Brasil e veja os itens da compra já na tela.",
    )
    st.markdown(f'<div class="ln-home-count">{open_total:,} editais abertos para participação</div>'.replace(",", "."), unsafe_allow_html=True)
    st.markdown(
        '<div class="ln-home-value"><strong>O diferencial do LicitaNexo:</strong> o edital já aparece com os itens da compra. Você entende a oportunidade antes de perder tempo abrindo documento por documento.</div>',
        unsafe_allow_html=True,
    )

    with st.form("essential_home_search", clear_on_submit=False, enter_to_submit=False):
        keyword = st.text_input("O que você procura?", placeholder="Ex.: papel A4, pneus, medicamentos, uniformes...")
        if st.form_submit_button("Buscar licitações", type="primary", icon=":material/search:", width="stretch"):
            st.session_state["essential_search_criteria"] = _criteria(keyword=keyword.strip())
            st.session_state["essential_search_page"] = 1
            st.session_state["_navigation_request"] = "Buscar licitações"
            st.rerun()

    st.markdown('<div class="ln-home-section">Explore de outras formas</div>', unsafe_allow_html=True)
    shortcuts = [
        ("Por Estado", "Estados", "Veja os editais abertos em cada UF.", ":material/map:"),
        ("Por Cidade", "Cidades", "Procure oportunidades em uma cidade específica.", ":material/location_on:"),
        ("Por Modalidade", "Modalidades", "Escolha pregão, dispensa, concorrência e outras.", ":material/category:"),
        ("Por site de disputa", "Sites de disputa", "Veja onde a participação acontece.", ":material/language:"),
    ]
    cols = st.columns(4)
    for col, (target, label, description, icon) in zip(cols, shortcuts):
        with col.container(border=True):
            st.markdown(f'<div class="ln-shortcut-copy">{description}</div>', unsafe_allow_html=True)
            if st.button(label, icon=icon, key=f"home_{target}", width="stretch"):
                st.session_state["_navigation_request"] = target
                st.rerun()
'''
s = s[:start] + home.rstrip() + s[end:]

# Portal discovery with stronger card hierarchy.
start = s.index("def portal_page(db, user: dict) -> None:")
end = s.index("\n\ndef search_page", start)
portal = r'''def portal_page(db, user: dict) -> None:
    _apply_styles()
    _page_header("EXPLORAR LICITAÇÕES", "Por site de disputa", "Escolha onde deseja participar. Se não tiver preferência, consulte todos os sites.")

    if st.button("Ver todos os sites", icon=":material/public:", key="portal_all", type="primary", width="stretch"):
        st.session_state["essential_search_criteria"] = _criteria(portal="Todos os sites")
        st.session_state["essential_search_page"] = 1
        st.session_state["_navigation_request"] = "Buscar licitações"
        st.rerun()

    st.markdown('<div class="ln-state-grid-title">Portais disponíveis</div>', unsafe_allow_html=True)
    portals = list(PORTAL_ACCESS.keys())
    for start_index in range(0, len(portals), 3):
        cols = st.columns(3)
        for col, portal_name in zip(cols, portals[start_index:start_index + 3]):
            access = portal_access_info(portal_name)
            with col.container(border=True):
                st.markdown(f'<div class="ln-portal-name">{escape(portal_name)}</div>', unsafe_allow_html=True)
                st.caption(f"Custo do acesso: {access['label']}")
                st.caption(access["detail"])
                if st.button("Ver oportunidades", icon=":material/arrow_forward:", key=f"portal_{portal_name}", width="stretch"):
                    st.session_state["essential_search_criteria"] = _criteria(portal=portal_name)
                    st.session_state["essential_search_page"] = 1
                    st.session_state["_navigation_request"] = "Buscar licitações"
                    st.rerun()
'''
s = s[:start] + portal.rstrip() + s[end:]

# State discovery is the visual showcase: all UFs, real flags and large counts.
start = s.index("def state_page(db, user: dict) -> None:")
end = s.index("\n\ndef city_page", start)
state_page = r'''def state_page(db, user: dict) -> None:
    _apply_styles()
    counts = db.global_catalog_group_counts("state", closing_from=date.today().isoformat())
    count_by_state = {str(row.get("label") or "").upper(): int(row.get("total") or 0) for row in counts}
    open_total = sum(count_by_state.values())
    _page_header(
        "EXPLORAR LICITAÇÕES",
        "Por Estado",
        f"Escolha uma UF para ver oportunidades abertas. Hoje o catálogo reúne {open_total:,} editais ativos no Brasil.".replace(",", "."),
    )
    st.markdown('<div class="ln-state-grid-title">Estados do Brasil</div>', unsafe_allow_html=True)
    for start_index in range(0, len(BRAZIL_STATES), 3):
        cols = st.columns(3)
        for col, state in zip(cols, BRAZIL_STATES[start_index:start_index + 3]):
            total = count_by_state.get(state, 0)
            with col.container(border=True):
                flag = FLAGS_DIR / f"{state.lower()}.svg"
                if flag.exists():
                    st.image(str(flag), width=68)
                st.markdown(
                    f'<div class="ln-state-name">{escape(STATE_NAMES.get(state, state))}<span class="ln-state-code">({escape(state)})</span></div>'
                    f'<div class="ln-state-count">{total:,}</div><div class="ln-state-label">editais abertos</div>'.replace(",", "."),
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Ver oportunidades", icon=":material/arrow_forward:", key=f"state_{state}",
                    type="primary", width="stretch", disabled=total <= 0,
                ):
                    st.session_state["essential_search_criteria"] = _criteria(states=[state])
                    st.session_state["essential_search_page"] = 1
                    st.session_state["_navigation_request"] = "Buscar licitações"
                    st.rerun()
'''
s = s[:start] + state_page.rstrip() + s[end:]

# City page: clear task, card-like form.
start = s.index("def city_page(db, user: dict) -> None:")
end = s.index("\n\ndef modality_page", start)
city_page = r'''def city_page(db, user: dict) -> None:
    _apply_styles()
    _page_header("EXPLORAR LICITAÇÕES", "Por Cidade", "Digite uma cidade e, se quiser, refine pelo Estado.")
    with st.form("essential_city_search", clear_on_submit=False, enter_to_submit=False):
        city = st.text_input("Nome da cidade", placeholder="Ex.: Londrina")
        state = st.selectbox("Estado (opcional)", ["Todos", *BRAZIL_STATES])
        if st.form_submit_button("Buscar oportunidades", type="primary", icon=":material/search:", width="stretch"):
            if not city.strip():
                st.warning("Digite o nome da cidade.")
            else:
                st.session_state["essential_search_criteria"] = _criteria(
                    city=city.strip(), states=[] if state == "Todos" else [state]
                )
                st.session_state["essential_search_page"] = 1
                st.session_state["_navigation_request"] = "Buscar licitações"
                st.rerun()
'''
s = s[:start] + city_page.rstrip() + s[end:]

# Modality page: counts receive the same hierarchy as state cards.
start = s.index("def modality_page(db, user: dict) -> None:")
end = s.index("\n\ndef advanced_search_page", start)
modality_page = r'''def modality_page(db, user: dict) -> None:
    _apply_styles()
    _page_header("EXPLORAR LICITAÇÕES", "Por Modalidade", "Escolha a modalidade para ver os editais abertos para participação.")
    counts = db.global_catalog_group_counts("modality", closing_from=date.today().isoformat())
    if not counts:
        st.info("Ainda não há modalidades disponíveis no catálogo.")
        return
    st.markdown('<div class="ln-state-grid-title">Modalidades disponíveis</div>', unsafe_allow_html=True)
    for start_index in range(0, len(counts), 3):
        cols = st.columns(3)
        for col, row in zip(cols, counts[start_index:start_index + 3]):
            label = str(row.get("label") or "Não informada")
            total = int(row.get("total") or 0)
            with col.container(border=True):
                st.markdown(
                    f'<div class="ln-modality-name">{escape(label)}</div>'
                    f'<div class="ln-card-count">{total:,}</div><div class="ln-card-caption">editais abertos</div>'.replace(",", "."),
                    unsafe_allow_html=True,
                )
                if st.button("Ver oportunidades", icon=":material/arrow_forward:", key=f"modality_{label}", width="stretch"):
                    st.session_state["essential_search_criteria"] = _criteria(modalities=[label])
                    st.session_state["essential_search_page"] = 1
                    st.session_state["_navigation_request"] = "Buscar licitações"
                    st.rerun()
'''
s = s[:start] + modality_page.rstrip() + s[end:]

# Upgrade page headers without touching functional logic of the forms/results.
replacements = {
    "st.markdown('<div class=\"ln-discovery-title\">Buscar licitações</div>', unsafe_allow_html=True)\n    st.markdown('<div class=\"ln-discovery-sub\">Escolha só o que fizer sentido. Campos vazios deixam a busca mais ampla.</div>', unsafe_allow_html=True)":
        '_page_header("ENCONTRE OPORTUNIDADES", "Buscar licitações", "Escolha só o que fizer sentido. Campos vazios deixam a busca mais ampla.")',
    "st.markdown('<div class=\"ln-discovery-title\">Filtro avançado</div>', unsafe_allow_html=True)\n    st.markdown('<div class=\"ln-discovery-sub\">Combine os filtros que quiser. Nenhum campo é obrigatório.</div>', unsafe_allow_html=True)":
        '_page_header("REFINE SUA BUSCA", "Filtro avançado", "Combine os filtros que quiser. Nenhum campo é obrigatório.")',
    "st.markdown('<div class=\"ln-discovery-title\">Em destaque</div>', unsafe_allow_html=True)\n    st.markdown('<div class=\"ln-discovery-sub\">50 editais recentes para você explorar sem precisar definir uma busca.</div>', unsafe_allow_html=True)":
        '_page_header("DESCUBRA OPORTUNIDADES", "Em destaque", "50 editais recentes para você explorar sem precisar definir uma busca.")',
    "st.markdown('<div class=\"ln-discovery-title\">Minha lista</div>', unsafe_allow_html=True)\n    st.markdown('<div class=\"ln-discovery-sub\">Decida apenas se vai participar, não vai participar ou quer descartar o edital.</div>', unsafe_allow_html=True)":
        '_page_header("ORGANIZE SUAS OPORTUNIDADES", "Minha lista", "Decida apenas se vai participar, não vai participar ou quer descartar o edital.")',
    "st.markdown('<div class=\"ln-discovery-title\">Preferências</div>', unsafe_allow_html=True)\n    st.markdown('<div class=\"ln-discovery-sub\">Se quiser, salve o que costuma procurar. Isso ajuda o Radar, mas não é obrigatório.</div>', unsafe_allow_html=True)":
        '_page_header("PERSONALIZE O LICITANEXO", "Preferências", "Se quiser, salve o que costuma procurar. Isso ajuda o Radar, mas não é obrigatório.")',
    "st.markdown('<div class=\"ln-discovery-title\">Radar de licitações</div>', unsafe_allow_html=True)\n    st.markdown('<div class=\"ln-discovery-sub\">Veja editais novos relacionados ao que você escolheu acompanhar.</div>', unsafe_allow_html=True)":
        '_page_header("ACOMPANHE O QUE IMPORTA", "Radar de licitações", "Veja editais novos relacionados ao que você escolheu acompanhar.")',
}
for old, new in replacements.items():
    if old not in s:
        raise SystemExit(f"anchor ausente: header {old[:45]}")
    s = s.replace(old, new, 1)

# Modern pagination glyphs -> Material Symbols.
s = replace_once(
    s,
    'if n1.button("◀ Anterior", disabled=current <= 1, key=f"{page_key}_prev", width="stretch"):',
    'if n1.button("Anterior", icon=":material/chevron_left:", disabled=current <= 1, key=f"{page_key}_prev", width="stretch"):',
    "pagination previous",
)
s = replace_once(
    s,
    'if n3.button("Próxima ▶", disabled=current >= total_pages, key=f"{page_key}_next", width="stretch"):',
    'if n3.button("Próxima", icon=":material/chevron_right:", disabled=current >= total_pages, key=f"{page_key}_next", width="stretch"):',
    "pagination next",
)

p.write_text(s, encoding="utf-8")


# -----------------------------------------------------------------------------
# Version, regression contracts and release notes
# -----------------------------------------------------------------------------
p = Path("src/config.py")
s = p.read_text(encoding="utf-8")
s = replace_once(s, 'APP_VERSION = "1.0 Essential RC31.11"', 'APP_VERSION = "1.0 Essential RC31.12"', "version")
p.write_text(s, encoding="utf-8")

for test_path in Path("tests").glob("test_rc31_*.py"):
    text = test_path.read_text(encoding="utf-8")
    text = text.replace('APP_VERSION = "1.0 Essential RC31.11"', 'APP_VERSION = "1.0 Essential RC31.12"')
    text = text.replace('"Minha lista": ":material/bookmarks:"', '"Minha lista": ":material/bookmark:"')
    test_path.write_text(text, encoding="utf-8")

Path("tests/test_rc31_12_premium_ui.py").write_text(
    '''from pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\n\nclass PremiumUiContracts(unittest.TestCase):\n    def test_version(self):\n        cfg=(ROOT/"src"/"config.py").read_text(encoding="utf-8")\n        self.assertIn('APP_VERSION = "1.0 Essential RC31.12"', cfg)\n\n    def test_sidebar_has_large_pastel_icon_tiles_and_sections(self):\n        app=(ROOT/"app.py").read_text(encoding="utf-8")\n        self.assertIn('width:2.75rem !important', app)\n        self.assertIn('min-height:3.55rem !important', app)\n        self.assertIn('_nav_group("MINHA CONTA", account_pages, "account")', app)\n        self.assertIn('"Radar de licitações": ":material/radar:"', app)\n        self.assertIn('"Minha lista": ":material/bookmark:"', app)\n\n    def test_internal_app_uses_depth_and_strong_typography(self):\n        src=(ROOT/"src"/"essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('background:#F4F7FA !important', src)\n        self.assertIn('font-weight:750 !important', src)\n        self.assertIn('box-shadow:0 5px 18px', src)\n        self.assertIn('background:#0E7C75 !important', src)\n\n    def test_state_page_uses_real_flags_and_large_counts(self):\n        src=(ROOT/"src"/"essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('FLAGS_DIR / f"{state.lower()}.svg"', src)\n        self.assertIn('class="ln-state-count"', src)\n        self.assertIn('"Ver oportunidades", icon=":material/arrow_forward:"', src)\n        self.assertIn('for start_index in range(0, len(BRAZIL_STATES), 3):', src)\n\n    def test_page_kickers_create_hierarchy(self):\n        src=(ROOT/"src"/"essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn('def _page_header', src)\n        self.assertIn('"EXPLORAR LICITAÇÕES"', src)\n        self.assertIn('"ENCONTRE OPORTUNIDADES"', src)\n        self.assertIn('"ORGANIZE SUAS OPORTUNIDADES"', src)\n\nif __name__ == "__main__": unittest.main()\n''',
    encoding="utf-8",
)

Path("docs/rc31-12-premium-ui.md").write_text(
    """# RC31.12 · linguagem visual premium\n\nObjetivo: elevar a percepção de qualidade do LicitaNexo sem copiar concorrentes, usando os ativos e diferenciais próprios do produto.\n\n- Fundo principal cinza-claro, cards brancos e barra superior azul-marinho para criar profundidade.\n- Tipografia com hierarquia mais forte: títulos e números importantes recebem peso visual real.\n- Sidebar ampliada para 276 px, com Material Symbols grandes em blocos pastéis e grupos bem separados.\n- `Minha lista` mantém bookmark; `Radar` usa símbolo de radar.\n- CTAs principais usam teal da marca, com contraste alto.\n- Página Por Estado mostra todas as UFs em grade de três colunas, bandeiras reais e contadores grandes.\n- Páginas de Cidade, Modalidade, Portais, Busca, Filtro, Destaques, Lista, Preferências e Radar usam o mesmo sistema visual.\n- Login recebe o mesmo acabamento visual: tipografia forte, card com profundidade e CTA principal teal.\n- Paginação troca glifos por Material Symbols.\n- Sem migration e sem alteração de estrutura de dados.\n""",
    encoding="utf-8",
)
