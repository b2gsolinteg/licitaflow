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
MEI_VERSION = "1.0 MEI Preview 4"
MEI_PRICE = "R$ 29,90/mês"

db = Database(database_path(PROJECT_ROOT))
catalog = MeiCatalogService(db)


CSS = """
<style>
:root{
  --ln-navy:#102A43;
  --ln-navy-2:#173B5E;
  --ln-teal:#0F8F7B;
  --ln-teal-dark:#0B6F61;
  --ln-teal-soft:#E8F6F3;
  --ln-blue:#2D6CDF;
  --ln-gold:#D7A82F;
  --ln-bg:#F3F5F7;
  --ln-surface:#FFFFFF;
  --ln-surface-2:#F8FAFB;
  --ln-line:#E1E6EB;
  --ln-text:#172B3A;
  --ln-muted:#657786;
  --ln-green:#12805C;
  --ln-amber:#9A6700;
}

html,body,[data-testid="stAppViewContainer"],.stApp{
  background:var(--ln-bg)!important;
  color:var(--ln-text)!important;
}
header[data-testid="stHeader"]{
  background:rgba(243,245,247,.97)!important;
}
.block-container{
  max-width:1210px!important;
  padding-top:.4rem!important;
  padding-bottom:1.4rem!important;
}
h1,h2,h3,h4,p,label,span,div{font-family:inherit}

[data-testid="stSidebar"]{
  background:#FFFFFF!important;
  border-right:1px solid var(--ln-line)!important;
}
[data-testid="stSidebar"]>div:first-child{
  padding-top:.35rem!important;
}
[data-testid="stSidebar"] img{
  max-width:150px!important;
  display:block;
  margin:.35rem auto .15rem;
}
.ln-side-copy{
  color:#738493;
  font-size:.78rem;
  line-height:1.35;
  margin:.05rem .1rem .65rem;
}
.ln-side-group{
  color:#93A1AE;
  font-size:.65rem;
  font-weight:850;
  letter-spacing:.09em;
  text-transform:uppercase;
  margin:.48rem .1rem .18rem;
}
[data-testid="stSidebar"] div.stButton>button{
  justify-content:flex-start!important;
  text-align:left!important;
  min-height:2.2rem!important;
  padding:.4rem .6rem!important;
  border-radius:9px!important;
  font-size:.84rem!important;
  font-weight:700!important;
  box-shadow:none!important;
}
[data-testid="stSidebar"] div.stButton>button[kind="secondary"]{
  background:transparent!important;
  border:1px solid transparent!important;
  color:#27445E!important;
}
[data-testid="stSidebar"] div.stButton>button[kind="secondary"]:hover{
  background:#F6F8FA!important;
  border-color:#EDF0F3!important;
}
[data-testid="stSidebar"] div.stButton>button[kind="primary"]{
  background:var(--ln-teal-soft)!important;
  border:1px solid #C9E8E1!important;
  border-left:3px solid var(--ln-teal)!important;
  color:#123E39!important;
}
.ln-plan{
  background:#F7F8FA;
  border:1px solid var(--ln-line);
  border-radius:10px;
  padding:.6rem .68rem;
  margin:.75rem .1rem .4rem;
  color:#6C7C89;
  font-size:.73rem;
}
.ln-plan strong{
  display:block;
  color:var(--ln-navy);
  font-size:1rem;
  margin:.08rem 0 .12rem;
}

.ln-masthead{
  background:linear-gradient(100deg,var(--ln-navy) 0%,var(--ln-navy-2) 100%);
  border-radius:14px;
  padding:.82rem 1rem;
  margin:0 0 .55rem;
  box-shadow:0 5px 15px rgba(16,42,67,.08);
}
.ln-mast-kicker{
  display:inline-block;
  color:#BEEAE2;
  font-size:.64rem;
  font-weight:850;
  letter-spacing:.07em;
  text-transform:uppercase;
  margin-bottom:.12rem;
}
.ln-masthead h1{
  color:#fff;
  font-size:1.42rem;
  line-height:1.08;
  margin:.02rem 0 .14rem;
}
.ln-masthead p{
  color:#D9E4EC;
  font-size:.82rem;
  line-height:1.35;
  margin:0;
}

.ln-filter-head{
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:1rem;
  margin:0 0 .35rem;
}
.ln-filter-head strong{
  color:var(--ln-navy);
  font-size:.92rem;
}
.ln-filter-head span{
  color:#7B8A97;
  font-size:.73rem;
}
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--ln-surface)!important;
  border:1px solid var(--ln-line)!important;
  border-radius:13px!important;
  box-shadow:0 2px 8px rgba(17,34,51,.025)!important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div{
  padding-top:.68rem!important;
  padding-bottom:.68rem!important;
}
[data-baseweb="input"]>div,[data-baseweb="select"]>div{
  background:#FFFFFF!important;
  border-color:#CCD6DE!important;
  color:var(--ln-text)!important;
  min-height:2.35rem!important;
}
input,textarea{
  background:#FFFFFF!important;
  color:var(--ln-text)!important;
  -webkit-text-fill-color:var(--ln-text)!important;
}
[data-testid="stWidgetLabel"] p{
  color:#526575!important;
  font-size:.73rem!important;
  font-weight:760!important;
  margin-bottom:.03rem!important;
}

div.stButton>button,a[data-testid="stLinkButton"]{
  border-radius:8px!important;
  min-height:2.28rem!important;
  font-weight:780!important;
  box-shadow:none!important;
}
div.stButton>button[kind="primary"]{
  background:var(--ln-teal)!important;
  border-color:var(--ln-teal)!important;
  color:#FFFFFF!important;
}
div.stButton>button[kind="primary"]:hover{
  background:var(--ln-teal-dark)!important;
  border-color:var(--ln-teal-dark)!important;
}
a[data-testid="stLinkButton"]{
  color:#31526E!important;
}

.ln-results{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin:.75rem 0 .32rem;
}
.ln-results h3{
  color:var(--ln-navy);
  font-size:1.08rem;
  margin:0;
}
.ln-results span{
  color:#6F7F8C;
  font-size:.76rem;
}
.ln-results-note{
  color:#758592;
  font-size:.76rem;
  margin:-.12rem 0 .42rem;
}

.ln-op-head{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:.6rem;
  flex-wrap:wrap;
}
.ln-tags{
  display:flex;
  align-items:center;
  gap:.28rem;
  flex-wrap:wrap;
}
.ln-badge,.ln-cat,.ln-count,.ln-portal{
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  font-size:.63rem;
  font-weight:800;
}
.ln-badge{
  padding:.2rem .46rem;
  background:#EAF7F3;
  color:#0D765E;
  border:1px solid #CBE9E0;
}
.ln-cat{
  padding:.2rem .46rem;
  background:#EEF3FB;
  color:#365F9D;
  border:1px solid #D9E4F3;
}
.ln-count{
  padding:.2rem .46rem;
  background:#FFF6DF;
  color:#7A5A12;
  border:1px solid #EFDEA9;
}
.ln-portal{
  padding:.24rem .5rem;
  background:#F7F9FA;
  color:#455E73;
  border:1px solid #E2E7EB;
  gap:.28rem;
  white-space:nowrap;
}
.ln-free{color:#0E7B58;font-weight:850}
.ln-paid{color:#9A620B;font-weight:850}
.ln-unknown{color:#7A8792;font-weight:800}
.ln-object{
  color:#172F45;
  font-size:1rem;
  font-weight:820;
  line-height:1.3;
  margin:.32rem 0 .48rem;
}
.ln-meta-strip{
  display:grid;
  grid-template-columns:1fr 1.4fr .9fr 1fr;
  border-top:1px solid #EDF0F2;
  border-bottom:1px solid #EDF0F2;
  padding:.45rem 0;
  margin:.1rem 0 .5rem;
}
.ln-meta-cell{
  padding:.05rem .58rem;
  border-right:1px solid #EDF0F2;
}
.ln-meta-cell:first-child{padding-left:0}
.ln-meta-cell:last-child{border-right:0}
.ln-meta-cell small{
  display:block;
  color:#8A98A4;
  font-size:.57rem;
  font-weight:850;
  text-transform:uppercase;
  letter-spacing:.03em;
  margin-bottom:.05rem;
}
.ln-meta-cell strong{
  display:block;
  color:#27425A;
  font-size:.79rem;
  line-height:1.22;
  overflow-wrap:anywhere;
}

.ln-items-title{
  display:flex;
  align-items:center;
  justify-content:space-between;
  color:#25445F;
  font-size:.8rem;
  font-weight:850;
  margin:.18rem 0 .14rem;
}
.ln-items-title span{
  color:#8A98A4;
  font-size:.65rem;
  font-weight:700;
}
.ln-item-head,.ln-item-row{
  display:grid;
  grid-template-columns:minmax(0,1fr) 105px 105px;
  gap:.42rem;
  align-items:start;
}
.ln-item-head{
  color:#8B99A5;
  font-size:.56rem;
  text-transform:uppercase;
  font-weight:850;
  padding:.12rem 0 .17rem;
}
.ln-item-head div:nth-child(2),.ln-item-head div:nth-child(3){text-align:right}
.ln-item-row{
  border-top:1px solid #EEF1F3;
  padding:.3rem 0;
}
.ln-item-name{
  color:#385064;
  font-size:.77rem;
  line-height:1.25;
}
.ln-item-qty,.ln-item-price{
  color:#60717E;
  font-size:.74rem;
  text-align:right;
}
.ln-item-price{
  color:#203D55;
  font-weight:850;
}
.ln-price-note{
  background:#F4FAF8;
  border-left:3px solid #8FD1C3;
  border-radius:7px;
  padding:.38rem .5rem;
  margin:.18rem 0 .22rem;
  color:#60786F;
  font-size:.7rem;
}

[data-testid="stMetric"]{
  background:#F8FAFB;
  border:1px solid var(--ln-line);
  border-radius:9px;
  padding:.4rem .48rem;
}
[data-testid="stMetricLabel"] *,[data-testid="stMetricValue"] *{
  color:#27425A!important;
}

.ln-page-head{
  background:#FFFFFF;
  border:1px solid var(--ln-line);
  border-radius:12px;
  padding:.7rem .8rem;
  margin-bottom:.55rem;
}
.ln-page-head h2{
  color:var(--ln-navy);
  font-size:1.16rem;
  margin:0 0 .12rem;
}
.ln-page-head p{
  color:#70808D;
  font-size:.78rem;
  margin:0;
}
.ln-choice{
  background:#fff;
  border:1px solid var(--ln-line);
  border-radius:10px;
  padding:.48rem .56rem;
  margin-bottom:.24rem;
}
.ln-choice strong{
  color:#27425A;
  font-size:.84rem;
}
.ln-choice span{
  display:block;
  color:#8795A0;
  font-size:.68rem;
  margin-top:.04rem;
}
.ln-empty{
  background:#FFFFFF;
  border:1px dashed #CBD5DD;
  border-radius:11px;
  color:#74838F;
  padding:1rem;
  text-align:center;
}
.ln-radar{
  display:flex;
  flex-wrap:wrap;
  gap:.3rem;
  background:#fff;
  border:1px solid var(--ln-line);
  border-radius:10px;
  padding:.5rem .55rem;
  margin:.35rem 0 .5rem;
}
.ln-chip{
  background:#F3F6F8;
  border:1px solid #E2E7EB;
  border-radius:999px;
  color:#506576;
  font-size:.72rem;
  padding:.24rem .44rem;
}
.ln-chip b{color:#29465E}

[data-testid="stAlert"]{
  border-radius:9px!important;
  padding:.58rem .68rem!important;
}

@media(max-width:900px){
  .ln-meta-strip{grid-template-columns:1fr 1fr}
  .ln-meta-cell{border-right:0;border-bottom:1px solid #EDF0F2;padding:.35rem .2rem}
  .ln-meta-cell:nth-last-child(-n+2){border-bottom:0}
}
@media(max-width:800px){
  .block-container{padding-left:.65rem!important;padding-right:.65rem!important}
  .ln-item-head{display:none}
  .ln-item-row{grid-template-columns:1fr}
  .ln-item-qty,.ln-item-price{text-align:left}
  .ln-masthead h1{font-size:1.25rem}
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
        {
            "source_reference": item_reference,
            "catalog_code": catalog_code,
            "description": description,
        },
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
        "mei_filters": {
            "region": "",
            "states": [],
            "city": "",
            "modalities": [],
            "keyword": "",
        },
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _sidebar():
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=150)
        st.markdown(
            '<div class="ln-side-copy">Licitações para quem quer descobrir oportunidades sem complicação.</div>',
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

        st.markdown('<div class="ln-side-group">Explorar</div>', unsafe_allow_html=True)
        for i, label in enumerate(explore):
            if st.button(
                label,
                key=f"nav_e_{i}",
                type="primary" if current == label else "secondary",
                width="stretch",
            ):
                st.session_state.mei_section = label
                st.rerun()

        st.markdown('<div class="ln-side-group">Minha área</div>', unsafe_allow_html=True)
        for i, label in enumerate(personal):
            if st.button(
                label,
                key=f"nav_p_{i}",
                type="primary" if current == label else "secondary",
                width="stretch",
            ):
                st.session_state.mei_section = label
                st.rerun()

        st.markdown(
            '<div class="ln-plan">LicitaNexo MEI'
            '<strong>R&#36; 29,90/mês</strong>'
            '<span>Descubra oportunidades e preços praticados pelo governo.</span></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"{MEI_VERSION} · B2G SaaS")
    return current


def _filter_panel():
    filters = dict(st.session_state.mei_filters)
    st.markdown(
        '<div class="ln-masthead">'
        '<span class="ln-mast-kicker">LICITANEXO MEI</span>'
        '<h1>Descubra o que o governo está comprando</h1>'
        '<p>Navegue sem definir um nicho. Quando algo chamar sua atenção, veja os itens e os preços já praticados.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            '<div class="ln-filter-head"><strong>Encontre oportunidades</strong>'
            '<span>Todos os campos são opcionais</span></div>',
            unsafe_allow_html=True,
        )
        regions = ["Brasil inteiro"] + list(BRAZIL_REGIONS)
        current_region = filters.get("region") or "Brasil inteiro"
        if current_region not in regions:
            current_region = "Brasil inteiro"

        c1, c2, c3, c4 = st.columns([1, 1.15, 1.2, 1.2])
        region = c1.selectbox(
            "Região",
            regions,
            index=regions.index(current_region),
        )
        states = c2.multiselect(
            "Estado",
            list(BRAZIL_STATES),
            default=filters.get("states") or [],
            placeholder="Todos",
        )
        city = c3.text_input(
            "Cidade",
            value=filters.get("city") or "",
            placeholder="Ex.: Londrina",
        )
        modalities = c4.multiselect(
            "Modalidade",
            list(MODALITIES.keys()),
            default=filters.get("modalities") or [],
            placeholder="Todas",
        )

        k1, k2, k3 = st.columns([3.6, 1.25, .8])
        keyword = k1.text_input(
            "Produto, serviço ou palavra-chave",
            value=filters.get("keyword") or "",
            placeholder="Opcional — ex.: papel, café, uniforme, manutenção",
        )
        search_clicked = k2.button(
            "🔎 Buscar",
            type="primary",
            width="stretch",
        )
        clear_clicked = k3.button(
            "Limpar",
            width="stretch",
        )

        if search_clicked:
            st.session_state.mei_filters = {
                "region": "" if region == "Brasil inteiro" else region,
                "states": list(states),
                "city": city.strip(),
                "modalities": list(modalities),
                "keyword": keyword.strip(),
            }
            st.session_state.mei_page = 1
            st.rerun()
        if clear_clicked:
            st.session_state.mei_filters = {
                "region": "",
                "states": [],
                "city": "",
                "modalities": [],
                "keyword": "",
            }
            st.session_state.mei_page = 1
            st.rerun()


def _render_price_history(history):
    if not history.get("available"):
        st.info(history.get("reason") or "Histórico ainda não disponível para este produto.")
        return

    summary = history["summary"]
    st.markdown("#### 📊 Histórico de preços públicos")
    st.caption(
        f"Fonte: Compras.gov · código de catálogo {history.get('catalog_code')}. "
        "Compare especificações antes de tratar produtos como equivalentes."
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Último", _money(summary.get("last_price")))
    c2.metric("Média", _money(summary.get("average")))
    c3.metric("Mediana", _money(summary.get("median")))
    c4.metric("Menor", _money(summary.get("minimum")))
    c5.metric("Maior", _money(summary.get("maximum")))

    st.caption(
        f"{summary.get('count', 0)} compra(s) homologada(s) considerada(s) nos últimos 18 meses."
    )

    left, right = st.columns(2)
    brands = summary.get("brands") or []
    suppliers = summary.get("suppliers") or []

    with left:
        st.markdown("**🏷️ Marcas encontradas**")
        if brands:
            st.dataframe(
                pd.DataFrame(
                    [{"Marca": x["name"], "Ocorrências": x["count"]} for x in brands]
                ),
                hide_index=True,
                width="stretch",
            )
        else:
            st.caption("Marca não informada de forma confiável na amostra.")

    with right:
        st.markdown("**🏆 Fornecedores vencedores**")
        if suppliers:
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Fornecedor": x["name"], "Ocorrências": x["count"]}
                        for x in suppliers
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
        else:
            st.caption("Fornecedor não disponível na amostra.")

    rows = summary.get("rows") or []
    if rows:
        frame = pd.DataFrame(
            [
                {
                    "Data": str(x.get("published_at") or "")[:10],
                    "Órgão": x.get("agency") or "",
                    "Cidade/UF": "/".join(
                        p
                        for p in (
                            str(x.get("city") or ""),
                            str(x.get("state") or ""),
                        )
                        if p
                    ),
                    "Qtd.": x.get("quantity"),
                    "Preço homologado": _money(x.get("homologated_unit_value")),
                    "Marca": x.get("brand_normalized")
                    or x.get("brand")
                    or "Não informada",
                    "Fornecedor": x.get("supplier") or "",
                }
                for x in rows[:12]
            ]
        )
        st.markdown("**Compras recentes**")
        st.dataframe(frame, hide_index=True, width="stretch")


def _render_items(pack, opportunity_id, state):
    items = pack.get("items") or []
    total = int(pack.get("item_count") or len(items))

    if not items:
        msg = (
            pack.get("items_error")
            or "O PNCP não publicou itens estruturados para esta contratação."
        )
        st.markdown(
            '<div class="ln-items-title"><b>📦 Produtos do edital</b>'
            '<span>dados do PNCP</span></div>'
            f'<div class="ln-price-note">{escape(msg)}</div>',
            unsafe_allow_html=True,
        )
        return

    expanded = st.session_state.mei_open_opportunity == opportunity_id
    shown = items if expanded else items[:3]

    lines = [
        f'<div class="ln-items-title"><b>📦 Produtos do edital · {total} item(ns)</b>'
        '<span>fonte PNCP</span></div>',
        '<div class="ln-item-head"><div>Produto / serviço</div>'
        '<div>Quantidade</div><div>Preço estimado</div></div>',
    ]

    for row in shown:
        desc = escape(
            _short(
                row.get("description") or "Item não descrito",
                300 if expanded else 185,
            )
        )
        try:
            qty = (
                f"{float(row.get('quantity')):,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except (TypeError, ValueError):
            qty = "—"
        unit = escape(str(row.get("unit_measure") or ""))
        price = (
            "Sigiloso"
            if row.get("confidential")
            else _html_money(row.get("unit_price"))
        )
        lines.append(
            f'<div class="ln-item-row"><div class="ln-item-name">{desc}</div>'
            f'<div class="ln-item-qty">{qty} {unit}</div>'
            f'<div class="ln-item-price">{price}</div></div>'
        )

    st.markdown("".join(lines), unsafe_allow_html=True)

    actions = st.columns([1.15, 2.25])
    if total > 3:
        label = "Mostrar menos" if expanded else f"Ver todos os {total} itens"
        if actions[0].button(
            label,
            key=f"all_{opportunity_id}",
            width="stretch",
        ):
            st.session_state.mei_open_opportunity = (
                "" if expanded else opportunity_id
            )
            st.rerun()
    else:
        actions[0].caption("Todos os itens visíveis")

    if actions[1].button(
        "💰 Ver histórico de preços",
        key=f"prices_{opportunity_id}",
        type="primary",
        width="stretch",
    ):
        st.session_state.mei_open_opportunity = opportunity_id
        st.rerun()

    st.markdown(
        '<div class="ln-price-note">Consulte quanto o governo já pagou, além de marcas e fornecedores quando publicados nas fontes oficiais.</div>',
        unsafe_allow_html=True,
    )

    if expanded:
        choices = [
            x for x in items if str(x.get("description") or "").strip()
        ]
        if choices:
            selector, consult = st.columns([4, 1])
            selected = selector.selectbox(
                "Escolha o produto",
                range(len(choices)),
                format_func=lambda i: _short(
                    choices[i].get("description") or "",
                    105,
                ),
                key=f"sel_{opportunity_id}",
            )
            item = choices[selected]
            ref = str(
                item.get("source_reference")
                or f"{opportunity_id}:{selected}"
            )
            if consult.button(
                "Consultar",
                key=f"hist_{opportunity_id}",
                width="stretch",
            ):
                st.session_state.mei_price_item = ref
                st.rerun()

            if st.session_state.mei_price_item == ref:
                with st.spinner(
                    "Consultando compras homologadas no Compras.gov..."
                ):
                    history = _history(
                        ref,
                        str(item.get("catalog_code") or ""),
                        str(item.get("description") or ""),
                        state,
                    )
                _render_price_history(history)


def _render_opportunity(row, pack):
    oid = str(row.get("id") or row.get("pncp_control_number") or "")
    modality = escape(
        str(row.get("modality") or "Modalidade não informada")
    )
    category = escape(
        str(pack.get("category") or row.get("category") or "Outros")
    )
    obj = escape(_short(row.get("object") or "Objeto não informado", 290))
    agency = escape(str(row.get("agency") or "Órgão não informado"))
    city = escape(str(row.get("city") or "Município não informado"))
    state = escape(str(row.get("state") or "--"))
    portal = escape(str(row.get("portal") or "Não identificado"))
    access = escape(
        str(row.get("portal_access") or "Verificar condições")
    )
    tone = str(row.get("portal_access_tone") or "unknown")
    tone_class = (
        "ln-free"
        if tone == "free"
        else "ln-paid"
        if tone in {"paid", "conditional"}
        else "ln-unknown"
    )
    total = int(pack.get("item_count") or len(pack.get("items") or []))

    with st.container(border=True):
        st.markdown(
            f'<div class="ln-op-head">'
            f'<div class="ln-tags">'
            f'<span class="ln-badge">{modality}</span>'
            f'<span class="ln-cat">{category}</span>'
            f'<span class="ln-count">📦 {total} item(ns)</span>'
            f'</div>'
            f'<span class="ln-portal">🌐 {portal} '
            f'<span class="{tone_class}">● {access}</span></span>'
            f'</div>'
            f'<div class="ln-object">{obj}</div>'
            f'<div class="ln-meta-strip">'
            f'<div class="ln-meta-cell"><small>Cidade</small>'
            f'<strong>{city} — {state}</strong></div>'
            f'<div class="ln-meta-cell"><small>Órgão</small>'
            f'<strong>{agency}</strong></div>'
            f'<div class="ln-meta-cell"><small>Valor estimado</small>'
            f'<strong>{_html_money(row.get("estimated_value"))}</strong></div>'
            f'<div class="ln-meta-cell"><small>Fim das propostas</small>'
            f'<strong>{escape(_dt(row.get("closing_at")))}</strong></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        _render_items(
            pack,
            oid,
            str(row.get("state") or ""),
        )

        a, b, c = st.columns([1.15, 1, 1])
        saved = oid in st.session_state.mei_saved
        if a.button(
            "✓ Salvo" if saved else "⭐ Salvar",
            key=f"save_{oid}",
            disabled=saved,
            width="stretch",
        ):
            st.session_state.mei_saved[oid] = dict(row)
            st.rerun()

        source_url = str(row.get("source_url") or "")
        pncp_url = str(row.get("pncp_url") or "")
        if source_url.startswith(("http://", "https://")):
            b.link_button(
                "🌐 Portal da disputa",
                source_url,
                width="stretch",
            )
        if pncp_url.startswith(("http://", "https://")):
            c.link_button(
                "📄 Ver no PNCP",
                pncp_url,
                width="stretch",
            )


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

    st.markdown(
        f'<div class="ln-results"><h3>Oportunidades abertas</h3>'
        f'<span>{len(rows)} encontrada(s)</span></div>'
        '<div class="ln-results-note">Comece olhando os itens. '
        'Os filtros servem apenas para reduzir a lista quando você quiser.</div>',
        unsafe_allow_html=True,
    )

    if not rows:
        st.markdown(
            '<div class="ln-empty">Nenhuma oportunidade encontrada. '
            'Amplie os filtros para continuar explorando.</div>',
            unsafe_allow_html=True,
        )
        return

    per_page = 10
    total_pages = max((len(rows) + per_page - 1) // per_page, 1)
    current = min(
        max(int(st.session_state.mei_page), 1),
        total_pages,
    )
    visible = rows[(current - 1) * per_page : current * per_page]
    controls = tuple(
        str(x.get("pncp_control_number") or "")
        for x in visible
    )

    with st.spinner("Buscando os produtos dos editais no PNCP..."):
        item_map = _items(controls)

    for row in visible:
        control = str(row.get("pncp_control_number") or "")
        pack = item_map.get(
            control,
            {
                "items": [],
                "item_count": 0,
                "items_error": "",
                "category": row.get("category") or "Outros",
            },
        )
        _render_opportunity(row, pack)

    p1, p2, p3 = st.columns([1, 1, 2])
    if p1.button(
        "◀ Anterior",
        disabled=current <= 1,
        width="stretch",
    ):
        st.session_state.mei_page = current - 1
        st.rerun()
    if p2.button(
        "Próxima ▶",
        disabled=current >= total_pages,
        width="stretch",
    ):
        st.session_state.mei_page = current + 1
        st.rerun()
    p3.caption(f"Página {current} de {total_pages}")


def _apply_discovery(
    *,
    region="",
    states=None,
    city="",
    modalities=None,
    keyword="",
):
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


def _page_head(title, copy):
    st.markdown(
        f'<div class="ln-page-head"><h2>{escape(title)}</h2>'
        f'<p>{escape(copy)}</p></div>',
        unsafe_allow_html=True,
    )


def _region_page():
    _page_head(
        "🗺️ Explore por região",
        "Entre por uma região e veja as oportunidades abertas sem precisar escolher um produto.",
    )
    counts = _region_counts()
    cols = st.columns(3)
    for i, region in enumerate(BRAZIL_REGIONS):
        with cols[i % 3]:
            total = int(counts.get(region, 0))
            st.markdown(
                f'<div class="ln-choice"><strong>{escape(region)}</strong>'
                f'<span>{total} oportunidade(s) aberta(s)</span></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "Ver oportunidades",
                key=f"region_{region}",
                width="stretch",
            ):
                _apply_discovery(region=region)


def _state_page():
    _page_head(
        "📍 Explore por estado",
        "Veja primeiro onde existem mais oportunidades abertas e escolha uma UF.",
    )
    counts = _state_counts()
    states = sorted(
        BRAZIL_STATES,
        key=lambda x: (-int(counts.get(x, 0)), x),
    )
    cols = st.columns(4)
    for i, state in enumerate(states):
        with cols[i % 4]:
            if st.button(
                f"{state} · {int(counts.get(state, 0))}",
                key=f"state_{state}",
                width="stretch",
            ):
                _apply_discovery(states=[state])


def _city_page():
    _page_head(
        "🏙️ Explore por cidade",
        "Digite a cidade onde você quer descobrir compras públicas abertas.",
    )
    c1, c2 = st.columns([4, 1])
    city = c1.text_input(
        "Cidade",
        placeholder="Ex.: Londrina, João Pessoa, Sao Jose",
    )
    if c2.button(
        "Buscar",
        type="primary",
        width="stretch",
    ):
        if city.strip():
            _apply_discovery(city=city.strip())
        else:
            st.warning("Digite uma cidade para continuar.")


def _modality_page():
    _page_head(
        "📋 Explore por modalidade",
        "Escolha o tipo de contratação para descobrir oportunidades abertas.",
    )
    options = list(MODALITIES.keys())
    cols = st.columns(2)
    for i, modality in enumerate(options):
        with cols[i % 2]:
            if st.button(
                str(modality),
                key=f"mod_{i}",
                width="stretch",
            ):
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
            parsed = datetime.fromisoformat(
                str(closing).replace("Z", "+00:00")
            )
            now = (
                datetime.now(parsed.tzinfo)
                if parsed.tzinfo
                else datetime.now()
            )
            hours = (parsed - now).total_seconds() / 3600
            if 24 <= hours <= 240:
                score += 2
            elif 8 <= hours < 24:
                score += .5
        except (TypeError, ValueError):
            pass
    return score


def _highlight_page():
    _page_head(
        "🔥 Oportunidades em destaque",
        "Priorizamos oportunidades com dados mais completos, itens publicados e prazo útil. Não é recomendação automática de participação.",
    )
    rows = _search("", tuple(), "", tuple(), "", 80)
    pre = sorted(
        rows,
        key=_highlight_score,
        reverse=True,
    )[:24]
    controls = tuple(
        str(x.get("pncp_control_number") or "")
        for x in pre
    )
    with st.spinner("Organizando os destaques..."):
        item_map = _items(controls)

    ranked = []
    for row in pre:
        control = str(row.get("pncp_control_number") or "")
        pack = item_map.get(
            control,
            {
                "items": [],
                "item_count": 0,
                "items_error": "",
                "category": row.get("category") or "Outros",
            },
        )
        score = _highlight_score(row)
        if int(pack.get("item_count") or 0) > 0:
            score += 4
        if str(pack.get("category") or "Outros") != "Outros":
            score += 1
        ranked.append((score, row, pack))

    for _, row, pack in sorted(
        ranked,
        key=lambda x: x[0],
        reverse=True,
    )[:10]:
        _render_opportunity(row, pack)


def _saved_page():
    _page_head(
        "⭐ Minha lista",
        "Guarde oportunidades para comparar depois.",
    )
    saved = list(st.session_state.mei_saved.values())
    if not saved:
        st.markdown(
            '<div class="ln-empty">Você ainda não salvou nenhuma oportunidade.</div>',
            unsafe_allow_html=True,
        )
        return

    controls = tuple(
        str(x.get("pncp_control_number") or "")
        for x in saved
    )
    item_map = _items(controls)

    for row in saved:
        control = str(row.get("pncp_control_number") or "")
        _render_opportunity(
            row,
            item_map.get(
                control,
                {
                    "items": [],
                    "item_count": 0,
                    "items_error": "",
                    "category": row.get("category") or "Outros",
                },
            ),
        )
        oid = str(
            row.get("id")
            or row.get("pncp_control_number")
            or ""
        )
        if st.button(
            "Remover da lista",
            key=f"remove_{oid}",
        ):
            st.session_state.mei_saved.pop(oid, None)
            st.rerun()


def _radar_page():
    _page_head(
        "🔔 Radar",
        "Salve uma combinação de busca para reutilizar depois.",
    )
    filters = dict(st.session_state.mei_filters)
    chips = [
        ("Região", filters.get("region") or "Brasil inteiro"),
        ("Estado", ", ".join(filters.get("states") or []) or "Todos"),
        ("Cidade", filters.get("city") or "Todas"),
        (
            "Modalidade",
            ", ".join(filters.get("modalities") or []) or "Todas",
        ),
        (
            "Palavra",
            filters.get("keyword") or "Modo descoberta",
        ),
    ]
    html = "".join(
        f'<span class="ln-chip"><b>{escape(k)}:</b> '
        f'{escape(str(v))}</span>'
        for k, v in chips
    )
    st.markdown(
        f'<div class="ln-radar">{html}</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([3, 1])
    name = c1.text_input(
        "Nome do radar",
        placeholder="Ex.: oportunidades em Londrina",
    )
    if c2.button(
        "🔔 Salvar radar",
        type="primary",
        width="stretch",
    ):
        st.session_state.mei_radars.append(
            {
                "name": name.strip()
                or f"Radar {len(st.session_state.mei_radars) + 1}",
                "filters": filters,
            }
        )
        st.success("Radar salvo nesta sessão.")

    for i, radar in enumerate(st.session_state.mei_radars):
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{escape(radar['name'])}**")
            if right.button(
                "Usar",
                key=f"use_radar_{i}",
                width="stretch",
            ):
                st.session_state.mei_filters = dict(
                    radar["filters"]
                )
                st.session_state.mei_section = (
                    "🔎 Todas as oportunidades"
                )
                st.session_state.mei_page = 1
                st.rerun()

    st.caption(
        "Alertas automáticos entram na etapa comercial; neste preview o Radar salva a busca na sessão."
    )


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
