from __future__ import annotations

from datetime import date, datetime, time
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from .formatters import format_brl, parse_brl
from .pncp import MODALITIES
from .pncp_items import PncpItemsError, fetch_contract_items
from .radar_items import fetch_radar_item_summaries
from .sources import PORTAL_ACCESS, opportunity_source_and_portal, pncp_official_url, portal_access_info


BRAZIL_STATES = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
)

STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}
FLAGS_DIR = Path(__file__).resolve().parents[1] / "assets" / "state_flags"
PORTAL_OPTIONS = ("Todos os sites", *PORTAL_ACCESS.keys())
PORTAL_SEARCH_TERMS = {
    "Compras.gov": ("compras.gov", "comprasnet", "siasg", "gov.br/compras"),
    "BLL Compras": ("bll",),
    "BNC Compras": ("bnc", "bolsa nacional de compras"),
    "BBMNET": ("bbmnet", "bolsa brasileira de mercadorias"),
    "LicitaNET": ("licitanet",),
    "M2A Compras": ("m2a",),
    "Portal de Compras Públicas": ("portal de compras publicas", "portal de compras públicas"),
    "Licitações-e / Banco do Brasil": ("banco do brasil", "licitacoes-e", "licitações-e"),
    "BEC-SP": ("bec-sp", "bec.sp.gov.br", "bolsa eletronica de compras", "bolsa eletrônica de compras"),
}


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#FFFFFF !important;}
        [data-testid="stMain"] .block-container{max-width:1180px !important;padding-top:1.15rem !important;}
        [data-testid="stMain"] *{font-weight:400 !important;}
        [data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3,
        [data-testid="stMain"] p,[data-testid="stMain"] label p,[data-testid="stMain"] .stCaption p{color:#293746 !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{background:#FFFFFF !important;border-color:#DCE3E8 !important;box-shadow:none !important;}
        .ln-discovery-title{font-size:1.95rem;font-weight:400 !important;letter-spacing:-.015em;margin:.05rem 0 .2rem;color:#293746}
        .ln-discovery-sub{color:#667786;font-size:.96rem;margin:0 0 1rem}
        .ln-modality-badge{display:inline-block;background:#F2F5F7;color:#526371;border:1px solid #DCE3E8;border-radius:999px;padding:.2rem .6rem;font-size:.72rem;text-transform:uppercase;letter-spacing:.02em}
        .ln-reference{font-size:1.05rem;color:#293746;margin:.42rem 0 .7rem}
        .ln-info-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem;margin:.15rem 0 .8rem}
        .ln-info-box,.ln-meta-box{background:#FFFFFF;border:1px solid #DCE3E8;border-radius:12px;padding:.72rem .76rem;min-height:82px}
        .ln-info-label,.ln-meta-label{font-size:.69rem;color:#71808D;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.30rem}
        .ln-info-value,.ln-meta-value{color:#293746;font-size:.9rem;line-height:1.28}
        .ln-info-extra,.ln-meta-help{color:#71808D;font-size:.70rem;margin-top:.32rem;line-height:1.32}
        .ln-object-label{font-size:.72rem;color:#667786;text-transform:uppercase;margin:.3rem 0 .18rem}
        .ln-meta-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.55rem;margin:.65rem 0}
        .ln-meta-link{color:#3F7076;text-decoration:none;border-bottom:1px solid #B8CDD0}
        .ln-items-box{background:#FFFFFF;border:1px solid #DCE3E8;border-radius:12px;padding:.72rem .78rem;margin:.65rem 0}
        .ln-items-title{color:#293746;font-size:.88rem;margin-bottom:.4rem}
        .ln-item-row{display:grid;grid-template-columns:48px minmax(0,1fr) 130px 132px;gap:.5rem;align-items:start;padding:.42rem .08rem;border-top:1px solid #EDF1F4;color:#344452}
        .ln-item-row:first-of-type{border-top:0}
        .ln-item-number,.ln-item-qty,.ln-item-price{font-size:.74rem;line-height:1.32;color:#667786}
        .ln-item-desc{font-size:.78rem;line-height:1.32}
        .ln-item-qty,.ln-item-price{text-align:right}
        .ln-items-note{font-size:.72rem;color:#71808D;margin-top:.35rem}
        [data-testid="stMain"] .stButton button,[data-testid="stMain"] .stDownloadButton button{background:#FFFFFF !important;color:#293746 !important;border:1px solid #CCD6DD !important;box-shadow:none !important;}
        [data-testid="stMain"] .stButton button[kind="primary"],[data-testid="stMain"] button[kind="primary"]{background:#EAF2F3 !important;color:#293746 !important;border:1px solid #ADC6C9 !important;box-shadow:none !important;}
        [data-testid="stMain"] .stButton button:hover{background:#F4F7F8 !important;border-color:#AFC0C9 !important;}
        [data-testid="stMain"] div[class*="st-key-state_"] button{min-height:2.8rem !important;font-size:.88rem !important;background:#FFFFFF !important;color:#293746 !important;border:1px solid #CCD6DD !important;}
        .ln-state-card{min-height:154px;}
.ln-home-count{font-size:1.55rem;color:#293746;margin:.25rem 0 .95rem;}
[data-testid="stSidebar"] .stButton button{font-weight:600 !important;}
        @media(max-width:900px){.ln-info-grid,.ln-meta-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.ln-item-row{grid-template-columns:38px minmax(0,1fr)}.ln-item-qty,.ln-item-price{text-align:left;grid-column:2}}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=600, show_spinner=False)
def _cached_item_summaries(control_numbers: tuple[str, ...]) -> dict[str, dict]:
    return fetch_radar_item_summaries(
        control_numbers,
        max_workers=4,
        preview_items=20,
    )


@st.cache_data(ttl=1800, show_spinner=False)
def _cached_full_items(control_number: str) -> list[dict]:
    control = str(control_number or "").strip()
    if not control:
        return []
    return fetch_contract_items(control, timeout=12, page_size=200)


def _now_local() -> datetime:
    try:
        return datetime.now(ZoneInfo("America/Sao_Paulo"))
    except Exception:
        return datetime.now()


def _datetime_text(value) -> str:
    if not value:
        return "Não informada"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(ZoneInfo("America/Sao_Paulo"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return str(value).replace("T", " ")[:16]


def _countdown(value) -> str:
    if not value:
        return ""
    try:
        target = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        now = _now_local()
        if target.tzinfo is None and now.tzinfo is not None:
            target = target.replace(tzinfo=now.tzinfo)
        elif target.tzinfo is not None and now.tzinfo is not None:
            target = target.astimezone(now.tzinfo)
        seconds = int((target - now).total_seconds())
    except (TypeError, ValueError):
        return ""
    if seconds <= 0:
        return "Prazo encerrado"
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"Faltam {days}d {hours}h"
    if hours:
        return f"Faltam {hours}h {minutes}min"
    return f"Faltam {minutes}min"


def _quantity_text(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return "—"
    if number.is_integer():
        return f"{int(number):,}".replace(",", ".")
    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _item_price_text(row: dict) -> str:
    if row.get("confidential"):
        return "Sigiloso"
    try:
        price = float(row.get("unit_price") or 0)
    except (TypeError, ValueError):
        price = 0.0
    return format_brl(price) if price > 0 else "Não publicado"


def _criteria(**updates) -> dict:
    base = {
        "keyword": "",
        "city": "",
        "states": [],
        "modalities": [],
        "minimum": None,
        "maximum": None,
        "closing_from": date.today().isoformat(),
        "closing_to": None,
        "order": "recent",
        "portal": "Todos os sites",
    }
    base.update(updates)
    return base


def _profile_defaults(db, company_id: str) -> dict:
    profile = db.get_company_profile(company_id) or {}
    states = [
        x.strip().upper()
        for x in str(profile.get("service_states") or "").replace(";", ",").split(",")
        if x.strip().upper() in BRAZIL_STATES
    ]
    modalities = [
        x.strip() for x in str(profile.get("search_modalities") or "").split("|")
        if x.strip() in MODALITIES
    ]
    return {
        "keyword": str(profile.get("search_keyword") or ""),
        "states": states,
        "modalities": modalities,
        "minimum": profile.get("search_minimum"),
        "maximum": profile.get("search_maximum"),
    }


def _query_catalog(db, criteria: dict, *, limit: int = 10000) -> list[dict]:
    cities = [str(criteria.get("city") or "").strip()] if str(criteria.get("city") or "").strip() else []
    portal = str(criteria.get("portal") or "Todos os sites")
    return db.list_global_catalog(
        search=str(criteria.get("keyword") or "").strip(),
        states=list(criteria.get("states") or []),
        cities=cities,
        modalities=list(criteria.get("modalities") or []),
        minimum=criteria.get("minimum"),
        maximum=criteria.get("maximum"),
        closing_from=criteria.get("closing_from") or date.today().isoformat(),
        closing_to=criteria.get("closing_to"),
        limit=limit,
        order_by=str(criteria.get("order") or "recent"),
        portal_terms=PORTAL_SEARCH_TERMS.get(portal),
    )


def _save_to_list(db, company_id: str, catalog_id: str) -> None:
    opportunity_id = db.add_global_catalog_item_to_pipeline(company_id, catalog_id)
    if opportunity_id:
        db.update_stage(company_id, opportunity_id, "Nova oportunidade")
    st.success("Edital salvo. Ele está na sua lista para você decidir depois.")


def _render_items(opportunity: dict, pack: dict) -> None:
    control = str(opportunity.get("pncp_control_number") or "").strip()
    preview = list(pack.get("items") or [])
    known_total = int(pack.get("item_count") or len(preview))
    count_known = bool(pack.get("count_known"))
    has_more = bool(pack.get("has_more")) or (count_known and known_total > len(preview))
    error = str(pack.get("items_error") or "").strip()
    item_key = str(opportunity.get("id") or control or id(opportunity))
    limit_key = f"essential_item_limit_{item_key}"
    visible_limit = max(20, int(st.session_state.get(limit_key, 20)))

    items = preview
    full_loaded = False
    if visible_limit > len(preview) and control:
        try:
            with st.spinner("Buscando mais itens..."):
                items = _cached_full_items(control)
            full_loaded = True
        except PncpItemsError:
            items = preview

    if full_loaded:
        known_total = len(items)
        count_known = True
        has_more = known_total > visible_limit

    visible = items[:visible_limit]
    if count_known:
        count_label = f"{known_total} item(ns)"
    elif preview:
        count_label = f"{len(preview)}+ item(ns)"
    else:
        count_label = "itens da licitação"

    html = [f'<div class="ln-items-box"><div class="ln-items-title">📦 Itens da licitação · {escape(count_label)}</div>']
    if error and not preview:
        html.append('<div class="ln-items-note">Os itens ainda não estão disponíveis no PNCP.</div>')
    elif not visible:
        html.append('<div class="ln-items-note">O PNCP ainda não publicou a lista de itens desta licitação.</div>')
    else:
        for row in visible:
            number = escape(str(row.get("number") or "—"))
            desc = escape(str(row.get("description") or "Item não descrito").strip())
            qty = _quantity_text(row.get("quantity"))
            unit = escape(str(row.get("unit_measure") or "").strip())
            qty_text = escape(f"{qty} {unit}".strip())
            price = escape(_item_price_text(row))
            html.append(
                '<div class="ln-item-row">'
                f'<div class="ln-item-number">{number}</div>'
                f'<div class="ln-item-desc">{desc}</div>'
                f'<div class="ln-item-qty">{qty_text}</div>'
                f'<div class="ln-item-price">{price}</div>'
                '</div>'
            )
        if count_known and known_total > len(visible):
            html.append(f'<div class="ln-items-note">+ {known_total - len(visible)} item(ns) para ver.</div>')
        elif has_more and not count_known:
            html.append('<div class="ln-items-note">Há mais itens nesta licitação.</div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)

    can_expand = bool(control and (has_more or (count_known and known_total > len(visible))))
    if can_expand:
        b1, b2 = st.columns(2)
        if b1.button("Mostrar mais 20 itens", key=f"essential_more_items_{item_key}", width="stretch"):
            st.session_state[limit_key] = visible_limit + 20
            st.rerun()
        if visible_limit > 20 and b2.button("Voltar para 20 itens", key=f"essential_less_items_{item_key}", width="stretch"):
            st.session_state[limit_key] = 20
            st.rerun()


def _render_card(db, user: dict, item: dict, pack: dict) -> None:
    company_id = user["company_id"]
    modality = str(item.get("modality") or "Licitação")
    control = str(item.get("pncp_control_number") or "").strip()
    city = str(item.get("city") or "Município não informado")
    state = str(item.get("state") or "--")
    agency = str(item.get("agency") or "Órgão não informado")
    reference = agency
    estimated_value = item.get("estimated_value")
    value = format_brl(estimated_value) if estimated_value not in (None, "") else "Não informado"
    opening = item.get("opening_at") or item.get("closing_at")
    deadline = item.get("closing_at")
    opening_text = _datetime_text(opening)
    published_text = _datetime_text(item.get("published_at"))
    countdown = _countdown(deadline)
    obj = str(item.get("object") or "Objeto não informado").strip()

    source_name, portal = opportunity_source_and_portal(
        item.get("source_name"), item.get("source_channel"), item.get("source_url")
    )
    access = portal_access_info(portal)
    source_url = str(item.get("source_url") or "").strip()
    has_site = source_url.startswith(("http://", "https://"))
    portal_text = escape(portal if portal not in {"", "Não informado"} else "Não identificado")
    if portal_text == "Não identificado":
        portal_help = "Consultar edital."
    elif has_site:
        safe_url = escape(source_url, quote=True)
        portal_text = f'<a class="ln-meta-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">{portal_text}</a>'
        portal_help = "Clique no nome para abrir o site."
    else:
        portal_help = "Consultar edital para confirmar o endereço."

    with st.container(border=True):
        st.markdown(f'<span class="ln-modality-badge">{escape(modality)}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="ln-reference">{escape(reference)}</div>', unsafe_allow_html=True)
        extra = f'<div class="ln-info-extra">{escape(countdown)}</div>' if countdown else ""
        st.markdown(
            '<div class="ln-info-grid">'
            f'<div class="ln-info-box"><div class="ln-info-label">Cidade</div><div class="ln-info-value">{escape(city)} — {escape(state)}</div></div>'
            f'<div class="ln-info-box"><div class="ln-info-label">Valor</div><div class="ln-info-value">{escape(value)}</div></div>'
            f'<div class="ln-info-box"><div class="ln-info-label">Data e prazo</div><div class="ln-info-value">{escape(opening_text)}</div>{extra}</div>'
            f'<div class="ln-info-box"><div class="ln-info-label">Publicado em</div><div class="ln-info-value">{escape(published_text)}</div></div>'
            '</div>', unsafe_allow_html=True,
        )
        st.markdown('<div class="ln-object-label">O que o governo quer comprar ou contratar</div>', unsafe_allow_html=True)
        st.write(obj)
        st.markdown(
            '<div class="ln-meta-grid">'
            f'<div class="ln-meta-box"><div class="ln-meta-label">Onde participar</div><div class="ln-meta-value">{portal_text}</div><div class="ln-meta-help">{escape(portal_help)}</div></div>'
            f'<div class="ln-meta-box"><div class="ln-meta-label">Custo do acesso</div><div class="ln-meta-value">{escape(access["label"])}</div><div class="ln-meta-help">{escape(access["detail"])}</div></div>'
            '</div>', unsafe_allow_html=True,
        )
        _render_items(item, pack)

        official = pncp_official_url(control)
        primary_url = official or (source_url if has_site else "")
        a1, a2 = st.columns(2)
        if primary_url:
            a1.link_button("Acessar edital", primary_url, width="stretch")
        else:
            a1.button("Acessar edital", disabled=True, width="stretch", key=f"no_link_{item['id']}")
        if a2.button("Salvar na lista", key=f"save_list_{item['id']}", width="stretch"):
            try:
                _save_to_list(db, company_id, item["id"])
            except Exception as exc:
                st.error(f"Não foi possível salvar este edital: {exc}")


def _render_results(db, user: dict, items: list[dict], *, page_key: str, per_page: int = 6) -> None:
    if not items:
        st.info("Nenhum edital aberto foi encontrado. Tente retirar um filtro ou pesquisar outra palavra.")
        return
    st.caption(f"{len(items):,} editais abertos para participação".replace(",", "."))
    total_pages = max((len(items) + per_page - 1) // per_page, 1)
    current = min(max(int(st.session_state.get(page_key, 1)), 1), total_pages)
    start = (current - 1) * per_page
    visible = items[start:start + per_page]
    controls = tuple(
        str(row.get("pncp_control_number") or "").strip()
        for row in visible if str(row.get("pncp_control_number") or "").strip()
    )
    packs = _cached_item_summaries(controls)
    for item in visible:
        control = str(item.get("pncp_control_number") or "").strip()
        _render_card(db, user, item, packs.get(control, {
            "items": [], "item_count": 0, "count_known": False, "has_more": False, "items_error": "",
        }))

    if total_pages > 1:
        n1, n2, n3 = st.columns([1, 1, 1])
        if n1.button("◀ Anterior", disabled=current <= 1, key=f"{page_key}_prev", width="stretch"):
            st.session_state[page_key] = current - 1
            st.rerun()
        n2.markdown(f"<div style='text-align:center;padding:.7rem;color:#52657C'>Página {current} de {total_pages}</div>", unsafe_allow_html=True)
        if n3.button("Próxima ▶", disabled=current >= total_pages, key=f"{page_key}_next", width="stretch"):
            st.session_state[page_key] = current + 1
            st.rerun()


def home_page(db, user: dict) -> None:
    _apply_styles()
    counts = db.global_catalog_group_counts("state", closing_from=date.today().isoformat())
    open_total = sum(int(row.get("total") or 0) for row in counts)

    st.markdown('<div class="ln-discovery-title">Encontre o que o governo está comprando</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Você pode pesquisar um produto ou começar por estado, cidade, modalidade ou site da disputa.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ln-home-count">{open_total:,} editais abertos para participação</div>'.replace(",", "."), unsafe_allow_html=True)

    with st.form("essential_home_search", clear_on_submit=False, enter_to_submit=False):
        keyword = st.text_input("O que você procura?", placeholder="Ex.: papel A4, pneus, medicamentos, uniformes...")
        if st.form_submit_button("Buscar licitações", type="primary", width="stretch"):
            st.session_state["essential_search_criteria"] = _criteria(keyword=keyword.strip())
            st.session_state["essential_search_page"] = 1
            st.session_state["_navigation_request"] = "🔎 Buscar licitações"
            st.rerun()

    st.caption("Ou comece por uma destas opções:")
    shortcuts = [
        ("🗺️ Por Estado", "Ver estados"),
        ("📍 Por Cidade", "Buscar cidade"),
        ("☰ Por Modalidade", "Ver modalidades"),
        ("🌐 Por site de disputa", "Ver sites"),
    ]
    cols = st.columns(4)
    for col, (target, label) in zip(cols, shortcuts):
        if col.button(label, key=f"home_{target}", width="stretch"):
            st.session_state["_navigation_request"] = target
            st.rerun()


def portal_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">🌐 Por site de disputa</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Escolha onde deseja participar. Se não tiver preferência, use Todos os sites.</div>', unsafe_allow_html=True)

    if st.button("Todos os sites", key="portal_all", type="primary", width="stretch"):
        st.session_state["essential_search_criteria"] = _criteria(portal="Todos os sites")
        st.session_state["essential_search_page"] = 1
        st.session_state["_navigation_request"] = "🔎 Buscar licitações"
        st.rerun()

    portals = list(PORTAL_ACCESS.keys())
    for start in range(0, len(portals), 3):
        cols = st.columns(3)
        for col, portal in zip(cols, portals[start:start + 3]):
            access = portal_access_info(portal)
            with col.container(border=True):
                st.write(portal)
                st.caption(f"Custo do acesso: {access['label']}")
                if st.button("Ver editais", key=f"portal_{portal}", width="stretch"):
                    st.session_state["essential_search_criteria"] = _criteria(portal=portal)
                    st.session_state["essential_search_page"] = 1
                    st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                    st.rerun()


def search_page(db, user: dict, usage=None) -> None:
    _apply_styles()
    company_id = user["company_id"]
    defaults = _profile_defaults(db, company_id)
    current = st.session_state.get("essential_search_criteria") or {}

    st.markdown('<div class="ln-discovery-title">🔎 Buscar licitações</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Pesquise pelo que deseja vender. Se deixar em branco, mostramos editais de vários tipos.</div>', unsafe_allow_html=True)

    with st.form("essential_quick_search", clear_on_submit=False, enter_to_submit=False):
        keyword = st.text_input(
            "O que você procura?",
            value=str(current.get("keyword") if "keyword" in current else defaults["keyword"]),
            placeholder="Ex.: papel A4, pneus, medicamentos, uniformes...",
        )
        c1, c2 = st.columns(2)
        states = c1.multiselect(
            "Estado", list(BRAZIL_STATES),
            default=list(current.get("states") if "states" in current else defaults["states"]),
            placeholder="Brasil inteiro",
        )
        city = c2.text_input("Cidade (opcional)", value=str(current.get("city") or ""), placeholder="Ex.: Londrina")
        m1, m2 = st.columns(2)
        modalities = m1.multiselect(
            "Modalidade", list(MODALITIES.keys()),
            default=list(current.get("modalities") if "modalities" in current else defaults["modalities"]),
            placeholder="Todas",
        )
        current_portal = str(current.get("portal") or "Todos os sites")
        portal_index = PORTAL_OPTIONS.index(current_portal) if current_portal in PORTAL_OPTIONS else 0
        portal = m2.selectbox("Site da disputa", PORTAL_OPTIONS, index=portal_index)
        v1, v2 = st.columns(2)
        min_default = current.get("minimum") if "minimum" in current else defaults["minimum"]
        max_default = current.get("maximum") if "maximum" in current else defaults["maximum"]
        minimum_text = v1.text_input("Valor mínimo", value="" if min_default in (None, "") else str(min_default), placeholder="Sem mínimo")
        maximum_text = v2.text_input("Valor máximo", value="" if max_default in (None, "") else str(max_default), placeholder="Sem máximo")
        submitted = st.form_submit_button("Buscar licitações", type="primary", width="stretch")

    if submitted:
        minimum = parse_brl(minimum_text) if minimum_text.strip() else None
        maximum = parse_brl(maximum_text) if maximum_text.strip() else None
        if minimum_text.strip() and minimum is None:
            st.error("Confira o valor mínimo digitado.")
            return
        if maximum_text.strip() and maximum is None:
            st.error("Confira o valor máximo digitado.")
            return
        current = _criteria(
            keyword=keyword.strip(), city=city.strip(), states=states, modalities=modalities,
            minimum=minimum, maximum=maximum, portal=portal,
        )
        st.session_state["essential_search_criteria"] = current
        st.session_state["essential_search_page"] = 1
        if usage is not None:
            usage.record_search(company_id, user.get("id", ""), keyword.strip())
        db.save_company_profile(
            company_id, search_keyword=keyword.strip(), service_states=", ".join(states),
            search_modalities="|".join(modalities), search_minimum=minimum, search_maximum=maximum,
            search_order="Mais recentes",
        )

    if not current:
        st.info("Digite uma palavra, escolha um estado ou clique em Buscar licitações para ver editais abertos.")
        return

    with st.spinner("Buscando editais abertos..."):
        items = _query_catalog(db, current)
    st.markdown("### Editais abertos para participação")
    _render_results(db, user, items, page_key="essential_search_page", per_page=6)


def state_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">🗺️ Por Estado</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Escolha um estado para ver os editais abertos para participação.</div>', unsafe_allow_html=True)
    counts = db.global_catalog_group_counts("state", closing_from=date.today().isoformat())
    if not counts:
        st.info("Ainda não há editais abertos por estado.")
        return
    for start in range(0, len(counts), 4):
        cols = st.columns(4)
        for col, row in zip(cols, counts[start:start + 4]):
            state = str(row.get("label") or "").upper()
            total = int(row.get("total") or 0)
            with col.container(border=True):
                flag = FLAGS_DIR / f"{state.lower()}.svg"
                if flag.exists():
                    st.image(str(flag), width=72)
                st.write(f"{STATE_NAMES.get(state, state)} ({state})")
                st.caption(f"{total:,} editais abertos para participação".replace(",", "."))
                if st.button("Ver editais", key=f"state_{state}", width="stretch"):
                    st.session_state["essential_search_criteria"] = _criteria(states=[state])
                    st.session_state["essential_search_page"] = 1
                    st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                    st.rerun()


def city_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">📍 Por Cidade</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Digite a cidade para ver os editais abertos para participação.</div>', unsafe_allow_html=True)
    with st.form("essential_city_search", clear_on_submit=False, enter_to_submit=False):
        city = st.text_input("Nome da cidade", placeholder="Ex.: Londrina")
        state = st.selectbox("Estado (opcional)", ["Todos", *BRAZIL_STATES])
        if st.form_submit_button("Buscar licitações", type="primary", width="stretch"):
            if not city.strip():
                st.warning("Digite o nome da cidade.")
            else:
                st.session_state["essential_search_criteria"] = _criteria(
                    city=city.strip(), states=[] if state == "Todos" else [state]
                )
                st.session_state["essential_search_page"] = 1
                st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                st.rerun()


def modality_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">☰ Por Modalidade</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Escolha a modalidade para ver os editais abertos para participação.</div>', unsafe_allow_html=True)
    counts = db.global_catalog_group_counts("modality", closing_from=date.today().isoformat())
    if not counts:
        st.info("Nenhum edital aberto foi encontrado por modalidade agora.")
        return
    for start in range(0, len(counts), 3):
        cols = st.columns(3)
        for col, row in zip(cols, counts[start:start + 3]):
            label = str(row.get("label") or "Modalidade")
            total = int(row.get("total") or 0)
            with col.container(border=True):
                st.markdown(f"**{label}**")
                st.caption(f"{total:,} editais abertos para participação".replace(",", "."))
                if st.button("Ver editais", key=f"modality_{label}", width="stretch"):
                    st.session_state["essential_search_criteria"] = _criteria(modalities=[label])
                    st.session_state["essential_search_page"] = 1
                    st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                    st.rerun()


def advanced_search_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">⚙️ Filtro avançado</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Use só os filtros que quiser. Você não precisa preencher todos.</div>', unsafe_allow_html=True)
    with st.form("essential_advanced_search", clear_on_submit=False, enter_to_submit=False):
        states = st.multiselect("Estados", list(BRAZIL_STATES), placeholder="Todos")
        city = st.text_input("Cidade", placeholder="Opcional")
        m1, m2 = st.columns(2)
        modalities = m1.multiselect("Modalidades", list(MODALITIES.keys()), placeholder="Todas")
        portal = m2.selectbox("Site da disputa", PORTAL_OPTIONS)
        keyword = st.text_input("O que você procura?", placeholder="Ex.: material de limpeza")
        v1, v2 = st.columns(2)
        minimum_text = v1.text_input("Valor mínimo", placeholder="Sem mínimo")
        maximum_text = v2.text_input("Valor máximo", placeholder="Sem máximo")
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Participação a partir de", value=date.today())
        no_end = d2.checkbox("Sem data final", value=True)
        end_date = d2.date_input("Participação até", value=date.today(), disabled=no_end)
        if st.form_submit_button("Buscar licitações", type="primary", width="stretch"):
            minimum = parse_brl(minimum_text) if minimum_text.strip() else None
            maximum = parse_brl(maximum_text) if maximum_text.strip() else None
            if minimum_text.strip() and minimum is None:
                st.error("Confira o valor mínimo digitado.")
            elif maximum_text.strip() and maximum is None:
                st.error("Confira o valor máximo digitado.")
            else:
                st.session_state["essential_search_criteria"] = _criteria(
                    keyword=keyword.strip(), city=city.strip(), states=states, modalities=modalities,
                    minimum=minimum, maximum=maximum, portal=portal,
                    closing_from=start_date.isoformat(),
                    closing_to=None if no_end else end_date.isoformat(),
                )
                st.session_state["essential_search_page"] = 1
                st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                st.rerun()


def top50_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">🔥 Em destaque</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">50 editais recentes para você explorar sem precisar definir uma busca.</div>', unsafe_allow_html=True)
    items = db.list_global_catalog(
        closing_from=date.today().isoformat(), limit=50, order_by="recent"
    )
    _render_results(db, user, items, page_key="essential_top50_page", per_page=5)


def my_list_page(db, user: dict) -> None:
    _apply_styles()
    company_id = user["company_id"]
    st.markdown('<div class="ln-discovery-title">❤️ Minha lista</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Decida apenas se vai participar, não vai participar ou quer descartar o edital.</div>', unsafe_allow_html=True)
    rows = [
        row for row in db.pipeline_summaries(company_id, "")
        if str(row.get("stage") or "") in {"Nova oportunidade", "Decisão"}
    ]
    if not rows:
        st.info("Sua lista está vazia. Salve um edital durante a busca para encontrá-lo aqui depois.")
        return

    for row in rows:
        source_name, portal = opportunity_source_and_portal(
            row.get("source_name"), row.get("source_channel"), row.get("source_url")
        )
        access = portal_access_info(portal)
        with st.container(border=True):
            st.write(row.get("agency") or "Órgão não informado")
            st.write(row.get("object") or "Objeto não informado")
            estimated_value = row.get("estimated_value")
            value = format_brl(estimated_value) if estimated_value not in (None, "") else "Não informado"
            st.caption(
                f"{row.get('city') or 'Município não informado'}/{row.get('state') or '--'} · "
                f"{row.get('modality') or 'Modalidade não informada'} · {value} · "
                f"{_datetime_text(row.get('closing_at'))}"
            )
            portal_text = portal if portal not in {"", "Não informado"} else "Não identificado"
            st.caption(f"Onde participar: {portal_text} · Custo: {access['label']}")

            current_decision = str(row.get("decision") or "")
            default_action = "Vou participar" if current_decision == "Participar" else "Escolha uma opção"
            options = ["Escolha uma opção", "Vou participar", "Não vou participar", "Descartar"]
            action = st.selectbox(
                "O que você vai fazer?", options, index=options.index(default_action),
                key=f"list_action_{row['id']}",
            )

            parsed_certame = None
            if row.get("certame_at"):
                try:
                    parsed_certame = datetime.fromisoformat(str(row.get("certame_at")).replace("Z", "+00:00"))
                except (TypeError, ValueError):
                    parsed_certame = None

            certame_date = None
            certame_time = None
            if action == "Vou participar":
                c1, c2 = st.columns(2)
                certame_date = c1.date_input(
                    "Dia do certame", value=parsed_certame.date() if parsed_certame else date.today(),
                    key=f"list_certame_date_{row['id']}",
                )
                certame_time = c2.time_input(
                    "Hora do certame",
                    value=parsed_certame.time().replace(second=0, microsecond=0) if parsed_certame else time(9, 0),
                    key=f"list_certame_time_{row['id']}",
                )

            b1, b2 = st.columns(2)
            if b1.button("Salvar decisão", key=f"list_save_decision_{row['id']}", type="primary", width="stretch"):
                if action == "Escolha uma opção":
                    st.warning("Escolha se vai participar, não vai participar ou descartar.")
                elif action == "Descartar":
                    db.delete_opportunity(company_id, row["id"])
                    st.rerun()
                elif action == "Não vou participar":
                    db.update_details(company_id, row["id"], decision="Não participar", certame_at=None)
                    db.update_stage(company_id, row["id"], "Arquivada")
                    st.success("Edital marcado como não participar.")
                    st.rerun()
                else:
                    certame_at = datetime.combine(certame_date, certame_time).isoformat(timespec="minutes")
                    db.update_details(company_id, row["id"], decision="Participar", certame_at=certame_at)
                    db.update_stage(company_id, row["id"], "Decisão")
                    st.success("Participação salva. O certame já aparece no Calendário.")
                    st.rerun()

            official = pncp_official_url(row.get("pncp_control_number"))
            source_url = str(row.get("source_url") or "")
            target = official or (source_url if source_url.startswith(("http://", "https://")) else "")
            if target:
                b2.link_button("Acessar edital", target, width="stretch")
            else:
                b2.button("Acessar edital", disabled=True, key=f"list_no_link_{row['id']}", width="stretch")


def preferences_page(db, user: dict) -> None:
    _apply_styles()
    company_id = user["company_id"]
    defaults = _profile_defaults(db, company_id)
    st.markdown('<div class="ln-discovery-title">🔔 Preferências</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Se quiser, salve o que costuma procurar. Isso ajuda o Radar, mas não é obrigatório.</div>', unsafe_allow_html=True)
    with st.form("essential_preferences_simple", clear_on_submit=False, enter_to_submit=False):
        keyword = st.text_input(
            "O que costuma procurar?",
            value=defaults["keyword"],
            placeholder="Ex.: papel, limpeza, informática, pneus",
        )
        states = st.multiselect("Estados favoritos", list(BRAZIL_STATES), default=defaults["states"])
        modalities = st.multiselect("Modalidades favoritas", list(MODALITIES.keys()), default=defaults["modalities"])
        if st.form_submit_button("Salvar preferências", type="primary", width="stretch"):
            db.save_company_profile(
                company_id,
                search_keyword=keyword.strip(),
                service_states=", ".join(states),
                search_modalities="|".join(modalities),
                search_order="Mais recentes",
            )
            st.success("Preferências salvas.")


def radar_page(db, user: dict) -> None:
    _apply_styles()
    defaults = _profile_defaults(db, user["company_id"])
    st.markdown('<div class="ln-discovery-title">📡 Radar de licitações</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Veja editais novos relacionados ao que você escolheu acompanhar.</div>', unsafe_allow_html=True)
    if not (defaults["keyword"].strip() or defaults["states"] or defaults["modalities"]):
        st.info("Você ainda não escolheu o que quer acompanhar. Continue usando a busca normalmente ou configure o Radar quando quiser.")
        if st.button("Configurar preferências", type="primary", width="stretch"):
            st.session_state["_navigation_request"] = "🔔 Preferências"
            st.rerun()
        return
    criteria = _criteria(
        keyword=defaults["keyword"], states=defaults["states"], modalities=defaults["modalities"]
    )
    items = _query_catalog(db, criteria, limit=500)
    if defaults["keyword"]:
        st.caption(f"Você acompanha: {defaults['keyword']}")
    _render_results(db, user, items, page_key="essential_radar_page", per_page=6)
