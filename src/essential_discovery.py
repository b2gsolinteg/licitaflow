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
BRAZIL_REGIONS = {
    "Brasil inteiro": (),
    "Norte": ("AC", "AP", "AM", "PA", "RO", "RR", "TO"),
    "Nordeste": ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"),
    "Centro-Oeste": ("DF", "GO", "MT", "MS"),
    "Sudeste": ("ES", "MG", "RJ", "SP"),
    "Sul": ("PR", "RS", "SC"),
}
REGION_OPTIONS = tuple(BRAZIL_REGIONS.keys())
NATURE_OPTIONS = ("Todos", "Produtos", "Serviços")
SRP_OPTIONS = ("Todos", "Com registro de preços", "Sem registro de preços")
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
        [data-testid="stMain"]{background:#F4F7FA !important;font-family:Inter,"Segoe UI",Arial,sans-serif !important;}
        [data-testid="stMain"] .block-container{max-width:1180px !important;padding-top:1.35rem !important;}
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
        [data-testid="stMain"] .block-container .stButton button,[data-testid="stMain"] .block-container .stDownloadButton button{background:#FFFFFF !important;color:#263947 !important;border:1px solid #CBD7DF !important;border-radius:11px !important;box-shadow:none !important;font-weight:600 !important;}
        [data-testid="stMain"] .block-container .stButton button[kind="primary"],[data-testid="stMain"] .block-container .stDownloadButton button[kind="primary"]{background:#0E7C75 !important;color:#FFFFFF !important;border:1px solid #0E7C75 !important;box-shadow:0 4px 10px rgba(14,124,117,.12) !important;}
        [data-testid="stMain"] .block-container .stButton button[kind="primary"] *,[data-testid="stMain"] .block-container .stDownloadButton button[kind="primary"] *{color:#FFFFFF !important;}
        [data-testid="stMain"] .block-container .stButton button:hover{border-color:#9FB3C0 !important;}
        [data-testid="stMain"] .block-container .stButton button[kind="primary"]:hover{background:#0A655F !important;border-color:#0A655F !important;}
        .ln-home-count{font-size:1.52rem;color:#0B4160;margin:.2rem 0 .85rem;font-weight:700 !important;}
        .ln-home-value{background:#FFFFFF;border:1px solid #DCE7EA;border-left:4px solid #55A89F;border-radius:14px;padding:.85rem 1rem;margin:.65rem 0 1rem;color:#4F6573;font-size:.9rem;line-height:1.48;box-shadow:0 4px 14px rgba(30,52,69,.035)}
        .ln-home-section{font-size:.72rem;color:#7A8A97;margin:1rem 0 .5rem;font-weight:750 !important;letter-spacing:.08em;text-transform:uppercase}
        .ln-shortcut-copy{min-height:2.25rem;color:#71808D;font-size:.76rem;line-height:1.38;margin:.05rem 0 .55rem;}
        .ln-state-name{font-size:1.02rem;color:#172B3A;font-weight:700 !important;margin:.42rem 0 0}.ln-state-code{font-size:.78rem;color:#7A8B98;margin-left:.25rem;font-weight:600 !important}.ln-state-count{font-size:1.85rem;color:#0B4B76;font-weight:750 !important;line-height:1.05;margin:.9rem 0 .05rem}.ln-state-label{font-size:.78rem;color:#748592;margin-bottom:.65rem}.ln-state-card-note{font-size:.70rem;color:#8A99A5;margin-top:.2rem}.ln-state-grid-title{font-size:.73rem;color:#788995;font-weight:750 !important;letter-spacing:.08em;text-transform:uppercase;margin:.95rem 0 .48rem}
        .ln-portal-name,.ln-modality-name{font-size:1rem;color:#172B3A;font-weight:700 !important;margin-bottom:.2rem}.ln-card-count{font-size:1.55rem;color:#0B4B76;font-weight:750 !important;margin:.55rem 0 .08rem;line-height:1}.ln-card-caption{font-size:.76rem;color:#748592;margin-bottom:.65rem}
        [data-testid="stMain"] .block-container div[class*="st-key-state_"] button{min-height:2.7rem !important;}
        /* RC31.14 density polish */
        header[data-testid="stHeader"]{height:44px !important;min-height:44px !important;box-shadow:0 1px 8px rgba(7,29,48,.08) !important;}
        [data-testid="stMain"]{background:#F3F6F9 !important;}
        [data-testid="stMain"] .block-container{max-width:900px !important;padding-top:.78rem !important;padding-bottom:1.8rem !important;}
        [data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:240px !important;min-width:240px !important;max-width:240px !important;}
        [data-testid="stSidebar"] > div:first-child{padding-bottom:.7rem !important;}
        [data-testid="stSidebar"] [data-testid="stImage"] img{max-width:154px !important;width:154px !important;margin:.08rem auto 0 !important;}
        [data-testid="stSidebar"] .stButton button{min-height:2.85rem !important;border-radius:10px !important;padding:.24rem .42rem !important;gap:.55rem !important;font-size:.84rem !important;font-weight:650 !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{flex:0 0 2.15rem !important;width:2.15rem !important;height:2.15rem !important;border-radius:9px !important;font-size:1.08rem !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#F3F8F7 !important;border-color:#DCEAE7 !important;box-shadow:inset 3px 0 0 #13877F !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{margin-top:.46rem !important;margin-bottom:.08rem !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.64rem !important;letter-spacing:.09em !important;}
        [data-testid="stSidebar"] div[style*="background:#F6F9FA"]{padding:.52rem .6rem !important;margin:.1rem 0 .52rem !important;border-radius:10px !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px !important;border-color:#E7EBEF !important;box-shadow:0 4px 14px rgba(30,52,69,.05) !important;}
        [data-testid="stMain"] [data-testid="stForm"]{border-radius:12px !important;padding:.78rem .82rem .72rem !important;box-shadow:0 4px 14px rgba(30,52,69,.04) !important;}
        .ln-page-kicker{padding:.18rem .48rem !important;font-size:.61rem !important;margin-bottom:.38rem !important;}
        .ln-discovery-title{font-size:1.62rem !important;line-height:1.1 !important;margin:0 0 .18rem !important;letter-spacing:-.02em !important;}
        .ln-discovery-sub{font-size:.88rem !important;line-height:1.42 !important;margin:0 0 .7rem !important;max-width:48rem !important;}
        .ln-home-count{font-size:1.34rem !important;margin:.08rem 0 .55rem !important;}
        .ln-home-value{padding:.66rem .78rem !important;margin:.4rem 0 .72rem !important;border-radius:11px !important;font-size:.84rem !important;line-height:1.42 !important;}
        .ln-home-section{font-size:.66rem !important;margin:.72rem 0 .36rem !important;}
        .ln-shortcut-copy{min-height:1.72rem !important;font-size:.71rem !important;line-height:1.3 !important;margin:0 0 .35rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-copy){border-radius:11px !important;box-shadow:0 3px 10px rgba(30,52,69,.035) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-shortcut-copy) > div{padding:.62rem .68rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name){border:1px solid #E7EBEF !important;border-radius:12px !important;box-shadow:0 5px 15px rgba(30,52,69,.055) !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) > div{padding:.66rem .72rem .7rem !important;}
        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.ln-state-name) [data-testid="stImage"] img{width:42px !important;max-width:42px !important;}
        [data-testid="stMain"] div[data-testid="stHorizontalBlock"]:has(.ln-state-name){gap:.68rem !important;}
        .ln-state-name{font-size:.93rem !important;margin:.2rem 0 0 !important;}
        .ln-state-code{font-size:.7rem !important;}
        .ln-state-count{font-size:1.48rem !important;margin:.48rem 0 .02rem !important;}
        .ln-state-label{font-size:.7rem !important;margin-bottom:.4rem !important;}
        .ln-state-grid-title{font-size:.66rem !important;margin:.62rem 0 .36rem !important;}
        [data-testid="stMain"] .block-container .stButton button,[data-testid="stMain"] .block-container .stDownloadButton button{min-height:2.3rem !important;border-radius:9px !important;font-size:.82rem !important;}
        [data-testid="stMain"] .block-container div[class*="st-key-state_"] button{min-height:2.25rem !important;}
        [data-testid="stMain"] .block-container .stButton button[kind="primary"] p,[data-testid="stMain"] .block-container .stButton button[kind="primary"] span{color:#FFFFFF !important;}
        .ln-info-grid{gap:.48rem !important;margin:.14rem 0 .65rem !important;}
        .ln-info-box,.ln-meta-box{padding:.6rem .64rem !important;min-height:70px !important;border-radius:10px !important;}
        .ln-reference{font-size:1rem !important;margin:.35rem 0 .55rem !important;}
        @media(max-width:900px){[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:230px !important;min-width:230px !important;max-width:230px !important;}[data-testid="stMain"] .block-container{max-width:100% !important;padding:.68rem .72rem 1.4rem !important;}.ln-discovery-title{font-size:1.45rem !important;}}
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



SERVICE_TERMS = (
    "serviço", "servicos", "serviços", "prestação de serviço", "prestacao de servico",
    "manutenção", "manutencao", "locação", "locacao", "consultoria", "engenharia",
    "obra", "reforma", "limpeza", "vigilância", "vigilancia", "instalação", "instalacao",
    "suporte técnico", "suporte tecnico", "capacitação", "capacitacao", "transporte",
    "terceirização", "terceirizacao", "mão de obra", "mao de obra", "seguro", "apólice", "apolice",
)
PRODUCT_TERMS = (
    "aquisição", "aquisicao", "compra", "fornecimento", "material", "materiais", "medicamento",
    "equipamento", "produto", "insumo", "gênero alimentício", "genero alimenticio", "mobiliário",
    "mobiliario", "uniforme", "peça", "peca",
)


def _opportunity_nature(item: dict) -> str:
    text = " ".join(str(item.get("object") or "").lower().split())
    service_anchors = (
        "prestação de serviço", "prestacao de servico", "prestação dos serviços", "prestacao dos servicos",
        "contratação de serviço", "contratacao de servico", "serviços de ", "servicos de ",
        "mão de obra", "mao de obra", "seguro", "apólice", "apolice", "manutenção", "manutencao",
        "locação", "locacao", "consultoria", "terceirização", "terceirizacao", "vigilância", "vigilancia",
        "limpeza", "capacitação", "capacitacao", "obra", "reforma",
    )
    product_anchors = (
        "aquisição de ", "aquisicao de ", "compra de ", "registro de preços para aquisição",
        "registro de precos para aquisicao", "fornecimento de materiais", "fornecimento de medicamentos",
        "fornecimento de equipamentos", "fornecimento de produtos", "fornecimento de insumos",
        "fornecimento de mobiliário", "fornecimento de mobiliario", "fornecimento de uniformes",
    )
    explicit_service = any(term in text for term in service_anchors)
    explicit_product = any(term in text for term in product_anchors)
    if explicit_service and not explicit_product:
        return "Serviços"
    if explicit_product and not explicit_service:
        return "Produtos"
    if explicit_service and explicit_product:
        return "Produtos e serviços"
    service = any(term in text for term in SERVICE_TERMS)
    product = any(term in text for term in PRODUCT_TERMS)
    if service and not product:
        return "Serviços"
    if product and not service:
        return "Produtos"
    if service and product:
        return "Produtos e serviços"
    return "Não classificado"


def _nature_matches(item: dict, wanted: str) -> bool:
    if wanted == "Todos":
        return True
    nature = _opportunity_nature(item)
    if wanted == "Produtos":
        return nature in {"Produtos", "Produtos e serviços"}
    if wanted == "Serviços":
        return nature in {"Serviços", "Produtos e serviços"}
    return True


def _effective_states(criteria: dict) -> list[str]:
    selected = [state for state in list(criteria.get("states") or []) if state in BRAZIL_STATES]
    region_states = list(BRAZIL_REGIONS.get(str(criteria.get("region") or "Brasil inteiro")) or ())
    if not region_states:
        return selected
    if not selected:
        return region_states
    return [state for state in selected if state in region_states]


def _srp_query_value(label: str):
    if label == "Com registro de preços":
        return True
    if label == "Sem registro de preços":
        return False
    return None


def _srp_profile_value(label: str) -> str:
    return {"Com registro de preços": "Sim", "Sem registro de preços": "Não"}.get(label, "Todos")


def _criteria(**updates) -> dict:
    base = {
        "keyword": "", "city": "", "region": "Brasil inteiro", "states": [],
        "nature": "Todos", "srp": "Todos", "modalities": [],
        "minimum": None, "maximum": None,
        "closing_from": date.today().isoformat(), "closing_to": None,
        "order": "recent", "portal": "Todos os sites",
    }
    base.update(updates)
    return base

def _profile_defaults(db, company_id: str) -> dict:
    profile = db.get_company_profile(company_id) or {}
    states = [x.strip().upper() for x in str(profile.get("service_states") or "").replace(";", ",").split(",") if x.strip().upper() in BRAZIL_STATES]
    modalities = [x.strip() for x in str(profile.get("search_modalities") or "").split("|") if x.strip() in MODALITIES]
    nature = str(profile.get("search_nature") or "Todos")
    if nature not in NATURE_OPTIONS:
        nature = "Todos"
    srp = {"Sim": "Com registro de preços", "Não": "Sem registro de preços"}.get(str(profile.get("search_srp") or "Todos"), str(profile.get("search_srp") or "Todos"))
    if srp not in SRP_OPTIONS:
        srp = "Todos"
    return {
        "keyword": str(profile.get("search_keyword") or ""), "states": states,
        "modalities": modalities, "nature": nature, "srp": srp,
        "minimum": profile.get("search_minimum"), "maximum": profile.get("search_maximum"),
    }

def _query_catalog(db, criteria: dict, *, limit: int = 10000) -> list[dict]:
    cities = [str(criteria.get("city") or "").strip()] if str(criteria.get("city") or "").strip() else []
    portal = str(criteria.get("portal") or "Todos os sites")
    items = db.list_global_catalog(
        search=str(criteria.get("keyword") or "").strip(), states=_effective_states(criteria), cities=cities,
        modalities=list(criteria.get("modalities") or []), srp=_srp_query_value(str(criteria.get("srp") or "Todos")),
        minimum=criteria.get("minimum"), maximum=criteria.get("maximum"),
        closing_from=criteria.get("closing_from") or date.today().isoformat(), closing_to=criteria.get("closing_to"),
        limit=limit, order_by=str(criteria.get("order") or "recent"), portal_terms=PORTAL_SEARCH_TERMS.get(portal),
    )
    nature = str(criteria.get("nature") or "Todos")
    return items if nature == "Todos" else [item for item in items if _nature_matches(item, nature)]

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

    html = [f'<div class="ln-items-box"><div class="ln-items-title">Itens da licitação · {escape(count_label)}</div>']
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
        if n1.button("Anterior", icon=":material/chevron_left:", disabled=current <= 1, key=f"{page_key}_prev", width="stretch"):
            st.session_state[page_key] = current - 1
            st.rerun()
        n2.markdown(f"<div style='text-align:center;padding:.7rem;color:#52657C'>Página {current} de {total_pages}</div>", unsafe_allow_html=True)
        if n3.button("Próxima", icon=":material/chevron_right:", disabled=current >= total_pages, key=f"{page_key}_next", width="stretch"):
            st.session_state[page_key] = current + 1
            st.rerun()


def home_page(db, user: dict) -> None:
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

def portal_page(db, user: dict) -> None:
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

def search_page(db, user: dict, usage=None) -> None:
    _apply_styles()
    company_id = user["company_id"]
    defaults = _profile_defaults(db, company_id)
    current = st.session_state.get("essential_search_criteria") or {}
    _page_header("ENCONTRE OPORTUNIDADES", "Buscar licitações", "Escolha só o que fizer sentido. Campos vazios deixam a busca mais ampla.")
    with st.form("essential_quick_search", clear_on_submit=False, enter_to_submit=False):
        keyword = st.text_input("O que você procura?", value=str(current.get("keyword") if "keyword" in current else defaults["keyword"]), placeholder="Ex.: papel A4, pneus, medicamentos, manutenção...")
        g1, g2, g3 = st.columns([1, 1.2, 1.2])
        current_region = str(current.get("region") or "Brasil inteiro")
        region = g1.selectbox("Região", REGION_OPTIONS, index=REGION_OPTIONS.index(current_region) if current_region in REGION_OPTIONS else 0)
        states = g2.multiselect("Estado (opcional)", list(BRAZIL_STATES), default=list(current.get("states") if "states" in current else defaults["states"]), placeholder="Todos da região")
        city = g3.text_input("Cidade (opcional)", value=str(current.get("city") or ""), placeholder="Ex.: Londrina")
        f1, f2, f3 = st.columns(3)
        current_nature = str(current.get("nature") if "nature" in current else defaults["nature"])
        nature = f1.selectbox("O que procura", NATURE_OPTIONS, index=NATURE_OPTIONS.index(current_nature) if current_nature in NATURE_OPTIONS else 0)
        current_srp = str(current.get("srp") if "srp" in current else defaults["srp"])
        srp = f2.selectbox("Registro de preços", SRP_OPTIONS, index=SRP_OPTIONS.index(current_srp) if current_srp in SRP_OPTIONS else 0)
        current_portal = str(current.get("portal") or "Todos os sites")
        portal = f3.selectbox("Site da disputa", PORTAL_OPTIONS, index=PORTAL_OPTIONS.index(current_portal) if current_portal in PORTAL_OPTIONS else 0)
        modalities = st.multiselect("Modalidade", list(MODALITIES.keys()), default=list(current.get("modalities") if "modalities" in current else defaults["modalities"]), placeholder="Todas")
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
            st.error("Confira o valor mínimo digitado."); return
        if maximum_text.strip() and maximum is None:
            st.error("Confira o valor máximo digitado."); return
        current = _criteria(keyword=keyword.strip(), city=city.strip(), region=region, states=states, nature=nature, srp=srp, modalities=modalities, minimum=minimum, maximum=maximum, portal=portal)
        st.session_state["essential_search_criteria"] = current
        st.session_state["essential_search_page"] = 1
        if usage is not None:
            usage.record_search(company_id, user.get("id", ""), keyword.strip())
        db.save_company_profile(company_id, search_keyword=keyword.strip(), search_nature=nature, service_states=", ".join(states), search_modalities="|".join(modalities), search_srp=_srp_profile_value(srp), search_minimum=minimum, search_maximum=maximum, search_order="Mais recentes")
    if not current:
        st.info("Digite uma palavra ou escolha um filtro para começar."); return
    if str(current.get("region") or "Brasil inteiro") != "Brasil inteiro":
        st.caption(f"Região: {current['region']} · UFs consideradas: {', '.join(_effective_states(current)) or 'nenhuma'}")
    with st.spinner("Buscando editais abertos..."):
        items = _query_catalog(db, current)
    st.markdown("### Editais abertos para participação")
    _render_results(db, user, items, page_key="essential_search_page", per_page=6)

def state_page(db, user: dict) -> None:
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

def city_page(db, user: dict) -> None:
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

def modality_page(db, user: dict) -> None:
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

def advanced_search_page(db, user: dict) -> None:
    _apply_styles()
    _page_header("REFINE SUA BUSCA", "Filtro avançado", "Combine os filtros que quiser. Nenhum campo é obrigatório.")
    with st.form("essential_advanced_search", clear_on_submit=False, enter_to_submit=False):
        r1, r2 = st.columns(2)
        region = r1.selectbox("Região", REGION_OPTIONS)
        states = r2.multiselect("Estados", list(BRAZIL_STATES), placeholder="Todos da região")
        city = st.text_input("Cidade", placeholder="Opcional")
        c1, c2, c3 = st.columns(3)
        nature = c1.selectbox("O que procura", NATURE_OPTIONS)
        srp = c2.selectbox("Registro de preços", SRP_OPTIONS)
        portal = c3.selectbox("Site da disputa", PORTAL_OPTIONS)
        modalities = st.multiselect("Modalidades", list(MODALITIES.keys()), placeholder="Todas")
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
                st.session_state["essential_search_criteria"] = _criteria(keyword=keyword.strip(), city=city.strip(), region=region, states=states, nature=nature, srp=srp, modalities=modalities, minimum=minimum, maximum=maximum, portal=portal, closing_from=start_date.isoformat(), closing_to=None if no_end else end_date.isoformat())
                st.session_state["essential_search_page"] = 1
                st.session_state["_navigation_request"] = "Buscar licitações"
                st.rerun()

def top50_page(db, user: dict) -> None:
    _apply_styles()
    _page_header("DESCUBRA OPORTUNIDADES", "Em destaque", "50 editais recentes para você explorar sem precisar definir uma busca.")
    items = db.list_global_catalog(
        closing_from=date.today().isoformat(), limit=50, order_by="recent"
    )
    _render_results(db, user, items, page_key="essential_top50_page", per_page=5)


def my_list_page(db, user: dict) -> None:
    _apply_styles()
    company_id = user["company_id"]
    _page_header("ORGANIZE SUAS OPORTUNIDADES", "Minha lista", "Decida apenas se vai participar, não vai participar ou quer descartar o edital.")
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
    _page_header("PERSONALIZE O LICITANEXO", "Preferências", "Se quiser, salve o que costuma procurar. Isso ajuda o Radar, mas não é obrigatório.")
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
    _page_header("ACOMPANHE O QUE IMPORTA", "Radar de licitações", "Veja editais novos relacionados ao que você escolheu acompanhar.")
    if not (defaults["keyword"].strip() or defaults["states"] or defaults["modalities"]):
        st.info("Você ainda não escolheu o que quer acompanhar. Continue usando a busca normalmente ou configure o Radar quando quiser.")
        if st.button("Configurar preferências", type="primary", width="stretch"):
            st.session_state["_navigation_request"] = "Preferências"
            st.rerun()
        return
    criteria = _criteria(
        keyword=defaults["keyword"], states=defaults["states"], modalities=defaults["modalities"]
    )
    items = _query_catalog(db, criteria, limit=500)
    if defaults["keyword"]:
        st.caption(f"Você acompanha: {defaults['keyword']}")
    _render_results(db, user, items, page_key="essential_radar_page", per_page=6)
