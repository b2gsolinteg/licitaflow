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
MEI_VERSION = "1.0 MEI Preview 6"
MEI_PRICE = "R$ 29,90/mês"

db = Database(database_path(PROJECT_ROOT))
catalog = MeiCatalogService(db)

UF_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}

CSS = """
<style>
:root{
  --ink:#172B3A;--navy:#11314D;--muted:#6F8190;--brand:#0F8F7B;--brand-dark:#0B6F61;
  --brand-soft:#EAF7F4;--gold:#D4A72C;--gold-soft:#FFF7DF;--bg:#F3F6F8;--card:#FFFFFF;
  --line:#DFE6EC;--soft:#F8FAFB;--danger:#A15B16;
}
html,body,[data-testid="stAppViewContainer"],.stApp{background:var(--bg)!important;color:var(--ink)!important}
header[data-testid="stHeader"]{background:rgba(243,246,248,.97)!important}
.block-container{max-width:1190px!important;padding-top:.55rem!important;padding-bottom:1.5rem!important}

[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--line)!important}
[data-testid="stSidebar"]>div:first-child{padding-top:.45rem!important}
[data-testid="stSidebar"] img{max-width:154px!important;display:block;margin:.4rem .15rem .1rem 0!important}
.ln-version{display:inline-flex;align-items:center;gap:.28rem;background:#F0F4F7;border:1px solid #DCE4EA;border-radius:999px;padding:.27rem .55rem;font-size:.71rem;font-weight:850;color:#39556A;margin:.15rem 0 .55rem}
.ln-side-copy{font-size:.78rem;line-height:1.35;color:#738493;margin:0 0 .55rem;text-align:left}
.ln-side-group{font-size:.65rem;font-weight:900;letter-spacing:.09em;color:#9AA7B2;text-transform:uppercase;margin:.52rem 0 .13rem;text-align:left}
[data-testid="stSidebar"] div.stButton{margin:.03rem 0!important}
[data-testid="stSidebar"] div.stButton>button{justify-content:flex-start!important;text-align:left!important;width:100%!important;min-height:2.48rem!important;padding:.42rem .62rem!important;border-radius:9px!important;font-size:.96rem!important;font-weight:750!important;box-shadow:none!important}
[data-testid="stSidebar"] div.stButton>button p{width:100%!important;text-align:left!important;margin:0!important;font-size:.96rem!important}
[data-testid="stSidebar"] div.stButton>button[kind="secondary"]{background:transparent!important;border:1px solid transparent!important;color:#27465D!important}
[data-testid="stSidebar"] div.stButton>button[kind="secondary"]:hover{background:#F4F7F8!important;border-color:#E8EDF1!important}
[data-testid="stSidebar"] div.stButton>button[kind="primary"]{background:var(--brand-soft)!important;border:1px solid #CDE9E3!important;border-left:4px solid var(--brand)!important;color:#123F39!important}
.ln-plan{margin-top:.65rem;padding:.62rem .7rem;border-radius:10px;background:#F7F9FA;border:1px solid var(--line);color:#6C7F8E;font-size:.73rem;line-height:1.35}.ln-plan strong{display:block;color:var(--ink);font-size:1rem;margin:.06rem 0}.ln-plan b{color:var(--brand-dark)}

.ln-page-head{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin:.15rem 0 .7rem}.ln-page-head h1{font-size:1.65rem;line-height:1.12;margin:0;color:var(--navy)}.ln-page-head p{margin:.22rem 0 0;color:#6C7F90;font-size:.88rem}.ln-page-chip{background:var(--gold-soft);border:1px solid #EFDBA2;border-radius:10px;padding:.48rem .65rem;color:#775907;font-size:.72rem;font-weight:800;white-space:nowrap}
.ln-kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:.55rem;margin-bottom:.8rem}.ln-kpi{background:#fff;border:1px solid var(--line);border-radius:12px;padding:.7rem .8rem}.ln-kpi small{display:block;color:#8796A3;text-transform:uppercase;font-size:.6rem;font-weight:850;letter-spacing:.04em}.ln-kpi strong{display:block;color:var(--navy);font-size:1.32rem;margin-top:.06rem}.ln-kpi span{font-size:.72rem;color:#718393}
.ln-section-title{font-size:1.15rem;font-weight:880;color:var(--navy);margin:.12rem 0 .08rem}.ln-section-sub{font-size:.8rem;color:#758697;margin:0 0 .5rem}

.ln-state-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:.7rem .75rem .58rem;margin-bottom:.16rem;box-shadow:0 3px 10px rgba(27,49,69,.025)}.ln-state-card .name{font-size:.92rem;font-weight:850;color:#173B55}.ln-state-card .uf{color:#7A8997;font-weight:700}.ln-state-card .count{font-size:1.45rem;line-height:1.15;font-weight:900;color:var(--navy);margin-top:.32rem}.ln-state-card .label{font-size:.7rem;color:#738493}

.ln-search{background:#fff;border:1px solid var(--line);border-radius:13px;padding:.72rem .82rem;margin-bottom:.65rem}.ln-search-title{font-size:.92rem;font-weight:850;color:#223E53;margin-bottom:.18rem}.ln-search-hint{font-size:.73rem;color:#80909D;margin-bottom:.25rem}
[data-testid="stWidgetLabel"] p{font-size:.74rem!important;font-weight:760!important;color:#415A6E!important;margin-bottom:.03rem!important}
[data-baseweb="input"]>div,[data-baseweb="select"]>div{background:#fff!important;color:var(--ink)!important;border-color:#C9D4DE!important;min-height:2.42rem!important;border-radius:8px!important}
input,textarea{color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;background:#fff!important}
div.stButton>button,a[data-testid="stLinkButton"]{border-radius:8px!important;min-height:2.42rem!important;font-weight:800!important}
div.stButton>button[kind="primary"]{background:var(--brand)!important;border-color:var(--brand)!important;color:#fff!important}div.stButton>button[kind="primary"]:hover{background:var(--brand-dark)!important;border-color:var(--brand-dark)!important}

.ln-resultsbar{display:flex;align-items:end;justify-content:space-between;gap:.8rem;margin:.65rem .05rem .35rem}.ln-resultsbar h2{font-size:1.18rem;color:var(--navy);margin:0}.ln-resultsbar span{font-size:.75rem;color:#738697}
div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:13px!important;box-shadow:0 4px 14px rgba(28,49,68,.035)!important;margin-bottom:.5rem!important}div[data-testid="stVerticalBlockBorderWrapper"]>div{padding:.72rem .8rem .68rem!important}
.ln-card-top{display:flex;align-items:center;justify-content:space-between;gap:.5rem;flex-wrap:wrap;margin-bottom:.25rem}.ln-tags{display:flex;gap:.28rem;flex-wrap:wrap}.ln-tag{display:inline-flex;align-items:center;border-radius:999px;padding:.19rem .44rem;font-size:.64rem;font-weight:850}.ln-mode{background:#EAF7F4;color:#0C6F61;border:1px solid #CFE9E3}.ln-cat{background:#EEF3F8;color:#3D5E7D;border:1px solid #DEE7EF}.ln-items{background:#FFF7E7;color:#80600A;border:1px solid #F0DCA3}.ln-deadline{background:#FFF1DF;color:#8D5810;border:1px solid #EFD2A3}.ln-portal{display:inline-flex;gap:.28rem;align-items:center;background:#F6F8FA;border:1px solid #E0E6EB;border-radius:999px;padding:.22rem .48rem;font-size:.65rem;font-weight:750;color:#516A7D}.ln-free{color:#0B7655}.ln-paid{color:#956006}.ln-unknown{color:#728193}.ln-title{font-size:1rem;font-weight:850;line-height:1.27;color:#16354D;margin:.08rem 0 .42rem}
.ln-facts{display:grid;grid-template-columns:1.05fr 1.3fr .85fr .95fr;gap:0;border-top:1px solid #EDF1F4;border-bottom:1px solid #EDF1F4;margin:.2rem 0 .42rem}.ln-fact{padding:.43rem .52rem;border-right:1px solid #EDF1F4}.ln-fact:last-child{border-right:0}.ln-fact small{display:block;font-size:.58rem;color:#8B99A6;text-transform:uppercase;font-weight:850}.ln-fact strong{display:block;font-size:.78rem;color:#29465D;margin-top:.06rem;line-height:1.2}.ln-preview-items{font-size:.76rem;color:#51697B;line-height:1.35}.ln-preview-items b{color:#24445C}
.ln-detail-title{font-size:1.35rem;font-weight:900;color:var(--navy);line-height:1.22;margin:.15rem 0 .5rem}.ln-detail-note{background:#F4F8F8;border:1px solid #DCEBE8;border-left:4px solid var(--brand);border-radius:9px;padding:.52rem .6rem;color:#58736E;font-size:.74rem;margin:.5rem 0}.ln-item-head,.ln-item-row{display:grid;grid-template-columns:minmax(0,1fr) 105px 105px;gap:.4rem;align-items:start}.ln-item-head{font-size:.59rem;color:#8795A2;text-transform:uppercase;font-weight:850;border-bottom:1px solid #E6EBEF;padding:.14rem 0 .22rem}.ln-item-row{padding:.34rem 0;border-bottom:1px solid #EFF2F4}.ln-item-name{font-size:.78rem;color:#385267;line-height:1.28}.ln-item-qty,.ln-item-price{text-align:right;font-size:.74rem;color:#65788A}.ln-item-price{font-weight:850;color:#173F58}.ln-intel-lock{background:#FFF9EA;border:1px solid #EEDCA8;border-radius:10px;padding:.58rem .65rem;color:#705B1E;font-size:.74rem;margin:.55rem 0}.ln-empty{background:#fff;border:1px dashed #C7D3DC;border-radius:12px;padding:1rem;text-align:center;color:#758697}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:9px;padding:.45rem .52rem}[data-testid="stMetricLabel"] *,[data-testid="stMetricValue"] *{color:#24435D!important}
@media(max-width:850px){.ln-kpis{grid-template-columns:1fr}.ln-facts{grid-template-columns:1fr 1fr}.ln-item-head{display:none}.ln-item-row{grid-template-columns:1fr}.ln-item-qty,.ln-item-price{text-align:left}.block-container{padding-left:.7rem!important;padding-right:.7rem!important}}
</style>
"""


def _money(value):
    try:
        if value is None or float(value) <= 0:
            return "Não informado"
    except (TypeError, ValueError):
        return "Não informado"
    return format_brl(value)


def _html_money(value):
    return escape(_money(value)).replace("$", "&#36;")


def _dt(value):
    if not value:
        return "Não informado"
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return str(value).replace("T", " ")[:16]


def _deadline(value):
    if not value:
        return "Prazo não informado"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
        hours = (parsed - now).total_seconds() / 3600
        if hours < 0:
            return "Encerrado"
        if hours < 24:
            return f"Encerra em {max(1, int(hours))}h"
        days = max(1, int(hours // 24))
        return "Encerra amanhã" if days == 1 else f"Encerra em {days} dias"
    except (TypeError, ValueError):
        return "Prazo informado"


def _short(value, limit=190):
    clean = " ".join(str(value or "").split())
    return clean if len(clean) <= limit else clean[: limit - 1].rstrip(" ,.;:-") + "…"


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
    shells = [{"pncp_control_number": value, "category": "Outros"} for value in controls if value]
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
def _history(reference, catalog_code, description, state):
    return fetch_price_history_for_item(
        {"source_reference": reference, "catalog_code": catalog_code, "description": description},
        state=state,
        months=18,
    )


@st.cache_data(ttl=120, show_spinner=False)
def _state_counts():
    return catalog.counts_by_state()


@st.cache_data(ttl=120, show_spinner=False)
def _region_counts():
    return catalog.counts_by_region()


def _init_state():
    defaults = {
        "mei_section": "🏠 Início",
        "mei_filters": {"region": "", "states": [], "city": "", "modalities": [], "keyword": ""},
        "mei_page": 1,
        "mei_detail_id": "",
        "mei_decided_id": "",
        "mei_price_item": "",
        "mei_saved": {},
        "mei_radars": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _go(section):
    st.session_state.mei_section = section
    st.session_state.mei_detail_id = ""
    st.session_state.mei_decided_id = ""
    st.session_state.mei_price_item = ""
    st.rerun()


def _sidebar():
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=154)
        st.markdown(f'<div class="ln-version">● {MEI_VERSION}</div>', unsafe_allow_html=True)
        st.markdown('<div class="ln-side-copy">Descubra o que o governo compra e encontre oportunidades sem precisar escolher um nicho antes.</div>', unsafe_allow_html=True)
        current = st.session_state.mei_section
        explore = ["🏠 Início", "🔎 Buscar editais", "📍 Por localização", "📋 Por modalidade", "🔥 Em destaque"]
        personal = ["⭐ Salvos", "🔔 Radar"]
        st.markdown('<div class="ln-side-group">Explorar</div>', unsafe_allow_html=True)
        for index, label in enumerate(explore):
            if st.button(label, key=f"nav_explore_{index}", type="primary" if current == label else "secondary", width="stretch"):
                _go(label)
        st.markdown('<div class="ln-side-group">Minha área</div>', unsafe_allow_html=True)
        for index, label in enumerate(personal):
            if st.button(label, key=f"nav_personal_{index}", type="primary" if current == label else "secondary", width="stretch"):
                _go(label)
        st.markdown('<div class="ln-plan">LicitaNexo MEI<strong>R&#36; 29,90/mês</strong><b>Descubra → avalie → salve.</b><br>Itens oficiais do PNCP e inteligência de preço quando você decidir avançar.</div>', unsafe_allow_html=True)
    return current


def _set_state_and_search(uf):
    st.session_state.mei_filters = {"region": "", "states": [uf], "city": "", "modalities": [], "keyword": ""}
    st.session_state.mei_page = 1
    st.session_state.mei_section = "🔎 Buscar editais"
    st.session_state.mei_detail_id = ""
    st.rerun()


def _home_page():
    counts = _state_counts()
    total = sum(int(counts.get(uf, 0)) for uf in BRAZIL_STATES)
    active_states = sum(1 for uf in BRAZIL_STATES if int(counts.get(uf, 0)) > 0)
    top_uf = max(BRAZIL_STATES, key=lambda uf: int(counts.get(uf, 0))) if BRAZIL_STATES else "--"
    st.markdown(
        f'<div class="ln-page-head"><div><h1>Licitações abertas no Brasil</h1><p>Comece explorando por Estado. Você não precisa saber o que quer vender para encontrar oportunidades.</p></div><div class="ln-page-chip">Plano MEI · R&#36; 29,90/mês</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ln-kpis"><div class="ln-kpi"><small>Oportunidades abertas</small><strong>{total:,}</strong><span>na base atual</span></div><div class="ln-kpi"><small>Estados com oportunidades</small><strong>{active_states}</strong><span>UFs com editais abertos</span></div><div class="ln-kpi"><small>Maior volume agora</small><strong>{top_uf}</strong><span>{int(counts.get(top_uf,0))} oportunidade(s)</span></div></div>'.replace(",", "."),
        unsafe_allow_html=True,
    )
    st.markdown('<div class="ln-section-title">Explore por Estado</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-section-sub">Clique em um Estado para ver as oportunidades abertas e os itens publicados no PNCP.</div>', unsafe_allow_html=True)
    states = list(BRAZIL_STATES)
    cols = st.columns(3)
    for index, uf in enumerate(states):
        with cols[index % 3]:
            count = int(counts.get(uf, 0))
            name = UF_NAMES.get(uf, uf)
            st.markdown(
                f'<div class="ln-state-card"><div class="name">{escape(name)} <span class="uf">({uf})</span></div><div class="count">{count}</div><div class="label">licitação(ões) aberta(s)</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Ver oportunidades", key=f"home_state_{uf}", width="stretch"):
                _set_state_and_search(uf)


def _filter_panel():
    filters = dict(st.session_state.mei_filters)
    regions = ["Brasil inteiro"] + list(BRAZIL_REGIONS)
    region_value = filters.get("region") or "Brasil inteiro"
    if region_value not in regions:
        region_value = "Brasil inteiro"
    st.markdown('<div class="ln-search"><div class="ln-search-title">Buscar oportunidades</div><div class="ln-search-hint">Todos os campos são opcionais. Deixe em branco para descobrir novos nichos.</div>', unsafe_allow_html=True)
    keyword = st.text_input("Produto, serviço ou palavra-chave", value=filters.get("keyword") or "", placeholder="Ex.: papel, café, uniforme — ou deixe em branco")
    c1, c2, c3, c4 = st.columns([1, 1.1, 1.3, 1.2])
    region = c1.selectbox("Região", regions, index=regions.index(region_value))
    states = c2.multiselect("Estado", list(BRAZIL_STATES), default=filters.get("states") or [], placeholder="Todos")
    city = c3.text_input("Cidade", value=filters.get("city") or "", placeholder="Ex.: Londrina")
    modalities = c4.multiselect("Modalidade", list(MODALITIES.keys()), default=filters.get("modalities") or [], placeholder="Todas")
    b1, b2 = st.columns([5, 1])
    search_clicked = b1.button("🔎 Ver oportunidades", type="primary", width="stretch")
    clear_clicked = b2.button("Limpar", width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)
    if search_clicked:
        st.session_state.mei_filters = {
            "region": "" if region == "Brasil inteiro" else region,
            "states": list(states),
            "city": city.strip(),
            "modalities": list(modalities),
            "keyword": keyword.strip(),
        }
        st.session_state.mei_page = 1
        st.session_state.mei_detail_id = ""
        st.rerun()
    if clear_clicked:
        st.session_state.mei_filters = {"region": "", "states": [], "city": "", "modalities": [], "keyword": ""}
        st.session_state.mei_page = 1
        st.session_state.mei_detail_id = ""
        st.rerun()


def _render_list_card(row, pack):
    oid = str(row.get("id") or row.get("pncp_control_number") or "")
    modality = escape(str(row.get("modality") or "Modalidade não informada"))
    category = escape(str(pack.get("category") or row.get("category") or "Outros"))
    title = escape(_short(row.get("object") or "Objeto não informado", 250))
    city = escape(str(row.get("city") or "Município não informado"))
    state = escape(str(row.get("state") or "--"))
    agency = escape(str(row.get("agency") or "Órgão não informado"))
    portal = escape(str(row.get("portal") or "Não identificado"))
    access = escape(str(row.get("portal_access") or "Verificar condições"))
    tone = str(row.get("portal_access_tone") or "unknown")
    tone_class = "ln-free" if tone == "free" else "ln-paid" if tone in {"paid", "conditional"} else "ln-unknown"
    items = pack.get("items") or []
    total = int(pack.get("item_count") or len(items))
    preview = " · ".join(escape(_short(item.get("description") or "Item", 72)) for item in items[:3]) or "Itens não publicados de forma estruturada no PNCP."
    with st.container(border=True):
        st.markdown(
            f'<div class="ln-card-top"><div class="ln-tags"><span class="ln-tag ln-mode">{modality}</span><span class="ln-tag ln-cat">{category}</span><span class="ln-tag ln-items">📦 {total} item(ns)</span><span class="ln-tag ln-deadline">{escape(_deadline(row.get("closing_at")))}</span></div><div class="ln-portal">🌐 {portal} <span class="{tone_class}">● {access}</span></div></div><div class="ln-title">{title}</div><div class="ln-facts"><div class="ln-fact"><small>Cidade</small><strong>{city} — {state}</strong></div><div class="ln-fact"><small>Órgão</small><strong>{agency}</strong></div><div class="ln-fact"><small>Valor estimado</small><strong>{_html_money(row.get("estimated_value"))}</strong></div><div class="ln-fact"><small>Fim das propostas</small><strong>{escape(_dt(row.get("closing_at")))}</strong></div></div><div class="ln-preview-items"><b>Principais itens:</b> {preview}</div>',
            unsafe_allow_html=True,
        )
        a, b = st.columns([3, 1])
        if a.button("Ver oportunidade", key=f"open_{oid}", type="primary", width="stretch"):
            st.session_state.mei_detail_id = oid
            st.session_state.mei_decided_id = ""
            st.session_state.mei_price_item = ""
            st.rerun()
        if b.button("⭐ Salvar", key=f"save_{oid}", disabled=oid in st.session_state.mei_saved, width="stretch"):
            st.session_state.mei_saved[oid] = dict(row)
            st.rerun()


def _render_price_history(history):
    if not history.get("available"):
        st.info(history.get("reason") or "Histórico ainda não disponível para este item.")
        return
    summary = history["summary"]
    st.markdown("### 💰 Histórico de preços públicos")
    st.caption(f"Fonte: Compras.gov · código de catálogo {history.get('catalog_code')}. Compare especificações antes de considerar produtos equivalentes.")
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
        frame = pd.DataFrame([
            {
                "Data": str(x.get("published_at") or "")[:10],
                "Órgão": x.get("agency") or "",
                "Cidade/UF": "/".join(part for part in (str(x.get("city") or ""), str(x.get("state") or "")) if part),
                "Qtd.": x.get("quantity"),
                "Preço homologado": _money(x.get("homologated_unit_value")),
                "Marca": x.get("brand_normalized") or x.get("brand") or "Não informada",
                "Fornecedor": x.get("supplier") or "",
            }
            for x in rows[:12]
        ])
        st.markdown("**Compras recentes**")
        st.dataframe(frame, hide_index=True, width="stretch")


def _render_detail(row, pack):
    oid = str(row.get("id") or row.get("pncp_control_number") or "")
    items = pack.get("items") or []
    total = int(pack.get("item_count") or len(items))
    if st.button("← Voltar às oportunidades"):
        st.session_state.mei_detail_id = ""
        st.session_state.mei_decided_id = ""
        st.session_state.mei_price_item = ""
        st.rerun()
    st.markdown(f'<div class="ln-detail-title">{escape(str(row.get("object") or "Objeto não informado"))}</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cidade", f"{row.get('city') or '—'} / {row.get('state') or '—'}")
    c2.metric("Valor estimado", _money(row.get("estimated_value")))
    c3.metric("Fim das propostas", _dt(row.get("closing_at")))
    c4.metric("Itens no PNCP", total)
    portal = str(row.get("portal") or "Não identificado")
    access = str(row.get("portal_access") or "Verificar condições")
    st.caption(f"Portal da disputa: {portal} · {access}")

    st.markdown("### 📦 Itens da oportunidade")
    if not items:
        st.info(pack.get("items_error") or "O PNCP não publicou itens estruturados para esta contratação.")
    else:
        st.markdown('<div class="ln-item-head"><div>Produto / serviço</div><div>Quantidade</div><div>Estimado</div></div>', unsafe_allow_html=True)
        lines = []
        for item in items:
            description = escape(str(item.get("description") or "Item não descrito"))
            try:
                qty = f"{float(item.get('quantity')):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except (TypeError, ValueError):
                qty = "—"
            unit = escape(str(item.get("unit_measure") or ""))
            price = "Sigiloso" if item.get("confidential") else _html_money(item.get("unit_price"))
            lines.append(f'<div class="ln-item-row"><div class="ln-item-name">{description}</div><div class="ln-item-qty">{qty} {unit}</div><div class="ln-item-price">{price}</div></div>')
        st.markdown("".join(lines), unsafe_allow_html=True)

    source_url = str(row.get("source_url") or "")
    pncp_url = str(row.get("pncp_url") or "")
    links = st.columns(3)
    if source_url.startswith(("http://", "https://")):
        links[0].link_button("🌐 Portal da disputa", source_url, width="stretch")
    if pncp_url.startswith(("http://", "https://")):
        links[1].link_button("📄 Ver no PNCP", pncp_url, width="stretch")
    if links[2].button("⭐ Salvar oportunidade", key=f"detail_save_{oid}", disabled=oid in st.session_state.mei_saved, width="stretch"):
        st.session_state.mei_saved[oid] = dict(row)
        st.rerun()

    if st.session_state.mei_decided_id != oid:
        st.markdown('<div class="ln-intel-lock"><b>Quer avaliar se vale a pena avançar?</b><br>Ao decidir avaliar esta oportunidade, o LicitaNexo libera a consulta de preços históricos dos itens para apoiar sua decisão.</div>', unsafe_allow_html=True)
        if st.button("Quero avaliar esta oportunidade", key=f"decide_{oid}", type="primary", width="stretch"):
            st.session_state.mei_decided_id = oid
            st.rerun()
        return

    st.markdown('<div class="ln-detail-note"><b>Modo de avaliação ativado.</b> Agora escolha um item para comparar com compras públicas homologadas anteriores. O histórico é apoio de decisão, não garantia de preço futuro.</div>', unsafe_allow_html=True)
    choices = [item for item in items if str(item.get("description") or "").strip()]
    if not choices:
        st.info("Não há item estruturado disponível para consulta histórica.")
        return
    selected = st.selectbox(
        "Item para consultar histórico",
        range(len(choices)),
        format_func=lambda index: _short(choices[index].get("description") or "", 110),
        key=f"detail_item_{oid}",
    )
    item = choices[selected]
    reference = str(item.get("source_reference") or f"{oid}:{selected}")
    if st.button("Consultar histórico deste item", key=f"history_{oid}", type="primary"):
        st.session_state.mei_price_item = reference
    if st.session_state.mei_price_item == reference:
        with st.spinner("Buscando compras homologadas..."):
            history = _history(reference, str(item.get("catalog_code") or ""), str(item.get("description") or ""), str(row.get("state") or ""))
        _render_price_history(history)


def _load_rows(filters, limit=160):
    return _search(
        filters.get("region") or "",
        tuple(filters.get("states") or []),
        filters.get("city") or "",
        tuple(filters.get("modalities") or []),
        filters.get("keyword") or "",
        limit,
    )


def _search_page():
    st.markdown('<div class="ln-page-head"><div><h1>Buscar editais</h1><p>Filtre quando quiser. Sem filtros, o LicitaNexo mostra oportunidades abertas para você explorar.</p></div></div>', unsafe_allow_html=True)
    _filter_panel()
    filters = st.session_state.mei_filters
    with st.spinner("Organizando oportunidades..."):
        rows = _load_rows(filters, 160)
    if st.session_state.mei_detail_id:
        row = next((item for item in rows if str(item.get("id") or item.get("pncp_control_number") or "") == st.session_state.mei_detail_id), None)
        if row:
            control = str(row.get("pncp_control_number") or "")
            pack = _items((control,)).get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"})
            _render_detail(row, pack)
            return
        st.session_state.mei_detail_id = ""

    st.markdown(f'<div class="ln-resultsbar"><h2>Oportunidades abertas</h2><span>{len(rows)} encontrada(s)</span></div>', unsafe_allow_html=True)
    if not rows:
        st.markdown('<div class="ln-empty">Nenhuma oportunidade encontrada. Remova um filtro para ampliar a descoberta.</div>', unsafe_allow_html=True)
        return
    per_page = 8
    total_pages = max((len(rows) + per_page - 1) // per_page, 1)
    current = min(max(int(st.session_state.mei_page), 1), total_pages)
    visible = rows[(current - 1) * per_page : current * per_page]
    controls = tuple(str(row.get("pncp_control_number") or "") for row in visible)
    with st.spinner("Carregando itens do PNCP..."):
        item_map = _items(controls)
    for row in visible:
        control = str(row.get("pncp_control_number") or "")
        pack = item_map.get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"})
        _render_list_card(row, pack)
    p1, p2, p3 = st.columns([1, 1, 3])
    if p1.button("◀ Anterior", disabled=current <= 1, width="stretch"):
        st.session_state.mei_page = current - 1
        st.rerun()
    if p2.button("Próxima ▶", disabled=current >= total_pages, width="stretch"):
        st.session_state.mei_page = current + 1
        st.rerun()
    p3.caption(f"Página {current} de {total_pages}")


def _location_page():
    st.markdown('<div class="ln-page-head"><div><h1>Explorar por localização</h1><p>Escolha uma região, um Estado ou uma cidade.</p></div></div>', unsafe_allow_html=True)
    region_counts = _region_counts()
    cols = st.columns(5)
    for index, region in enumerate(BRAZIL_REGIONS):
        with cols[index % 5]:
            st.metric(region, int(region_counts.get(region, 0)))
            if st.button("Explorar", key=f"region_{region}", width="stretch"):
                st.session_state.mei_filters = {"region": region, "states": [], "city": "", "modalities": [], "keyword": ""}
                st.session_state.mei_section = "🔎 Buscar editais"
                st.session_state.mei_page = 1
                st.rerun()
    st.divider()
    c1, c2 = st.columns([1, 2])
    state = c1.selectbox("Estado", ["Selecione"] + list(BRAZIL_STATES))
    city = c2.text_input("Cidade", placeholder="Ex.: Londrina")
    b1, b2 = st.columns(2)
    if b1.button("Ver oportunidades do Estado", disabled=state == "Selecione", width="stretch"):
        _set_state_and_search(state)
    if b2.button("Buscar cidade", type="primary", width="stretch"):
        if city.strip():
            st.session_state.mei_filters = {"region": "", "states": [], "city": city.strip(), "modalities": [], "keyword": ""}
            st.session_state.mei_section = "🔎 Buscar editais"
            st.session_state.mei_page = 1
            st.rerun()
        else:
            st.warning("Digite uma cidade para continuar.")


def _modality_page():
    st.markdown('<div class="ln-page-head"><div><h1>Explorar por modalidade</h1><p>Escolha como o órgão está contratando e veja as oportunidades abertas.</p></div></div>', unsafe_allow_html=True)
    options = list(MODALITIES.keys())
    cols = st.columns(2)
    for index, modality in enumerate(options):
        with cols[index % 2]:
            if st.button(str(modality), key=f"modality_{index}", width="stretch"):
                st.session_state.mei_filters = {"region": "", "states": [], "city": "", "modalities": [modality], "keyword": ""}
                st.session_state.mei_section = "🔎 Buscar editais"
                st.session_state.mei_page = 1
                st.rerun()


def _highlight_score(row):
    score = 0.0
    if str(row.get("portal") or "").strip() and str(row.get("portal") or "").strip().casefold() != "não identificado":
        score += 3
    if str(row.get("portal_access_tone") or "") == "free":
        score += 2
    try:
        value = float(row.get("estimated_value") or 0)
    except (TypeError, ValueError):
        value = 0
    if 0 < value <= 250000:
        score += 1.5
    return score


def _highlight_page():
    st.markdown('<div class="ln-page-head"><div><h1>Oportunidades em destaque</h1><p>Priorizamos oportunidades com informações mais completas para facilitar sua leitura.</p></div></div>', unsafe_allow_html=True)
    rows = _search("", tuple(), "", tuple(), "", 80)
    preselected = sorted(rows, key=_highlight_score, reverse=True)[:20]
    controls = tuple(str(row.get("pncp_control_number") or "") for row in preselected)
    item_map = _items(controls)
    ranked = []
    for row in preselected:
        control = str(row.get("pncp_control_number") or "")
        pack = item_map.get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"})
        score = _highlight_score(row) + (4 if int(pack.get("item_count") or 0) > 0 else 0)
        ranked.append((score, row, pack))
    for _, row, pack in sorted(ranked, key=lambda item: item[0], reverse=True)[:8]:
        _render_list_card(row, pack)


def _saved_page():
    st.markdown('<div class="ln-page-head"><div><h1>Oportunidades salvas</h1><p>Guarde o que chamou sua atenção para comparar depois.</p></div></div>', unsafe_allow_html=True)
    saved = list(st.session_state.mei_saved.values())
    if not saved:
        st.markdown('<div class="ln-empty">Você ainda não salvou nenhuma oportunidade.</div>', unsafe_allow_html=True)
        return
    controls = tuple(str(row.get("pncp_control_number") or "") for row in saved)
    item_map = _items(controls)
    for row in saved:
        control = str(row.get("pncp_control_number") or "")
        pack = item_map.get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"})
        _render_list_card(row, pack)


def _radar_page():
    st.markdown('<div class="ln-page-head"><div><h1>Radar</h1><p>Salve uma combinação de busca para voltar a ela rapidamente.</p></div></div>', unsafe_allow_html=True)
    filters = dict(st.session_state.mei_filters)
    st.caption(f"Busca atual: região {filters.get('region') or 'Brasil'} · estado {', '.join(filters.get('states') or []) or 'todos'} · cidade {filters.get('city') or 'todas'} · modalidade {', '.join(filters.get('modalities') or []) or 'todas'}")
    c1, c2 = st.columns([3, 1])
    name = c1.text_input("Nome do radar", placeholder="Ex.: oportunidades no Paraná")
    if c2.button("Salvar radar", type="primary", width="stretch"):
        st.session_state.mei_radars.append({"name": name.strip() or f"Radar {len(st.session_state.mei_radars) + 1}", "filters": filters})
        st.success("Radar salvo nesta sessão.")
    for index, radar in enumerate(st.session_state.mei_radars):
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{escape(radar['name'])}**")
            if right.button("Usar", key=f"use_radar_{index}", width="stretch"):
                st.session_state.mei_filters = dict(radar["filters"])
                st.session_state.mei_section = "🔎 Buscar editais"
                st.session_state.mei_page = 1
                st.rerun()
    st.caption("No preview, os radares ficam apenas nesta sessão. Alertas automáticos entram na etapa comercial.")


def main():
    st.markdown(CSS, unsafe_allow_html=True)
    _init_state()
    section = _sidebar()
    if section == "🏠 Início":
        _home_page()
    elif section == "🔎 Buscar editais":
        _search_page()
    elif section == "📍 Por localização":
        _location_page()
    elif section == "📋 Por modalidade":
        _modality_page()
    elif section == "🔥 Em destaque":
        _highlight_page()
    elif section == "⭐ Salvos":
        _saved_page()
    else:
        _radar_page()
