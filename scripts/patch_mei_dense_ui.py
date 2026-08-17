from pathlib import Path
import re

path = Path('mei_app.py')
text = path.read_text(encoding='utf-8')

text = text.replace('MEI_VERSION = "1.0 MEI Preview 1"', 'MEI_VERSION = "1.0 MEI Preview 2"')

css = '''LIGHT_CSS = """
<style>
:root {
  --ln-navy:#0B2745; --ln-blue:#2A63DA; --ln-blue-dark:#174BAE;
  --ln-green:#119A67; --ln-gold:#D6A126; --ln-red:#C94747;
  --ln-bg:#EDF2F7; --ln-card:#FFFFFF; --ln-line:#D7E0EA; --ln-muted:#65768A;
}
html, body, [data-testid="stAppViewContainer"], .stApp {
  background:var(--ln-bg) !important; color:var(--ln-navy) !important;
}
header[data-testid="stHeader"] {background:rgba(237,242,247,.96) !important;}
.block-container {max-width:1240px !important; padding-top:.7rem !important; padding-bottom:1.25rem !important;}
[data-testid="stSidebar"] {
  background:#FFFFFF !important; border-right:1px solid #D7E0EA !important;
  border-top:7px solid var(--ln-navy) !important;
}
[data-testid="stSidebar"] > div:first-child {padding-top:.45rem !important;}
[data-testid="stSidebar"] * {color:var(--ln-navy);}
[data-testid="stSidebar"] img {max-width:158px !important; margin:.15rem auto .05rem; display:block;}
[data-testid="stSidebar"] hr {margin:.55rem 0 !important; border-color:#E4EAF1 !important;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:.2rem !important;}
[data-testid="stSidebar"] [role="radiogroup"] label {
  padding:.58rem .62rem !important; border-radius:11px !important; margin:0 !important;
  font-weight:760 !important; transition:background .12s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {background:#F1F5FA !important;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#EAF1FC !important;}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {display:none !important;}
.ln-side-tag {font-size:.72rem;color:#708198;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin:.25rem 0 .25rem;}
.ln-side-copy {font-size:.82rem;line-height:1.38;color:#68798D;margin:.15rem 0 .6rem;}
.ln-side-plan {background:#F2F6FB;border:1px solid #DCE5EF;border-radius:12px;padding:.65rem .75rem;margin:.7rem 0 .55rem;font-size:.78rem;color:#66778A;}
.ln-side-plan strong {display:block;font-size:.98rem;color:#102E4D;margin-top:.12rem;}
h1,h2,h3,h4,p,label,span,div {color:inherit;}
.ln-hero {background:#F7FAFD;border:1px solid #D6E1EE;border-left:5px solid var(--ln-blue);border-radius:16px;padding:.9rem 1.05rem;margin-bottom:.65rem;box-shadow:0 5px 14px rgba(18,47,78,.045)}
.ln-kicker {display:inline-block;font-size:.68rem;font-weight:850;color:#116B49;background:#E5F8EF;border:1px solid #B9E7D2;border-radius:999px;padding:.22rem .48rem;margin-bottom:.35rem}
.ln-hero h1 {font-size:1.62rem;line-height:1.1;margin:.02rem 0 .25rem;color:var(--ln-navy)}
.ln-hero p {font-size:.91rem;color:#56697E;margin:0;max-width:900px;line-height:1.4}
.ln-filter-title {font-size:1rem;font-weight:850;color:#143452;margin:0 0 .25rem}
.ln-results-head {display:flex;align-items:end;justify-content:space-between;gap:1rem;margin:.8rem 0 .25rem}
.ln-results-head h3 {font-size:1.32rem;margin:0;color:#102E4D}.ln-results-head span {font-size:.8rem;color:#6A7A8E}
.ln-card {background:#FFFFFF;border:1px solid var(--ln-line);border-radius:16px;padding:.82rem .9rem .72rem;margin:.5rem 0 .28rem;box-shadow:0 5px 15px rgba(17,45,78,.045)}
.ln-badge {display:inline-block;border-radius:999px;padding:.22rem .5rem;font-size:.67rem;font-weight:850;background:#E5F8EF;color:#106C49;border:1px solid #BDE8D5;margin-bottom:.32rem}
.ln-category {display:inline-block;border-radius:999px;padding:.21rem .48rem;font-size:.66rem;font-weight:800;background:#EDF3FC;color:#285AAE;border:1px solid #D7E3F5;margin-left:.3rem}
.ln-object {font-size:1rem;font-weight:820;line-height:1.31;color:#142E4C;margin:.08rem 0 .5rem}
.ln-meta-grid {display:grid;grid-template-columns:1.05fr 1.35fr .9fr 1fr;gap:.45rem;margin:.45rem 0}
.ln-meta {background:#F6F8FB;border:1px solid #E0E7EF;border-radius:10px;padding:.48rem .56rem;min-height:58px}
.ln-meta small {display:block;font-size:.61rem;color:#76869A;font-weight:850;text-transform:uppercase;letter-spacing:.035em;margin-bottom:.12rem}
.ln-meta strong {font-size:.82rem;color:#173351;line-height:1.22;display:block;overflow-wrap:anywhere}
.ln-portal {display:flex;gap:.4rem;align-items:center;flex-wrap:wrap;background:#F6F8FB;border:1px solid #E0E6EE;border-radius:10px;padding:.43rem .58rem;margin:.45rem 0 .18rem;font-size:.84rem}
.ln-portal strong {color:#173351}.ln-free {color:#117C53;font-weight:850}.ln-paid {color:#A25C08;font-weight:850}.ln-unknown {color:#68788D;font-weight:800}
.ln-portal-note {font-size:.7rem;color:#7A899B;margin:.1rem 0 0}
.ln-items {background:#F8FAFD;border:1px solid #D8E2EE;border-radius:12px;padding:.55rem .68rem;margin:.18rem 0 .38rem}
.ln-items-title {font-weight:850;color:#173351;margin-bottom:.3rem;font-size:.88rem}
.ln-item-head,.ln-item-row {display:grid;grid-template-columns:minmax(0,1fr) 105px 105px;gap:.45rem;align-items:start}
.ln-item-head {padding:.15rem 0 .25rem;border-bottom:1px solid #DDE5EE;font-size:.62rem;color:#7B899A;text-transform:uppercase;font-weight:850}
.ln-item-head div:nth-child(2),.ln-item-head div:nth-child(3){text-align:right}
.ln-item-row {padding:.34rem 0;border-bottom:1px solid #E4EAF1}
.ln-item-row:last-child {border-bottom:0}.ln-item-name {font-size:.81rem;color:#243D59;line-height:1.28}.ln-item-qty,.ln-item-price {font-size:.78rem;color:#4E6075;text-align:right}.ln-item-price {font-weight:850;color:#173351}
.ln-note {font-size:.74rem;color:#6C7C90;line-height:1.4}
.ln-empty {padding:1.25rem;text-align:center;background:#FFFFFF;border:1px dashed #C7D3E1;border-radius:14px;color:#68788D}
.ln-radar-summary {display:flex;flex-wrap:wrap;gap:.38rem;background:#FFFFFF;border:1px solid #D8E1EB;border-radius:13px;padding:.65rem .72rem;margin:.45rem 0 .65rem}
.ln-radar-chip {background:#EEF3F8;border:1px solid #DCE5EF;border-radius:999px;padding:.3rem .55rem;font-size:.77rem;color:#38516B}.ln-radar-chip b{color:#173351}
div[data-testid="stVerticalBlockBorderWrapper"] {background:#FFFFFF;border-radius:14px !important;}
div[data-testid="stVerticalBlockBorderWrapper"] > div {padding-top:.72rem !important;padding-bottom:.72rem !important;}
div.stButton > button, div.stDownloadButton > button, a[data-testid="stLinkButton"] {border-radius:9px !important;min-height:2.4rem !important;font-weight:800 !important}
div.stButton > button[kind="primary"] {background:var(--ln-blue) !important;border-color:var(--ln-blue) !important;color:#FFF !important}
[data-baseweb="input"] > div, [data-baseweb="select"] > div {background:#FFFFFF !important;color:#173351 !important;border-color:#C8D4E2 !important;min-height:2.45rem !important}
input, textarea {color:#173351 !important;-webkit-text-fill-color:#173351 !important;background:#FFFFFF !important}
[data-testid="stWidgetLabel"] p {font-size:.78rem !important;font-weight:760 !important;color:#344C66 !important;margin-bottom:.08rem !important}
[data-testid="stMetric"] {background:#FFFFFF;border:1px solid var(--ln-line);border-radius:11px;padding:.55rem .62rem}
[data-testid="stMetricLabel"] *, [data-testid="stMetricValue"] * {color:#173351 !important}
[data-testid="stAlert"] {padding:.65rem .8rem !important;border-radius:11px !important}
@media(max-width:800px){.ln-meta-grid{grid-template-columns:1fr 1fr}.ln-item-head{display:none}.ln-item-row{grid-template-columns:1fr}.ln-item-qty,.ln-item-price{text-align:left}.ln-hero h1{font-size:1.42rem}.block-container{padding-left:.75rem!important;padding-right:.75rem!important}}
</style>
"""
st.markdown'''

text, count = re.subn(r'LIGHT_CSS = """.*?"""\nst\.markdown', css, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit('CSS block not found')

money_anchor = '''def _money(value):
    try:
        if value is None or float(value) <= 0:
            return "Não informado"
    except (TypeError, ValueError):
        return "Não informado"
    return format_brl(value)
'''
helpers = money_anchor + '''\n\ndef _html_money(value):
    """Evita que o cifrão seja interpretado como delimitador Markdown/LaTeX dentro do HTML."""
    return escape(_money(value)).replace("$", "&#36;")


def _short_text(value, limit=230):
    clean = " ".join(str(value or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: max(limit - 1, 1)].rstrip(" ,.;:-") + "…"
'''
if '_html_money' not in text:
    if money_anchor not in text:
        raise SystemExit('money anchor not found')
    text = text.replace(money_anchor, helpers, 1)

sidebar = '''def _sidebar():
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=158)
        st.markdown('<div class="ln-side-copy">Descubra produtos, preços e compras públicas sem precisar definir um nicho antes.</div>', unsafe_allow_html=True)
        st.markdown('<div class="ln-side-tag">Explorar</div>', unsafe_allow_html=True)
        page = st.radio(
            "Navegação",
            ["🔎 Explorar licitações", "⭐ Minha lista", "🔔 Radar"],
            label_visibility="collapsed",
        )
        st.markdown(
            '<div class="ln-side-plan">Plano de lançamento<strong>R&#36; 29,90/mês</strong></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"{MEI_VERSION} · B2G SaaS")
    return page


'''
text, count = re.subn(r'def _sidebar\(\):.*?(?=def _filter_panel\(\):)', sidebar, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit('sidebar block not found')

filter_panel = '''def _filter_panel():
    filters = dict(st.session_state.mei_filters)
    st.markdown(
        """<div class="ln-hero"><span class="ln-kicker">EXPLORAR LICITAÇÕES</span>
        <h1>O que o governo está comprando?</h1>
        <p>Explore por localização ou deixe tudo em branco para descobrir produtos e novos nichos.</p></div>""",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown('<div class="ln-filter-title">Encontre oportunidades</div>', unsafe_allow_html=True)
        region_options = ["Brasil inteiro"] + list(BRAZIL_REGIONS)
        current_region = filters.get("region") or "Brasil inteiro"
        if current_region not in region_options:
            current_region = "Brasil inteiro"
        c1, c2, c3 = st.columns([1.05, 1.45, 1.5])
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
            placeholder="Todos os estados",
        )
        city = c3.text_input(
            "Cidade",
            value=filters.get("city") or "",
            placeholder="Ex.: Londrina",
        )
        c4, c5 = st.columns([1.25, 2.75])
        modalities = c4.multiselect(
            "Modalidade",
            list(MODALITIES.keys()),
            default=filters.get("modalities") or [],
            placeholder="Todas",
        )
        keyword = c5.text_input(
            "Produto, serviço ou palavra-chave",
            value=filters.get("keyword") or "",
            placeholder="Opcional — deixe em branco para descobrir oportunidades",
        )
        b1, b2 = st.columns([4, 1])
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
            st.rerun()


'''
text, count = re.subn(r'def _filter_panel\(\):.*?(?=def _render_items\()', filter_panel, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit('filter panel not found')

render_items = '''def _render_items(item_pack, opportunity_id, state):
    items = item_pack.get("items") or []
    total = int(item_pack.get("item_count") or len(items))
    if not items:
        message = item_pack.get("items_error") or "O PNCP não publicou itens estruturados para esta contratação."
        st.markdown(f'<div class="ln-items"><div class="ln-items-title">📦 Produtos do edital</div><div class="ln-note">{escape(message)}</div></div>', unsafe_allow_html=True)
        return

    expanded = st.session_state.mei_open_opportunity == opportunity_id
    shown = items if expanded else items[:4]
    lines = [
        f'<div class="ln-items"><div class="ln-items-title">📦 {total} produto(s)/item(ns) no PNCP</div>',
        '<div class="ln-item-head"><div>Produto / serviço</div><div>Quantidade</div><div>Estimado</div></div>',
    ]
    for row in shown:
        description = escape(_short_text(row.get("description") or "Item não descrito", 300 if expanded else 220))
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

    if total > 4:
        label = "Mostrar menos" if expanded else f"Ver todos os {total} produtos"
        if st.button(label, key=f"mei_all_items_{opportunity_id}"):
            st.session_state.mei_open_opportunity = "" if expanded else opportunity_id
            st.rerun()

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
            if st.button("💰 Ver quanto o governo pagou", key=f"mei_price_btn_{opportunity_id}", type="primary"):
                st.session_state.mei_price_item = ref
            if st.session_state.mei_price_item == ref:
                with st.spinner("Consultando compras homologadas no Compras.gov..."):
                    history = _price_history_cached(
                        ref,
                        str(item.get("catalog_code") or ""),
                        str(item.get("description") or ""),
                        state,
                    )
                _render_price_history(history)


'''
text, count = re.subn(r'def _render_items\(.*?(?=def _render_price_history\()', render_items, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit('render items not found')

opportunity = '''def _render_opportunity(row, item_pack):
    opportunity_id = str(row.get("id") or row.get("pncp_control_number") or "")
    modality = escape(str(row.get("modality") or "Modalidade não informada"))
    category = escape(str(item_pack.get("category") or row.get("category") or "Outros"))
    object_text = escape(_short_text(row.get("object") or "Objeto não informado", 330))
    agency = escape(str(row.get("agency") or "Órgão não informado"))
    city = escape(str(row.get("city") or "Município não informado"))
    state = escape(str(row.get("state") or "--"))
    portal = escape(str(row.get("portal") or "Não identificado"))
    access = escape(str(row.get("portal_access") or "Verificar condições"))
    tone = str(row.get("portal_access_tone") or "unknown")
    tone_class = "ln-free" if tone == "free" else "ln-paid" if tone in {"paid", "conditional"} else "ln-unknown"
    verified = escape(str(row.get("portal_verified_at") or ""))

    st.markdown(
        f"""<div class="ln-card"><span class="ln-badge">{modality}</span><span class="ln-category">{category}</span>
        <div class="ln-object">{object_text}</div>
        <div class="ln-meta-grid">
          <div class="ln-meta"><small>Cidade</small><strong>{city} — {state}</strong></div>
          <div class="ln-meta"><small>Órgão</small><strong>{agency}</strong></div>
          <div class="ln-meta"><small>Valor estimado</small><strong>{_html_money(row.get('estimated_value'))}</strong></div>
          <div class="ln-meta"><small>Fim das propostas</small><strong>{escape(_dt(row.get('closing_at')))}</strong></div>
        </div>
        <div class="ln-portal">🌐 <strong>{portal}</strong><span class="{tone_class}">● {access}</span></div>
        <div class="ln-portal-note">Portal da disputa · condição verificada em {verified or 'data não informada'}.</div>
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
        c.link_button("📄 PNCP", pncp_url, width="stretch")


'''
text, count = re.subn(r'def _render_opportunity\(.*?(?=def _explore_page\()', opportunity, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit('opportunity renderer not found')

text = text.replace('    st.markdown("### Oportunidades abertas")\n', '    st.markdown(f\'<div class="ln-results-head"><h3>Oportunidades abertas</h3><span>{len(rows) if "rows" in locals() else ""}</span></div>\', unsafe_allow_html=True)\n', 1)
# Corrige a posição: rows ainda não existe nesse ponto na versão original; usa título normal e injeta contador após a busca.
text = text.replace('    st.markdown(f\'<div class="ln-results-head"><h3>Oportunidades abertas</h3><span>{len(rows) if "rows" in locals() else ""}</span></div>\', unsafe_allow_html=True)\n    if not rows:', '    st.markdown(f\'<div class="ln-results-head"><h3>Oportunidades abertas</h3><span>{len(rows)} encontrada(s)</span></div>\', unsafe_allow_html=True)\n    if not rows:', 1)
text = text.replace('    st.caption(f"{len(rows)} oportunidade(s) encontradas nesta consulta. A palavra-chave é opcional: deixe vazia para descobrir novos nichos.")\n    per_page = 8', '    st.caption("Use os filtros apenas quando quiser restringir a descoberta.")\n    per_page = 10', 1)

radar = '''def _radar_page():
    st.markdown("## 🔔 Radar")
    st.caption("Guarde uma combinação de busca para reutilizar depois. Nenhum nicho é obrigatório.")
    filters = dict(st.session_state.mei_filters)
    chips = [
        ("Região", filters.get("region") or "Brasil inteiro"),
        ("Estado", ", ".join(filters.get("states") or []) or "Todos"),
        ("Cidade", filters.get("city") or "Todas"),
        ("Modalidade", ", ".join(filters.get("modalities") or []) or "Todas"),
        ("Palavra", filters.get("keyword") or "Modo descoberta"),
    ]
    chip_html = "".join(
        f'<span class="ln-radar-chip"><b>{escape(label)}:</b> {escape(str(value))}</span>'
        for label, value in chips
    )
    st.markdown(f'<div class="ln-radar-summary">{chip_html}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    name = c1.text_input("Nome do radar", placeholder="Ex.: oportunidades em Londrina")
    if c2.button("🔔 Salvar radar", type="primary", width="stretch"):
        st.session_state.mei_radars.append({"name": name.strip() or f"Radar {len(st.session_state.mei_radars)+1}", "filters": filters})
        st.success("Radar salvo nesta sessão.")
    if st.session_state.mei_radars:
        st.markdown("### Meus radares")
        for index, radar in enumerate(st.session_state.mei_radars):
            rfilters = radar["filters"]
            summary = " · ".join(part for part in [
                rfilters.get("region") or "Brasil",
                ", ".join(rfilters.get("states") or []),
                rfilters.get("city") or "",
                ", ".join(rfilters.get("modalities") or []),
                rfilters.get("keyword") or "descoberta",
            ] if part)
            with st.container(border=True):
                left, right = st.columns([4, 1])
                left.markdown(f"**{escape(radar['name'])}**")
                left.caption(summary)
                if right.button("Usar", key=f"mei_use_radar_{index}", width="stretch"):
                    st.session_state.mei_filters = dict(rfilters)
                    st.session_state.mei_page = 1
                    st.rerun()
    st.caption("Alertas automáticos por e-mail/WhatsApp entram na etapa comercial; neste preview o Radar salva a busca na sessão.")


'''
text, count = re.subn(r'def _radar_page\(\):.*?(?=def main\(\):)', radar, text, count=1, flags=re.S)
if count != 1:
    raise SystemExit('radar block not found')

path.write_text(text, encoding='utf-8')
print('MEI Preview 2 compactado e corrigido')
