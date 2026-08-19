from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor ausente: {label}")
    return text.replace(old, new, 1)


# app.py — posicionamento, login e detalhes visuais da sidebar
p = Path("app.py")
s = p.read_text(encoding="utf-8")

s = replace_once(
    s,
    "'Busque editais. Analise. Acompanhe.</div>'",
    "'Encontre editais. Veja os itens. Decida.</div>'",
    "brand header",
)

s = replace_once(
    s,
    '        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#F0F4F5 !important;color:#243746 !important;border-color:#E1E8EC !important;box-shadow:none !important;}\n',
    '        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#F0F4F5 !important;color:#243746 !important;border-color:#E1E8EC !important;box-shadow:none !important;}\n'
    '        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{display:inline-flex !important;align-items:center !important;justify-content:center !important;width:1.75rem !important;height:1.75rem !important;border-radius:8px !important;background:#F3F6F7 !important;color:#58767A !important;}\n'
    '        [data-testid="stSidebar"] .st-key-nav_explore_0 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_1 [data-testid="stIconMaterial"]{background:#E9F3EE !important;color:#4F846E !important;}\n'
    '        [data-testid="stSidebar"] .st-key-nav_explore_2 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_3 [data-testid="stIconMaterial"]{background:#F4EFE8 !important;color:#8A7357 !important;}\n'
    '        [data-testid="stSidebar"] .st-key-nav_explore_4 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_5 [data-testid="stIconMaterial"]{background:#EAF0F4 !important;color:#557387 !important;}\n'
    '        [data-testid="stSidebar"] .st-key-nav_explore_6 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_7 [data-testid="stIconMaterial"]{background:#F0ECF4 !important;color:#766487 !important;}\n'
    '        [data-testid="stSidebar"] .st-key-nav_work_0 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_work_1 [data-testid="stIconMaterial"]{background:#EDF2F5 !important;color:#536F80 !important;}\n'
    '        [data-testid="stSidebar"] .st-key-nav_account_0 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_account_1 [data-testid="stIconMaterial"]{background:#EEF3EA !important;color:#668057 !important;}\n'
    '        [data-testid="stSidebar"] .st-key-nav_account_2 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_account_3 [data-testid="stIconMaterial"]{background:#F4ECEA !important;color:#8A675F !important;}\n',
    "sidebar icon palette",
)

s = replace_once(
    s,
    '        .ln-login-copy{color:#667786;font-size:1rem;line-height:1.55;max-width:32rem;}\n',
    '        .ln-login-copy{color:#667786;font-size:1rem;line-height:1.55;max-width:32rem;}\n'
    '        .ln-login-value{margin:1.15rem 0 0;display:grid;gap:.55rem;max-width:31rem;}\n'
    '        .ln-login-value-item{display:flex;align-items:center;gap:.65rem;color:#526371;font-size:.9rem;}\n'
    '        .ln-login-value-dot{width:1.75rem;height:1.75rem;border-radius:8px;background:#EAF3EF;color:#4F846E;display:flex;align-items:center;justify-content:center;font-size:.72rem;}\n',
    "login value css",
)

s = replace_once(
    s,
    '        st.markdown(\'<div class="ln-login-intro">Licitações sem complicação.</div>\', unsafe_allow_html=True)\n        st.markdown(\'<div class="ln-login-copy">Encontre editais, veja o que o governo quer comprar e organize os certames que você decidiu participar.</div>\', unsafe_allow_html=True)\n',
    '        st.markdown(\'<div class="ln-login-intro">Encontre oportunidades para vender ao governo.</div>\', unsafe_allow_html=True)\n'
    '        st.markdown(\'<div class="ln-login-copy">Você não precisa adivinhar o que vender. Veja primeiro o que o governo está comprando e encontre oportunidades de forma simples.</div>\', unsafe_allow_html=True)\n'
    '        st.markdown(\n'
    '            \'<div class="ln-login-value">\'\n'
    '            \'<div class="ln-login-value-item"><span class="ln-login-value-dot">01</span><span>Editais com os itens da compra já abertos na busca</span></div>\'\n'
    '            \'<div class="ln-login-value-item"><span class="ln-login-value-dot">02</span><span>Pesquisa simples em todo o Brasil</span></div>\'\n'
    '            \'<div class="ln-login-value-item"><span class="ln-login-value-dot">03</span><span>Salve as oportunidades e organize os certames</span></div>\'\n'
    '            \'</div>\',\n'
    '            unsafe_allow_html=True,\n'
    '        )\n',
    "login positioning copy",
)

s = replace_once(
    s,
    "'<strong>R$ 49,90</strong><small>/mês</small></div>'",
    "'<strong>R$ 29,90</strong><small>/mês</small></div>'",
    "login price",
)

s = s.replace("Tela pública de entrada — RC19.8: composição visual final aprovada.", "Tela pública de entrada — RC31.11: valor do Essential e linguagem para iniciantes.")
p.write_text(s, encoding="utf-8")


# essential_discovery.py — home mais densa e diferencial dos itens explícito
p = Path("src/essential_discovery.py")
s = p.read_text(encoding="utf-8")

s = replace_once(
    s,
    '.ln-home-count{font-size:1.55rem;color:#293746;margin:.25rem 0 .95rem;}\n',
    '.ln-home-count{font-size:1.55rem;color:#293746;margin:.25rem 0 .8rem;}\n'
    '.ln-home-value{background:#F7FAFA;border:1px solid #DDE7E8;border-radius:12px;padding:.8rem .9rem;margin:.65rem 0 1rem;color:#526371;font-size:.9rem;line-height:1.45;}\n'
    '.ln-home-section{font-size:.82rem;color:#667786;margin:.9rem 0 .45rem;}\n'
    '.ln-shortcut-copy{min-height:2.1rem;color:#71808D;font-size:.75rem;line-height:1.35;margin:0 0 .45rem;}\n',
    "home styles",
)

start = s.index("def home_page(db, user: dict) -> None:")
end = s.index("\n\ndef portal_page", start)
replacement = '''def home_page(db, user: dict) -> None:
    _apply_styles()
    counts = db.global_catalog_group_counts("state", closing_from=date.today().isoformat())
    open_total = sum(int(row.get("total") or 0) for row in counts)

    st.markdown('<div class="ln-discovery-title">Descubra o que o governo está comprando.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ln-discovery-sub">Você não precisa adivinhar o que vender. Pesquise editais de todo o Brasil e veja os itens da compra já na tela.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="ln-home-count">{open_total:,} editais abertos para participação</div>'.replace(",", "."), unsafe_allow_html=True)
    st.markdown(
        '<div class="ln-home-value">No LicitaNexo, o edital já aparece com os itens da compra. Você entende a oportunidade antes de perder tempo abrindo documento por documento.</div>',
        unsafe_allow_html=True,
    )

    with st.form("essential_home_search", clear_on_submit=False, enter_to_submit=False):
        keyword = st.text_input("O que você procura?", placeholder="Ex.: papel A4, pneus, medicamentos, uniformes...")
        if st.form_submit_button("Buscar licitações", type="primary", icon=":material/search:", width="stretch"):
            st.session_state["essential_search_criteria"] = _criteria(keyword=keyword.strip())
            st.session_state["essential_search_page"] = 1
            st.session_state["_navigation_request"] = "Buscar licitações"
            st.rerun()

    st.markdown('<div class="ln-home-section">Ou comece explorando:</div>', unsafe_allow_html=True)
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
s = s[:start] + replacement.rstrip() + s[end:]
p.write_text(s, encoding="utf-8")


# config.py — preço real do Essential e versão
p = Path("src/config.py")
s = p.read_text(encoding="utf-8")
s = replace_once(s, 'APP_VERSION = "1.0 Essential RC31.10"', 'APP_VERSION = "1.0 Essential RC31.11"', "version")
s = replace_once(s, "ESSENTIAL_PRICE_CENTS = 4990", "ESSENTIAL_PRICE_CENTS = 2990", "essential price")
p.write_text(s, encoding="utf-8")


# contrato de regressão da RC31.11
Path("tests/test_rc31_11_value_login_home.py").write_text(
    '''from pathlib import Path\nimport unittest\n\n\nROOT = Path(__file__).resolve().parents[1]\n\n\nclass ValueLoginHomeContracts(unittest.TestCase):\n    def test_essential_price_is_2990(self):\n        config = (ROOT / "src" / "config.py").read_text(encoding="utf-8")\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn("ESSENTIAL_PRICE_CENTS = 2990", config)\n        self.assertIn("R$ 29,90", app)\n        self.assertNotIn("R$ 49,90", app)\n        self.assertNotIn("menos de R$1", app.lower())\n\n    def test_home_leads_with_beginner_value_and_open_items(self):\n        text = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")\n        self.assertIn("Descubra o que o governo está comprando.", text)\n        self.assertIn("Você não precisa adivinhar o que vender", text)\n        self.assertIn("itens da compra já na tela", text)\n        self.assertIn("documento por documento", text)\n\n    def test_login_explains_the_product_without_overpromising(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn("Encontre oportunidades para vender ao governo.", app)\n        self.assertIn("Editais com os itens da compra já abertos na busca", app)\n        self.assertIn("Pesquisa simples em todo o Brasil", app)\n        self.assertNotIn("sem estoque", app.lower())\n\n    def test_sidebar_keeps_professional_icons_with_muted_palette(self):\n        app = (ROOT / "app.py").read_text(encoding="utf-8")\n        self.assertIn('icon=nav_icons.get(option)', app)\n        self.assertIn('background:#E9F3EE !important', app)\n        self.assertIn('background:#F0ECF4 !important', app)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
    encoding="utf-8",
)

Path("docs/rc31-11-value-login-home.md").write_text(
    """# RC31.11 · valor para iniciantes e entrada mais clara\n\n- Home passa a explicar que o usuário pode descobrir o que o governo está comprando antes de decidir o que vender.\n- Diferencial de produto explícito: resultados mostram os itens da compra já na busca.\n- Login usa a mesma mensagem de valor, com três benefícios curtos e sem promessa de venda sem estoque.\n- Preço do Essential corrigido para R$ 29,90/mês também na constante comercial (`2990` centavos).\n- Removida qualquer âncora de \"menos de R$1 por dia\".\n- Sidebar mantém Material Symbols profissionais e recebe paleta suave com baixa saturação.\n- Home fica mais densa com atalhos explicativos e ícones funcionais.\n- Sem migration e sem alteração de estrutura de dados.\n""",
    encoding="utf-8",
)
