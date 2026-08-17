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


PROJECT_ROOT = Path(__file__).parent
LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo.png"
MEI_VERSION = "1.0 MEI Preview 1"
MEI_PRICE = "R$ 29,90/mês"

st.set_page_config(
    page_title="LicitaNexo MEI",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

db = Database(database_path(PROJECT_ROOT))
catalog = MeiCatalogService(db)


LIGHT_CSS = """
<style>
:root {
  --ln-navy:#0E2A47; --ln-blue:#2866E8; --ln-blue-dark:#1D53C7;
  --ln-green:#159C68; --ln-gold:#D6A126; --ln-red:#D24B4B;
  --ln-bg:#F5F7FB; --ln-card:#FFFFFF; --ln-line:#DFE6F0; --ln-muted:#66768A;
}
html, body, [data-testid="stAppViewContainer"], .stApp {
  background:var(--ln-bg) !important; color:var(--ln-navy) !important;
}
header[data-testid="stHeader"] {background:rgba(245,247,251,.94) !important;}
.block-container {max-width:1180px !important; padding-top:1.4rem !important;}
[data-testid="stSidebar"] {background:#FFFFFF !important; border-right:1px solid var(--ln-line) !important;}
[data-testid="stSidebar"] * {color:var(--ln-navy);}
[data-testid="stSidebar"] img {max-width:185px !important; margin:.5rem auto .1rem; display:block;}
h1,h2,h3,h4,p,label,span,div {color:inherit;}
.ln-hero {background:linear-gradient(135deg,#FFFFFF 0%,#F1F7FF 100%);border:1px solid #DCE7F5;border-radius:24px;padding:1.55rem 1.7rem;margin-bottom:1.1rem;box-shadow:0 12px 30px rgba(20,54,91,.06)}
.ln-kicker {display:inline-block;font-size:.76rem;font-weight:850;color:#116B49;background:#E8FAF2;border:1px solid #B9EBD6;border-radius:999px;padding:.32rem .65rem;margin-bottom:.65rem}
.ln-hero h1 {font-size:2rem;line-height:1.08;margin:.05rem 0 .45rem;color:var(--ln-navy)}
.ln-hero p {font-size:1.02rem;color:#53667D;margin:0;max-width:820px;line-height:1.55}
.ln-price {margin-top:.8rem;font-weight:850;color:#116B49;font-size:1.05rem}
.ln-card {background:#FFFFFF;border:1px solid var(--ln-line);border-radius:20px;padding:1.15rem 1.2rem 1.05rem;margin:.75rem 0;box-shadow:0 9px 24px rgba(17,45,78,.055)}
.ln-badge {display:inline-block;border-radius:999px;padding:.27rem .58rem;font-size:.72rem;font-weight:850;background:#E8FAF2;color:#106C49;border:1px solid #BDEBD8;margin-bottom:.45rem}
.ln-category {display:inline-block;border-radius:999px;padding:.25rem .55rem;font-size:.7rem;font-weight:800;background:#EEF4FF;color:#2D5DB4;border:1px solid #D7E4FB;margin-left:.35rem}
.ln-object {font-size:1.07rem;font-weight:820;line-height:1.38;color:#142E4C;margin:.15rem 0 .75rem}
.ln-meta-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.65rem 0}
.ln-meta {background:#F9FBFE;border:1px solid #E3EAF3;border-radius:14px;padding:.65rem .72rem;min-height:72px}
.ln-meta small {display:block;font-size:.67rem;color:#728197;font-weight:800;text-transform:uppercase;letter-spacing:.035em;margin-bottom:.22rem}
.ln-meta strong {font-size:.91rem;color:#173351;line-height:1.28;display:block;overflow-wrap:anywhere}
.ln-portal {display:flex;gap:.45rem;align-items:center;flex-wrap:wrap;background:#FAFBFD;border:1px solid #E2E8F0;border-radius:12px;padding:.55rem .7rem;margin:.68rem 0}
.ln-portal strong {color:#173351}.ln-free {color:#117C53;font-weight:850}.ln-paid {color:#A25C08;font-weight:850}.ln-unknown {color:#68788D;font-weight:800}
.ln-items {background:#F8FBFF;border:1px solid #DCE8F8;border-radius:15px;padding:.72rem .8rem;margin:.7rem 0}
.ln-items-title {font-weight:850;color:#173351;margin-bottom:.45rem}
.ln-item-row {display:grid;grid-template-columns:minmax(0,1fr) 115px 125px;gap:.55rem;padding:.4rem 0;border-bottom:1px solid #E6EDF6;align-items:start}
.ln-item-row:last-child {border-bottom:0}.ln-item-name {font-size:.88rem;color:#243D59;line-height:1.32}.ln-item-qty,.ln-item-price {font-size:.82rem;color:#4E6075;text-align:right}.ln-item-price {font-weight:820;color:#173351}
.ln-note {font-size:.79rem;color:#6C7C90;line-height:1.45}
.ln-empty {padding:2rem;text-align:center;background:#FFFFFF;border:1px dashed #CCD7E5;border-radius:18px;color:#68788D}
div.stButton > button, div.stDownloadButton > button, a[data-testid="stLinkButton"] {border-radius:11px !important;min-height:2.75rem !important;font-weight:800 !important}
div.stButton > button[kind="primary"] {background:var(--ln-blue) !important;border-color:var(--ln-blue) !important;color:#FFF !important}
[data-baseweb="input"] > div, [data-baseweb="select"] > div {background:#FFFFFF !important;color:#173351 !important;border-color:#CAD6E5 !important}
input, textarea {color:#173351 !important;-webkit-text-fill-color:#173351 !important;background:#FFFFFF !important}
[data-testid="stMetric"] {background:#FFFFFF;border:1px solid var(--ln-line);border-radius:14px;padding:.7rem .78rem}
[data-testid="stMetricLabel"] *, [data-testid="stMetricValue"] * {color:#173351 !important}
@media(max-width:800px){.ln-meta-grid{grid-template-columns:1fr 1fr}.ln-item-row{grid-template-columns:1fr}.ln-item-qty,.ln-item-price{text-align:left}.ln-hero h1{font-size:1.65rem}}
</style>
"""
st.markdown(LIGHT_CSS, unsafe_allow_html=True)


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


@st.cache_data(ttl=45, show_spinner=False)
def _search_cached(region, states, city, modalities, keyword, limit=160):
    return catalog.search(
        region=region,
        states=states,
        city=city,
        modalities=modalities,
        keyword=keyword,
        limit=limit,
    )


@st.cache_data(ttl=1800, show_spinner=False)
def _items_cached(controls):
    shells = [
        {"pncp_control_number": control, "category": "Outros"}
        for control in controls
        if control
    ]
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
def _price_history_cached(item_reference, catalog_code, description, state):
    return fetch_price_history_for_item({
        "source_reference": item_reference,
        "catalog_code": catalog_code,
        "description": description,
    }, state=state, months=18)


def _init_state():
    st.session_state.setdefault("mei_saved", {})
    st.session_state.setdefault("mei_radars", [])
    st.session_state.setdefault("mei_page", 1)
    st.session_state.setdefault("mei_open_opportunity", "")
    st.session_state.setdefault("mei_price_item", "")
    st.session_state.setdefault("mei_filters", {
        "region": "",
        "states": [],
        "city": "",
        "modalities": [],
        "keyword": "",
    })


def _sidebar():
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=180)
        st.caption("LicitaNexo MEI")
        st.markdown(f"**{MEI_PRICE}**")
        st.caption("Descubra o que o governo compra e quanto ele realmente paga.")
        st.divider()
        page = st.radio(
            "Navegação",
            ["🔎 Explorar licitações", "⭐ Minha lista", "🔔 Radar"],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(f"{MEI_VERSION} · B2G SaaS")
    return page


def _filter_panel():
    filters = dict(st.session_state.mei_filters)
    st.markdown(
        """<div class="ln-hero"><span class="ln-kicker">OPORTUNIDADES ABERTAS</span>
        <h1>Descubra o que o governo está comprando</h1>
        <p>Você não precisa escolher um nicho antes de começar. Navegue pelo Brasil, região, estado ou cidade e veja os produtos publicados nos editais.</p>
        <div class="ln-price">LicitaNexo MEI · R$ 29,90/mês no lançamento</div></div>""",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("### Onde você quer procurar?")
        c1, c2 = st.columns([1, 2])
        region_options = ["Brasil inteiro"] + list(BRAZIL_REGIONS)
        current_region = filters.get("region") or "Brasil inteiro"
        if current_region not in region_options:
            current_region = "Brasil inteiro"
        region = c1.selectbox(
            "Região",
            region_options,
            index=region_options.index(current_region),
            help="Deixe Brasil inteiro para explorar sem limitar a região.",
        )
        states = c2.multiselect(
            "Estados (opcional)",
            list(BRAZIL_STATES),
            default=filters.get("states") or [],
            placeholder="Vazio = todos os estados da região escolhida",
        )
        c3, c4 = st.columns(2)
        city = c3.text_input(
            "Cidade (opcional)",
            value=filters.get("city") or "",
            placeholder="Ex.: Londrina",
        )
        modalities = c4.multiselect(
            "Modalidade (opcional)",
            list(MODALITIES.keys()),
            default=filters.get("modalities") or [],
            placeholder="Todas as modalidades",
        )
        keyword = st.text_input(
            "Produto, serviço ou palavra-chave (opcional)",
            value=filters.get("keyword") or "",
            placeholder="Pode deixar em branco para descobrir oportunidades",
        )
        b1, b2 = st.columns([3, 1])
        submitted = b1.button("🔎 Ver oportunidades", type="primary", width="stretch")
        clear = b2.button("Limpar filtros", width="stretch")
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


def _render_items(item_pack, opportunity_id, state):
    items = item_pack.get("items") or []
    total = int(item_pack.get("item_count") or len(items))
    if not items:
        message = item_pack.get("items_error") or "O PNCP não publicou itens estruturados para esta contratação."
        st.markdown(f'<div class="ln-items"><div class="ln-items-title">📦 Produtos do edital</div><div class="ln-note">{escape(message)}</div></div>', unsafe_allow_html=True)
        return

    shown = items if st.session_state.mei_open_opportunity == opportunity_id else items[:4]
    lines = [f'<div class="ln-items"><div class="ln-items-title">📦 {total} produto(s)/item(ns) publicado(s) no PNCP</div>']
    for row in shown:
        description = escape(str(row.get("description") or "Item não descrito"))
        quantity = row.get("quantity")
        unit = escape(str(row.get("unit_measure") or ""))
        price = "Sigiloso" if row.get("confidential") else _money(row.get("unit_price"))
        try:
            qty_text = f"{float(quantity):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            qty_text = "—"
        lines.append(
            f'<div class="ln-item-row"><div class="ln-item-name">{description}</div>'
            f'<div class="ln-item-qty">{qty_text} {unit}</div><div class="ln-item-price">{escape(price)}</div></div>'
        )
    lines.append('</div>')
    st.markdown("".join(lines), unsafe_allow_html=True)

    if total > 4:
        label = "Mostrar menos produtos" if st.session_state.mei_open_opportunity == opportunity_id else f"Ver todos os {total} produtos"
        if st.button(label, key=f"mei_all_items_{opportunity_id}"):
            st.session_state.mei_open_opportunity = "" if st.session_state.mei_open_opportunity == opportunity_id else opportunity_id
            st.rerun()

    if st.session_state.mei_open_opportunity == opportunity_id:
        choices = [row for row in items if str(row.get("description") or "").strip()]
        if choices:
            selected = st.selectbox(
                "Escolha um produto para ver quanto o governo realmente pagou",
                range(len(choices)),
                format_func=lambda idx: str(choices[idx].get("description") or "")[:110],
                key=f"mei_item_select_{opportunity_id}",
            )
            item = choices[selected]
            ref = str(item.get("source_reference") or f"{opportunity_id}:{selected}")
            if st.button("💰 Ver preço real do governo", key=f"mei_price_btn_{opportunity_id}", type="primary"):
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


def _render_price_history(history):
    if not history.get("available"):
        st.info(history.get("reason") or "Histórico ainda não disponível para este produto.")
        return
    summary = history["summary"]
    st.markdown("#### 📊 Preços homologados encontrados")
    st.caption(
        f"Fonte oficial de preços: Compras.gov · código de catálogo {history.get('catalog_code')}. "
        "São compras anteriores encontradas para o mesmo código de catálogo; confirme especificações antes de comparar."
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Último preço", _money(summary.get("last_price")))
    c2.metric("Média", _money(summary.get("average")))
    c3.metric("Mediana", _money(summary.get("median")))
    c4.metric("Menor", _money(summary.get("minimum")))
    c5.metric("Maior", _money(summary.get("maximum")))
    st.caption(f"{summary.get('count', 0)} compra(s) homologada(s) considerada(s) nos últimos 18 meses.")

    left, right = st.columns(2)
    with left:
        st.markdown("**🏷️ Marcas encontradas**")
        brands = summary.get("brands") or []
        if brands:
            st.dataframe(pd.DataFrame([{"Marca": row["name"], "Ocorrências": row["count"]} for row in brands]), hide_index=True, width="stretch")
        else:
            st.caption("A marca não foi informada de forma confiável nas compras encontradas.")
    with right:
        st.markdown("**🏆 Fornecedores vencedores encontrados**")
        suppliers = summary.get("suppliers") or []
        if suppliers:
            st.dataframe(pd.DataFrame([{"Fornecedor": row["name"], "Ocorrências": row["count"]} for row in suppliers]), hide_index=True, width="stretch")
        else:
            st.caption("Fornecedor não disponível na amostra encontrada.")

    rows = summary.get("rows") or []
    if rows:
        st.markdown("**Compras recentes**")
        frame = pd.DataFrame([{
            "Data": str(row.get("published_at") or "")[:10],
            "Órgão": row.get("agency") or "",
            "Cidade/UF": "/".join(part for part in (str(row.get("city") or ""), str(row.get("state") or "")) if part),
            "Quantidade": row.get("quantity"),
            "Preço homologado": _money(row.get("homologated_unit_value")),
            "Marca": row.get("brand_normalized") or row.get("brand") or "Não informada",
            "Fornecedor": row.get("supplier") or "",
        } for row in rows[:12]])
        st.dataframe(frame, hide_index=True, width="stretch")


def _render_opportunity(row, item_pack):
    opportunity_id = str(row.get("id") or row.get("pncp_control_number") or "")
    modality = escape(str(row.get("modality") or "Modalidade não informada"))
    category = escape(str(item_pack.get("category") or row.get("category") or "Outros"))
    object_text = escape(str(row.get("object") or "Objeto não informado"))
    agency = escape(str(row.get("agency") or "Órgão não informado"))
    city = escape(str(row.get("city") or "Município não informado"))
    state = escape(str(row.get("state") or "--"))
    portal = escape(str(row.get("portal") or "Não identificado"))
    access = escape(str(row.get("portal_access") or "Verificar condições"))
    tone = str(row.get("portal_access_tone") or "unknown")
    tone_class = "ln-free" if tone == "free" else "ln-paid" if tone in {"paid", "conditional"} else "ln-unknown"

    st.markdown(
        f"""<div class="ln-card"><span class="ln-badge">{modality}</span><span class="ln-category">{category}</span>
        <div class="ln-object">{object_text}</div>
        <div class="ln-meta-grid">
          <div class="ln-meta"><small>Cidade</small><strong>{city} — {state}</strong></div>
          <div class="ln-meta"><small>Órgão</small><strong>{agency}</strong></div>
          <div class="ln-meta"><small>Valor estimado</small><strong>{escape(_money(row.get('estimated_value')))}</strong></div>
          <div class="ln-meta"><small>Fim das propostas</small><strong>{escape(_dt(row.get('closing_at')))}</strong></div>
        </div>
        <div class="ln-portal">🌐 <strong>Portal da disputa: {portal}</strong><span class="{tone_class}">● {access}</span></div>
        <div class="ln-note">Condição do portal verificada em {escape(str(row.get('portal_verified_at') or ''))}. Quando o custo depende de plano, modalidade ou êxito, o LicitaNexo informa isso em vez de chamar o portal simplesmente de gratuito.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    _render_items(item_pack, opportunity_id, str(row.get("state") or ""))

    a, b, c = st.columns([1.2, 1, 1])
    saved = opportunity_id in st.session_state.mei_saved
    if a.button("✓ Salvo" if saved else "⭐ Salvar na minha lista", key=f"mei_save_{opportunity_id}", disabled=saved, width="stretch"):
        st.session_state.mei_saved[opportunity_id] = dict(row)
        st.rerun()
    source_url = str(row.get("source_url") or "")
    pncp_url = str(row.get("pncp_url") or "")
    if source_url.startswith(("http://", "https://")):
        b.link_button("🌐 Abrir portal", source_url, width="stretch")
    if pncp_url.startswith(("http://", "https://")):
        c.link_button("📄 Ver no PNCP", pncp_url, width="stretch")
    st.divider()


def _explore_page():
    _filter_panel()
    filters = st.session_state.mei_filters
    with st.spinner("Organizando oportunidades abertas..."):
        rows = _search_cached(
            filters.get("region") or "",
            tuple(filters.get("states") or []),
            filters.get("city") or "",
            tuple(filters.get("modalities") or []),
            filters.get("keyword") or "",
            160,
        )
    st.markdown("### Oportunidades abertas")
    if not rows:
        st.markdown('<div class="ln-empty">Nenhuma oportunidade aberta foi encontrada com esses filtros. Limpe um dos campos para ampliar a busca.</div>', unsafe_allow_html=True)
        return

    st.caption(f"{len(rows)} oportunidade(s) encontradas nesta consulta. A palavra-chave é opcional: deixe vazia para descobrir novos nichos.")
    per_page = 8
    total_pages = max((len(rows) + per_page - 1) // per_page, 1)
    current = min(max(int(st.session_state.mei_page), 1), total_pages)
    start = (current - 1) * per_page
    visible = rows[start:start + per_page]
    controls = tuple(str(row.get("pncp_control_number") or "") for row in visible)
    with st.spinner("Buscando os produtos dos editais no PNCP..."):
        item_map = _items_cached(controls)

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


def _saved_page():
    st.markdown("## ⭐ Minha lista")
    st.caption("No preview, a lista fica nesta sessão do navegador. A persistência por conta será ligada junto da assinatura MEI, sem misturar dados com o LicitaNexo Pro.")
    saved = list(st.session_state.mei_saved.values())
    if not saved:
        st.markdown('<div class="ln-empty">Você ainda não salvou nenhuma oportunidade. Volte para Explorar licitações e use ⭐ Salvar na minha lista.</div>', unsafe_allow_html=True)
        return
    controls = tuple(str(row.get("pncp_control_number") or "") for row in saved)
    item_map = _items_cached(controls)
    for row in saved:
        control = str(row.get("pncp_control_number") or "")
        _render_opportunity(row, item_map.get(control, {"items": [], "item_count": 0, "items_error": "", "category": row.get("category") or "Outros"}))
        opportunity_id = str(row.get("id") or row.get("pncp_control_number") or "")
        if st.button("Remover da lista", key=f"mei_remove_{opportunity_id}"):
            st.session_state.mei_saved.pop(opportunity_id, None)
            st.rerun()


def _radar_page():
    st.markdown("## 🔔 Radar")
    st.caption("Salve combinações de região, estado, cidade, modalidade e palavra-chave. Nenhum nicho é obrigatório.")
    filters = dict(st.session_state.mei_filters)
    with st.container(border=True):
        st.write("**Busca atual**")
        st.write({
            "Região": filters.get("region") or "Brasil inteiro",
            "Estados": ", ".join(filters.get("states") or []) or "Todos",
            "Cidade": filters.get("city") or "Todas",
            "Modalidade": ", ".join(filters.get("modalities") or []) or "Todas",
            "Palavra-chave": filters.get("keyword") or "Nenhuma — modo descoberta",
        })
        name = st.text_input("Nome para este radar", placeholder="Ex.: oportunidades em Londrina")
        if st.button("🔔 Salvar este radar", type="primary"):
            st.session_state.mei_radars.append({"name": name.strip() or f"Radar {len(st.session_state.mei_radars)+1}", "filters": filters})
            st.success("Radar salvo nesta sessão.")
    if st.session_state.mei_radars:
        st.markdown("### Meus radares")
        for index, radar in enumerate(st.session_state.mei_radars):
            with st.container(border=True):
                st.write(f"**{radar['name']}**")
                st.caption(str(radar["filters"]))
                if st.button("Usar este radar", key=f"mei_use_radar_{index}"):
                    st.session_state.mei_filters = dict(radar["filters"])
                    st.session_state.mei_page = 1
                    st.rerun()
    st.info("A entrega automática de alertas por e-mail/WhatsApp será conectada quando ativarmos autenticação e cobrança do plano MEI. O motor de filtros já fica separado do LicitaNexo Pro.")


def main():
    _init_state()
    page = _sidebar()
    if page == "🔎 Explorar licitações":
        _explore_page()
    elif page == "⭐ Minha lista":
        _saved_page()
    else:
        _radar_page()


if __name__ == "__main__":
    main()
