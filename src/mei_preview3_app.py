from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import database_path
from src.database import Database
from src.formatters import format_brl
from src.mei_catalog import (
    BRAZIL_REGIONS,
    BRAZIL_STATES,
    MeiCatalogService,
    enrich_with_items,
    fetch_price_history_for_item,
)
from src.pncp import MODALITIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo.png"
MEI_VERSION = "1.0 MEI Preview 3"
MEI_PRICE = "R$ 29,90/mês"

db = Database(database_path(PROJECT_ROOT))
catalog = MeiCatalogService(db)

CSS = """
<style>
:root{
 --navy:#0B2745;--blue:#2A63DA;--green:#119A67;--gold:#D6A126;
 --bg:#E9EFF5;--card:#fff;--line:#D5DFEA;--muted:#65768A;
}
html,body,[data-testid="stAppViewContainer"],.stApp{background:var(--bg)!important;color:var(--navy)!important}
header[data-testid="stHeader"]{background:rgba(233,239,245,.96)!important}
.block-container{max-width:1260px!important;padding-top:.45rem!important;padding-bottom:1rem!important}
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--line)!important;border-top:7px solid var(--navy)!important}
[data-testid="stSidebar"]>div:first-child{padding-top:.35rem!important}
[data-testid="stSidebar"] img{max-width:150px!important;margin:.1rem auto .05rem;display:block}
[data-testid="stSidebar"] hr{margin:.4rem 0!important}
[data-testid="stSidebar"] div.stButton>button{
 justify-content:flex-start!important;text-align:left!important;min-height:2.08rem!important;
 padding:.36rem .52rem!important;border-radius:10px!important;font-size:.84rem!important;
 box-shadow:none!important
}
[data-testid="stSidebar"] div.stButton>button[kind="secondary"]{
 background:transparent!important;border:1px solid transparent!important;color:#173351!important
}
[data-testid="stSidebar"] div.stButton>button[kind="secondary"]:hover{
 background:#F1F5FA!important;border-color:#E2E9F1!important
}
[data-testid="stSidebar"] div.stButton>button[kind="primary"]{
 background:#E7F0FE!important;border:1px solid #CADDF8!important;color:#12365B!important
}
.ln-side-copy{font-size:.79rem;line-height:1.35;color:#68798D;margin:.05rem 0 .52rem}
.ln-side-tag{font-size:.68rem;color:#7A8A9E;font-weight:850;letter-spacing:.08em;text-transform:uppercase;margin:.25rem 0 .15rem}
.ln-plan{background:#F2F6FB;border:1px solid #D9E3ED;border-radius:11px;padding:.58rem .66rem;margin:.58rem 0 .4rem;font-size:.75rem;color:#6B7C90}
.ln-plan strong{display:block;font-size:.95rem;color:#102E4D;margin:.08rem 0}
.ln-hero{background:#F7FAFD;border:1px solid #D5E0EC;border-left:5px solid var(--blue);border-radius:13px;padding:.55rem .78rem;margin-bottom:.38rem}
.ln-kicker{display:inline-block;font-size:.64rem;font-weight:850;color:#116B49;background:#E6F8F0;border:1px solid #BDE7D4;border-radius:999px;padding:.18rem .42rem;margin-bottom:.18rem}
.ln-hero h1{font-size:1.35rem;line-height:1.08;margin:.02rem 0 .12rem;color:var(--navy)}
.ln-hero p{font-size:.82rem;color:#5C6F83;margin:0;line-height:1.34}
.ln-results{display:flex;justify-content:space-between;align-items:end;margin:.55rem 0 .18rem}
.ln-results h3{font-size:1.2rem;margin:0;color:#102E4D}.ln-results span{font-size:.78rem;color:#718196}
.ln-card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:.66rem .75rem .58rem;margin:.35rem 0 .14rem;box-shadow:0 4px 12px rgba(17,45,78,.035)}
.ln-top{display:flex;align-items:center;justify-content:space-between;gap:.45rem;flex-wrap:wrap;margin-bottom:.08rem}
.ln-top-left{display:flex;align-items:center;gap:.25rem;flex-wrap:wrap}
.ln-badge,.ln-cat,.ln-count,.ln-portal{display:inline-flex;align-items:center;border-radius:999px;font-size:.64rem;font-weight:820}
.ln-badge{padding:.19rem .43rem;background:#E7F8F0;color:#106C49;border:1px solid #BFE7D5}
.ln-cat{padding:.19rem .43rem;background:#EDF3FC;color:#285AAE;border:1px solid #D6E2F4}
.ln-count{padding:.19rem .43rem;background:#FFF5D8;color:#7B570A;border:1px solid #EFD78D}
.ln-portal{padding:.23rem .48rem;background:#F1F5F9;color:#29435D;border:1px solid #DCE4ED;gap:.28rem}
.ln-free{color:#117C53}.ln-paid{color:#9A5A0B}.ln-unknown{color:#6D7D90}
.ln-object{font-size:.94rem;font-weight:820;line-height:1.26;color:#142E4C;margin:.12rem 0 .35rem}
.ln-meta-grid{display:grid;grid-template-columns:1.05fr 1.35fr .9fr 1fr;gap:.36rem;margin:.35rem 0}
.ln-meta{background:#F6F8FB;border:1px solid #E1E7EF;border-radius:9px;padding:.4rem .48rem;min-height:52px}
.ln-meta small{display:block;font-size:.58rem;color:#79899C;font-weight:850;text-transform:uppercase;margin-bottom:.08rem}
.ln-meta strong{display:block;font-size:.79rem;color:#173351;line-height:1.2;overflow-wrap:anywhere}
.ln-items{background:#F8FAFD;border:1px solid #D8E2EE;border-radius:11px;padding:.48rem .58rem;margin:.12rem 0 .24rem}
.ln-items-title{font-size:.84rem;font-weight:850;color:#173351;margin-bottom:.22rem}
.ln-item-head,.ln-item-row{display:grid;grid-template-columns:minmax(0,1fr) 100px 100px;gap:.4rem;align-items:start}
.ln-item-head{font-size:.59rem;color:#7A899A;text-transform:uppercase;font-weight:850;border-bottom:1px solid #DDE5EE;padding:.1rem 0 .2rem}
.ln-item-head div:nth-child(2),.ln-item-head div:nth-child(3){text-align:right}
.ln-item-row{padding:.29rem 0;border-bottom:1px solid #E5EAF0}
.ln-item-row:last-child{border-bottom:0}
.ln-item-name{font-size:.78rem;color:#263F5B;line-height:1.25}
.ln-item-qty,.ln-item-price{font-size:.75rem;text-align:right;color:#53657A}.ln-item-price{font-weight:850;color:#173351}
.ln-price-note{background:#EEF5FF;border:1px solid #CFE0FA;border-radius:9px;padding:.42rem .52rem;margin:.18rem 0 .3rem;font-size:.72rem;color:#3F5D78}
.ln-discovery-title{font-size:1.2rem;font-weight:850;color:#102E4D;margin:.05rem 0 .12rem}
.ln-discovery-sub{font-size:.8rem;color:#68798C;margin:0 0 .5rem}
.ln-choice{background:#fff;border:1px solid #D8E1EB;border-radius:11px;padding:.48rem .58rem;margin-bottom:.25rem}
.ln-choice strong{font-size:.86rem;color:#173351}.ln-choice span{display:block;font-size:.69rem;color:#748498;margin-top:.05rem}
.ln-empty{padding:1rem;text-align:center;background:#fff;border:1px dashed #C8D4E1;border-radius:12px;color:#68788D}
.ln-radar{display:flex;flex-wrap:wrap;gap:.3rem;background:#fff;border:1px solid #D8E1EB;border-radius:11px;padding:.52rem .58rem;margin:.35rem 0 .5rem}
.ln-chip{background:#EEF3F8;border:1px solid #DCE5EF;border-radius:999px;padding:.25rem .46rem;font-size:.73rem;color:#38516B}.ln-chip b{color:#173351}
div.stButton>button,a[data-testid="stLinkButton"]{border-radius:8px!important;min-height:2.25rem!important;font-weight:800!important}
div.stButton>button[kind="primary"]{background:var(--blue)!important;border-color:var(--blue)!important;color:#fff!important}
[data-baseweb="input"]>div,[data-baseweb="select"]>div{background:#fff!important;color:#173351!important;border-color:#C7D3E1!important;min-height:2.35rem!important}
input,textarea{color:#173351!important;-webkit-text-fill-color:#173351!important;background:#fff!important}
[data-testid="stWidgetLabel"] p{font-size:.75rem!important;font-weight:760!important;color:#344C66!important;margin-bottom:.04rem!important}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:10px;padding:.45rem .52rem}
[data-testid="stMetricLabel"] *,[data-testid="stMetricValue"] *{color:#173351!important}
[data-testid="stAlert"]{padding:.58rem .7rem!important;border-radius:10px!important}
@media(max-width:800px){
 .ln-meta-grid{grid-template-columns:1fr 1fr}.ln-item-head{display:none}.ln-item-row{grid-template-columns:1fr}
 .ln-item-qty,.ln-item-price{text-align:left}.block-container{padding-left:.65rem!important;padding-right:.65rem!important}
}
</style>
"""

def _dt(value):
    if not value:
        return "Não informado"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return str(value).replace("T", " ")[:16]

def _money(value):
    try:
        if value is None or float(value) <= 0:
            return "Não informado"
    except (TypeError, ValueError):
        return "Não informado"
    return format_brl(value)

def _html_money(value):
    return escape(_money(value)).replace("$", "&#36;")

def _short(value, limit=220):
    clean = " ".join(str(value or "").split())
    return clean if len(clean) <= limit else clean[:limit-1].rstrip(" ,.;:-") + "…"

@st.cache_data(ttl=45, show_spinner=False)
def _search(region, states, city, modalities, keyword, limit=160):
    return catalog.search(
        region=region,
        states=states,
        city=city,
        modalities=modalities,
        keyword=keyword,
        limit=limit,
    )

@st.cache_data(ttl=1800, show_spinner=False)
def _items(controls):
    shells = [{"pncp_control_number": c, "category": "Outros"} for c in controls if c]
    enriched = enrich_with_items(shells, max_workers=4, max_items=80)
    return {
        row.get("pncp_control_number"): {
            "items": row.get("items") or [],
            "item_count": int(row.get("item_count") or 0),
            "items_error": row.get("items_error") or "",
            "category": row.get("category") or "Outros",
        }
        for row in enriched
    }

@st.cache_data(ttl=3600, show_spinner=False)
def _history(item_reference, catalog_code, description, state):
    return fetch_price_history_for_item(
        {"source_reference": item_reference, "catalog_code": catalog_code, "description": description},
        state=state,
        months=18,
    )

@st.cache_data(ttl=120, show_spinner=False)
def _region_counts():
    return catalog.counts_by_region()

@st.cache_data(ttl=120, show_spinner=False)
def _state_counts():
    return catalog.counts_by_state()

def _init_state():
    defaults = {
        "mei_saved": {},
        "mei_radars": [],
        "mei_page": 1,
        "mei_open_opportunity": "",
        "mei_price_item": "",
        "mei_section": "🔎 Todas as oportunidades",
        "mei_filters": {"region": "", "states": [], "city": "", "modalities": [], "keyword": ""},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

def _sidebar():
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=150)
        st.markdown('<div class="ln-side-copy">Descubra oportunidades, produtos e preços reais de compras públicas.</div>', unsafe_allow_html=True)
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
        for i, label in enumerate(explore):
            if st.button(label, key=f"nav_e_{i}", type="primary" if current == label else "secondary", width="stretch"):
                st.session_state.mei_section = label
                st.rerun()
        st.markdown('<div class="ln-side-tag" style="margin-top:.45rem">Minha área</div>', unsafe_allow_html=True)
        for i, label in enumerate(personal):
            if st.button(label, key=f"nav_p_{i}", type="primary" if current == label else "secondary", width="stretch"):
                st.session_state.mei_section = label
                st.rerun()
        st.markdown(
            '<div class="ln-plan">LicitaNexo MEI<strong>R&#36; 29,90/mês</strong>'
            '<span>Oportunidades e inteligência de preços públicos.</span></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"{MEI_VERSION} · B2G SaaS")
    return current

def _filter_panel():
    filters = dict(st.session_state.mei_filters)
    st.markdown(
        '<div class="ln-hero"><span class="ln-kicker">DESCOBERTA DE OPORTUNIDADES</span>'
        '<h1>O que o governo está comprando?</h1>'
        '<p>Explore livremente. Você não precisa saber o que quer vender para começar.</p></div>',
        unsafe_allow_html=True,
    )
    regions = ["Brasil inteiro"] + list(BRAZIL_REGIONS)
    current_region = filters.get("region") or "Brasil inteiro"
    if current_region not in regions:
        current_region = "Brasil inteiro"
    c1, c2, c3, c4, c5 = st.columns([1, 1.15, 1.25, 1.15, 2.15])
    region = c1.selectbox("Região", regions, index=regions.index(current_region))
    states = c2.multiselect("Estados", list(BRAZIL_STATES), default=filters.get("states") or [], placeholder="Todos")
    city = c3.text_input("Cidade", value=filters.get("city") or "", placeholder="Ex.: Londrina")
    modalities = c4.multiselect("Modalidade", list(MODALITIES.keys()), default=filters.get("modalities") or [], placeholder="Todas")
    keyword = c5.text_input(
        "Produto, serviço ou palavra-chave",
        value=filters.get("keyword") or "",
        placeholder="Opcional — deixe em branco para descobrir",
    )
    b1, b2 = st.columns([5, 1])
    if b1.button("🔎 Buscar licitações", type="primary", width="stretch"):
        st.session_state.mei_filters = {
            "region": "" if region == "Brasil inteiro" else region,
            "states": list(states),
            "city": city.strip(),
            "modalities": list(modalities),
            "keyword": keyword.strip(),
        }
        st.session_state.mei_page = 1
        st.rerun()
    if b2.button("Limpar", width="stretch"):
        st.session_state.mei_filters = {"region": "", "states": [], "city": "", "modalities": [], "keyword": ""}
        st.session_state.mei_page = 1
        st.rerun()

def _render_price_history(history):
    if not history.get("available"):
        st.info(history.get("reason") or "Histórico ainda não disponível para este produto.")
        return
    summary = history["summary"]
    st.markdown("#### 📊 Quanto o governo pagou")
    st.caption(
        f"Fonte: Compras.gov · código de catálogo {history.get('catalog_code')}. "
        "Compare especificações antes de tratar itens como equivalentes."
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Último", _money(summary.get("last_price")))
    c2.metric("Média", _money(summary.get("average")))
    c3.metric("Mediana", _money(summary.get("median")))
    c4.metric("Menor", _money(summary.get("minimum")))
    c5.metric("Maior", _money(summary.get("maximum")))
    st.caption(f"{summary.get('count', 0)} compra(s) homologada(s) considerada(s) nos últimos 18 meses.")
    left, right = st.columns(2)
    brands = summary.get("brands") or []
    suppliers = summary.get("suppliers") or []
    with left:
        st.markdown("**🏷️ Marcas encontradas**")
        if brands:
            st.dataframe(pd.DataFrame([{"Marca": x["name"], "Ocorrências": x["count"]} for x in brands]), hide_index=True, width="stretch")
        else:
            st.caption("Marca não informada de forma confiável na amostra.")
    with right:
        st.markdown("**🏆 Fornecedores vencedores**")
        if suppliers:
            st.dataframe(pd.DataFrame([{"Fornecedor": x["name"], "Ocorrências": x["count"]} for x in suppliers]), hide_index=True, width="stretch")
        else:
            st.caption("Fornecedor não disponível na amostra.")
    rows = summary.get("rows") or []
    if rows:
        frame = pd.DataFrame([{
            "Data": str(x.get("published_at") or "")[:10],
            "Órgão": x.get("agency") or "",
            "Cidade/UF": "/".join(p for p in (str(x.get("city") or ""), str(x.get("state") or "")) if p),
            "Qtd.": x.get("quantity"),
            "Preço homologado": _money(x.get("homologated_unit_value")),
            "Marca": x.get("brand_normalized") or x.get("brand") or "Não informada",
            "Fornecedor": x.get("supplier") or "",
        } for x in rows[:12]])
        st.markdown("**Compras recentes**")
        st.dataframe(frame, hide_index=True, width="stretch")

def _render_items(pack, opportunity_id, state):
    items = pack.get("items") or []
    total = int(pack.get("item_count") or len(items))
    if not items:
        msg = pack.get("items_error") or "O PNCP não publicou itens estruturados para esta contratação."
        st.markdown(f'<div class="ln-items"><div class="ln-items-title">📦 Produtos do edital</div><div class="ln-item-name">{escape(msg)}</div></div>', unsafe_allow_html=True)
        return
    expanded = st.session_state.mei_open_opportunity == opportunity_id
    shown = items if expanded else items[:3]
    lines = [
        f'<div class="ln-items"><div class="ln-items-title">📦 Produtos do edital · {total} item(ns)</div>',
        '<div class="ln-item-head"><div>Produto / serviço</div><div>Quantidade</div><div>Estimado</div></div>',
    ]
    for row in shown:
        desc = escape(_short(row.get("description") or "Item não descrito", 300 if expanded else 185))
        try:
            qty = f"{float(row.get('quantity')):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            qty = "—"
        unit = escape(str(row.get("unit_measure") or ""))
        price = "Sigiloso" if row.get("confidential") else _html_money(row.get("unit_price"))
        lines.append(
            f'<div class="ln-item-row"><div class="ln-item-name">{desc}</div>'
            f'<div class="ln-item-qty">{qty} {unit}</div><div class="ln-item-price">{price}</div></div>'
        )
    lines.append("</div>")
    st.markdown("".join(lines), unsafe_allow_html=True)

    left, right = st.columns([1.2, 2.2])
    if total > 3:
        label = "Mostrar menos" if expanded else f"Ver todos os {total} produtos"
        if left.button(label, key=f"all_{opportunity_id}", width="stretch"):
            st.session_state.mei_open_opportunity = "" if expanded else opportunity_id
            st.rerun()
    else:
        left.caption("Todos os itens estão visíveis.")
    if right.button("💰 Ver preços pagos pelo governo", key=f"prices_{opportunity_id}", type="primary", width="stretch"):
        st.session_state.mei_open_opportunity = opportunity_id
        st.rerun()
    st.markdown(
        '<div class="ln-price-note">Veja compras homologadas, faixas de preço, marcas e fornecedores vencedores quando publicados nas fontes oficiais.</div>',
        unsafe_allow_html=True,
    )

    if expanded:
        choices = [x for x in items if str(x.get("description") or "").strip()]
        if choices:
            selected = st.selectbox(
                "Produto para consultar histórico",
                range(len(choices)),
                format_func=lambda i: _short(choices[i].get("description") or "", 105),
                key=f"sel_{opportunity_id}",
            )
            item = choices[selected]
            ref = str(item.get("source_reference") or f"{opportunity_id}:{selected}")
            if st.button("Consultar histórico deste produto", key=f"hist_{opportunity_id}"):
                st.session_state.mei_price_item = ref
            if st.session_state.mei_price_item == ref:
                with st.spinner("Consultando compras homologadas no Compras.gov..."):
                    history = _history(ref, str(item.get("catalog_code") or ""), str(item.get("description") or ""), state)
                _render_price_history(history)

def _render_opportunity(row, pack):
    oid = str(row.get("id") or row.get("pncp_control_number") or "")
    modality = escape(str(row.get("modality") or "Modalidade não informada"))
    category = escape(str(pack.get("category") or row.get("category") or "Outros"))
    obj = escape(_short(row.get("object") or "Objeto não informado", 290))
    agency = escape(str(row.get("agency") or "Órgão não informado"))
    city = escape(str(row.get("city") or "Município não informado"))
    state = escape(str(row.get("state") or "--"))
    portal = escape(str(row.get("portal") or "Não identificado"))
    access = escape(str(row.get("portal_access") or "Verificar condições"))
    tone = str(row.get("portal_access_tone") or "unknown")
    tone_class = "ln-free" if tone == "free" else "ln-paid" if tone in {"paid", "conditional"} else "ln-unknown"
    total = int(pack.get("item_count") or len(pack.get("items") or []))
    st.markdown(
        f'<div class="ln-card"><div class="ln-top"><div class="ln-top-left">'
        f'<span class="ln-badge">{modality}</span><span class="ln-cat">{category}</span><span class="ln-count">📦 {total} item(ns)</span>'
        f'</div><div class="ln-portal">🌐 {portal} <span class="{tone_class}">● {access}</span></div></div>'
        f'<div class="ln-object">{obj}</div><div class="ln-meta-grid">'
        f'<div class="ln-meta"><small>Cidade</small><strong>{city} — {state}</strong></div>'
        f'<div class="ln-meta"><small>Órgão</small><strong>{agency}</strong></div>'
        f'<div class="ln-meta"><small>Valor estimado</small><strong>{_html_money(row.get("estimated_value"))}</strong></div>'
        f'<div class="ln-meta"><small>Fim das propostas</small><strong>{escape(_dt(row.get("closing_at")))}</strong></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    _render_items(pack, oid, str(row.get("state") or ""))
    a, b, c = st.columns([1.2, 1, 1])
    saved = oid in st.session_state.mei_saved
    if a.button("✓ Salvo" if saved else "⭐ Salvar", key=f"save_{oid}", disabled=saved, width="stretch"):
        st.session_state.mei_saved[oid] = dict(row)
        st.rerun()
    source_url = str(row.get("source_url") or "")
    pncp_url = str(row.get("pncp_url") or "")
    if source_url.startswith(("http://", "https://")):
        b.link_button("🌐 Portal", source_url, width="stretch")
    if pncp_url.startswith(("http://", "https://")):
        c.link_button("📄 PNCP", pncp_url, width="stretch")

def _load_rows(filters, limit=160):
    return _search(
        filters.get("region") or "",
        tuple(filters.get("states") or []),
        filters.get("city") or "",
        tuple(filters.get("modalities") or []),
        filters.get("keyword") or "",
        limit,
    )

def _explore_page():
    _filter_panel()
    filters = st.session_state.mei_filters
    with st.spinner("Organizando oportunidades abertas..."):
        rows = _load_rows(filters, 160)
    st.markdown(f'<div class="ln-results"><h3>Oportunidades abertas</h3><span>{len(rows)} encontrada(s)</span></div>', unsafe_allow_html=True)
    if not rows:
        st.markdown('<div class="ln-empty">Nenhuma oportunidade encontrada. Amplie os filtros para continuar explorando.</div>', unsafe_allow_html=True)
        return
    st.caption("Explore livremente. Os filtros servem apenas para aproximar a busca do que chamou sua atenção.")
    per_page = 10
    total_pages = max((len(rows) + per_page - 1) // per_page, 1)
    current = min(max(int(st.session_state.mei_page), 1), total_pages)
    visible = rows[(current-1)*per_page: current*per_page]
    controls = tuple(str(x.get("pncp_control_number") or "") for x in visible)
    with st.spinner("Buscando os produtos dos editais no PNCP..."):
        item_map = _items(controls)
    for row in visible:
        control = str(row.get("pncp_control_number") or "")
        pack = item_map.get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"})
        _render_opportunity(row, pack)
    p1, p2, p3 = st.columns([1, 1, 2])
    if p1.button("◀ Anterior", disabled=current <= 1, width="stretch"):
        st.session_state.mei_page = current - 1
        st.rerun()
    if p2.button("Próxima ▶", disabled=current >= total_pages, width="stretch"):
        st.session_state.mei_page = current + 1
        st.rerun()
    p3.caption(f"Página {current} de {total_pages}")

def _apply_discovery(*, region="", states=None, city="", modalities=None, keyword=""):
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
    counts = _region_counts()
    cols = st.columns(3)
    for i, region in enumerate(BRAZIL_REGIONS):
        with cols[i % 3]:
            total = int(counts.get(region, 0))
            st.markdown(f'<div class="ln-choice"><strong>{escape(region)}</strong><span>{total} oportunidade(s) aberta(s)</span></div>', unsafe_allow_html=True)
            if st.button("Ver licitações", key=f"region_{region}", width="stretch"):
                _apply_discovery(region=region)

def _state_page():
    st.markdown('<div class="ln-discovery-title">📍 Explore por estado</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Escolha uma UF para ver somente as oportunidades abertas daquele estado.</div>', unsafe_allow_html=True)
    counts = _state_counts()
    states = sorted(BRAZIL_STATES, key=lambda x: (-int(counts.get(x, 0)), x))
    cols = st.columns(4)
    for i, state in enumerate(states):
        with cols[i % 4]:
            if st.button(f"{state} · {int(counts.get(state, 0))}", key=f"state_{state}", width="stretch"):
                _apply_discovery(states=[state])

def _city_page():
    st.markdown('<div class="ln-discovery-title">🏙️ Explore por cidade</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Digite uma cidade. A busca aceita nomes com ou sem acento.</div>', unsafe_allow_html=True)
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
    for i, modality in enumerate(options):
        with cols[i % 2]:
            if st.button(str(modality), key=f"mod_{i}", width="stretch"):
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
    rows = _search("", tuple(), "", tuple(), "", 80)
    pre = sorted(rows, key=_highlight_score, reverse=True)[:24]
    controls = tuple(str(x.get("pncp_control_number") or "") for x in pre)
    with st.spinner("Organizando os destaques..."):
        item_map = _items(controls)
    ranked = []
    for row in pre:
        control = str(row.get("pncp_control_number") or "")
        pack = item_map.get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"})
        score = _highlight_score(row) + (4 if int(pack.get("item_count") or 0) > 0 else 0)
        if str(pack.get("category") or "Outros") != "Outros":
            score += 1
        ranked.append((score, row, pack))
    for _, row, pack in sorted(ranked, key=lambda x: x[0], reverse=True)[:10]:
        _render_opportunity(row, pack)

def _saved_page():
    st.markdown("## ⭐ Minha lista")
    st.caption("No preview, a lista fica nesta sessão do navegador.")
    saved = list(st.session_state.mei_saved.values())
    if not saved:
        st.markdown('<div class="ln-empty">Você ainda não salvou nenhuma oportunidade.</div>', unsafe_allow_html=True)
        return
    controls = tuple(str(x.get("pncp_control_number") or "") for x in saved)
    item_map = _items(controls)
    for row in saved:
        control = str(row.get("pncp_control_number") or "")
        _render_opportunity(row, item_map.get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"}))
        oid = str(row.get("id") or row.get("pncp_control_number") or "")
        if st.button("Remover da lista", key=f"remove_{oid}"):
            st.session_state.mei_saved.pop(oid, None)
            st.rerun()

def _radar_page():
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
    html = "".join(f'<span class="ln-chip"><b>{escape(k)}:</b> {escape(str(v))}</span>' for k, v in chips)
    st.markdown(f'<div class="ln-radar">{html}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    name = c1.text_input("Nome do radar", placeholder="Ex.: oportunidades em Londrina")
    if c2.button("🔔 Salvar radar", type="primary", width="stretch"):
        st.session_state.mei_radars.append({"name": name.strip() or f"Radar {len(st.session_state.mei_radars)+1}", "filters": filters})
        st.success("Radar salvo nesta sessão.")
    for i, radar in enumerate(st.session_state.mei_radars):
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{escape(radar['name'])}**")
            if right.button("Usar", key=f"use_radar_{i}", width="stretch"):
                st.session_state.mei_filters = dict(radar["filters"])
                st.session_state.mei_section = "🔎 Todas as oportunidades"
                st.session_state.mei_page = 1
                st.rerun()
    st.caption("Alertas automáticos entram na etapa comercial; neste preview o Radar salva a busca na sessão.")

def main():
    st.markdown(CSS, unsafe_allow_html=True)
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
        _radar_page()
