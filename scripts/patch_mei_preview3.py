from pathlib import Path

PATH = Path("mei_app.py")
text = PATH.read_text(encoding="utf-8")


def replace_block(source: str, start: str, end: str, replacement: str) -> str:
    begin = source.index(start)
    finish = source.index(end, begin)
    return source[:begin] + replacement.rstrip() + "\n\n\n" + source[finish:]


text = text.replace('MEI_VERSION = "1.0 MEI Preview 2"', 'MEI_VERSION = "1.0 MEI Preview 3"')

# Mais densidade no topo, menu lateral em formato de navegação e portal visível no card.
text = text.replace(
    '.ln-hero {background:#F7FAFD;border:1px solid #D6E1EE;border-left:5px solid var(--ln-blue);border-radius:16px;padding:.9rem 1.05rem;margin-bottom:.65rem;box-shadow:0 5px 14px rgba(18,47,78,.045)}',
    '.ln-hero {background:#F7FAFD;border:1px solid #D6E1EE;border-left:5px solid var(--ln-blue);border-radius:14px;padding:.62rem .85rem;margin-bottom:.42rem;box-shadow:0 4px 12px rgba(18,47,78,.04)}',
)
text = text.replace(
    '.ln-hero h1 {font-size:1.62rem;line-height:1.1;margin:.02rem 0 .25rem;color:var(--ln-navy)}',
    '.ln-hero h1 {font-size:1.42rem;line-height:1.08;margin:.02rem 0 .16rem;color:var(--ln-navy)}',
)
text = text.replace(
    '.ln-hero p {font-size:.91rem;color:#56697E;margin:0;max-width:900px;line-height:1.4}',
    '.ln-hero p {font-size:.84rem;color:#56697E;margin:0;max-width:980px;line-height:1.35}',
)
text = text.replace(
    '.ln-card {background:#FFFFFF;border:1px solid var(--ln-line);border-radius:16px;padding:.82rem .9rem .72rem;margin:.5rem 0 .28rem;box-shadow:0 5px 15px rgba(17,45,78,.045)}',
    '.ln-card {background:#FFFFFF;border:1px solid var(--ln-line);border-radius:15px;padding:.72rem .82rem .62rem;margin:.42rem 0 .18rem;box-shadow:0 4px 13px rgba(17,45,78,.04)}',
)
text = text.replace(
    '.ln-object {font-size:1rem;font-weight:820;line-height:1.31;color:#142E4C;margin:.08rem 0 .5rem}',
    '.ln-object {font-size:.96rem;font-weight:820;line-height:1.28;color:#142E4C;margin:.12rem 0 .42rem}',
)

css_anchor = '.ln-category {display:inline-block;border-radius:999px;padding:.21rem .48rem;font-size:.66rem;font-weight:800;background:#EDF3FC;color:#285AAE;border:1px solid #D7E3F5;margin-left:.3rem}\n'
css_extra = '''.ln-card-top {display:flex;align-items:center;justify-content:space-between;gap:.55rem;flex-wrap:wrap;margin-bottom:.08rem}\n.ln-card-top-left {display:flex;align-items:center;gap:.28rem;flex-wrap:wrap}\n.ln-item-count {display:inline-block;border-radius:999px;padding:.21rem .48rem;font-size:.66rem;font-weight:800;background:#FFF6DD;color:#865C08;border:1px solid #F0D891}\n.ln-portal-pill {display:flex;align-items:center;gap:.32rem;border-radius:999px;padding:.27rem .5rem;background:#F1F5F9;border:1px solid #DCE4ED;font-size:.72rem;font-weight:760;color:#29435D}\n.ln-price-cta {background:#EEF5FF;border:1px solid #CFE0FA;border-radius:10px;padding:.5rem .62rem;margin:.28rem 0 .4rem;font-size:.76rem;color:#39566F;line-height:1.35}\n.ln-discovery-title {font-size:1.26rem;font-weight:850;color:#102E4D;margin:.1rem 0 .2rem}\n.ln-discovery-sub {font-size:.82rem;color:#66798D;margin:0 0 .65rem}\n.ln-choice-card {background:#FFFFFF;border:1px solid #D8E1EB;border-radius:12px;padding:.58rem .66rem;margin-bottom:.35rem}\n.ln-choice-card strong {font-size:.9rem;color:#173351}.ln-choice-card span {display:block;font-size:.72rem;color:#748498;margin-top:.08rem}\n'''
if css_extra not in text:
    text = text.replace(css_anchor, css_anchor + css_extra)

sidebar_css_anchor = '[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {display:none !important;}\n'
sidebar_css_extra = '''[data-testid="stSidebar"] div.stButton > button {justify-content:flex-start !important;text-align:left !important;background:transparent !important;color:#173351 !important;border:1px solid transparent !important;box-shadow:none !important;min-height:2.15rem !important;padding:.42rem .55rem !important;font-size:.84rem !important}\n[data-testid="stSidebar"] div.stButton > button:hover {background:#F1F5FA !important;border-color:#E3EAF2 !important}\n[data-testid="stSidebar"] div.stButton > button[kind="primary"] {background:#EAF1FC !important;border-color:#D3E1F5 !important;color:#12365B !important}\n'''
if sidebar_css_extra not in text:
    text = text.replace(sidebar_css_anchor, sidebar_css_anchor + sidebar_css_extra)

# Cache de contagens para páginas de exploração dedicadas.
cache_anchor = '''@st.cache_data(ttl=3600, show_spinner=False)\ndef _price_history_cached(item_reference, catalog_code, description, state):\n'''
cache_extra = '''@st.cache_data(ttl=120, show_spinner=False)\ndef _region_counts_cached():\n    return catalog.counts_by_region()\n\n\n@st.cache_data(ttl=120, show_spinner=False)\ndef _state_counts_cached():\n    return catalog.counts_by_state()\n\n\n'''
if cache_extra not in text:
    text = text.replace(cache_anchor, cache_extra + cache_anchor)

text = text.replace(
    '    st.session_state.setdefault("mei_price_item", "")\n',
    '    st.session_state.setdefault("mei_price_item", "")\n    st.session_state.setdefault("mei_section", "🔎 Todas as oportunidades")\n',
)

new_sidebar = r'''def _sidebar():
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=154)
        st.markdown(
            '<div class="ln-side-copy">Descubra oportunidades, produtos e preços reais de compras públicas.</div>',
            unsafe_allow_html=True,
        )
        current = st.session_state.mei_section
        explore = [
            "🔎 Todas as oportunidades",
            "🗺️ Por região",
            "📍 Por estado",
            "🏙️ Por cidade",
            "📋 Por modalidade",
            "🔥 Em destaque",
        ]
        personal = ["⭐ Minha lista", "🔔 Radar"]

        st.markdown('<div class="ln-side-tag">Explorar</div>', unsafe_allow_html=True)
        for index, label in enumerate(explore):
            if st.button(
                label,
                key=f"mei_nav_explore_{index}",
                type="primary" if current == label else "secondary",
                width="stretch",
            ):
                st.session_state.mei_section = label
                st.rerun()

        st.markdown('<div class="ln-side-tag" style="margin-top:.55rem">Minha área</div>', unsafe_allow_html=True)
        for index, label in enumerate(personal):
            if st.button(
                label,
                key=f"mei_nav_personal_{index}",
                type="primary" if current == label else "secondary",
                width="stretch",
            ):
                st.session_state.mei_section = label
                st.rerun()

        st.markdown(
            '<div class="ln-side-plan">LicitaNexo MEI<strong>R&#36; 29,90/mês</strong>'
            '<span style="display:block;margin-top:.18rem">Oportunidades e inteligência de preços públicos.</span></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"{MEI_VERSION} · B2G SaaS")
    return st.session_state.mei_section'''
text = replace_block(text, 'def _sidebar():', 'def _filter_panel():', new_sidebar)

new_filter = r'''def _filter_panel():
    filters = dict(st.session_state.mei_filters)
    st.markdown(
        """<div class="ln-hero"><span class="ln-kicker">DESCOBERTA DE OPORTUNIDADES</span>
        <h1>O que o governo está comprando?</h1>
        <p>Explore livremente. Você não precisa saber o que quer vender para começar.</p></div>""",
        unsafe_allow_html=True,
    )

    region_options = ["Brasil inteiro"] + list(BRAZIL_REGIONS)
    current_region = filters.get("region") or "Brasil inteiro"
    if current_region not in region_options:
        current_region = "Brasil inteiro"

    c1, c2, c3, c4, c5 = st.columns([1, 1.15, 1.25, 1.15, 2.15])
    region = c1.selectbox(
        "Região",
        region_options,
        index=region_options.index(current_region),
        help="Brasil inteiro não limita a localização.",
    )
    states = c2.multiselect(
        "Estados",
        list(BRAZIL_STATES),
        default=filters.get("states") or [],
        placeholder="Todos",
    )
    city = c3.text_input("Cidade", value=filters.get("city") or "", placeholder="Ex.: Londrina")
    modalities = c4.multiselect(
        "Modalidade",
        list(MODALITIES.keys()),
        default=filters.get("modalities") or [],
        placeholder="Todas",
    )
    keyword = c5.text_input(
        "Produto, serviço ou palavra-chave",
        value=filters.get("keyword") or "",
        placeholder="Opcional — deixe em branco para descobrir",
    )
    b1, b2 = st.columns([5, 1])
    submitted = b1.button("🔎 Buscar licitações", type="primary", width="stretch")
    clear = b2.button("Limpar", width="stretch")
    if clear:
        st.session_state.mei_filters = {"region": "", "states": [], "city": "", "modalities": [], "keyword": ""}
        st.session_state.mei_page = 1
        st.rerun()
    if submitted:
        st.session_state.mei_filters = {
            "region": "" if region == "Brasil inteiro" else region,
            "states": list(states),
            "city": city.strip(),
            "modalities": list(modalities),
            "keyword": keyword.strip(),
        }
        st.session_state.mei_page = 1
        st.rerun()'''
text = replace_block(text, 'def _filter_panel():', 'def _render_items(', new_filter)

new_items = r'''def _render_items(item_pack, opportunity_id, state):
    items = item_pack.get("items") or []
    total = int(item_pack.get("item_count") or len(items))
    if not items:
        message = item_pack.get("items_error") or "O PNCP não publicou itens estruturados para esta contratação."
        st.markdown(
            f'<div class="ln-items"><div class="ln-items-title">📦 Produtos do edital</div>'
            f'<div class="ln-note">{escape(message)}</div></div>',
            unsafe_allow_html=True,
        )
        return

    expanded = st.session_state.mei_open_opportunity == opportunity_id
    shown = items if expanded else items[:3]
    lines = [
        f'<div class="ln-items"><div class="ln-items-title">📦 Produtos do edital · {total} item(ns)</div>',
        '<div class="ln-item-head"><div>Produto / serviço</div><div>Quantidade</div><div>Estimado</div></div>',
    ]
    for row in shown:
        description = escape(_short_text(row.get("description") or "Item não descrito", 300 if expanded else 190))
        quantity = row.get("quantity")
        unit = escape(str(row.get("unit_measure") or ""))
        price = "Sigiloso" if row.get("confidential") else _html_money(row.get("unit_price"))
        try:
            qty_text = f"{float(quantity):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            qty_text = "—"
        lines.append(
            f'<div class="ln-item-row"><div class="ln-item-name">{description}</div>'
            f'<div class="ln-item-qty">{qty_text} {unit}</div><div class="ln-item-price">{price}</div></div>'
        )
    lines.append('</div>')
    st.markdown("".join(lines), unsafe_allow_html=True)

    action_left, action_right = st.columns([1.15, 2.15])
    if total > 3:
        label = "Mostrar menos" if expanded else f"Ver todos os {total} produtos"
        if action_left.button(label, key=f"mei_all_items_{opportunity_id}", width="stretch"):
            st.session_state.mei_open_opportunity = "" if expanded else opportunity_id
            st.rerun()
    else:
        action_left.caption("Todos os itens estão visíveis.")

    if action_right.button(
        "💰 Ver preços pagos pelo governo",
        key=f"mei_price_open_{opportunity_id}",
        type="primary",
        width="stretch",
    ):
        st.session_state.mei_open_opportunity = opportunity_id
        if len(items) == 1:
            only = items[0]
            st.session_state.mei_price_item = str(only.get("source_reference") or f"{opportunity_id}:0")
        st.rerun()

    st.markdown(
        '<div class="ln-price-cta">Histórico de compras homologadas, faixas de preço, marcas e fornecedores vencedores quando essas informações estiverem publicadas.</div>',
        unsafe_allow_html=True,
    )

    if expanded:
        choices = [row for row in items if str(row.get("description") or "").strip()]
        if choices:
            selected = st.selectbox(
                "Produto para consultar histórico de compras",
                range(len(choices)),
                format_func=lambda idx: _short_text(choices[idx].get("description") or "", 110),
                key=f"mei_item_select_{opportunity_id}",
            )
            item = choices[selected]
            ref = str(item.get("source_reference") or f"{opportunity_id}:{selected}")
            if st.button("Consultar histórico deste produto", key=f"mei_price_btn_{opportunity_id}"):
                st.session_state.mei_price_item = ref
            if st.session_state.mei_price_item == ref:
                with st.spinner("Consultando compras homologadas no Compras.gov..."):
                    history = _price_history_cached(
                        ref,
                        str(item.get("catalog_code") or ""),
                        str(item.get("description") or ""),
                        state,
                    )
                _render_price_history(history)'''
text = replace_block(text, 'def _render_items(', 'def _render_price_history(', new_items)

new_opportunity = r'''def _render_opportunity(row, item_pack):
    opportunity_id = str(row.get("id") or row.get("pncp_control_number") or "")
    modality = escape(str(row.get("modality") or "Modalidade não informada"))
    category = escape(str(item_pack.get("category") or row.get("category") or "Outros"))
    object_text = escape(_short_text(row.get("object") or "Objeto não informado", 300))
    agency = escape(str(row.get("agency") or "Órgão não informado"))
    city = escape(str(row.get("city") or "Município não informado"))
    state = escape(str(row.get("state") or "--"))
    portal = escape(str(row.get("portal") or "Não identificado"))
    access = escape(str(row.get("portal_access") or "Verificar condições"))
    tone = str(row.get("portal_access_tone") or "unknown")
    tone_class = "ln-free" if tone == "free" else "ln-paid" if tone in {"paid", "conditional"} else "ln-unknown"
    total_items = int(item_pack.get("item_count") or len(item_pack.get("items") or []))

    st.markdown(
        f"""<div class="ln-card">
        <div class="ln-card-top">
          <div class="ln-card-top-left"><span class="ln-badge">{modality}</span><span class="ln-category">{category}</span><span class="ln-item-count">📦 {total_items} item(ns)</span></div>
          <div class="ln-portal-pill">🌐 {portal} <span class="{tone_class}">● {access}</span></div>
        </div>
        <div class="ln-object">{object_text}</div>
        <div class="ln-meta-grid">
          <div class="ln-meta"><small>Cidade</small><strong>{city} — {state}</strong></div>
          <div class="ln-meta"><small>Órgão</small><strong>{agency}</strong></div>
          <div class="ln-meta"><small>Valor estimado</small><strong>{_html_money(row.get('estimated_value'))}</strong></div>
          <div class="ln-meta"><small>Fim das propostas</small><strong>{escape(_dt(row.get('closing_at')))}</strong></div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )
    _render_items(item_pack, opportunity_id, str(row.get("state") or ""))

    a, b, c = st.columns([1.2, 1, 1])
    saved = opportunity_id in st.session_state.mei_saved
    if a.button("✓ Salvo" if saved else "⭐ Salvar", key=f"mei_save_{opportunity_id}", disabled=saved, width="stretch"):
        st.session_state.mei_saved[opportunity_id] = dict(row)
        st.rerun()
    source_url = str(row.get("source_url") or "")
    pncp_url = str(row.get("pncp_url") or "")
    if source_url.startswith(("http://", "https://")):
        b.link_button("🌐 Portal", source_url, width="stretch")
    if pncp_url.startswith(("http://", "https://")):
        c.link_button("📄 PNCP", pncp_url, width="stretch")'''
text = replace_block(text, 'def _render_opportunity(', 'def _explore_page():', new_opportunity)

# Ajusta mensagem da busca principal.
text = text.replace(
    '    st.caption("Use os filtros apenas quando quiser restringir a descoberta.")',
    '    st.caption("Explore livremente. Os filtros servem apenas para aproximar a busca do que chamou sua atenção.")',
)

# Novas formas de exploração. Elas só preenchem filtros e reaproveitam o mesmo motor de busca.
insert_before_saved = r'''def _apply_discovery(*, region="", states=None, city="", modalities=None, keyword=""):
    st.session_state.mei_filters = {
        "region": region,
        "states": list(states or []),
        "city": city,
        "modalities": list(modalities or []),
        "keyword": keyword,
    }
    st.session_state.mei_page = 1
    st.session_state.mei_section = "🔎 Todas as oportunidades"
    st.rerun()


def _region_page():
    st.markdown('<div class="ln-discovery-title">🗺️ Explore por região</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Veja quantas oportunidades abertas existem em cada região e entre com um clique.</div>', unsafe_allow_html=True)
    counts = _region_counts_cached()
    cols = st.columns(3)
    for index, region in enumerate(BRAZIL_REGIONS):
        with cols[index % 3]:
            total = int(counts.get(region, 0))
            st.markdown(f'<div class="ln-choice-card"><strong>{escape(region)}</strong><span>{total} oportunidade(s) aberta(s)</span></div>', unsafe_allow_html=True)
            if st.button("Ver licitações", key=f"mei_region_{region}", width="stretch"):
                _apply_discovery(region=region)


def _state_page():
    st.markdown('<div class="ln-discovery-title">📍 Explore por estado</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Escolha uma UF para ver somente as oportunidades abertas daquele estado.</div>', unsafe_allow_html=True)
    counts = _state_counts_cached()
    states = sorted(BRAZIL_STATES, key=lambda value: (-int(counts.get(value, 0)), value))
    cols = st.columns(4)
    for index, state in enumerate(states):
        with cols[index % 4]:
            if st.button(f"{state} · {int(counts.get(state, 0))}", key=f"mei_state_{state}", width="stretch"):
                _apply_discovery(states=[state])


def _city_page():
    st.markdown('<div class="ln-discovery-title">🏙️ Explore por cidade</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Digite apenas a cidade. A busca aceita nomes com ou sem acento.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    city = c1.text_input("Cidade", placeholder="Ex.: Londrina, João Pessoa, Sao Jose")
    if c2.button("Buscar", type="primary", width="stretch"):
        if city.strip():
            _apply_discovery(city=city.strip())
        else:
            st.warning("Digite uma cidade para continuar.")


def _modality_page():
    st.markdown('<div class="ln-discovery-title">📋 Explore por modalidade</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Escolha o tipo de contratação para descobrir oportunidades abertas nessa modalidade.</div>', unsafe_allow_html=True)
    options = list(MODALITIES.keys())
    cols = st.columns(2)
    for index, modality in enumerate(options):
        with cols[index % 2]:
            if st.button(str(modality), key=f"mei_modality_{index}", width="stretch"):
                _apply_discovery(modalities=[modality])


def _highlight_score(row):
    score = 0.0
    portal = str(row.get("portal") or "").strip().casefold()
    if portal and portal != "não identificado":
        score += 3
    if str(row.get("portal_access_tone") or "") == "free":
        score += 2
    try:
        value = float(row.get("estimated_value") or 0)
    except (TypeError, ValueError):
        value = 0
    if 0 < value <= 250000:
        score += 1.5
    closing = row.get("closing_at")
    if closing:
        try:
            parsed = datetime.fromisoformat(str(closing).replace("Z", "+00:00"))
            now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
            hours = (parsed - now).total_seconds() / 3600
            if 24 <= hours <= 240:
                score += 2
            elif 8 <= hours < 24:
                score += .5
        except (TypeError, ValueError):
            pass
    return score


def _highlight_page():
    st.markdown('<div class="ln-discovery-title">🔥 Oportunidades em destaque</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Destaques priorizam dados claros, portal identificado, prazo útil e itens publicados. Não é recomendação automática de participação.</div>', unsafe_allow_html=True)
    rows = _search_cached("", tuple(), "", tuple(), "", 80)
    preselected = sorted(rows, key=_highlight_score, reverse=True)[:24]
    controls = tuple(str(row.get("pncp_control_number") or "") for row in preselected)
    with st.spinner("Organizando os destaques..."):
        item_map = _items_cached(controls)
    ranked = []
    for row in preselected:
        control = str(row.get("pncp_control_number") or "")
        pack = item_map.get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"})
        score = _highlight_score(row)
        if int(pack.get("item_count") or 0) > 0:
            score += 4
        if str(pack.get("category") or "Outros") != "Outros":
            score += 1
        ranked.append((score, row, pack))
    ranked.sort(key=lambda item: item[0], reverse=True)
    for _, row, pack in ranked[:10]:
        _render_opportunity(row, pack)


'''
if 'def _region_page():' not in text:
    text = text.replace('def _saved_page():', insert_before_saved + 'def _saved_page():')

new_main = r'''def main():
    _init_state()
    section = _sidebar()
    if section == "🔎 Todas as oportunidades":
        _explore_page()
    elif section == "🗺️ Por região":
        _region_page()
    elif section == "📍 Por estado":
        _state_page()
    elif section == "🏙️ Por cidade":
        _city_page()
    elif section == "📋 Por modalidade":
        _modality_page()
    elif section == "🔥 Em destaque":
        _highlight_page()
    elif section == "⭐ Minha lista":
        _saved_page()
    else:
        _radar_page()'''
text = replace_block(text, 'def main():', 'if __name__ == "__main__":', new_main)

# Contratos simples para o patch falhar cedo se algo não tiver sido aplicado.
required = [
    'MEI_VERSION = "1.0 MEI Preview 3"',
    '"🗺️ Por região"',
    '"📍 Por estado"',
    '"🏙️ Por cidade"',
    '"📋 Por modalidade"',
    '"🔥 Em destaque"',
    '💰 Ver preços pagos pelo governo',
    'def _highlight_page():',
    'Explore livremente. Você não precisa saber o que quer vender para começar.',
]
for needle in required:
    if needle not in text:
        raise SystemExit(f"patch incompleto: {needle}")

PATH.write_text(text, encoding="utf-8")
print("LicitaNexo MEI Preview 3 aplicado")
