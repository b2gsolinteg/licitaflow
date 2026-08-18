from __future__ import annotations

from datetime import date, datetime
from html import escape
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from .formatters import format_brl, parse_brl
from .pncp import MODALITIES
from .pncp_items import PncpItemsError, fetch_contract_items
from .radar_items import fetch_radar_item_summaries
from .sources import opportunity_source_and_portal, pncp_official_url, portal_access_info


BRAZIL_STATES = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
)


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
        .ln-discovery-title{font-size:2rem;font-weight:900;letter-spacing:-.025em;margin:.05rem 0 .2rem;color:#F7F9FC}
        .ln-discovery-sub{color:#AEBBCD;font-size:.96rem;margin:0 0 1rem}
        .ln-opportunity-shell{margin:.75rem 0}
        .ln-modality-badge{display:inline-block;background:#E7F8EC;color:#176B3A;border:1px solid #BDE9CA;
            border-radius:999px;padding:.2rem .6rem;font-weight:850;font-size:.72rem;text-transform:uppercase;letter-spacing:.02em}
        .ln-reference{font-weight:900;font-size:1.05rem;color:#F7F9FC;margin:.42rem 0 .7rem}
        .ln-info-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem;margin:.15rem 0 .8rem}
        .ln-info-box{background:#F8FAFC;border:1px solid #DCE4EE;border-radius:12px;padding:.68rem .72rem;min-height:84px}
        .ln-info-label{font-size:.69rem;color:#718096;font-weight:850;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.32rem}
        .ln-info-value{color:#10243F;font-size:.9rem;line-height:1.28;font-weight:650}
        .ln-info-extra{color:#C66B12;font-size:.69rem;font-weight:800;margin-top:.35rem}
        .ln-object-label{font-size:.72rem;color:#D7A52E;font-weight:900;text-transform:uppercase;margin:.3rem 0 .18rem}
        .ln-portal-box{background:#0D1D31;border:1px solid #2A405B;border-radius:11px;padding:.65rem .75rem;margin:.65rem 0}
        .ln-portal-main{color:#F4F7FA;font-weight:800;font-size:.85rem}
        .ln-portal-detail{color:#9FB0C4;font-size:.74rem;line-height:1.35;margin-top:.2rem}
        .ln-items-box{background:#F8FBFF;border:1px solid #DDE7F2;border-radius:12px;padding:.72rem .78rem;margin:.65rem 0}
        .ln-items-title{color:#17324F;font-weight:900;font-size:.88rem;margin-bottom:.4rem}
        .ln-item-row{display:grid;grid-template-columns:48px minmax(0,1fr) 130px 132px;gap:.5rem;align-items:start;
            padding:.42rem .08rem;border-top:1px solid #E7EDF4;color:#24364D}
        .ln-item-row:first-of-type{border-top:0}
        .ln-item-number{font-size:.75rem;font-weight:900;color:#65758A}
        .ln-item-desc{font-size:.78rem;line-height:1.32}
        .ln-item-qty,.ln-item-price{font-size:.74rem;line-height:1.32;color:#52657C;text-align:right}
        .ln-items-note{font-size:.72rem;color:#6D7F93;margin-top:.35rem}
        .ln-section-label{font-size:.72rem;color:#8EA0B6;font-weight:850;letter-spacing:.05em;text-transform:uppercase;margin:.95rem 0 .35rem}
        .ln-state-count{font-size:.73rem;color:#8090A5}
        @media(max-width:900px){
            .ln-info-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
            .ln-item-row{grid-template-columns:38px minmax(0,1fr)}
            .ln-item-qty,.ln-item-price{text-align:left;grid-column:2}
        }
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
    )


def _save_to_list(db, company_id: str, catalog_id: str) -> None:
    opportunity_id = db.add_global_catalog_item_to_pipeline(company_id, catalog_id)
    if opportunity_id:
        db.update_stage(company_id, opportunity_id, "Nova oportunidade")
    st.success("Salvo na Minha lista. Você pode decidir depois se quer começar a preparação.")


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
            with st.spinner("Buscando mais itens oficiais..."):
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
        count_label = "itens oficiais"

    html = [f'<div class="ln-items-box"><div class="ln-items-title">📦 Itens da licitação · {escape(count_label)}</div>']
    if error and not preview:
        html.append('<div class="ln-items-note">Itens estruturados temporariamente indisponíveis no PNCP.</div>')
    elif not visible:
        html.append('<div class="ln-items-note">O PNCP não publicou itens estruturados para esta contratação.</div>')
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
            html.append(f'<div class="ln-items-note">+ {known_total - len(visible)} item(ns) ainda não exibido(s).</div>')
        elif has_more and not count_known:
            html.append('<div class="ln-items-note">Há mais itens nesta contratação.</div>')
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
    reference = control or "Contratação pública"
    city = str(item.get("city") or "Município não informado")
    state = str(item.get("state") or "--")
    agency = str(item.get("agency") or "Órgão não informado")
    value = format_brl(item.get("estimated_value"))
    opening = item.get("opening_at") or item.get("closing_at")
    deadline = item.get("closing_at")
    opening_text = _datetime_text(opening)
    countdown = _countdown(deadline)
    obj = str(item.get("object") or "Objeto não informado").strip()

    source_name, portal = opportunity_source_and_portal(
        item.get("source_name"), item.get("source_channel"), item.get("source_url")
    )
    access = portal_access_info(portal)

    with st.container(border=True):
        st.markdown(f'<span class="ln-modality-badge">{escape(modality)}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="ln-reference">{escape(reference)}</div>', unsafe_allow_html=True)
        extra = f'<div class="ln-info-extra">{escape(countdown)}</div>' if countdown else ""
        st.markdown(
            '<div class="ln-info-grid">'
            f'<div class="ln-info-box"><div class="ln-info-label">Cidade</div><div class="ln-info-value">{escape(city)} — {escape(state)}</div></div>'
            f'<div class="ln-info-box"><div class="ln-info-label">Órgão</div><div class="ln-info-value">{escape(agency)}</div></div>'
            f'<div class="ln-info-box"><div class="ln-info-label">Valor</div><div class="ln-info-value">{escape(value)}</div></div>'
            f'<div class="ln-info-box"><div class="ln-info-label">Abertura / prazo</div><div class="ln-info-value">{escape(opening_text)}</div>{extra}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="ln-object-label">Objeto</div>', unsafe_allow_html=True)
        st.write(obj)
        st.markdown(
            '<div class="ln-portal-box">'
            f'<div class="ln-portal-main">🌐 Portal de disputa: {escape(portal)} · {escape(access["label"])}</div>'
            f'<div class="ln-portal-detail">Fonte do dado: {escape(source_name)}. {escape(access["detail"])}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        _render_items(item, pack)

        official = pncp_official_url(control)
        source_url = str(item.get("source_url") or "").strip()
        primary_url = official or (source_url if source_url.startswith(("http://", "https://")) else "")
        a1, a2 = st.columns(2)
        if primary_url:
            a1.link_button("Acessar edital", primary_url, type="primary", width="stretch")
        else:
            a1.button("Acessar edital", disabled=True, width="stretch", key=f"no_link_{item['id']}")
        if a2.button("Salvar na lista", key=f"save_list_{item['id']}", width="stretch"):
            try:
                _save_to_list(db, company_id, item["id"])
            except Exception as exc:
                st.error(f"Não foi possível salvar esta oportunidade: {exc}")

        if source_url.startswith(("http://", "https://")) and source_url != primary_url:
            st.link_button("🌐 Ir ao portal de disputa", source_url, width="stretch")


def _render_results(db, user: dict, items: list[dict], *, page_key: str, per_page: int = 6) -> None:
    if not items:
        st.info("Nenhuma licitação encontrada com esses filtros. Altere apenas o que for necessário e pesquise novamente.")
        return
    st.caption(f"{len(items)} licitação(ões) encontrada(s).")
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
        n2.markdown(f"<div style='text-align:center;padding:.7rem'>Página {current} de {total_pages}</div>", unsafe_allow_html=True)
        if n3.button("Próxima ▶", disabled=current >= total_pages, key=f"{page_key}_next", width="stretch"):
            st.session_state[page_key] = current + 1
            st.rerun()


def search_page(db, user: dict, usage=None) -> None:
    _apply_styles()
    company_id = user["company_id"]
    defaults = _profile_defaults(db, company_id)
    current = st.session_state.get("essential_search_criteria") or {}

    st.markdown('<div class="ln-discovery-title">🔎 Buscar licitações</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Digite o que procura e veja as oportunidades com os itens já abertos. Campo vazio amplia a busca.</div>', unsafe_allow_html=True)

    with st.form("essential_quick_search", clear_on_submit=False, enter_to_submit=False):
        keyword = st.text_input(
            "O que você procura?",
            value=str(current.get("keyword") if "keyword" in current else defaults["keyword"]),
            placeholder="Ex.: papel A4, pneus, medicamentos, uniformes...",
        )
        c1, c2 = st.columns(2)
        states = c1.multiselect(
            "UF",
            list(BRAZIL_STATES),
            default=list(current.get("states") if "states" in current else defaults["states"]),
            placeholder="Brasil inteiro",
        )
        city = c2.text_input(
            "Cidade (opcional)",
            value=str(current.get("city") or ""),
            placeholder="Ex.: Londrina",
        )
        modalities = st.multiselect(
            "Modalidade",
            list(MODALITIES.keys()),
            default=list(current.get("modalities") if "modalities" in current else defaults["modalities"]),
            placeholder="Todas as modalidades",
        )
        v1, v2 = st.columns(2)
        min_default = current.get("minimum") if "minimum" in current else defaults["minimum"]
        max_default = current.get("maximum") if "maximum" in current else defaults["maximum"]
        minimum_text = v1.text_input("Valor mínimo", value="" if min_default in (None, "") else str(min_default), placeholder="Sem mínimo")
        maximum_text = v2.text_input("Valor máximo", value="" if max_default in (None, "") else str(max_default), placeholder="Sem máximo")
        submitted = st.form_submit_button("🔎 Buscar licitações", type="primary", width="stretch")

    if submitted:
        minimum = parse_brl(minimum_text) if minimum_text.strip() else None
        maximum = parse_brl(maximum_text) if maximum_text.strip() else None
        if minimum_text.strip() and minimum is None:
            st.error("O valor mínimo não pôde ser interpretado.")
            return
        if maximum_text.strip() and maximum is None:
            st.error("O valor máximo não pôde ser interpretado.")
            return
        current = _criteria(
            keyword=keyword.strip(),
            city=city.strip(),
            states=states,
            modalities=modalities,
            minimum=minimum,
            maximum=maximum,
        )
        st.session_state["essential_search_criteria"] = current
        st.session_state["essential_search_page"] = 1
        if usage is not None:
            usage.record_search(company_id, user.get("id", ""), keyword.strip())
        db.save_company_profile(
            company_id,
            search_keyword=keyword.strip(),
            service_states=", ".join(states),
            search_modalities="|".join(modalities),
            search_minimum=minimum,
            search_maximum=maximum,
            search_order="Mais recentes",
        )

    if not current:
        st.info("Comece por uma palavra, um estado ou simplesmente clique em Buscar licitações para explorar tudo que está aberto.")
        return

    with st.spinner("Localizando oportunidades abertas..."):
        items = _query_catalog(db, current)
    st.markdown("### Oportunidades")
    _render_results(db, user, items, page_key="essential_search_page", per_page=6)


def state_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">🗺️ Por Estado</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Escolha uma UF e veja diretamente as licitações que ainda estão abertas.</div>', unsafe_allow_html=True)
    counts = db.global_catalog_group_counts("state", closing_from=date.today().isoformat())
    if not counts:
        st.info("Ainda não há estados disponíveis no catálogo.")
        return
    for start in range(0, len(counts), 4):
        cols = st.columns(4)
        for col, row in zip(cols, counts[start:start + 4]):
            state = str(row.get("label") or "").upper()
            total = int(row.get("total") or 0)
            if col.button(f"{state} · {total:,}".replace(",", "."), key=f"state_{state}", width="stretch"):
                st.session_state["essential_search_criteria"] = _criteria(states=[state])
                st.session_state["essential_search_page"] = 1
                st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                st.rerun()


def city_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">📍 Por Cidade</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Digite o município e veja as licitações abertas naquela cidade.</div>', unsafe_allow_html=True)
    with st.form("essential_city_search", clear_on_submit=False, enter_to_submit=False):
        city = st.text_input("Nome da cidade", placeholder="Ex.: Londrina")
        state = st.selectbox("UF (opcional)", ["Todas", *BRAZIL_STATES])
        if st.form_submit_button("Buscar licitações", type="primary", width="stretch"):
            if not city.strip():
                st.warning("Digite o nome da cidade.")
            else:
                st.session_state["essential_search_criteria"] = _criteria(
                    city=city.strip(), states=[] if state == "Todas" else [state]
                )
                st.session_state["essential_search_page"] = 1
                st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                st.rerun()


def modality_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">☰ Por Modalidade</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Escolha como o órgão está contratando e veja as oportunidades abertas.</div>', unsafe_allow_html=True)
    counts = db.global_catalog_group_counts("modality", closing_from=date.today().isoformat())
    if not counts:
        st.info("Nenhuma modalidade disponível no catálogo agora.")
        return
    for start in range(0, len(counts), 3):
        cols = st.columns(3)
        for col, row in zip(cols, counts[start:start + 3]):
            label = str(row.get("label") or "Modalidade")
            total = int(row.get("total") or 0)
            with col.container(border=True):
                st.markdown(f"**{label}**")
                st.caption(f"{total:,} licitação(ões)".replace(",", "."))
                if st.button("Ver licitações", key=f"modality_{label}", width="stretch"):
                    st.session_state["essential_search_criteria"] = _criteria(modalities=[label])
                    st.session_state["essential_search_page"] = 1
                    st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                    st.rerun()


def advanced_search_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">⚙️ Filtro avançado</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Combine apenas os filtros que fizerem sentido. Nenhum campo é obrigatório.</div>', unsafe_allow_html=True)
    with st.form("essential_advanced_search", clear_on_submit=False, enter_to_submit=False):
        states = st.multiselect("Estados", list(BRAZIL_STATES), placeholder="Todos")
        city = st.text_input("Cidade", placeholder="Opcional")
        modalities = st.multiselect("Modalidades", list(MODALITIES.keys()), placeholder="Todas")
        keyword = st.text_input("Palavra ou frase do objeto", placeholder="Ex.: material de limpeza")
        v1, v2 = st.columns(2)
        minimum_text = v1.text_input("Valor mínimo", placeholder="Sem mínimo")
        maximum_text = v2.text_input("Valor máximo", placeholder="Sem máximo")
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Prazo a partir de", value=date.today())
        no_end = d2.checkbox("Sem data final", value=True)
        end_date = d2.date_input("Prazo até", value=date.today(), disabled=no_end)
        if st.form_submit_button("Buscar licitações", type="primary", width="stretch"):
            minimum = parse_brl(minimum_text) if minimum_text.strip() else None
            maximum = parse_brl(maximum_text) if maximum_text.strip() else None
            if minimum_text.strip() and minimum is None:
                st.error("O valor mínimo não pôde ser interpretado.")
            elif maximum_text.strip() and maximum is None:
                st.error("O valor máximo não pôde ser interpretado.")
            else:
                st.session_state["essential_search_criteria"] = _criteria(
                    keyword=keyword.strip(), city=city.strip(), states=states, modalities=modalities,
                    minimum=minimum, maximum=maximum,
                    closing_from=start_date.isoformat(),
                    closing_to=None if no_end else end_date.isoformat(),
                )
                st.session_state["essential_search_page"] = 1
                st.session_state["_navigation_request"] = "🔎 Buscar licitações"
                st.rerun()


def top50_page(db, user: dict) -> None:
    _apply_styles()
    st.markdown('<div class="ln-discovery-title">🏆 Top 50</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">50 oportunidades recentes com prazo aberto para você explorar sem precisar configurar um perfil.</div>', unsafe_allow_html=True)
    items = db.list_global_catalog(
        closing_from=date.today().isoformat(), limit=50, order_by="recent"
    )
    _render_results(db, user, items, page_key="essential_top50_page", per_page=5)


def my_list_page(db, user: dict) -> None:
    _apply_styles()
    company_id = user["company_id"]
    st.markdown('<div class="ln-discovery-title">❤️ Minha lista</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Aqui ficam as oportunidades que chamaram sua atenção. Só leve para preparação quando decidir estudar de verdade.</div>', unsafe_allow_html=True)
    rows = [
        row for row in db.pipeline_summaries(company_id, "")
        if str(row.get("stage") or "") == "Nova oportunidade"
    ]
    if not rows:
        st.info("Sua lista está vazia. Salve oportunidades durante a pesquisa e volte aqui quando quiser decidir.")
        return
    for row in rows:
        source_name, portal = opportunity_source_and_portal(
            row.get("source_name"), row.get("source_channel"), row.get("source_url")
        )
        access = portal_access_info(portal)
        with st.container(border=True):
            st.markdown(f"### {row.get('agency') or 'Órgão não informado'}")
            st.write(row.get("object") or "Objeto não informado")
            st.caption(
                f"{row.get('city') or 'Município não informado'}/{row.get('state') or '--'} · "
                f"{row.get('modality') or 'Modalidade não informada'} · {format_brl(row.get('estimated_value'))} · "
                f"{_datetime_text(row.get('closing_at'))}"
            )
            st.caption(f"Portal: {portal} · {access['label']} · Fonte: {source_name}")
            official = pncp_official_url(row.get("pncp_control_number"))
            source_url = str(row.get("source_url") or "")
            target = official or (source_url if source_url.startswith(("http://", "https://")) else "")
            c1, c2, c3 = st.columns(3)
            if target:
                c1.link_button("Acessar edital", target, width="stretch")
            else:
                c1.button("Acessar edital", disabled=True, key=f"list_no_link_{row['id']}", width="stretch")
            if c2.button("Começar preparação", key=f"list_prepare_{row['id']}", type="primary", width="stretch"):
                db.update_stage(company_id, row["id"], "Em análise")
                st.session_state["pipeline_opportunity_id"] = row["id"]
                st.session_state["_navigation_request"] = "📋 Meus Editais"
                st.rerun()
            if c3.button("Remover", key=f"list_remove_{row['id']}", width="stretch"):
                db.delete_opportunity(company_id, row["id"])
                st.rerun()


def preferences_page(db, user: dict) -> None:
    _apply_styles()
    company_id = user["company_id"]
    defaults = _profile_defaults(db, company_id)
    st.markdown('<div class="ln-discovery-title">🔔 Preferências</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Opcional: salve alguns interesses para o Radar. Você pode usar todo o LicitaNexo sem preencher esta tela.</div>', unsafe_allow_html=True)
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
            st.success("Preferências salvas. Elas servem apenas como atalho para o Radar.")


def radar_page(db, user: dict) -> None:
    _apply_styles()
    defaults = _profile_defaults(db, user["company_id"])
    st.markdown('<div class="ln-discovery-title">📡 Radar de licitações</div>', unsafe_allow_html=True)
    st.markdown('<div class="ln-discovery-sub">Novas oportunidades relacionadas ao que você escolheu acompanhar — sem score e sem exigir CNAE.</div>', unsafe_allow_html=True)
    if not (defaults["keyword"].strip() or defaults["states"] or defaults["modalities"]):
        st.info("Você ainda não salvou preferências. Isso é opcional; use Buscar licitações normalmente ou configure o Radar quando quiser.")
        if st.button("Configurar preferências", type="primary", width="stretch"):
            st.session_state["_navigation_request"] = "🔔 Preferências"
            st.rerun()
        return
    criteria = _criteria(
        keyword=defaults["keyword"], states=defaults["states"], modalities=defaults["modalities"]
    )
    items = _query_catalog(db, criteria, limit=500)
    if defaults["keyword"]:
        st.caption(f"Encontrado porque você acompanha: {defaults['keyword']}")
    _render_results(db, user, items, page_key="essential_radar_page", per_page=6)
