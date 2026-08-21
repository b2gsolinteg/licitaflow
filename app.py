from datetime import date, datetime, timedelta
import random
import re
import time
import base64
from html import escape
from zoneinfo import ZoneInfo
from pathlib import Path

import pandas as pd
import streamlit as st

from src.security_rc25 import SecurityService, SecurityError, RateLimitError, SessionExpiredError
from src.conversion import ConversionService
from src.usage import UsageService
from src.account_admin import AccountAdminService, AccountAdminError
from src.support import SupportService, SupportError
from src.billing import BillingService, BillingError
from src.commercial import CommercialFoundation
from src.config import (
    APP_NAME, APP_POSITIONING, APP_TAGLINE, APP_VERSION, COMPANY_SIGNATURE, ENVIRONMENT, LEGAL_VERSION,
    SUPPORT_EMAIL, database_path, is_admin,
)
try:
    from src.config import PUBLIC_PRICES_ENABLED
except ImportError:
    # Compatibilidade com instalações que preservaram o config.py da versão 0.7.x.
    # O laboratório permanece seguro e oculto para clientes.
    PUBLIC_PRICES_ENABLED = False
from src.database import Database
from src.formatters import format_brl, parse_brl
from src.exports import catalog_excel, catalog_pdf
from src.intelligence_ui import analysis_page
from src.legal import PRIVACY_TEXT, TERMS_TEXT
from src.pncp import MODALITIES, PncpClient
from src.pncp_items import PncpItemsError, fetch_contract_items
from src.radar_items import fetch_radar_item_summaries
from src.pipeline_ui import pipeline_page
from src.company_ui import company_page
from src.essential_discovery import (
    home_page as essential_home_page,
    search_page as essential_search_page,
    state_page as essential_state_page,
    city_page as essential_city_page,
    modality_page as essential_modality_page,
    portal_page as essential_portal_page,
    advanced_search_page as essential_advanced_search_page,
    top50_page as essential_top50_page,
    my_list_page as essential_my_list_page,
    preferences_page as essential_preferences_page,
    radar_page as essential_radar_page,
)
from src.company_intelligence import profile_search_ready, rank_opportunities
from src.sources import source_label, opportunity_source_and_portal, pncp_official_url
from src.logging_setup import configure_logging
def render_sidebar_guides(page: str) -> None:
    """Carrega a ajuda sob demanda; falha do PDF nunca derruba o app."""
    try:
        import src as _src  # garante o pacote-pai em reruns/hot reload do Streamlit
        from src.help_guides import render_sidebar_guides as _render_sidebar_guides
        _render_sidebar_guides(page)
    except Exception:
        st.caption("📘 Guia PDF temporariamente indisponível.")

from src.mailer import MailError, is_configured as mail_is_configured, mail_config, send_invitation, send_recovery_code, send_test_email


PROJECT_ROOT = Path(__file__).parent
LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo.png"
LOGIN_ART_PATH = PROJECT_ROOT / "assets" / "login-licitacoes.png"
st.set_page_config(page_title=APP_NAME, page_icon="🛡️", layout="wide", initial_sidebar_state="locked")
logger = configure_logging(PROJECT_ROOT, ENVIRONMENT)
db = Database(database_path(PROJECT_ROOT))
commercial = CommercialFoundation(db.path, 7)
billing = BillingService(db.path)
account_admin = AccountAdminService(db.path)
usage = UsageService(db.path)
conversion = ConversionService(db.path)
security = SecurityService(db.path, PROJECT_ROOT)
support = SupportService(db)
logger.info("Aplicação iniciada · versão %s · ambiente %s", APP_VERSION, ENVIRONMENT)


@st.cache_data(ttl=15, show_spinner=False)
def _cached_control_room_stats():
    """Evita repetir o mesmo painel administrativo em cada rerun do Streamlit."""
    return db.control_room_stats()


@st.cache_data(ttl=10, show_spinner=False)
def _cached_pending_access_requests():
    return db.count_access_requests()


@st.cache_data(ttl=900, show_spinner=False)
def _cached_radar_item_summaries(control_numbers):
    return fetch_radar_item_summaries(
        tuple(control_numbers or ()), max_workers=6, preview_items=4
    )


@st.cache_data(ttl=1800, show_spinner=False)
def _cached_full_contract_items(control_number):
    control_number = str(control_number or "").strip()
    if not control_number:
        return []
    return fetch_contract_items(control_number, timeout=12, page_size=200)


@st.cache_data(ttl=30, show_spinner=False)
def _cached_admin_pncp_snapshot():
    """Agrupa as leituras pesadas do catálogo em um snapshot curto e consistente."""
    try:
        modality_counts = db.global_catalog_modality_breakdown()
    except AttributeError:
        modality_counts = db.global_catalog_modality_counts()
    return {
        "stats": db.global_catalog_stats(),
        "last_update": db.last_catalog_update(),
        "recent_runs": db.list_sync_runs(10),
        "modality_counts": modality_counts,
        "state_counts": db.global_catalog_group_counts("state"),
        "quality": db.global_catalog_quality_stats(),
    }


def _client_ip():
    try:
        value=str(getattr(st.context,"ip_address","") or "")
        if value:return value
        headers=getattr(st.context,"headers",{}) or {}
        return str(headers.get("X-Forwarded-For") or headers.get("X-Real-IP") or "").split(",")[0].strip()
    except Exception:
        return ""


def _is_admin_user(user):
    return bool(user) and (db.user_is_admin(user) or is_admin(user.get("email", "")))

ADMIN_SECTIONS = (
    "Visão geral",
    "Conversão e retenção",
    "Empresas e usuários",
    "Assinaturas e pagamentos",
    "Consumo e IA",
    "Cupons e indicações",
    "Trials e antifraude",
    "PNCP e fontes",
    "Acessos e convites",
    "Atendimentos",
    "Recuperação",
    "E-mails",
    "Auditoria",
    "Segurança e compliance",
    "Sistema",
)

ADMIN_SECTION_LABELS = {
    "Visão geral": "🏠 Visão geral",
    "Conversão e retenção": "📈 Conversão e retenção",
    "Empresas e usuários": "🏢 Empresas e usuários",
    "Assinaturas e pagamentos": "💳 Assinaturas e pagamentos",
    "Consumo e IA": "🧠 Consumo e IA",
    "Cupons e indicações": "🎟️ Cupons e indicações",
    "Trials e antifraude": "🛡️ Trials e antifraude",
    "PNCP e fontes": "🌐 PNCP e fontes",
    "Acessos e convites": "🔑 Acessos e convites",
    "Atendimentos": "🤝 Atendimentos",
    "Recuperação": "🔐 Recuperação",
    "E-mails": "✉️ E-mails",
    "Auditoria": "🧾 Auditoria",
    "Segurança e compliance": "🔒 Segurança e compliance",
    "Sistema": "⚙️ Sistema",
}


MOTIVATIONAL_PHRASES = (
    "Cada edital bem analisado é uma decisão mais segura.",
    "Organização transforma oportunidades em resultados.",
    "Preparação hoje, competitividade no próximo certame.",
    "Grandes conquistas começam com uma análise cuidadosa.",
    "Consistência e atenção aos detalhes fazem a diferença.",
    "Uma oportunidade de cada vez, uma empresa mais forte a cada participação.",
)

OFFICIAL_PRICE_SOURCES = (
    ("Pesquisa de Preços — Compras.gov", "https://pesquisaprecos.compras.gov.br/"),
    ("Painel de Preços do Governo Federal", "https://paineldeprecos.planejamento.gov.br/"),
    ("PNCP — Atas de Registro de Preços", "https://pncp.gov.br/app/atas"),
    ("Portal da Transparência — Licitações", "https://portaldatransparencia.gov.br/licitacoes/consulta"),
)


def _format_datetime(value):
    if not value:
        return "Não informada"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(ZoneInfo("America/Sao_Paulo"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return str(value).replace("T", " ")[:16]


def _local_now():
    try:
        return datetime.now(ZoneInfo("America/Sao_Paulo"))
    except Exception:
        return datetime.now()


def _first_name(user):
    name = str(user.get("name") or "").strip()
    return name.split()[0].title() if name else ""


def _greeting(user):
    hour = _local_now().hour
    period = "Bom dia" if hour < 12 else "Boa tarde" if hour < 18 else "Boa noite"
    first_name = _first_name(user)
    return f"{period}, {first_name}" if first_name else period


def _radar_compatibility(profile, item):
    """Pontuação simples de aderência ao perfil; não representa chance de vitória."""
    # Primeiro eliminamos incompatibilidades óbvias de natureza. Uma empresa cadastrada
    # somente como Produtos não deve receber mão de obra/serviço puro com pontuação alta.
    profile_activity = str(profile.get("activity_type") or "Produtos")
    nature = _opportunity_nature(item)
    if profile_activity == "Produtos" and nature != "Produtos":
        return 0
    if profile_activity == "Serviços" and nature != "Serviços":
        return 0

    text = " ".join(str(item.get(k) or "") for k in ("object", "agency", "city", "modality")).lower()
    raw_keywords = str(profile.get("procurement_interests") or profile.get("interest_keywords") or profile.get("offerings") or "")
    stopwords = {
        "para", "com", "sem", "uma", "uns", "das", "dos", "que", "não", "nao", "tenho", "interesse",
        "empresa", "empresas", "licitação", "licitacao", "licitações", "licitacoes", "quero", "procuro",
        "fornecer", "vender", "prestar", "meu", "minha", "nosso", "nossa", "por", "em", "de", "do", "da",
    }
    keywords = []
    for part in raw_keywords.replace(";", ",").replace("\n", ",").split(","):
        phrase = part.strip().lower()
        if len(phrase) >= 4:
            keywords.append(phrase)
        for token in re.findall(r"[a-záàâãéêíóôõúç0-9-]+", phrase):
            if len(token) >= 4 and token not in stopwords:
                keywords.append(token)
    keywords = list(dict.fromkeys(keywords))
    keyword_hits = sum(1 for term in keywords[:50] if term in text)
    score = 0
    if keywords:
        score += min(60, keyword_hits * 20)
    states = {x.strip().upper() for x in str(profile.get("service_states") or "").replace(";", ",").split(",") if x.strip()}
    if states and str(item.get("state") or "").upper() in states:
        score += 20
    max_value = float(profile.get("max_contract_value") or 0)
    value = float(item.get("estimated_value") or 0)
    if max_value and value and value <= max_value:
        score += 20
    return min(score, 100)


def _compatibility_label(score):
    score = int(score or 0)
    if score >= 80:
        return "🟢 Excelente oportunidade"
    if score >= 50:
        return "🟡 Vale analisar"
    return "🔴 Baixa aderência"


def _compatibility_reasons(profile, item):
    """Explica a pontuação com regras simples, sem sugerir chance de vitória."""
    reasons = []
    profile_activity = str(profile.get("activity_type") or "Produtos")
    nature = _opportunity_nature(item)
    if profile_activity == "Produtos" and nature != "Produtos":
        return ["✖ Esta oportunidade não é exclusivamente de produtos; sua empresa está cadastrada somente como Produtos."]
    if profile_activity == "Serviços" and nature != "Serviços":
        return ["✖ Esta oportunidade não é exclusivamente de serviços; sua empresa está cadastrada somente como Serviços."]
    reasons.append(f"✔ Tipo compatível: {nature}" if nature in {profile_activity, "Produtos e serviços"} else f"⚠ Tipo identificado: {nature}")

    text = " ".join(str(item.get(k) or "") for k in ("object", "agency", "city", "modality")).lower()
    raw = str(profile.get("procurement_interests") or profile.get("interest_keywords") or profile.get("offerings") or "")
    tokens = [t for t in re.findall(r"[a-záàâãéêíóôõúç0-9-]+", raw.lower()) if len(t) >= 4]
    hits = [t for t in dict.fromkeys(tokens) if t in text][:5]
    if hits:
        reasons.append("✔ Termos do seu interesse encontrados: " + ", ".join(hits))
    elif raw.strip():
        reasons.append("⚠ Poucos termos do Passaporte aparecem no objeto desta oportunidade.")

    states = {x.strip().upper() for x in str(profile.get("service_states") or "").replace(";", ",").split(",") if x.strip()}
    state = str(item.get("state") or "").upper()
    if states:
        reasons.append(f"✔ UF atendida: {state}" if state in states else f"⚠ UF {state or 'não informada'} não está entre as UFs cadastradas no Passaporte.")

    max_value = float(profile.get("max_contract_value") or 0)
    value = float(item.get("estimated_value") or 0)
    if max_value and value:
        reasons.append("✔ Valor dentro da capacidade informada." if value <= max_value else "⚠ Valor acima da capacidade de contrato informada.")
    return reasons[:4]


BRAZIL_STATES = (
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
)

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

def _opportunity_nature(item):
    """Classifica de forma conservadora para não oferecer serviço a quem vende só produtos."""
    text = re.sub(r"\s+", " ", str(item.get("object") or "").lower()).strip()

    # Âncoras explícitas têm prioridade sobre palavras soltas. Ex.: seguro de veículos é serviço,
    # embora a palavra "veículos" apareça no objeto; manutenção de equipamentos também é serviço.
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

def _nature_matches(item, wanted):
    nature = _opportunity_nature(item)
    if wanted == "Todos":
        return True
    if wanted == "Produtos e serviços":
        return nature in {"Produtos", "Serviços", "Produtos e serviços"}
    # Filtro estrito: quem pede somente Produtos não recebe oportunidade mista com execução
    # de serviços; quem pede somente Serviços não recebe contratação mista com fornecimento.
    return nature == wanted


def _document_alerts(company_id):
    today = _local_now().date()
    expired, expiring = [], []
    for row in db.list_company_documents(company_id):
        if row.get("applicable") != "Sim" or not row.get("expiry_date"):
            continue
        try:
            expiry = datetime.fromisoformat(str(row["expiry_date"])[:10]).date()
        except (TypeError, ValueError):
            continue
        item = (row.get("document_type") or "Documento", expiry)
        if expiry < today:
            expired.append(item)
        elif expiry <= today + timedelta(days=30):
            expiring.append(item)
    return sorted(expired, key=lambda item: item[1]), sorted(expiring, key=lambda item: item[1])


def apply_brand():
    st.markdown("""
        <style>
        :root{--ln-navy:#0B2944;--ln-teal:#0E7C75;--ln-teal-dark:#0A655F;--ln-bg:#F4F7FA;--ln-card:#FFFFFF;--ln-text:#172B3A;--ln-muted:#667786;--ln-border:#DEE6EC;}
        html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{font-family:Inter,"Segoe UI",Arial,sans-serif !important;color:var(--ln-text) !important;}
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--ln-bg) !important;}
        header[data-testid="stHeader"]{display:block !important;background:var(--ln-navy) !important;height:58px !important;border-bottom:1px solid rgba(255,255,255,.08) !important;box-shadow:0 1px 10px rgba(7,29,48,.10) !important;}
        [data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none !important;}
        [data-testid="stSidebar"]{background:#FFFFFF !important;border-right:1px solid #E2E8EE !important;box-shadow:2px 0 14px rgba(25,39,52,.035) !important;}
        [data-testid="stSidebar"] *{color:#223544 !important;}
        [data-testid="stSidebar"] > div:first-child{overflow-y:auto !important;overflow-x:hidden !important;max-height:100vh !important;padding-bottom:1rem !important;}
        @media(min-width:901px){[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:276px !important;min-width:276px !important;max-width:276px !important;}}
        [data-testid="stSidebar"] .stButton button{width:100% !important;min-height:3.55rem !important;justify-content:flex-start !important;background:transparent !important;color:#223544 !important;border:1px solid transparent !important;border-radius:13px !important;box-shadow:none !important;padding:.38rem .55rem !important;gap:.72rem !important;font-size:.91rem !important;font-weight:650 !important;transition:background .15s ease,border-color .15s ease,transform .15s ease !important;}
        [data-testid="stSidebar"] .stButton button:hover{background:#F7F9FB !important;border-color:#E7ECF0 !important;transform:translateX(1px);}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#F1F7F6 !important;color:#0D5F5A !important;border-color:#D6E8E5 !important;box-shadow:inset 3px 0 0 #16877F !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{display:inline-flex !important;align-items:center !important;justify-content:center !important;flex:0 0 2.75rem !important;width:2.75rem !important;height:2.75rem !important;border-radius:13px !important;background:#F2F5F7 !important;color:#58717F !important;font-size:1.35rem !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_0 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_1 [data-testid="stIconMaterial"]{background:#E4F4EE !important;color:#248466 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_2 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_3 [data-testid="stIconMaterial"]{background:#E7EFFB !important;color:#3E70B7 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_4 [data-testid="stIconMaterial"], [data-testid="stSidebar"] .st-key-nav_explore_5 [data-testid="stIconMaterial"]{background:#EEE9F8 !important;color:#765BA0 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_6 [data-testid="stIconMaterial"]{background:#FFF2CF !important;color:#A87822 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_7 [data-testid="stIconMaterial"]{background:#FBE8E8 !important;color:#A85C5C !important;}
        [data-testid="stSidebar"] .st-key-nav_work_0 [data-testid="stIconMaterial"]{background:#F5E7F0 !important;color:#93627D !important;}
        [data-testid="stSidebar"] .st-key-nav_work_1 [data-testid="stIconMaterial"]{background:#E7F3F5 !important;color:#357F88 !important;}
        [data-testid="stSidebar"] .st-key-nav_account_0 [data-testid="stIconMaterial"]{background:#E8F1FB !important;color:#4478B4 !important;}
        [data-testid="stSidebar"] .st-key-nav_account_1 [data-testid="stIconMaterial"]{background:#E9F4E5 !important;color:#5F8A4B !important;}
        [data-testid="stSidebar"] .st-key-nav_account_2 [data-testid="stIconMaterial"]{background:#FFF0E1 !important;color:#A66D35 !important;}
        [data-testid="stSidebar"] .st-key-nav_account_3 [data-testid="stIconMaterial"]{background:#E9EFF7 !important;color:#526F94 !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{margin-top:.8rem !important;margin-bottom:.18rem !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.70rem !important;font-weight:750 !important;letter-spacing:.10em !important;text-transform:uppercase !important;color:#8A9AA8 !important;}
        [data-testid="stSidebar"] [data-testid="stImage"] img{max-width:188px !important;width:188px !important;margin:.35rem auto .1rem !important;display:block !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout button{justify-content:center !important;min-height:2.8rem !important;background:#F7F9FB !important;border:1px solid #E1E8ED !important;color:#536675 !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout [data-testid="stIconMaterial"]{background:transparent !important;width:auto !important;height:auto !important;flex:0 0 auto !important;border-radius:0 !important;color:#6E7F8C !important;}
        .block-container{padding-top:1.5rem !important;padding-bottom:2.6rem !important;max-width:1220px !important;}
        div[data-testid="stVerticalBlockBorderWrapper"],div[data-testid="stMetric"]{background:#FFFFFF !important;border:1px solid #DEE6EC !important;border-radius:16px !important;box-shadow:0 4px 16px rgba(31,52,69,.045) !important;}
        [data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"] > div,textarea{background:#FFFFFF !important;color:#243746 !important;border-color:#CCD7DF !important;border-radius:11px !important;box-shadow:none !important;}
        input,textarea{background:#FFFFFF !important;color:#243746 !important;-webkit-text-fill-color:#243746 !important;}
        .stButton>button,.stDownloadButton>button{background:#FFFFFF !important;color:#263947 !important;border:1px solid #CCD7DF !important;border-radius:11px !important;box-shadow:none !important;font-weight:600 !important;}
        .stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:var(--ln-teal) !important;color:#FFFFFF !important;border-color:var(--ln-teal) !important;box-shadow:0 3px 8px rgba(14,124,117,.13) !important;}
        .stButton>button[kind="primary"]:hover,.stDownloadButton>button[kind="primary"]:hover{background:var(--ln-teal-dark) !important;border-color:var(--ln-teal-dark) !important;}
        .brand-mark{font-size:2.1rem;color:#293746;line-height:1}.brand-mark span{color:#5F858A}.brand-tagline{color:#667786;margin-top:.45rem;margin-bottom:1.4rem}
        @media(max-width:900px){header[data-testid="stHeader"]{height:50px !important;}.block-container{padding-top:.9rem !important;padding-left:.8rem !important;padding-right:.8rem !important;}.stButton button,.stDownloadButton button{min-height:2.65rem;}}
        /* RC31.18 exact reference shell */
        :root{--ref-navy:#0A1D34;--ref-blue:#2D5FE8;--ref-blue-hover:#244FCB;--ref-green:#20BF63;--ref-bg:#F1F4F8;--ref-card:#FFFFFF;--ref-border:#E5EAF0;--ref-text:#142033;--ref-muted:#65758A;}
        html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{font-family:"Poppins","Inter","Segoe UI",Arial,sans-serif !important;color:var(--ref-text) !important;}
        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--ref-bg) !important;}
        header[data-testid="stHeader"]{display:block !important;height:48px !important;min-height:48px !important;background:var(--ref-navy) !important;border:0 !important;box-shadow:0 2px 8px rgba(10,29,52,.14) !important;z-index:999990 !important;}
        [data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none !important;}
        .ln-app-topbar{position:fixed !important;top:0 !important;left:240px !important;right:0 !important;height:48px !important;z-index:999999 !important;display:flex !important;align-items:center !important;justify-content:space-between !important;padding:0 16px 0 18px !important;pointer-events:none !important;color:#FFFFFF !important;}
        .ln-app-topbar-menu{font-size:1.25rem !important;line-height:1 !important;color:#FFFFFF !important;font-weight:400 !important;letter-spacing:-.08em !important;}
        .ln-app-topbar-account{display:inline-flex !important;align-items:center !important;min-height:29px !important;padding:0 13px !important;border:1px solid rgba(255,255,255,.22) !important;border-radius:999px !important;background:rgba(255,255,255,.08) !important;color:#FFFFFF !important;font-size:.72rem !important;font-weight:650 !important;}
        [data-testid="stIconMaterial"],.material-symbols-rounded,.material-symbols-outlined{font-family:"Material Symbols Rounded","Material Symbols Outlined" !important;}
        .block-container{max-width:860px !important;padding:1rem .75rem 2rem !important;}
        [data-testid="stMain"] h1{font-size:1.28rem !important;line-height:1.18 !important;color:#111827 !important;font-weight:700 !important;letter-spacing:-.018em !important;}
        [data-testid="stMain"] h2{font-size:1.05rem !important;line-height:1.22 !important;color:#111827 !important;font-weight:700 !important;}
        [data-testid="stMain"] h3{font-size:.92rem !important;color:#111827 !important;font-weight:700 !important;}
        [data-testid="stMain"] p,[data-testid="stMain"] label p,[data-testid="stMain"] .stCaption p{font-size:.77rem !important;color:var(--ref-muted) !important;}
        [data-testid="stSidebar"]{background:#FFFFFF !important;border-right:1px solid #E3E8EE !important;box-shadow:none !important;z-index:999995 !important;}
        @media(min-width:901px){[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:240px !important;min-width:240px !important;max-width:240px !important;}}
        [data-testid="stSidebar"] > div:first-child{overflow-y:auto !important;overflow-x:hidden !important;max-height:100vh !important;padding:58px 12px 62px !important;}
        .ln-sidebar-brand{position:fixed !important;top:0 !important;left:0 !important;width:240px !important;height:48px !important;z-index:999999 !important;background:var(--ref-navy) !important;display:flex !important;align-items:center !important;padding:0 12px !important;border-right:1px solid rgba(255,255,255,.08) !important;}
        .ln-sidebar-brand img{display:block !important;width:auto !important;max-width:112px !important;max-height:28px !important;filter:brightness(0) invert(1) !important;object-fit:contain !important;}
        .ln-sidebar-brand-text{color:#FFFFFF !important;font-size:.91rem !important;font-weight:750 !important;letter-spacing:-.02em !important;}
        [data-testid="stSidebar"] .stButton{margin:0 0 .16rem !important;}
        [data-testid="stSidebar"] .stButton button{width:100% !important;min-height:2.45rem !important;justify-content:flex-start !important;background:transparent !important;color:#172033 !important;border:0 !important;border-radius:7px !important;box-shadow:none !important;padding:.16rem .2rem !important;gap:.52rem !important;font-size:.77rem !important;font-weight:600 !important;transition:background .12s ease !important;}
        [data-testid="stSidebar"] .stButton button:hover{background:#F6F8FA !important;border:0 !important;transform:none !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:transparent !important;color:#111827 !important;border:0 !important;box-shadow:none !important;font-weight:700 !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{display:inline-flex !important;align-items:center !important;justify-content:center !important;flex:0 0 2rem !important;width:2rem !important;height:2rem !important;border-radius:9px !important;background:#F2F4F7 !important;color:#66788B !important;font-size:1rem !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"] [data-testid="stIconMaterial"]{background:#DDF8E6 !important;color:#21A95A !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_0 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_1 [data-testid="stIconMaterial"]{background:#DDF8E6 !important;color:#24A95A !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_2 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_3 [data-testid="stIconMaterial"]{background:#E3EDFF !important;color:#3974E1 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_4 [data-testid="stIconMaterial"],[data-testid="stSidebar"] .st-key-nav_explore_5 [data-testid="stIconMaterial"]{background:#EFE7FF !important;color:#845CCB !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_6 [data-testid="stIconMaterial"]{background:#FFF1CB !important;color:#DB8E19 !important;}
        [data-testid="stSidebar"] .st-key-nav_explore_7 [data-testid="stIconMaterial"]{background:#FFE6E8 !important;color:#C55E68 !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{margin:.48rem 0 .12rem !important;}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{font-size:.55rem !important;font-weight:750 !important;letter-spacing:.10em !important;text-transform:uppercase !important;color:#97A4B3 !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout{position:fixed !important;left:12px !important;bottom:12px !important;width:216px !important;z-index:999999 !important;margin:0 !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout button{min-height:2.25rem !important;justify-content:center !important;background:var(--ref-green) !important;color:#FFFFFF !important;border:0 !important;border-radius:8px !important;font-size:.75rem !important;font-weight:700 !important;box-shadow:none !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout button *{color:#FFFFFF !important;}
        [data-testid="stSidebar"] .st-key-sidebar_logout [data-testid="stIconMaterial"]{display:none !important;}
        div[data-testid="stVerticalBlockBorderWrapper"],div[data-testid="stMetric"]{background:#FFFFFF !important;border:1px solid var(--ref-border) !important;border-radius:10px !important;box-shadow:0 3px 10px rgba(20,38,60,.05) !important;}
        [data-testid="stForm"]{background:#FFFFFF !important;border:1px solid var(--ref-border) !important;border-radius:10px !important;padding:.7rem .75rem .65rem !important;box-shadow:0 3px 10px rgba(20,38,60,.045) !important;}
        [data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"] > div,textarea{background:#FFFFFF !important;color:#263544 !important;border-color:#DCE3EA !important;border-radius:7px !important;box-shadow:none !important;}
        input,textarea{background:#FFFFFF !important;color:#263544 !important;-webkit-text-fill-color:#263544 !important;font-size:.78rem !important;}
        [data-testid="stMain"] .stButton>button,[data-testid="stMain"] .stDownloadButton>button{min-height:2.2rem !important;background:#FFFFFF !important;color:#263544 !important;border:1px solid #D8E0E8 !important;border-radius:7px !important;box-shadow:none !important;font-size:.75rem !important;font-weight:650 !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"],[data-testid="stMain"] .stDownloadButton>button[kind="primary"],[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button{background:var(--ref-blue) !important;color:#FFFFFF !important;border-color:var(--ref-blue) !important;box-shadow:0 2px 5px rgba(45,95,232,.18) !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"] *,[data-testid="stMain"] .stDownloadButton>button[kind="primary"] *,[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button *{color:#FFFFFF !important;}
        [data-testid="stMain"] .stButton>button[kind="primary"]:hover,[data-testid="stMain"] div[data-testid="stFormSubmitButton"] button:hover{background:var(--ref-blue-hover) !important;border-color:var(--ref-blue-hover) !important;}
        [data-testid="stTabs"] [data-baseweb="tab-list"]{gap:.18rem !important;border-bottom:1px solid #E3E8EF !important;}
        [data-testid="stTabs"] button{font-size:.76rem !important;font-weight:650 !important;}
        [data-testid="stExpander"]{background:#FFFFFF !important;border:1px solid var(--ref-border) !important;border-radius:9px !important;}
        [data-testid="stAlert"]{border-radius:9px !important;}
        [data-testid="stDataFrame"],[data-testid="stTable"]{background:#FFFFFF !important;border-radius:9px !important;overflow:hidden !important;}
        @media(max-width:900px){header[data-testid="stHeader"]{height:44px !important;min-height:44px !important;}.ln-app-topbar{left:0 !important;height:44px !important;}.ln-sidebar-brand{height:44px !important;}[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:225px !important;min-width:225px !important;max-width:225px !important;}.block-container{max-width:100% !important;padding:.72rem .6rem 1.5rem !important;}}

        
        /* RC31.19 navigation density */
        :root{--rc19-sidebar:276px;}
        @media(min-width:901px){
            [data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child{width:var(--rc19-sidebar) !important;min-width:var(--rc19-sidebar) !important;max-width:var(--rc19-sidebar) !important;}
        }
        .ln-app-topbar{left:var(--rc19-sidebar) !important;}
        [data-testid="stSidebar"] > div:first-child{padding:60px 12px 78px !important;}
        .ln-sidebar-brand{width:var(--rc19-sidebar) !important;padding:0 16px !important;}
        .ln-sidebar-brand img{max-width:150px !important;max-height:32px !important;}
        [data-testid="stSidebar"] .stCaption p{font-size:.72rem !important;font-weight:750 !important;letter-spacing:.08em !important;color:#91A0B3 !important;text-transform:uppercase !important;}
        [data-testid="stSidebar"] .stButton{margin:0 0 .24rem !important;}
        [data-testid="stSidebar"] .stButton button{min-height:3.12rem !important;padding:.28rem .5rem !important;gap:.72rem !important;font-size:.96rem !important;font-weight:650 !important;text-align:left !important;justify-content:flex-start !important;}
        [data-testid="stSidebar"] .stButton button p{font-size:.96rem !important;font-weight:650 !important;line-height:1.18 !important;text-align:left !important;}
        [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{flex:0 0 2.25rem !important;width:2.25rem !important;height:2.25rem !important;border-radius:10px !important;font-size:1.08rem !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"]{background:#EEF9F5 !important;box-shadow:inset 3px 0 0 #18A77B !important;color:#10253F !important;}
        [data-testid="stSidebar"] .stButton button[kind="primary"] [data-testid="stIconMaterial"]{background:#DDF5EA !important;color:#10865F !important;}
        .ln-home-color-logo{margin:0 0 .7rem !important;}
        @media(max-width:900px){.ln-app-topbar{left:0 !important;}.ln-sidebar-brand{width:225px !important;}[data-testid="stSidebar"] .stButton button,[data-testid="stSidebar"] .stButton button p{font-size:.9rem !important;}}

        </style>
    """, unsafe_allow_html=True)

def brand_header(compact=False):
    if LOGO_PATH.exists():
        # O arquivo é recortado no pacote Essential para eliminar margens vazias.
        st.image(str(LOGO_PATH), width=330 if not compact else 210)
    else:
        st.markdown(
            '<div class="brand-mark">Licita<span>Nexo</span></div>',
            unsafe_allow_html=True,
        )
    if not compact:
        st.markdown(
            '<div style="font-size:1.08rem;font-weight:700;margin:.15rem 0 .25rem 0">'
            'Encontre editais. Veja os itens. Decida.</div>'
            '<div style="color:#8FA0B6;font-size:.9rem;margin-bottom:.65rem">'
            'LicitaNexo · um produto da B2G SaaS</div>',
            unsafe_allow_html=True,
        )


def login_page():
    """Tela pública de entrada — RC31.11: valor do Essential e linguagem para iniciantes."""
    st.markdown(
        """<style>
        html, body, [data-testid="stAppViewContainer"], .stApp {margin:0 !important;padding:0 !important;background:#F4F7FA !important;min-height:100vh !important;color:#172B3A !important;overflow:auto !important;font-family:Inter,"Segoe UI",Arial,sans-serif !important;}
        header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none !important;height:0 !important;}
        .block-container{max-width:1180px !important;width:100% !important;margin:0 auto !important;padding:3.4rem 2rem !important;}
        [data-testid="stAppViewContainer"] *{font-weight:400 !important;}
        div[data-testid="stHorizontalBlock"]{gap:3rem !important;align-items:center !important;}
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]{background:transparent !important;padding:0 !important;}
        .ln-login-eyebrow{display:inline-flex;align-items:center;background:#E5F4EF;color:#23715D;border:1px solid #CDE8DE;border-radius:999px;padding:.28rem .58rem;font-size:.70rem;font-weight:750 !important;letter-spacing:.07em;margin:.75rem 0 .7rem}.ln-login-intro{color:#152B3B;font-size:2.2rem;line-height:1.14;margin:.2rem 0 .75rem;font-weight:750 !important;letter-spacing:-.025em;}
        .ln-login-copy{color:#667786;font-size:1rem;line-height:1.55;max-width:32rem;}
        .ln-login-value{margin:1.15rem 0 0;display:grid;gap:.55rem;max-width:31rem;}
        .ln-login-value-item{display:flex;align-items:center;gap:.65rem;color:#526371;font-size:.9rem;}
        .ln-login-value-dot{width:1.75rem;height:1.75rem;border-radius:8px;background:#EAF3EF;color:#4F846E;display:flex;align-items:center;justify-content:center;font-size:.72rem;}
        .ln-price{text-align:left;line-height:1.15;margin:0 0 1rem;}
        .ln-price span{display:inline;color:#667786;font-size:.82rem;margin-right:.35rem;}
        .ln-price strong,.ln-price small{color:#486F74;font-size:1rem;font-weight:400 !important;}
        .st-key-auth_card{width:100% !important;max-width:560px !important;margin:0 auto !important;padding:1.45rem 1.55rem 1.55rem !important;background:#FFFFFF !important;border:1px solid #DCE5EB !important;border-radius:18px !important;box-shadow:0 18px 45px rgba(25,45,61,.08) !important;}
        .st-key-auth_card > div,.st-key-auth_card [data-testid="stVerticalBlock"]{background:transparent !important;}
        .ln-auth-nav{display:grid !important;grid-template-columns:repeat(4,minmax(0,1fr)) !important;width:100% !important;gap:.25rem !important;margin:0 0 1rem !important;}
        .ln-auth-nav a{display:flex !important;align-items:center !important;justify-content:center !important;min-height:2.7rem !important;padding:.35rem .1rem !important;color:#526371 !important;font-size:.76rem !important;text-align:center !important;text-decoration:none !important;border:1px solid #DCE3E8 !important;border-radius:8px !important;background:#FFFFFF !important;}
        .ln-auth-nav a.active{color:#0C625D !important;border-color:#B7D8D4 !important;background:#EDF7F5 !important;font-weight:650 !important;}
        .st-key-auth_card label,.st-key-auth_card label p,.st-key-auth_card p,.st-key-auth_card span{color:#293746 !important;}
        .st-key-auth_card [data-baseweb="input"],.st-key-auth_card [data-baseweb="base-input"],.st-key-auth_card [data-testid="stTextInput"] > div > div{background:#FFFFFF !important;border-color:#C8D3DB !important;color:#293746 !important;border-radius:9px !important;}
        .st-key-auth_card input{background:#FFFFFF !important;color:#293746 !important;min-height:3rem !important;caret-color:#293746 !important;-webkit-text-fill-color:#293746 !important;}
        .st-key-auth_card input::placeholder{color:#8A98A5 !important;-webkit-text-fill-color:#8A98A5 !important;opacity:1 !important;}
        .st-key-auth_card [data-testid="stForm"]{background:#FFFFFF !important;border:0 !important;padding:0 !important;}
        .st-key-auth_card .stFormSubmitButton button{min-height:3.15rem !important;border-radius:11px !important;background:#0E7C75 !important;color:#FFFFFF !important;border:1px solid #0E7C75 !important;box-shadow:0 4px 12px rgba(14,124,117,.14) !important;font-size:.95rem !important;font-weight:650 !important;}
        .ln-forgot{text-align:right;margin-top:-2rem;margin-bottom:1rem;padding-right:.1rem;font-size:.78rem;color:#486F74;position:relative;z-index:4;}
        .ln-forgot a{color:#486F74 !important;text-decoration:none !important;}
        .ln-login-footer{width:100%;max-width:560px;margin:1rem auto 0;color:#667786;text-align:center;font-size:.82rem;line-height:1.5;}
        .ln-login-footer strong{color:#486F74 !important;font-weight:400 !important;}
        .ln-trial-seal{width:100%;margin:.1rem auto .75rem;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center;background:transparent;border:0;box-shadow:none;padding:0;}
        .ln-trial-seal .seal-badge{width:auto;height:auto;display:block;border-radius:8px;color:#526371;background:#F4F7F9;border:1px solid #DCE3E8;box-shadow:none;font-weight:400 !important;line-height:1.3;margin-bottom:.5rem;padding:.45rem .7rem;}
        .ln-trial-seal .seal-badge::before,.ln-trial-seal .seal-badge::after,.ln-trial-seal .seal-stars{display:none !important;}
        .ln-trial-seal .seal-days,.ln-trial-seal .seal-free{display:inline;font-size:.9rem;letter-spacing:0;color:#526371;background:transparent;padding:0;margin:0 .1rem;border-radius:0;}
        .ln-trial-seal .seal-copy{color:#667786;font-size:.88rem;line-height:1.4;text-align:center;}
        .ln-trial-seal .seal-copy strong{color:#486F74;font-size:.88rem;font-weight:400 !important;}
        .ln-login-footer .dev{margin-top:.15rem;padding-top:.6rem;border-top:1px solid #E3E8ED;}
        @media(max-width:800px){.block-container{padding:1.5rem 1rem !important;}div[data-testid="stHorizontalBlock"]{display:block !important;}.ln-login-intro,.ln-login-copy{text-align:center;margin-left:auto;margin-right:auto;}.ln-price{text-align:center;margin-top:1rem;}.st-key-auth_card,.ln-login-footer{max-width:560px !important;margin-left:auto !important;margin-right:auto !important;}.ln-auth-nav{grid-template-columns:repeat(2,minmax(0,1fr)) !important;}}
        </style>""",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1], gap="large")

    with left:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=300)
        st.markdown('<div class="ln-login-eyebrow">LICITANEXO ESSENTIAL</div>', unsafe_allow_html=True)
        st.markdown('<div class="ln-login-intro">Encontre oportunidades para vender ao governo.</div>', unsafe_allow_html=True)
        st.markdown('<div class="ln-login-copy">Você não precisa adivinhar o que vender. Veja primeiro o que o governo está comprando e encontre oportunidades de forma simples.</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="ln-login-value">'
            '<div class="ln-login-value-item"><span class="ln-login-value-dot">01</span><span>Editais com os itens da compra já abertos na busca</span></div>'
            '<div class="ln-login-value-item"><span class="ln-login-value-dot">02</span><span>Pesquisa simples em todo o Brasil</span></div>'
            '<div class="ln-login-value-item"><span class="ln-login-value-dot">03</span><span>Salve as oportunidades e organize os certames</span></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<div class="ln-price"><span>Planos a partir de</span>'
            '<strong>R$ 29,90</strong><small>/mês</small></div>',
            unsafe_allow_html=True,
        )

        raw_mode = st.query_params.get("auth", "login")
        if isinstance(raw_mode, list):
            raw_mode = raw_mode[0] if raw_mode else "login"
        mode = str(raw_mode or "login").strip().lower()
        if mode not in {"login", "request", "invite", "recovery"}:
            mode = "login"

        nav_items = [
            ("login", "Entrar"),
            ("request", "Solicitar acesso"),
            ("invite", "Ativar convite"),
            ("recovery", "Recuperar senha"),
        ]
        nav_html = '<div class="ln-auth-nav">' + ''.join(
            f'<a class="{"active" if key == mode else ""}" href="?auth={key}">{label}</a>'
            for key, label in nav_items
        ) + '</div>'

        with st.container(border=False, key="auth_card"):
            st.markdown(nav_html, unsafe_allow_html=True)

            if mode == "login":
                with st.form("login", clear_on_submit=False, enter_to_submit=False):
                    email = st.text_input("E-mail", placeholder="seu@email.com")
                    password = st.text_input("Senha", type="password", placeholder="Sua senha")
                    st.markdown('<div class="ln-forgot"><a href="?auth=recovery">Esqueceu a senha?</a></div>', unsafe_allow_html=True)
                    if st.form_submit_button("→  Entrar no LicitaNexo", width="stretch"):
                        client_ip = _client_ip()
                        try:
                            security.precheck("login", email, client_ip)
                            user = db.authenticate(email, password)
                            if user:
                                security.register_attempt("login", email, client_ip, success=True)
                                token = security.create_session(user.get("company_id",""), user.get("id",""))
                                conversion.record_event("login", user.get("company_id",""), user.get("id",""), {"email":user.get("email","")})
                                st.session_state.user = user
                                st.session_state.security_session_token = token
                                st.session_state.motivational_phrase = random.choice(MOTIVATIONAL_PHRASES)
                                st.session_state.just_logged_in = True
                                st.rerun()
                            security.register_attempt("login", email, client_ip, success=False)
                            st.error("E-mail ou senha inválidos.")
                        except RateLimitError as error:
                            st.warning(str(error))

            elif mode == "request":
                st.caption("Comece com 7 dias grátis, sem cartão. Depois, escolha sua forma de contratação.")
                with st.form("access_request", clear_on_submit=False, enter_to_submit=False):
                    company = st.text_input("Empresa / Razão social")
                    cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
                    name = st.text_input("Seu nome")
                    email = st.text_input("E-mail profissional", key="request_email")
                    whatsapp = st.text_input("WhatsApp", placeholder="(00) 00000-0000")
                    segment = st.text_input("Segmento da empresa", placeholder="Ex.: materiais hospitalares")
                    campaign_code = st.text_input(
                        "Código de indicação ou cupom (opcional)",
                        placeholder="Ex.: JOSE10 ou B2GSP",
                    )
                    if st.form_submit_button("Solicitar acesso", width="stretch"):
                        try:
                            client_ip = ""
                            try:
                                client_ip = str(getattr(st.context, "ip_address", "") or "")
                                if not client_ip:
                                    headers = getattr(st.context, "headers", {}) or {}
                                    client_ip = str(headers.get("X-Forwarded-For") or headers.get("X-Real-IP") or "").split(",")[0].strip()
                            except Exception:
                                client_ip = ""
                            security.precheck("access_request", email, client_ip)
                            decision = commercial.evaluate_trial(cnpj, email, client_ip)
                            if not decision.allowed:
                                commercial.record_trial_request(cnpj, email, client_ip, decision.outcome, decision.risk_score)
                                raise ValueError(decision.message)
                            risk = db.request_access(
                                company, name, email, whatsapp, segment,
                                cnpj=cnpj, client_ip=client_ip, campaign_code=campaign_code,
                            )
                            final_outcome = "review" if (decision.outcome == "review" or risk.get("outcome") == "review") else "allowed"
                            commercial.record_trial_request(cnpj, email, client_ip, final_outcome, max(decision.risk_score, int(risk.get("risk_score") or 0)))
                            security.register_attempt("access_request", email, client_ip, success=True)
                            if risk.get("outcome") == "review":
                                st.success(
                                    "Solicitação recebida. Para sua segurança, a liberação passará "
                                    "por uma validação rápida da equipe B2G SaaS."
                                )
                            else:
                                st.success(
                                    "Solicitação recebida. Seu teste é de 7 dias, sem cartão. "
                                    "A equipe B2G SaaS fará o contato."
                                )
                        except RateLimitError as error:
                            st.warning(str(error))
                        except ValueError as error:
                            st.warning(str(error))

            elif mode == "invite":
                st.caption("Recebeu um convite? Informe o código enviado pela B2G SaaS.")
                with st.form("activate_invitation", clear_on_submit=False, enter_to_submit=False):
                    email = st.text_input(
                        "E-mail do convite",
                        placeholder="seu@email.com",
                    )
                    invitation_code = st.text_input(
                        "Código de acesso",
                        placeholder="NX-XXXXXXXX",
                    )
                    password = st.text_input(
                        "Crie sua senha",
                        type="password",
                        placeholder="Mínimo de 8 caracteres",
                    )
                    password_confirmation = st.text_input(
                        "Confirme sua senha",
                        type="password",
                    )
                    if st.form_submit_button("→  Ativar convite", width="stretch"):
                        client_ip = _client_ip()
                        normalized_email = str(email or "").strip().lower()
                        try:
                            if not normalized_email or not str(invitation_code or "").strip():
                                raise ValueError("Informe o e-mail e o código de acesso do convite.")
                            if len(str(password or "")) < 8:
                                raise ValueError("A senha deve ter pelo menos 8 caracteres.")
                            if password != password_confirmation:
                                raise ValueError("As senhas não coincidem.")

                            security.precheck("invitation_activation", normalized_email, client_ip)
                            user = db.activate_invitation(
                                normalized_email,
                                invitation_code,
                                password,
                            )
                            if not user:
                                raise ValueError("Não foi possível ativar o convite.")

                            security.register_attempt(
                                "invitation_activation",
                                normalized_email,
                                client_ip,
                                success=True,
                            )
                            token = security.create_session(
                                user.get("company_id", ""),
                                user.get("id", ""),
                            )
                            st.session_state.user = user
                            st.session_state.security_session_token = token
                            st.session_state.motivational_phrase = random.choice(MOTIVATIONAL_PHRASES)
                            st.session_state.just_logged_in = True
                            st.rerun()
                        except RateLimitError as error:
                            st.warning(str(error))
                        except ValueError as error:
                            security.register_attempt(
                                "invitation_activation",
                                normalized_email,
                                client_ip,
                                success=False,
                            )
                            st.warning(str(error))

            else:
                st.caption("Solicite um código e depois crie uma nova senha.")
                with st.expander("1. Solicitar código de recuperação", expanded=True):
                    with st.form("password_recovery_request", clear_on_submit=False, enter_to_submit=False):
                        recovery_email = st.text_input(
                            "E-mail cadastrado",
                            placeholder="seu@email.com",
                            key="password_recovery_request_email",
                        )
                        if st.form_submit_button("Solicitar recuperação", width="stretch"):
                            normalized_email = str(recovery_email or "").strip().lower()
                            client_ip = _client_ip()
                            try:
                                security.precheck("password_recovery_request", normalized_email, client_ip)
                                db.request_password_reset(normalized_email)
                                security.register_attempt(
                                    "password_recovery_request", normalized_email, client_ip, success=True,
                                )
                                st.success(
                                    "Solicitação registrada. Se o e-mail estiver cadastrado, "
                                    "a equipe de suporte poderá gerar seu código de recuperação."
                                )
                            except RateLimitError as error:
                                st.warning(str(error))
                            except ValueError as error:
                                st.warning(str(error))

                with st.expander("2. Usar código e redefinir senha", expanded=False):
                    with st.form("password_recovery_reset", clear_on_submit=False, enter_to_submit=False):
                        reset_email = st.text_input(
                            "E-mail cadastrado",
                            placeholder="seu@email.com",
                            key="password_recovery_reset_email",
                        )
                        recovery_code = st.text_input(
                            "Código de recuperação",
                            placeholder="NX-R-XXXXXXXX",
                        )
                        new_password = st.text_input(
                            "Nova senha", type="password", placeholder="Mínimo de 8 caracteres",
                        )
                        new_password_confirmation = st.text_input(
                            "Confirme a nova senha", type="password",
                        )
                        if st.form_submit_button("Redefinir senha", width="stretch"):
                            normalized_email = str(reset_email or "").strip().lower()
                            client_ip = _client_ip()
                            try:
                                if not normalized_email or not str(recovery_code or "").strip():
                                    raise ValueError("Informe o e-mail e o código de recuperação.")
                                if len(str(new_password or "")) < 8:
                                    raise ValueError("A senha deve ter pelo menos 8 caracteres.")
                                if new_password != new_password_confirmation:
                                    raise ValueError("As senhas não coincidem.")
                                security.precheck("password_recovery_reset", normalized_email, client_ip)
                                db.reset_password(normalized_email, recovery_code, new_password)
                                security.register_attempt(
                                    "password_recovery_reset", normalized_email, client_ip, success=True,
                                )
                                st.success("Senha alterada. Volte à aba Entrar e use sua nova senha.")
                            except RateLimitError as error:
                                st.warning(str(error))
                            except ValueError as error:
                                security.register_attempt(
                                    "password_recovery_reset", normalized_email, client_ip, success=False,
                                )
                                st.warning(str(error))

        st.markdown(
            """
            <div class="ln-login-footer">
                <div class="ln-trial-seal">
                    <div class="seal-badge">
                        <div class="seal-stars">★ ★ ★</div>
                        <div class="seal-days">7 DIAS</div>
                        <div class="seal-free">GRÁTIS</div>
                    </div>
                    <div class="seal-copy">
                        Teste nosso sistema por <strong>7 dias grátis</strong><br>
                        e comprove antes de assinar.
                    </div>
                </div>
                <div class="dev">◉ &nbsp; Desenvolvido por <strong>B2G SaaS</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

def legal_acceptance_page(user):
    brand_header(compact=True)
    st.subheader("Um acordo transparente para avançarmos juntos")
    st.write(
        "Antes de continuar, leia e aceite os documentos iniciais da plataforma. "
        "Eles deverão passar por revisão jurídica antes do lançamento público."
    )
    with st.expander("Termos de Uso", expanded=True):
        st.markdown(TERMS_TEXT)
    with st.expander("Política de Privacidade"):
        st.markdown(PRIVACY_TEXT)
    terms = st.checkbox("Li e aceito os Termos de Uso.")
    privacy = st.checkbox("Li e aceito a Política de Privacidade.")
    if st.button("Aceitar e entrar na plataforma", type="primary", disabled=not (terms and privacy)):
        db.accept_legal(user["company_id"], user["id"], LEGAL_VERSION)
        security.event("legal_acceptance", user.get("email",""), _client_ip(), True, f"version={LEGAL_VERSION}")
        st.session_state.user = db.get_user(user["company_id"], user["id"])
        st.rerun()


def _date_text(value):
    if not value:
        return "Não definida"
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)


def account_page(user):
    allowed, message, account = db.subscription_access(user["company_id"])
    st.header("Minha conta")
    st.caption("Seu plano, acesso e informações da empresa em um só lugar.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Plano", account["plan"])
    c2.metric("Situação", message)
    c3.metric("Fim do teste", _date_text(account["trial_ends_at"]))
    if str(account.get("subscription_status") or "").lower() == "trialing" and account.get("trial_ends_at"):
        try:
            _trial_end = datetime.fromisoformat(str(account["trial_ends_at"]).replace("Z", "+00:00"))
            _trial_today = _local_now().date()
            _trial_days_left = (_trial_end.date() - _trial_today).days
            _trial_message = conversion.trial_message(_trial_days_left)
            if _trial_message:
                if _trial_days_left <= 2:
                    st.warning(_trial_message + " Se o LicitaNexo já está ajudando sua operação, escolha seu período de assinatura abaixo.")
                else:
                    st.info(_trial_message)
        except (TypeError, ValueError):
            pass
    with st.container(border=True):
        st.subheader(user["company_name"])
        st.write(f'**Usuário:** {user["name"]}')
        st.write(f'**E-mail:** {user["email"]}')
    if not allowed:
        st.warning(
            f"O acesso operacional está pausado: {message}. "
            f"Entre em contato pelo e-mail {SUPPORT_EMAIL}."
        )

    st.divider()
    st.subheader("Assinatura")
    st.caption("Escolha o período. O checkout é processado pelo Mercado Pago; o LicitaNexo não armazena dados do cartão.")
    cycles = billing.cycles()
    labels = {
        x["code"]: (f'{x["label"]} · R$ {x["amount"]:,.2f}').replace(",", "X").replace(".", ",").replace("X", ".")
        for x in cycles
    }
    a, b = st.columns([2, 1])
    cycle = a.selectbox("Período de contratação", [x["code"] for x in cycles], format_func=labels.get, key="account_billing_cycle")
    selected = next(x for x in cycles if x["code"] == cycle)
    b.metric("Equivale a", ("R$ {:,.2f}/mês".format(selected["monthly_equivalent"])).replace(",", "X").replace(".", ",").replace("X", "."))

    if billing.gateway_configured:
        if st.button("Gerar checkout seguro", type="primary", width="stretch", key="billing_create"):
            try:
                checkout = billing.create_checkout(user["company_id"], user["email"], cycle)
                conversion.record_event(
                    "checkout_created", user["company_id"], user.get("id", ""),
                    {"cycle": cycle, "checkout_id": checkout["id"]},
                )
                st.session_state.billing_checkout_url = checkout["init_point"]
                st.session_state.billing_checkout_id = checkout["id"]
                st.rerun()
            except BillingError as error:
                st.error(str(error))
        if st.session_state.get("billing_checkout_url"):
            st.link_button("Abrir pagamento no Mercado Pago", st.session_state.billing_checkout_url, type="primary", width="stretch")
        if st.session_state.get("billing_checkout_id") and st.button("Já paguei · verificar agora", width="stretch", key="billing_sync"):
            try:
                result = billing.sync_checkout(st.session_state.billing_checkout_id)
                if result["local_status"] == "active":
                    conversion.record_event(
                        "subscription_active", user["company_id"], user.get("id", ""),
                        {"checkout_id": st.session_state.billing_checkout_id},
                    )
                    st.success("Pagamento confirmado. Assinatura ativa.")
                    st.rerun()
                elif result["local_status"] == "pending":
                    st.info("Pagamento ainda aguardando confirmação.")
                else:
                    st.warning(f'Situação: {result["local_status"]}.')
            except BillingError as error:
                st.error(str(error))
    else:
        st.info("Checkout online preparado. Para ativá-lo no servidor, configure as credenciais do Mercado Pago e a URL pública.")

    history = billing.list_company(user["company_id"], 10)
    if history:
        with st.expander("Histórico de cobranças", expanded=False):
            st.dataframe(pd.DataFrame([{
                "Data": r.get("created_at"),
                "Período": labels.get(r.get("billing_cycle"), r.get("billing_cycle")),
                "Valor": ("R$ {:,.2f}".format(float(r.get("amount_cents") or 0)/100)).replace(",", "X").replace(".", ",").replace("X", "."),
                "Situação": r.get("local_status"),
            } for r in history]), hide_index=True, width="stretch")


def support_page(user):
    st.header("Suporte LicitaNexo")
    st.caption("Converse com nossa equipe dentro do aplicativo. As respostas ficam salvas no seu histórico.")

    with st.expander("Abrir novo atendimento", expanded=False):
        with st.form("support_new_conversation", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            request_type = c1.selectbox(
                "Assunto",
                ["Dúvida sobre o aplicativo", "Editais e oportunidades", "Conta e acesso", "Cobrança", "Outro"],
            )
            urgency = c2.selectbox("Prioridade", ["Normal", "Alta", "Urgente"])
            title = st.text_input("Título", placeholder="Ex.: preciso de ajuda para localizar um edital")
            body = st.text_area(
                "Mensagem", placeholder="Descreva sua dúvida com os detalhes necessários.", height=120,
            )
            if st.form_submit_button("Iniciar conversa", type="primary", width="stretch"):
                try:
                    support.create_conversation(user, request_type, title, body, urgency)
                    st.success("Conversa iniciada. Nossa equipe já pode visualizar sua mensagem.")
                    st.rerun()
                except (SupportError, ValueError) as error:
                    st.error(str(error))

    conversations = support.list_conversations(user["company_id"])
    st.markdown("### Minhas conversas")
    if not conversations:
        st.info("Você ainda não abriu nenhuma conversa.")
        return

    for request in conversations:
        label = f'{request["title"]} · {request["status"]}'
        with st.expander(label, expanded=False):
            st.caption(
                f'{request["request_type"]} · prioridade {request["urgency"]} · '
                f'aberto em {_format_datetime(request["created_at"])}'
            )
            if request["details"]:
                with st.chat_message("user"):
                    st.write(request["details"])
            if request["admin_notes"]:
                with st.chat_message("assistant"):
                    st.write(request["admin_notes"])
            for message in support.list_messages(request["id"], user["company_id"]):
                role = "assistant" if message["sender_role"] == "admin" else "user"
                with st.chat_message(role):
                    st.write(message["body"])
                    st.caption(f'{message["sender_name"]} · {_format_datetime(message["created_at"])}')

            if request["status"] not in {"Cancelada"}:
                with st.form(f'support_reply_{request["id"]}', clear_on_submit=True):
                    reply = st.text_area(
                        "Responder", key=f'support_reply_body_{request["id"]}',
                        placeholder="Digite sua mensagem...", height=90,
                    )
                    if st.form_submit_button("Enviar mensagem", type="primary"):
                        try:
                            support.add_message(
                                request["id"], user["id"], "user", reply,
                                company_id=user["company_id"],
                            )
                            st.rerun()
                        except SupportError as error:
                            st.error(str(error))


def admin_support_page(user):
    st.header("🤝 Atendimentos")
    st.caption("Conversas abertas pelos clientes do LicitaNexo.")

    status_filter = st.selectbox(
        "Filtrar por situação",
        ["Todos", "Recebida", "Em atendimento", "Concluída", "Cancelada"],
        key="support_admin_status_filter",
    )
    conversations = support.list_conversations()
    if status_filter != "Todos":
        conversations = [item for item in conversations if item["status"] == status_filter]
    if not conversations:
        st.info("Nenhum atendimento encontrado para este filtro.")
        return

    for request in conversations:
        label = f'{request["company_name"]} · {request["title"]} · {request["status"]}'
        with st.expander(label, expanded=request["status"] in {"Recebida", "Em atendimento"}):
            st.caption(
                f'{request["user_name"]} · {request["user_email"]} · '
                f'{request["request_type"]} · prioridade {request["urgency"]}'
            )
            if request["details"]:
                with st.chat_message("user"):
                    st.write(request["details"])
            if request["admin_notes"]:
                with st.chat_message("assistant"):
                    st.write(request["admin_notes"])
            for message in support.list_messages(request["id"]):
                role = "assistant" if message["sender_role"] == "admin" else "user"
                with st.chat_message(role):
                    st.write(message["body"])
                    st.caption(f'{message["sender_name"]} · {_format_datetime(message["created_at"])}')

            c1, c2 = st.columns([3, 1])
            with c1.form(f'admin_support_reply_{request["id"]}', clear_on_submit=True):
                reply = st.text_area(
                    "Responder ao cliente", key=f'admin_support_body_{request["id"]}',
                    placeholder="Digite a resposta da equipe...", height=90,
                )
                if st.form_submit_button("Enviar resposta", type="primary"):
                    try:
                        support.add_message(request["id"], user["id"], "admin", reply)
                        st.rerun()
                    except SupportError as error:
                        st.error(str(error))
            with c2.form(f'admin_support_status_{request["id"]}'):
                statuses = ["Recebida", "Em atendimento", "Concluída", "Cancelada"]
                status = st.selectbox(
                    "Situação", statuses,
                    index=statuses.index(request["status"]) if request["status"] in statuses else 0,
                    key=f'admin_support_status_value_{request["id"]}',
                )
                if st.form_submit_button("Atualizar situação"):
                    try:
                        support.update_status(request["id"], status)
                        st.rerun()
                    except SupportError as error:
                        st.error(str(error))

def knowledge_page():
    st.header("Primeiros Passos")
    st.caption("Use o LicitaNexo sem treinamento longo: primeiro aprenda o fluxo do app; depois aprofunde o básico de licitações.")
    manual_tab, learn_tab = st.tabs(["Como usar o LicitaNexo", "Aprenda licitações"])

    with manual_tab:
        st.markdown("### O fluxo em 5 passos")
        st.markdown(
            "**1. Passaporte** — diga o que sua empresa vende, onde atende e quais documentos possui.  \n"
            "**2. Radar** — procure oportunidades por produto/serviço, UF e modalidade.  \n"
            "**3. Jornada** — abra somente as oportunidades que merecem análise.  \n"
            "**4. Análise e preço** — leia o edital, confira exigências e calcule sua margem.  \n"
            "**5. Preparação final** — confira preços, documentação, tarefas e o portal oficial antes do certame."
        )
        st.info("Se você está começando, não tente preencher tudo de uma vez. Complete o Passaporte, faça uma busca simples e leve uma oportunidade real para a Jornada.")

        guides = [
            ("Central de Comando", "Mostra o que merece atenção agora: licitações em andamento, valor em disputa, próximos certames e alertas de documentos."),
            ("Radar de Oportunidades", "Digite o que procura. Produto/serviço, UF e modalidade são os filtros principais. Campo vazio significa 'todos'. Clique em Buscar oportunidades e os resultados ficam fixos até você escolher Buscar outra coisa."),
            ("Jornada da Licitação", "É sua mesa de trabalho. Defina Participar ou Não participar, abra o edital oficial, analise o PDF, forme preço e confira a preparação para o certame."),
            ("Análise de Edital", "Envie o PDF. O sistema procura exigências e compara com o Passaporte. É apoio à leitura; o edital e seus anexos continuam sendo a referência final."),
            ("Passaporte da Empresa", "Preencha uma vez e mantenha atualizado. Quanto melhor o Passaporte, mais úteis ficam a busca e a análise."),
        ]
        for title, text in guides:
            with st.expander(title):
                st.write(text)

    with learn_tab:
        st.markdown("### Sua primeira licitação, sem complicar")
        lessons = [
            ("1. Escolha antes de disputar", "Uma boa oportunidade precisa combinar objeto, local de entrega, documentação, capacidade financeira, prazo e margem. Comece pequeno e dentro do que sua empresa já sabe fornecer."),
            ("2. Leia o edital nesta ordem", "Primeiro veja objeto/lotes, data da sessão, condições de participação, habilitação, qualificação técnica, entrega, pagamento e anexos. Só depois faça a leitura completa."),
            ("3. Documentação", "Certidões, balanço, atestados e licenças variam conforme o edital. Não espere a habilitação para descobrir que algo venceu: mantenha o Passaporte atualizado."),
            ("4. Atestado técnico", "Não pense apenas 'tenho atestado'. Compare objeto, quantidade, complexidade e período comprovados com o que o edital exige."),
            ("5. Preço e margem", "Defina seu limite antes da disputa. Inclua custo, frete, impostos, taxas, despesas financeiras e risco. Vencer abaixo do custo não é vitória."),
            ("6. No dia do pregão", "Entre com antecedência, confira acesso ao portal e mantenha seu limite de lance visível. Não deixe a emoção substituir a conta."),
            ("7. Depois da disputa", "Acompanhe mensagens, habilitação, negociação e prazos. Se vencer, releia entrega e pagamento. Se perder, registre o motivo e aprenda."),
        ]
        for title, text in lessons:
            with st.expander(title, expanded=title.startswith("1.")):
                st.write(text)
        st.markdown("### Erros que mais prejudicam iniciantes")
        st.markdown(
            "- disputar sem ler anexos;\n"
            "- confundir publicação com data do certame;\n"
            "- descobrir documento vencido na habilitação;\n"
            "- esquecer frete, impostos ou prazo de pagamento;\n"
            "- baixar o lance sem conhecer o menor preço sustentável;\n"
            "- participar de tudo em vez de construir experiência em um nicho."
        )
        st.warning("O LicitaNexo ajuda a organizar e interpretar o processo, mas não substitui a leitura do edital e dos anexos nem orientação profissional quando necessária.")

def admin_page(user, admin_section="Visão geral"):
    if not _is_admin_user(user):
        st.error("Acesso restrito.")
        return
    if admin_section not in ADMIN_SECTIONS:
        admin_section = "Visão geral"
    st.header(ADMIN_SECTION_LABELS.get(admin_section, admin_section))
    st.caption("Administração · B2G SaaS · Sala de Controle do LicitaNexo")

    if admin_section == "Visão geral":
        stats = _cached_control_room_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Empresas", stats["companies"])
        c2.metric("Usuários", stats["users"])
        c3.metric("Trials ativos", stats["active_trials"])
        c4.metric("Assinaturas ativas", stats["active_subscriptions"])
        c5, c6, c7 = st.columns(3)
        c5.metric("Acessos pendentes", stats["pending_requests"])
        c6.metric("Revisões antifraude", stats["risk_reviews"])
        c7.metric("Recebido registrado", f'R$ {stats["paid_total"]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(
            "A sala de controle separa operação, cobrança, trials, acessos, catálogo e auditoria. "
            "Pagamentos, consumo, conversão e retenção agora possuem controles próprios na Sala de Controle."
        )

    if admin_section == "Conversão e retenção":
        st.subheader("Conversão e retenção")
        st.caption(
            "Do primeiro pedido de acesso até a assinatura e retenção. "
            "A fila abaixo prioriza quem precisa de ação comercial ou sucesso do cliente."
        )
        funnel = conversion.funnel()
        f1, f2, f3, f4, f5, f6 = st.columns(6)
        f1.metric("Solicitações", funnel["requests"])
        f2.metric("Ativadas", funnel["activated"])
        f3.metric("Trials", funnel["trials"])
        f4.metric("Com uso", funnel["engaged"])
        f5.metric("Checkout", funnel["checkout"])
        f6.metric("Pagantes", funnel["paid"])

        def _pct(part, total):
            return f"{(100 * part / total):.1f}%" if total else "—"

        r1, r2, r3 = st.columns(3)
        r1.metric("Solicitação → ativação", _pct(funnel["activated"], funnel["requests"]))
        r2.metric("Uso → checkout", _pct(funnel["checkout"], funnel["engaged"]))
        r3.metric("Checkout → pagamento", _pct(funnel["paid"], funnel["checkout"]))

        health_rows = conversion.customer_health()
        if health_rows:
            high_priority = [x for x in health_rows if x["priority"] == "high" and x["recommended_action"]]
            retention_risk = [x for x in health_rows if x["health"] == "risco de retenção"]
            t1, t2, t3 = st.columns(3)
            t1.metric("Ações prioritárias", len(high_priority))
            t2.metric("Risco de retenção", len(retention_risk))
            t3.metric(
                "Trials sem ativação",
                sum(1 for x in health_rows if x["health"] == "sem ativação"),
            )

            st.markdown("#### Saúde dos clientes")
            health_frame = pd.DataFrame([{
                "Empresa": x["company_name"],
                "E-mail": x["email"],
                "Status": x["status"],
                "Dias de trial": x["days_left"] if x["days_left"] is not None else "",
                "Buscas": x["searches"],
                "Análises": x["analyses"],
                "Última atividade": x["last_activity"],
                "Saúde": x["health"],
                "Próxima ação": x["recommended_action"],
            } for x in health_rows])
            st.dataframe(health_frame, hide_index=True, width="stretch")

        q1, q2 = st.columns([1, 2])
        if q1.button("Atualizar fila de ações", type="primary", key="rc24_refresh_actions"):
            created = conversion.refresh_action_queue()
            st.success(f"{created} nova(s) ação(ões) adicionada(s) à fila.")
            st.rerun()

        action_filter = q2.selectbox(
            "Fila", ["open", "done", "all"],
            format_func=lambda x: {"open": "Abertas", "done": "Concluídas", "all": "Todas"}[x],
            key="rc24_action_filter",
        )
        actions = conversion.actions(action_filter, 300)
        if actions:
            st.markdown("#### Ações comerciais e de retenção")
            for action in actions:
                with st.container(border=True):
                    a1, a2 = st.columns([4, 1])
                    a1.write(f'**{action["title"]}** · {action["action_type"]}')
                    a1.caption(action["details"])
                    a1.caption(
                        f'Prioridade: {action["priority"]} · Criada em {action["created_at"]}'
                    )
                    if action["status"] == "open":
                        if a2.button(
                            "Concluir", key=f'rc24_complete_{action["id"]}', width="stretch"
                        ):
                            conversion.complete_action(action["id"])
                            st.rerun()
                    else:
                        a2.success("Concluída")
        else:
            st.info("Nenhuma ação nesta fila.")

    if admin_section == "Consumo e IA":
        st.subheader("Consumo e IA")
        st.caption(
            "Medição mensal por empresa. O custo de análise é estimado e configurável; "
            "o valor padrão permanece R$ 0,00 enquanto a análise não consumir um provedor externo de IA."
        )
        usage_rows = usage.admin_summary()
        total_analyses = sum(r["analyses"] for r in usage_rows)
        total_searches = sum(r["searches"] for r in usage_rows)
        total_cost = sum(r["estimated_cost_cents"] for r in usage_rows) / 100
        u1, u2, u3, u4 = st.columns(4)
        u1.metric("Análises no mês", total_analyses)
        u2.metric("Buscas no mês", total_searches)
        u3.metric(
            "Custo estimado",
            ("R$ {:,.2f}".format(total_cost)).replace(",", "X").replace(".", ",").replace("X", "."),
        )
        u4.metric("Empresas com uso", len(usage_rows))

        with st.expander("Política padrão do Essential", expanded=False):
            with st.form("rc23_usage_defaults"):
                default_limit = st.number_input(
                    "Análises inteligentes / mês",
                    min_value=0, value=usage.default_analysis_limit(), step=1,
                    help="0 = sem limite. O padrão inicial é 15 para começarmos a medir o uso real.",
                )
                default_cost = st.number_input(
                    "Custo estimado por análise (R$)",
                    min_value=0.0,
                    value=usage.default_estimated_cost_cents() / 100,
                    step=0.01,
                    format="%.4f",
                    help="Enquanto não houver provedor externo de IA, mantenha em R$ 0,00.",
                )
                if st.form_submit_button("Salvar política padrão", type="primary"):
                    usage.set_setting("essential_analysis_monthly_limit", int(default_limit))
                    usage.set_setting("estimated_analysis_cost_cents", float(default_cost) * 100)
                    st.success("Política padrão atualizada.")
                    st.rerun()

        companies_usage = db.list_companies_admin()
        if companies_usage:
            st.markdown("#### Limite por empresa")
            usage_company_map = {
                f'{c["name"]} · {c.get("cnpj") or "sem CNPJ"}': c["id"]
                for c in companies_usage
            }
            usage_company_label = st.selectbox(
                "Empresa", list(usage_company_map), key="rc23_usage_company"
            )
            usage_company_id = usage_company_map[usage_company_label]
            current_policy = usage.company_policy(usage_company_id)
            current_summary = usage.company_summary(usage_company_id)
            p1, p2, p3 = st.columns(3)
            p1.metric("Análises usadas", current_summary["used"])
            p2.metric(
                "Limite atual",
                "Sem limite" if current_summary["limit"] == 0 else current_summary["limit"],
            )
            p3.metric("Buscas realizadas", current_summary["searches"])
            with st.form("rc23_company_usage_policy"):
                company_limit = st.number_input(
                    "Limite mensal desta empresa",
                    min_value=0, value=int(current_policy["analysis_monthly_limit"]), step=1,
                    help="0 = sem limite.",
                )
                company_cost = st.number_input(
                    "Custo estimado por análise desta empresa (R$)",
                    min_value=0.0,
                    value=float(current_policy["estimated_analysis_cost_cents"]) / 100,
                    step=0.01,
                    format="%.4f",
                )
                if st.form_submit_button("Salvar limite da empresa"):
                    usage.set_company_policy(
                        usage_company_id, int(company_limit), float(company_cost) * 100
                    )
                    st.success("Política da empresa atualizada.")
                    st.rerun()

        if usage_rows:
            st.markdown("#### Consumo do mês")
            usage_frame = pd.DataFrame([{
                "Empresa": r.get("company_name") or r.get("company_id"),
                "Análises": r.get("analyses"),
                "Limite": "Sem limite" if r.get("analysis_limit") == 0 else r.get("analysis_limit"),
                "Buscas": r.get("searches"),
                "Custo estimado": ("R$ {:,.2f}".format(float(r.get("estimated_cost_cents") or 0)/100))
                    .replace(",", "X").replace(".", ",").replace("X", "."),
                "Última atividade": r.get("last_activity"),
            } for r in usage_rows])
            st.dataframe(usage_frame, hide_index=True, width="stretch")
        else:
            st.info("O consumo começará a aparecer assim que usuários fizerem buscas ou análises.")

    if admin_section == "Cupons e indicações":
        st.subheader("Cupons e indicações")
        st.caption(
            "Campanhas comerciais e indicações sem abrir brecha para novo trial. "
            "O período gratuito continua pertencendo ao CNPJ."
        )
        campaigns = db.list_campaigns()
        uses = db.campaign_uses(500)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Campanhas", len(campaigns))
        c2.metric("Ativas", sum(1 for c in campaigns if c.get("active")))
        c3.metric("Utilizações", len(uses))
        c4.metric("Ativações", sum(1 for u in uses if u.get("status") in {"activated","paid"}))

        with st.expander("Nova campanha", expanded=False):
            with st.form("new_campaign"):
                a, b = st.columns(2)
                code = a.text_input("Código", placeholder="Ex.: JOSE10")
                name = b.text_input("Nome da campanha", placeholder="Indicação clientes agosto")
                a, b = st.columns(2)
                campaign_type = a.selectbox(
                    "Tipo", ["coupon", "referral"],
                    format_func=lambda x: "Cupom" if x=="coupon" else "Indicação"
                )
                owner_name = b.text_input("Parceiro / indicador", placeholder="Opcional")
                a, b = st.columns(2)
                benefit_type = a.selectbox(
                    "Benefício", ["percent","fixed","none"],
                    format_func=lambda x: {"percent":"Desconto percentual","fixed":"Desconto em reais","none":"Somente rastreamento"}[x]
                )
                benefit_value = b.number_input(
                    "Valor do benefício", min_value=0.0, value=10.0, step=1.0,
                    disabled=(benefit_type=="none")
                )
                a, b = st.columns(2)
                max_uses = a.number_input(
                    "Limite total de usos", min_value=0, value=0, step=1,
                    help="0 = sem limite total; permanece limitado a 1 uso por CNPJ."
                )
                cycles = b.multiselect(
                    "Períodos permitidos", ["Mensal","Trimestral","Semestral","Anual"],
                    default=["Mensal","Trimestral","Semestral","Anual"]
                )
                a, b = st.columns(2)
                valid_from = a.date_input("Início", value=date.today())
                no_end = b.checkbox("Sem data final", value=True)
                valid_until = b.date_input("Fim", value=date.today()+timedelta(days=30), disabled=no_end)
                notes = st.text_input("Observação interna", placeholder="Opcional")
                if st.form_submit_button("Criar campanha", type="primary"):
                    try:
                        db.create_campaign(
                            code, name, campaign_type, owner_name, benefit_type,
                            0 if benefit_type=="none" else benefit_value,
                            max_uses, valid_from.isoformat()+"T00:00:00",
                            None if no_end else valid_until.isoformat()+"T23:59:59",
                            ",".join(cycles), notes
                        )
                        st.success("Campanha criada.")
                        st.rerun()
                    except ValueError as error:
                        st.warning(str(error))

        if campaigns:
            frame = pd.DataFrame([{
                "Código":c.get("code"),"Campanha":c.get("name"),
                "Tipo":"Cupom" if c.get("campaign_type")=="coupon" else "Indicação",
                "Parceiro":c.get("owner_name"),
                "Benefício":(
                    f'{float(c.get("benefit_value") or 0):.0f}%'
                    if c.get("benefit_type")=="percent"
                    else (f'R$ {float(c.get("benefit_value") or 0):.2f}' if c.get("benefit_type")=="fixed" else "Rastreamento")
                ),
                "Usos":c.get("uses_count") or 0,
                "Ativações":c.get("conversions") or 0,
                "Ativa":"Sim" if c.get("active") else "Não",
                "Validade":c.get("valid_until") or "Sem prazo",
            } for c in campaigns])
            st.dataframe(frame, hide_index=True, width="stretch")

            cmap={f'{c["code"]} · {c["name"]} · {"ativa" if c["active"] else "inativa"}':c for c in campaigns}
            label=st.selectbox("Gerenciar campanha",list(cmap),key="campaign_admin_select")
            c=cmap[label]
            if st.button("Desativar campanha" if c["active"] else "Ativar campanha",key="campaign_toggle"):
                db.set_campaign_active(c["id"],not bool(c["active"]))
                st.rerun()

        if uses:
            st.markdown("#### Histórico de utilização")
            uf=pd.DataFrame([{
                "Data":u.get("created_at"),"Código":u.get("code"),"Campanha":u.get("campaign_name"),
                "E-mail":u.get("email"),"CNPJ":u.get("cnpj"),"Situação":u.get("status"),
                "Benefício":u.get("benefit_value")
            } for u in uses])
            st.dataframe(uf,hide_index=True,width="stretch")

    if admin_section == "Trials e antifraude":
        st.subheader("Trials e antifraude")
        st.caption(
            "CNPJ e e-mail são travas fortes. IP é apenas um sinal de risco, nunca uma identidade isolada."
        )
        attempts = db.list_trial_attempts(250)
        reviews = [r for r in db.list_access_requests() if r.get("risk_status") == "review"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Tentativas registradas", len(attempts))
        c2.metric("Em revisão", len(reviews))
        c3.metric("Bloqueadas", sum(1 for r in attempts if r.get("outcome") == "blocked"))
        if attempts:
            trial_frame = pd.DataFrame([{
                "Data": r.get("created_at"),
                "E-mail": r.get("email"),
                "CNPJ": r.get("cnpj"),
                "IP": r.get("ip_masked") or "Não disponível",
                "Risco": r.get("risk_score"),
                "Resultado": r.get("outcome"),
                "Motivos": r.get("reasons"),
            } for r in attempts])
            st.dataframe(trial_frame, hide_index=True, width="stretch")
        else:
            st.info("Ainda não há tentativas de trial registradas com o novo controle.")

    if admin_section == "Auditoria":
        st.subheader("Auditoria administrativa")
        account_audit_rows = account_admin.audit(200)
        if account_audit_rows:
            st.dataframe(pd.DataFrame([{
                "Data": r.get("created_at"), "Empresa": r.get("company_name"),
                "Ação": r.get("action"), "Administrador": r.get("actor_email"),
                "Motivo": r.get("reason"), "Detalhes": r.get("details"),
            } for r in account_audit_rows]), hide_index=True, width="stretch")
        else:
            st.info("Nenhuma ação administrativa de conta registrada.")
        st.divider()
        st.subheader("Auditoria")
        events = db.list_audit_events(250)
        if events:
            audit_frame = pd.DataFrame([{
                "Data": r.get("created_at"), "Ator": r.get("actor"),
                "Ação": r.get("action"), "Entidade": r.get("entity_type"),
                "ID": r.get("entity_id"), "Detalhes": r.get("details"),
            } for r in events])
            st.dataframe(audit_frame, hide_index=True, width="stretch")
        else:
            st.info("Nenhum evento de auditoria registrado ainda.")
    if admin_section == "Acessos e convites":
        pending_count = db.count_access_requests()
        st.caption(f"{pending_count} solicitação(ões) aguardando decisão ou contato.")
        request_filter = st.selectbox(
            "Mostrar", ["Pendentes", "Todas"], key="admin_access_filter"
        )
        requests = db.list_access_requests()
        if request_filter == "Pendentes":
            requests = [r for r in requests if r.get("status") in {"pending", "contacted"}]
        if not requests:
            st.info("Nenhuma solicitação de acesso nesta visão.")
        for request in requests:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.subheader(request["company_name"])
                c1.write(f'{request["name"]} · {request["email"]} · {request["whatsapp"]}')
                c1.caption(
                    f'CNPJ: {request.get("cnpj") or "Não informado"} · '
                    f'Risco: {request.get("risk_score", 0)} · '
                    f'Situação de risco: {request.get("risk_status") or "normal"}'
                )
                if request.get("risk_reasons"):
                    c1.warning(f'Sinais de atenção: {request["risk_reasons"]}')
                if request.get("campaign_code"):
                    c1.caption(f'Campanha / cupom: {request["campaign_code"]}')
                c1.caption(f'Segmento: {request["segment"] or "Não informado"} · Cargo: {request.get("job_title") or "Não informado"} · Origem: {request.get("how_heard") or "Não informado"}')
                if request["challenge"]:
                    c1.write(f'**Desafio:** {request["challenge"]}')
                c2.metric("Situação", request["status"])
                b1, b2, b3 = st.columns(3)
                locked = request["status"] in {"activated", "rejected"}
                if b1.button(
                    "Registrar contato", key=f'contact_{request["id"]}',
                    disabled=locked, width="stretch",
                ):
                    db.mark_request_contacted(request["id"])
                    st.rerun()
                trial_days = st.selectbox(
                    "Período de teste", [7, 15, 30], index=0, key=f'trial_{request["id"]}',
                    disabled=locked,
                )
                if b2.button(
                    "Aprovar e gerar convite", key=f'invite_{request["id"]}',
                    disabled=locked, type="primary", width="stretch",
                ):
                    code = db.approve_access_request(request["id"], trial_days=trial_days)
                    mail_status = "manual"
                    mail_message = "E-mail ainda não configurado. Copie o código e envie ao interessado."
                    if mail_is_configured():
                        try:
                            send_invitation(request["email"], request["name"], code, trial_days)
                            db.record_email_event("invitation", request["email"], "sent")
                            mail_status = "sent"
                            mail_message = "Convite enviado automaticamente por e-mail."
                        except MailError as error:
                            db.record_email_event("invitation", request["email"], "error", str(error))
                            mail_message = str(error)
                    invitation_data = {
                        "email": request["email"], "code": code, "mail_status": mail_status,
                        "mail_message": mail_message, "trial_days": trial_days,
                    }
                    st.session_state.last_invitation = invitation_data
                    st.session_state.setdefault("admin_invitation_codes", {})[
                        str(request["id"])
                    ] = invitation_data
                    logger.info("Convite gerado para %s · envio=%s", request["email"], mail_status)
                    st.rerun()
                if b3.button(
                    "Recusar", key=f'reject_{request["id"]}',
                    disabled=locked, width="stretch",
                ):
                    db.reject_access_request(request["id"])
                    st.rerun()
        invitation = st.session_state.get("last_invitation")
        if invitation:
            st.success("Convite gerado.")
            st.write(invitation.get("mail_message", ""))
            st.code(f'E-mail: {invitation["email"]}\nCódigo: {invitation["code"]}\nTeste: {invitation.get("trial_days", "-")} dias')
            st.warning("O código é mostrado para o administrador e não fica disponível em texto aberto no banco.")
            if st.button("Ocultar código exibido"):
                st.session_state.pop("last_invitation", None)
                st.rerun()
    if admin_section == "Empresas e usuários":
        active_accounts, access_requests = db.crm_accounts()
        c1, c2, c3 = st.columns(3)
        c1.metric("Empresas ativadas", len({row["company_id"] for row in active_accounts}))
        c2.metric("Usuários", len(active_accounts))
        c3.metric("Interessados", len(access_requests))
        if active_accounts:
            st.markdown("#### Contas ativas e em teste")
            frame = pd.DataFrame([{
                "Empresa": r["company_name"], "Responsável": r["name"], "E-mail": r["email"],
                "Plano": r["plan"], "Situação": r["subscription_status"],
                "Fim do teste": r["trial_ends_at"], "Último acesso": r["last_login_at"],
            } for r in active_accounts])
            st.dataframe(frame, hide_index=True, width="stretch")
        st.markdown("#### Gestão de contas")
        companies_admin = db.list_companies_admin()
        if not companies_admin:
            st.info("Nenhuma conta de cliente disponível para administrar.")
        else:
            company_labels = {
                c["id"]: f'{c["name"]} · {c.get("subscription_status") or "sem status"} · {c.get("users_count") or 0} usuário(s)'
                for c in companies_admin
            }
            managed_id = st.selectbox(
                "Conta", list(company_labels), format_func=company_labels.get,
                key="rc22_account_management_company",
            )
            managed = next(c for c in companies_admin if c["id"] == managed_id)
            current_status = str(managed.get("subscription_status") or "").lower()
            with st.container(border=True):
                m1, m2 = st.columns([2, 1])
                m1.write(f'**{managed["name"]}**')
                m1.caption(f'CNPJ: {managed.get("cnpj") or "não informado"} · Plano: {managed.get("plan") or "Essencial"}')
                m2.metric("Status", current_status or "não definido")

                if current_status == "suspended":
                    if st.button("Reativar conta", type="primary", key=f'rc22_reactivate_{managed_id}'):
                        try:
                            account_admin.reactivate(managed_id, user.get("email", ""))
                            st.success("Conta reativada.")
                            st.rerun()
                        except AccountAdminError as error:
                            st.error(str(error))
                else:
                    with st.form(f"rc22_deactivate_{managed_id}"):
                        reason = st.text_input("Motivo da desativação", placeholder="Ex.: solicitação do cliente")
                        if st.form_submit_button("Desativar conta"):
                            try:
                                account_admin.deactivate(managed_id, user.get("email", ""), reason)
                                st.success("Conta desativada. O acesso foi bloqueado e os dados foram preservados.")
                                st.rerun()
                            except AccountAdminError as error:
                                st.error(str(error))

                if current_status == "suspended":
                    with st.expander("Zona de perigo · excluir conta definitivamente", expanded=False):
                        st.warning(
                            "A exclusão definitiva remove os dados operacionais da empresa. "
                            "A trilha mínima de auditoria e os sinais antifraude são preservados."
                        )
                        expected_delete = f'EXCLUIR {managed["name"]}'
                        with st.form(f"rc22_purge_{managed_id}"):
                            purge_reason = st.text_area(
                                "Motivo da exclusão definitiva",
                                placeholder="Ex.: solicitação formal de encerramento e eliminação dos dados operacionais",
                            )
                            confirmation = st.text_input(
                                f"Confirmação: digite exatamente {expected_delete}"
                            )
                            if st.form_submit_button("Excluir conta definitivamente"):
                                try:
                                    account_admin.purge(
                                        managed_id, user.get("email", ""),
                                        purge_reason, confirmation,
                                    )
                                    st.success("Conta excluída definitivamente.")
                                    st.rerun()
                                except AccountAdminError as error:
                                    st.error(str(error))

        if access_requests:
            st.markdown("#### Funil de interessados")
            funnel = pd.DataFrame([{
                "Empresa": r["company_name"], "Responsável": r["name"], "E-mail": r["email"],
                "Segmento": r.get("segment") or "", "Situação": r["status"],
                "Solicitado": r["created_at"], "Convidado": r.get("invited_at"),
                "Ativado": r.get("activated_at"),
            } for r in access_requests])
            st.dataframe(funnel, hide_index=True, width="stretch")

            invited_requests = [
                request for request in access_requests if request.get("status") == "invited"
            ]
            if invited_requests:
                st.markdown("#### Códigos de acesso pendentes")
                st.caption(
                    "Por segurança, o banco guarda somente o hash do código. "
                    "Códigos gerados nesta sessão ficam visíveis abaixo; para convites antigos, "
                    "gere um novo código, que substitui o anterior."
                )
                invitation_codes = st.session_state.setdefault("admin_invitation_codes", {})
                invited_labels = {
                    str(request["id"]): f'{request["name"]} · {request["email"]}'
                    for request in invited_requests
                }
                selected_request_id = st.selectbox(
                    "Convite pendente",
                    list(invited_labels),
                    format_func=invited_labels.get,
                    key="admin_pending_invitation_request",
                )
                selected_request = next(
                    request for request in invited_requests
                    if str(request["id"]) == selected_request_id
                )
                selected_trial_days = int(selected_request.get("approved_trial_days") or 7)
                if selected_request_id in invitation_codes:
                    visible_invitation = invitation_codes[selected_request_id]
                    st.success("Código ativo gerado nesta sessão administrativa.")
                    st.code(
                        f'E-mail: {visible_invitation["email"]}\n'
                        f'Código: {visible_invitation["code"]}\n'
                        f'Teste: {visible_invitation.get("trial_days", selected_trial_days)} dias'
                    )
                else:
                    st.info(
                        "O código original não pode ser recuperado porque não é armazenado em texto aberto. "
                        "Use o botão abaixo para substituí-lo por um novo."
                    )
                if st.button(
                    "Gerar novo código para este convite",
                    type="primary",
                    key="admin_regenerate_pending_invitation",
                ):
                    code = db.approve_access_request(
                        selected_request["id"], trial_days=selected_trial_days,
                    )
                    invitation_data = {
                        "email": selected_request["email"],
                        "code": code,
                        "mail_status": "manual",
                        "mail_message": "Novo código gerado para envio ao interessado.",
                        "trial_days": selected_trial_days,
                    }
                    invitation_codes[selected_request_id] = invitation_data
                    st.session_state.last_invitation = invitation_data
                    logger.info(
                        "Código de convite regenerado para %s pela administração",
                        selected_request["email"],
                    )
                    st.rerun()

    if admin_section == "Atendimentos":
        admin_support_page(user)
    if admin_section == "Recuperação":
        recoveries = db.list_password_reset_requests()
        if not recoveries:
            st.info("Nenhuma recuperação de senha aguardando atendimento.")
        for recovery in recoveries:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.subheader(recovery["name"])
                c1.write(f'{recovery["company_name"]} · {recovery["email"]}')
                c2.metric("Situação", recovery["status"])
                if st.button(
                    "Gerar novo código de recuperação",
                    key=f'recovery_{recovery["id"]}', type="primary",
                ):
                    code = db.generate_password_reset_code(recovery["id"])
                    mail_message = "E-mail ainda não configurado. Envie o código manualmente."
                    if mail_is_configured():
                        try:
                            send_recovery_code(recovery["email"], recovery["name"], code)
                            db.record_email_event("password_recovery", recovery["email"], "sent")
                            mail_message = "Código enviado automaticamente por e-mail."
                        except MailError as error:
                            db.record_email_event("password_recovery", recovery["email"], "error", str(error))
                            mail_message = str(error)
                    st.session_state.last_recovery = {"email": recovery["email"], "code": code, "mail_message": mail_message}
                    st.rerun()
        last_recovery = st.session_state.get("last_recovery")
        if last_recovery:
            st.success("Código de recuperação gerado.")
            st.write(last_recovery.get("mail_message", ""))
            st.code(f'E-mail: {last_recovery["email"]}\nCódigo: {last_recovery["code"]}')
            st.warning("O código expira em 30 minutos e é apagado depois do uso.")
            if st.button("Ocultar código de recuperação"):
                st.session_state.pop("last_recovery", None)
                st.rerun()
    if admin_section == "Assinaturas e pagamentos":
        st.subheader("Assinaturas e pagamentos")
        st.caption("RC21 · cobrança online e sincronização do gateway.")
        bm = billing.metrics()
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Gateway", "Configurado" if billing.gateway_configured else "Aguardando credenciais")
        q2.metric("Ativas online", bm["active"])
        q3.metric("Pendentes online", bm["pending"])
        q4.metric("Inadimplentes", bm["past_due"])
        online = billing.list_all(200)
        if online:
            st.dataframe(pd.DataFrame([{
                "Data": r.get("created_at"), "Empresa ID": r.get("company_id"),
                "E-mail": r.get("payer_email"), "Período": r.get("billing_cycle"),
                "Valor": ("R$ {:,.2f}".format(float(r.get("amount_cents") or 0)/100)).replace(",", "X").replace(".", ",").replace("X", "."),
                "Status gateway": r.get("provider_status"), "Status LicitaNexo": r.get("local_status"),
            } for r in online]), hide_index=True, width="stretch")
            if billing.gateway_configured:
                sync_options={f'{r["payer_email"]} · {r["billing_cycle"]} · {r["local_status"]}':r["id"] for r in online if r.get("provider_id")}
                if sync_options:
                    sync_label=st.selectbox("Sincronizar cobrança", list(sync_options), key="admin_billing_select")
                    if st.button("Sincronizar Mercado Pago", key="admin_billing_sync"):
                        try:
                            result=billing.sync_checkout(sync_options[sync_label])
                            st.success(f'Gateway: {result["provider_status"]} · LicitaNexo: {result["local_status"]}')
                            st.rerun()
                        except BillingError as error:
                            st.error(str(error))

        payments = db.list_payments()
        companies_for_payment = db.list_companies_admin()
        p1, p2, p3 = st.columns(3)
        p1.metric("Pagamentos registrados", len(payments))
        p2.metric("Pagos", sum(1 for p in payments if p.get("status") == "paid"))
        p3.metric(
            "Recebido",
            ("R$ {:,.2f}".format(sum(float(p.get("amount") or 0) for p in payments if p.get("status") == "paid")))
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
        with st.expander("Registrar pagamento manual / PIX", expanded=False):
            if companies_for_payment:
                company_map = {f'{c["name"]} · {c.get("cnpj") or "sem CNPJ"}': c["id"] for c in companies_for_payment}
                with st.form("admin_payment_record"):
                    company_label = st.selectbox("Empresa", list(company_map))
                    amount = st.number_input("Valor", min_value=0.0, value=49.90, step=10.0)
                    method = st.selectbox("Forma", ["PIX", "Cartão", "Boleto", "Transferência"])
                    cycle = st.selectbox("Período", ["Mensal", "Trimestral", "Semestral", "Anual"])
                    pay_status = st.selectbox("Status", ["pending", "paid", "failed", "refunded", "canceled"])
                    external_id = st.text_input("ID externo / transação", placeholder="Opcional")
                    notes = st.text_input("Observação", placeholder="Opcional")
                    if st.form_submit_button("Registrar pagamento", type="primary"):
                        db.record_payment(
                            company_map[company_label], amount, method, cycle, pay_status,
                            external_id=external_id, notes=notes,
                        )
                        st.success("Pagamento registrado.")
                        st.rerun()
        if payments:
            pay_frame = pd.DataFrame([{
                "Data": p.get("created_at"), "Empresa": p.get("company_name"),
                "CNPJ": p.get("cnpj"), "Valor": p.get("amount"),
                "Forma": p.get("method"), "Período": p.get("billing_cycle"),
                "Status": p.get("status"), "Transação": p.get("external_id"),
            } for p in payments])
            st.dataframe(pay_frame, hide_index=True, width="stretch")

        companies = db.list_companies_admin()
        if not companies:
            st.info("Nenhuma empresa ativada.")
        else:
            labels = {
                company["id"]: f'{company["name"]} · {company["subscription_status"]} · {company["users_count"]} usuário(s)'
                for company in companies
            }
            selected_id = st.selectbox("Empresa", list(labels), format_func=labels.get)
            selected = next(company for company in companies if company["id"] == selected_id)
            statuses = ["trialing", "active", "grace", "past_due", "canceled", "suspended"]
            with st.form("admin_subscription"):
                plan = st.text_input("Plano", value=selected["plan"] or "Essencial")
                status = st.selectbox(
                    "Situação", statuses,
                    index=statuses.index(selected["subscription_status"])
                    if selected["subscription_status"] in statuses else 0,
                )
                trial_end = st.date_input(
                    "Fim do teste", value=datetime.fromisoformat(selected["trial_ends_at"]).date()
                    if selected["trial_ends_at"] else date.today(),
                )
                no_subscription_end = st.checkbox(
                    "Sem data de término da assinatura", value=not bool(selected["subscription_ends_at"])
                )
                subscription_end = st.date_input(
                    "Término da assinatura",
                    value=datetime.fromisoformat(selected["subscription_ends_at"]).date()
                    if selected["subscription_ends_at"] else date.today(),
                    disabled=no_subscription_end,
                )
                if st.form_submit_button("Salvar acesso", type="primary"):
                    db.update_company_subscription(
                        selected_id, plan, status, trial_end.isoformat() + "T23:59:59",
                        None if no_subscription_end else subscription_end.isoformat() + "T23:59:59",
                    )
                    st.success("Acesso comercial atualizado.")
                    st.rerun()

    if admin_section == "PNCP e fontes":
        st.subheader("Saúde do catálogo PNCP")
        pncp_snapshot = _cached_admin_pncp_snapshot()
        catalog_stats = pncp_snapshot["stats"]
        last_update = pncp_snapshot["last_update"]
        recent_runs = pncp_snapshot["recent_runs"]
        last_run = recent_runs[0] if recent_runs else None

        if not last_run:
            health_label, health_icon = "Sem sincronização", "⚪"
        elif last_run.get("status") == "success":
            health_label, health_icon = "Normal", "🟢"
        elif "429" in str(last_run.get("errors") or ""):
            health_label, health_icon = "PNCP limitado", "🟡"
        elif last_run.get("status") == "partial":
            health_label, health_icon = "Parcial", "🟡"
        else:
            health_label, health_icon = "Atenção", "🔴"

        quality = pncp_snapshot.get("quality") or {}
        state_counts = pncp_snapshot.get("state_counts") or []
        h1, h2, h3, h4, h5 = st.columns(5)
        h1.metric("Total bruto no banco", catalog_stats["total"])
        h2.metric("Com prazo futuro", quality.get("future_deadline", catalog_stats.get("open_now", 0)))
        h3.metric("Sem prazo informado", quality.get("without_deadline", 0))
        h4.metric("Novos hoje", catalog_stats["new_today"])
        h5.metric("Status", f"{health_icon} {health_label}")
        st.info(
            "O total bruto não é o mesmo número exibido ao cliente. A área de busca mostra o recorte de oportunidades abertas/viáveis; "
            "use estes indicadores para distinguir catálogo total, registros sem prazo e oportunidades com prazo futuro."
        )
        st.caption(
            f"Catálogo atualizado em: {str(last_update or 'Nunca')[:19].replace('T', ' ')} · "
            f"Versão: {APP_VERSION}"
        )
        modality_counts = pncp_snapshot["modality_counts"]
        st.markdown("#### Distribuição por modalidade")
        modality_rows = [
            {"Modalidade": name, "Quantidade": total}
            for name, total in sorted(modality_counts.items(), key=lambda pair: (-pair[1], pair[0]))
        ]
        modality_total = sum(row["Quantidade"] for row in modality_rows)
        if modality_rows:
            st.dataframe(pd.DataFrame(modality_rows), hide_index=True, width="stretch")
        st.caption(f"Soma das modalidades: {modality_total} · Total do catálogo: {catalog_stats['total']}")
        if state_counts:
            st.markdown("#### Cobertura por UF")
            state_frame = pd.DataFrame([
                {"UF": row.get("label"), "Quantidade": int(row.get("total") or 0)}
                for row in state_counts
            ])
            st.dataframe(state_frame, hide_index=True, width="stretch", height=min(460, 38 + 31 * len(state_frame)))
        q1, q2 = st.columns(2)
        q1.metric("Sem URL do portal", quality.get("without_portal_url", 0))
        q2.metric("Sem valor estimado", quality.get("without_value", 0))
        if modality_total != catalog_stats["total"]:
            st.warning(
                f"Há diferença de {catalog_stats['total'] - modality_total} registro(s) entre o total e a distribuição. "
                "Isso indica modalidade vazia ou dado legado e deve ser revisado."
            )
        st.info(
            "O Radar pesquisa a base local. Depois da carga completa, a atualização normal é incremental: busca publicações "
            "novas/recentes desde a última sincronização concluída e atualiza registros existentes sem duplicá-los. "
            "A reconciliação completa permanece disponível para conferência periódica."
        )

        last_incremental = db.last_successful_sync_run(["PNCP_INCREMENTAL"])
        last_full = db.last_successful_sync_run(["PNCP_FULL", "PNCP"])
        reference_run = last_incremental or last_full
        if reference_run:
            reference_at = reference_run.get("finished_at") or reference_run.get("started_at")
            st.caption(
                f"Última sincronização concluída: {str(reference_at or '-')[:19].replace('T', ' ')} · "
                f"modo: {'incremental' if reference_run.get('source') == 'PNCP_INCREMENTAL' else 'carga completa'} · "
                f"{int(reference_run.get('pages') or 0)} página(s) · {int(reference_run.get('records') or 0)} registro(s) processados"
            )
        else:
            st.caption("Ainda não há uma sincronização concluída registrada.")

        def _ordered_modalities(client):
            modalities = client.fetch_modalities()
            priority_codes = [
                ("Dispensa de licitação", 8),
                ("Pregão eletrônico", 6),
                ("Concorrência eletrônica", 4),
                ("Credenciamento", 12),
                ("Inexigibilidade", 9),
            ]
            dynamic_by_code = {int(code): name for name, code in modalities.items()}
            ordered, used_codes = [], set()
            for fallback_name, code in priority_codes:
                ordered.append((dynamic_by_code.get(code, fallback_name), code))
                used_codes.add(code)
            for name, code in modalities.items():
                code = int(code)
                if code not in used_codes:
                    ordered.append((name, code))
            return ordered

        def _run_pncp_sync(client, sync_start, sync_end, run_source, checkpoint_source,
                           checkpoint_period_start, checkpoint_period_end, label, item_filter=None):
            with db.sync_run_scope(run_source) as run_id:
                catalog_before = db.global_catalog_count()
                ordered_modalities = _ordered_modalities(client)
                progress = st.progress(0)
                status_box = st.empty()
                total_pages = total_records = total_received = total_skipped = 0
                errors = []
                stopped_by_rate_limit = False

                for idx, (name, code) in enumerate(ordered_modalities, start=1):
                    status_box.info(f"{label} · {name} · {idx}/{len(ordered_modalities)}")

                    def sync_progress(_day, page, partial_stats, modality_name=name, modality_index=idx):
                        total_for_modality = partial_stats.get("total_pages") or "?"
                        received_for_modality = partial_stats.get("received", 0)
                        status_box.info(
                            f"{label} · {modality_name} · modalidade {modality_index}/{len(ordered_modalities)} · "
                            f"página {page}/{total_for_modality} · {received_for_modality} registros recebidos"
                        )

                    stats = client.sync(
                        sync_start, sync_end, code, "",
                        checkpoint_getter=lambda day, c=code: db.get_global_checkpoint(
                            c, "", day, source=checkpoint_source,
                            period_start=checkpoint_period_start, period_end=checkpoint_period_end,
                        ),
                        page_saver=db.upsert_global_catalog_page,
                        checkpoint_saver=lambda day, page, completed, saved, error, c=code: db.save_global_checkpoint(
                            c, "", day, page, completed, saved, error, source=checkpoint_source,
                            period_start=checkpoint_period_start, period_end=checkpoint_period_end,
                        ),
                        progress=sync_progress,
                        max_pages_per_run=None,
                        item_filter=item_filter,
                    )
                    total_pages += stats.get("pages", 0)
                    total_records += stats.get("saved", 0)
                    total_received += stats.get("received", 0)
                    total_skipped += stats.get("skipped", 0)
                    modality_errors = stats.get("errors", [])
                    errors.extend(modality_errors)
                    progress.progress(idx / max(len(ordered_modalities), 1))
                    if modality_errors:
                        if any("429" in str(error) for error in modality_errors):
                            stopped_by_rate_limit = True
                            status_box.warning(
                                "O PNCP pediu redução de ritmo (429). O progresso ficou salvo e a próxima execução retoma do ponto interrompido."
                            )
                            break
                        status_box.warning(
                            f"{name} ficou incompleta por lentidão do PNCP. "
                            "O ponto foi salvo e a reconciliação continuará pelas demais modalidades."
                        )
                        if idx < len(ordered_modalities):
                            time.sleep(3.0)
                        continue
                    if idx < len(ordered_modalities):
                        time.sleep(1.2)

                progress.empty()
                final_status = "partial" if errors else "success"
                db.finish_sync_run(run_id, final_status, total_pages, total_records, " | ".join(errors))
                if not errors:
                    catalog_after = db.global_catalog_count()
                    new_items = max(0, catalog_after - catalog_before)
                    status_box.success(
                        f"Sincronização concluída: {total_received} registros consultados em {total_pages} página(s) · "
                        f"{total_skipped} anterior(es) ao marco ignorado(s) · {total_records} registro(s) aplicável(is) · "
                        f"{new_items} novo(s) edital(is). Existentes foram atualizados sem duplicação."
                    )
                elif not stopped_by_rate_limit:
                    status_box.warning(
                        f"Sincronização parcial: {total_received} registros recebidos. Tudo que chegou foi preservado."
                    )
                time.sleep(1.0)
                st.rerun()

        c1, c2 = st.columns([1, 2])
        horizon_days = c1.selectbox(
            "Horizonte da reconciliação completa",
            [7, 15, 30, 60], index=2, key="admin_sync_horizon",
            format_func=lambda value: f"{value} dias",
            help="Usado somente na reconciliação completa. A atualização normal busca apenas publicações novas/recentes.",
        )

        # A atualização normal usa a Data de Atualização Global do PNCP.
        # Se houver um checkpoint incompleto, ele é retomado primeiro com o mesmo
        # modo, intervalo e identidade usados na execução interrompida.
        if c2.button("Atualizar novidades do PNCP", type="primary", width="stretch"):
            pending = db.latest_incomplete_global_sync_period("PNCP_INCREMENTAL")

            if pending:
                pending_key = str(pending.get("publication_day") or "")
                pending_mode = PncpClient.checkpoint_mode_from_key(pending_key)
                pending_range = PncpClient.parse_range_checkpoint_key(pending_key)

                if pending_mode not in {"publication", "update"} or not pending_range:
                    st.error(
                        "Existe um checkpoint incremental incompleto com formato inválido. "
                        "A sincronização foi interrompida para evitar perda de registros."
                    )
                else:
                    resume_start, resume_end = pending_range
                    incremental_client = PncpClient(
                        mode=pending_mode,
                        timeout=30,
                        page_delay=0.25,
                        max_attempts=4,
                    )
                    _run_pncp_sync(
                        incremental_client,
                        resume_start,
                        resume_end,
                        "PNCP_INCREMENTAL" if pending_mode == "update" else "PNCP_INCREMENTAL_RESUME",
                        "PNCP_INCREMENTAL",
                        str(pending.get("period_start") or resume_start.isoformat()),
                        str(pending.get("period_end") or resume_end.isoformat()),
                        "Retomando atualização PNCP",
                    )

            else:
                anchor_run = db.last_successful_sync_run(
                    ["PNCP_INCREMENTAL", "PNCP_FULL", "PNCP"]
                )

                if not anchor_run and catalog_stats["total"] == 0:
                    st.warning(
                        "O catálogo ainda está vazio. Execute primeiro a carga completa abaixo."
                    )
                elif not anchor_run:
                    st.error(
                        "O catálogo possui dados, mas não há um marco de sincronização concluída "
                        "confiável. A atualização incremental foi interrompida para evitar lacunas."
                    )
                else:
                    raw_anchor = (
                        anchor_run.get("finished_at")
                        or anchor_run.get("started_at")
                    )
                    try:
                        anchor_dt = datetime.fromisoformat(
                            str(raw_anchor).replace("Z", "+00:00")
                        )
                    except (TypeError, ValueError):
                        st.error(
                            "O marco da última sincronização concluída é inválido. "
                            "A atualização incremental não foi iniciada."
                        )
                    else:
                        # Um dia de sobreposição protege contra atrasos de disponibilização
                        # e o upsert por número de controle evita duplicação.
                        incremental_start = anchor_dt.date() - timedelta(days=1)
                        incremental_end = date.today()

                        incremental_client = PncpClient(
                            mode="update",
                            timeout=30,
                            page_delay=0.25,
                            max_attempts=4,
                        )
                        _run_pncp_sync(
                            incremental_client,
                            incremental_start,
                            incremental_end,
                            "PNCP_INCREMENTAL",
                            "PNCP_INCREMENTAL",
                            incremental_start.isoformat(),
                            incremental_end.isoformat(),
                            "Atualizando novidades PNCP",
                        )

        with st.expander("Reconciliação completa do catálogo", expanded=False):
            st.caption(
                "Use quando quiser conferir novamente todas as oportunidades abertas. É mais demorado; "
                "a atualização diária normal acima é incremental."
            )
            pending_full = db.latest_incomplete_global_sync_period("PNCP_FULL_OPEN")
            if pending_full:
                st.info(
                    "A reconciliação completa já está na fila automática. O worker "
                    "retomará os checkpoints até concluir todas as modalidades; não é necessário clicar novamente."
                )
            if st.button(
                "Iniciar reconciliação automática das oportunidades abertas",
                key="admin_full_reconcile",
                width="stretch",
                disabled=bool(pending_full),
            ):
                full_start = date.today()
                full_end = date.today() + timedelta(days=int(horizon_days))
                checkpoint_key = (
                    f"open_proposals:range:{full_start.isoformat()}:{full_end.isoformat()}"
                )
                for modality_code in sorted({int(code) for code in MODALITIES.values()}):
                    db.save_global_checkpoint(
                        modality_code,
                        "",
                        checkpoint_key,
                        1,
                        False,
                        0,
                        "",
                        source="PNCP_FULL_OPEN",
                        period_start=full_start.isoformat(),
                        period_end=full_end.isoformat(),
                    )
                st.success(
                    "Reconciliação agendada. O processamento continuará automaticamente "
                    "a cada 15 minutos, retomando do último checkpoint até finalizar."
                )

        if recent_runs:
            st.markdown("#### Histórico recente")
            st.caption("Datas e horários exibidos no fuso de Brasília (America/Sao_Paulo).")
            rows = []
            for run in recent_runs:
                error_text = str(run.get("errors") or "")
                rows.append({
                    "Início": _format_datetime(run.get("started_at")),
                    "Fim": _format_datetime(run.get("finished_at")),
                    "Status": run.get("status"),
                    "Páginas": run.get("pages"),
                    "Aplicados": run.get("records"),
                    "429": error_text.count("429"),
                    "Resumo": "Limite temporário do PNCP" if "429" in error_text else (error_text[:160] or "Sem erros"),
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


    if admin_section == "E-mails":
        st.subheader("E-mails transacionais")
        cfg = mail_config()
        if mail_is_configured():
            st.success("SMTP configurado. Convites e recuperações podem ser enviados automaticamente.")
        else:
            st.warning("SMTP ainda não configurado. O sistema continuará exibindo códigos para envio manual.")
        st.write(f'**Servidor:** {cfg["host"] or "Não configurado"}')
        st.write(f'**Remetente:** {cfg["from_email"] or "Não configurado"}')
        st.write(f'**URL pública:** {cfg["app_url"] or "Não configurada"}')
        test_email = st.text_input("Enviar teste para", value=user.get("email", ""), key="smtp_test_email")
        if st.button("Testar envio", disabled=not mail_is_configured() or not test_email):
            try:
                send_test_email(test_email)
                db.record_email_event("test", test_email, "sent")
                st.success("E-mail de teste enviado.")
            except MailError as error:
                db.record_email_event("test", test_email, "error", str(error))
                st.error(str(error))
        events = db.list_email_events(20)
        if events:
            st.markdown("#### Histórico")
            st.dataframe(pd.DataFrame(events), hide_index=True, width="stretch")
        st.caption("As credenciais SMTP não são salvas no banco. Elas serão configuradas com variáveis de ambiente no servidor.")

    if admin_section == "Segurança e compliance":
        st.subheader("Segurança e compliance")
        st.caption("Controles operacionais de segurança e rastreabilidade. Termos e Política devem passar por revisão jurídica antes do lançamento.")
        sm=security.metrics()
        s1,s2,s3,s4=st.columns(4)
        s1.metric("Falhas em 24h",sm["failed_24h"])
        s2.metric("Bloqueios temporários",sm["blocked"])
        s3.metric("Sessões ativas",sm["active_sessions"])
        s4.metric("Backups verificados",sm["verified_backups"])
        st.markdown("#### Política ativa")
        st.write(f"**Login:** {security.LOGIN_MAX_FAILURES} falhas em {security.LOGIN_WINDOW_MINUTES} minutos → bloqueio temporário.")
        st.write(f"**Sessão:** {security.SESSION_IDLE_MINUTES} min sem atividade ou {security.SESSION_ABSOLUTE_HOURS}h de duração máxima.")
        st.write("**Privacidade:** a nova trilha de segurança armazena hash do IP, não o endereço bruto.")
        backup_flash = st.session_state.pop("rc26_backup_flash", None)
        if backup_flash:
            st.success(f"Backup {backup_flash} criado e validado.")
        if st.button("Criar backup verificado",type="primary",key="rc25_backup"):
            try:
                r=security.create_verified_backup()
                st.session_state["rc26_backup_flash"] = r["filename"]
                st.rerun()
            except SecurityError as error:
                st.error(str(error))
        backups=security.backup_history(30)
        if backups:
            st.dataframe(pd.DataFrame([{"Data":r.get("created_at"),"Arquivo":r.get("filename"),"Tamanho":r.get("size_bytes"),"Integridade":r.get("integrity_status")} for r in backups]),hide_index=True,width="stretch")
        events_security=security.recent_events(250)
        if events_security:
            st.markdown("#### Eventos de segurança")
            st.dataframe(pd.DataFrame([{"Data":r.get("created_at"),"Evento":r.get("event_type"),"Conta":r.get("subject"),"IP hash":r.get("ip_hash"),"Sucesso":"Sim" if r.get("success") else "Não","Detalhes":r.get("details")} for r in events_security]),hide_index=True,width="stretch")
        st.markdown("#### Checklist de lançamento")
        checks=[("HTTPS obrigatório em produção",ENVIRONMENT!="development"),("Rate limiting de login",True),("Expiração de sessão",True),("Auditoria administrativa",True),("Backups verificáveis",sm["verified_backups"]>0),("Termos e Política versionados",bool(LEGAL_VERSION))]
        for label,ok in checks:st.write(("✅ " if ok else "⚠️ ")+label)

    if admin_section == "Sistema":
        st.subheader("Sistema")
        stats = db.system_stats()
        a, b, c, d = st.columns(4)
        a.metric("Empresas", stats["companies"])
        b.metric("Usuários", stats["users"])
        c.metric("Testes ativos", stats["active_trials"])
        d.metric("Aprovações pendentes", stats["pending_requests"])
        st.write(f"**Versão:** {APP_VERSION}")
        st.write(f"**Ambiente:** {ENVIRONMENT}")
        st.write(f"**Banco:** {db.path}")
        st.write(f"**Logs:** {PROJECT_ROOT / 'logs' / 'licitanexo.log'}")
        st.write(f"**Backups automáticos:** {PROJECT_ROOT / 'backups'}")
        if ENVIRONMENT == "development":
            st.warning("Modo desenvolvimento ativo. Não use este modo no servidor público.")
        else:
            st.success("Modo produção ativo.")
        st.info("Para atualizar com segurança, use o script update_licitanexo.ps1. Ele preserva banco, .venv, logs e backups.")




def _radar_quantity_text(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return "—"
    if number.is_integer():
        return f"{int(number):,}".replace(",", ".")
    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _radar_item_price_text(row: dict) -> str:
    if row.get("confidential"):
        return "Preço sigiloso"
    try:
        price = float(row.get("unit_price") or 0)
    except (TypeError, ValueError):
        price = 0
    return format_brl(price) if price > 0 else "Sem preço publicado"


def _render_radar_item_summary(opportunity: dict, pack: dict) -> None:
    """Mostra itens oficiais já abertos para a decisão acontecer no próprio Radar."""
    control = str(opportunity.get("pncp_control_number") or "").strip()
    preview = list(pack.get("items") or [])
    total = int(pack.get("item_count") or len(preview))
    count_known = bool(pack.get("count_known"))
    has_more = bool(pack.get("has_more")) or total > len(preview)
    error = str(pack.get("items_error") or "").strip()

    if count_known:
        count_label = f"{total} item(ns)"
    elif preview:
        count_label = f"{max(total, len(preview))}+ item(ns)"
    else:
        count_label = "itens oficiais"

    lines = [
        f'<div class="radar-items-box"><div class="radar-items-title">📦 Itens da licitação · {escape(count_label)}</div>'
    ]
    if error:
        lines.append('<div class="radar-items-more">Itens temporariamente indisponíveis no PNCP. O restante do resultado continua acessível.</div>')
    elif not preview:
        lines.append('<div class="radar-items-more">O PNCP não publicou itens estruturados para esta contratação.</div>')
    else:
        for row in preview:
            number = escape(str(row.get("number") or ""))
            description = str(row.get("description") or "Item não descrito").strip()
            if len(description) > 150:
                description = description[:147].rstrip() + "..."
            description = escape(description)
            quantity = _radar_quantity_text(row.get("quantity"))
            unit = escape(str(row.get("unit_measure") or "").strip())
            qty_label = f"{quantity} {unit}".strip()
            price_label = escape(_radar_item_price_text(row))
            prefix = f"<b>{number}.</b> " if number else ""
            lines.append(
                f'<div class="radar-item-row"><div class="radar-item-name">{prefix}{description}</div>'
                f'<div class="radar-item-qty">{escape(qty_label)}</div>'
                f'<div class="radar-item-price">{price_label}</div></div>'
            )
        remaining = max(total - len(preview), 0) if count_known else 0
        if remaining:
            lines.append(f'<div class="radar-items-more">+ {remaining} outro(s) item(ns)</div>')
        elif has_more and not count_known:
            lines.append('<div class="radar-items-more">Há outros itens nesta contratação.</div>')
    lines.append("</div>")
    st.markdown("".join(lines), unsafe_allow_html=True)

    if not control or not preview or not has_more:
        return

    state_key = f"radar_all_items_open_{opportunity.get('id') or control}"
    opened = bool(st.session_state.get(state_key))
    label = "Mostrar apenas o resumo" if opened else "Ver todos os itens"
    if st.button(label, key=f"radar_all_items_button_{opportunity.get('id') or control}", width="stretch"):
        st.session_state[state_key] = not opened
        st.rerun()

    if not opened:
        return
    try:
        with st.spinner("Carregando a lista completa de itens do PNCP..."):
            full_items = _cached_full_contract_items(control)
    except PncpItemsError:
        st.caption("Não foi possível abrir a lista completa agora. O resumo acima continua disponível.")
        return
    if not full_items:
        st.caption("Nenhum item estruturado adicional foi publicado pelo PNCP.")
        return

    rows = []
    for row in full_items[:120]:
        rows.append({
            "Item": row.get("number") or "",
            "Descrição": row.get("description") or "",
            "Quantidade": _radar_quantity_text(row.get("quantity")),
            "Unidade": row.get("unit_measure") or "",
            "Preço ref.": _radar_item_price_text(row),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=min(360, 38 + 34 * len(rows)))
    if len(full_items) > 120:
        st.caption(f"Mostrando 120 de {len(full_items)} itens para manter a tela rápida.")

def search_page(user):
    company_id = user["company_id"]
    profile = db.get_company_profile(company_id)

    st.header("🔎 Buscar Editais")
    st.caption("Monitoramos as principais fontes de licitações públicas do Brasil. Separe assuntos diferentes por vírgula: medicamentos, uniformes, luvas.")

    profile_ready = profile_search_ready(profile)
    profile_enabled_raw = profile.get("profile_search_enabled")
    profile_enabled_default = bool(int(profile_enabled_raw if profile_enabled_raw is not None else 1))
    use_profile = st.toggle(
        "✨ Priorizar oportunidades compatíveis com minha empresa",
        value=profile_enabled_default,
        key="radar_profile_match",
        help="Ordena os resultados por aderência ao perfil da empresa sem esconder oportunidades.",
    )
    if use_profile and not profile_ready:
        st.info("Complete produtos/serviços, CNAEs ou palavras-chave em Minha Empresa para ativar a aderência automática.")

    criteria = st.session_state.get("radar_search_criteria") or {}

    def _csv_list(value):
        return [item.strip().upper() for item in str(value or "").replace(";", ",").split(",") if item.strip()]

    activity_options = ["Produtos", "Serviços", "Produtos e serviços", "Todos"]
    default_nature = criteria.get("nature") or profile.get("search_nature") or profile.get("activity_type") or "Produtos"
    if default_nature not in activity_options:
        default_nature = "Produtos"
    default_states = criteria.get("states") if "states" in criteria else _csv_list(profile.get("service_states"))
    default_states = [state for state in default_states if state in BRAZIL_STATES]
    default_modalities = criteria.get("modalities") if "modalities" in criteria else _csv_list(profile.get("search_modalities"))
    # Modalidades não são siglas; recupera a grafia canônica após a conversão acima.
    if "modalities" not in criteria:
        saved_modalities = [item.strip() for item in str(profile.get("search_modalities") or "").split("|") if item.strip()]
        default_modalities = [item for item in saved_modalities if item in MODALITIES]
    else:
        default_modalities = [item for item in default_modalities if item in MODALITIES]

    srp_options = ["Todos", "Sim", "Não"]
    order_options = ["Certame mais próximo", "Mais recentes", "Maior valor", "Menor valor"]
    default_srp = criteria.get("srp") or profile.get("search_srp") or "Todos"
    default_order = criteria.get("order") or profile.get("search_order") or "Certame mais próximo"
    if default_srp not in srp_options: default_srp = "Todos"
    if default_order not in order_options: default_order = "Certame mais próximo"

    # Campos da busca ficam como rascunho na sessão. Alterar texto, UF ou qualquer
    # filtro NÃO executa uma nova pesquisa. A busca só muda quando o usuário
    # clicar explicitamente em "Buscar editais". Isso evita Enter duplo e
    # retrabalho ao ajustar somente um critério.
    draft_defaults = {
        "radar_draft_keyword": criteria.get("keyword") if "keyword" in criteria else str(profile.get("search_keyword") or ""),
        "radar_draft_nature": default_nature,
        "radar_draft_srp": default_srp,
        "radar_draft_states": default_states,
        "radar_draft_modalities": default_modalities,
        "radar_draft_minimum": "" if (criteria.get("minimum") if "minimum" in criteria else profile.get("search_minimum")) in (None, "") else str(criteria.get("minimum") if "minimum" in criteria else profile.get("search_minimum")),
        "radar_draft_maximum": "" if (criteria.get("maximum") if "maximum" in criteria else profile.get("search_maximum")) in (None, "") else str(criteria.get("maximum") if "maximum" in criteria else profile.get("search_maximum")),
    }
    for draft_key, draft_value in draft_defaults.items():
        if draft_key not in st.session_state:
            st.session_state[draft_key] = draft_value

    st.text_input(
        "O que você procura?",
        key="radar_draft_keyword",
        placeholder="Ex.: medicamentos, uniformes, manutenção de ar-condicionado",
        help="Digite normalmente. A pesquisa só será executada quando você clicar em Buscar editais. Use vírgulas para alternativas.",
    )
    c1, c2 = st.columns(2)
    c1.selectbox("Tipo", activity_options, key="radar_draft_nature")
    c2.selectbox("Registro de preços", srp_options, key="radar_draft_srp")

    st.multiselect(
        "UFs", list(BRAZIL_STATES), key="radar_draft_states",
        placeholder="Vazio = Brasil inteiro",
        help="Selecione uma ou várias UFs. Vazio significa todos os estados.",
    )
    st.multiselect(
        "Modalidades", list(MODALITIES.keys()), key="radar_draft_modalities",
        placeholder="Vazio = todas as modalidades",
    )

    d1, d2 = st.columns(2)
    d1.text_input("Valor mínimo", key="radar_draft_minimum", placeholder="Sem mínimo")
    d2.text_input("Valor máximo", key="radar_draft_maximum", placeholder="Sem máximo")

    submitted = st.button("🔎 Buscar editais", type="primary", width="stretch", key="radar_search_button")

    # O calendário possui uma aba própria. A tela de busca permanece focada apenas em filtros e resultados.

    if submitted:
        keyword = str(st.session_state.get("radar_draft_keyword") or "")
        usage.record_search(company_id, user.get("id", ""), keyword)
        nature = st.session_state.get("radar_draft_nature") or "Todos"
        srp_label = st.session_state.get("radar_draft_srp") or "Todos"
        horizon_label = "Todos os abertos"
        selected_states = list(st.session_state.get("radar_draft_states") or [])
        selected_modalities = list(st.session_state.get("radar_draft_modalities") or [])
        minimum_text = str(st.session_state.get("radar_draft_minimum") or "")
        maximum_text = str(st.session_state.get("radar_draft_maximum") or "")
        order_label = "Mais recentes"

        minimum = parse_brl(minimum_text) if minimum_text.strip() else None
        maximum = parse_brl(maximum_text) if maximum_text.strip() else None
        if minimum_text and minimum is None:
            st.error("O valor mínimo não pôde ser interpretado.")
        elif maximum_text and maximum is None:
            st.error("O valor máximo não pôde ser interpretado.")
        else:
            criteria = {
                "keyword": keyword.strip(), "nature": nature,
                "states": selected_states, "modalities": selected_modalities,
                "srp": srp_label, "horizon": horizon_label, "order": order_label,
                "minimum": minimum, "maximum": maximum,
                "use_profile": bool(use_profile and profile_ready),
            }
            st.session_state.radar_search_criteria = criteria
            st.session_state.catalog_page = 1
            # A última busca confirmada vira também o padrão da próxima sessão.
            db.save_company_profile(
                company_id,
                search_keyword=keyword.strip(), search_nature=nature,
                service_states=", ".join(selected_states),
                search_modalities="|".join(selected_modalities), search_srp=srp_label,
                search_horizon=horizon_label, search_minimum=minimum,
                search_maximum=maximum, search_order=order_label,
            )

    if not criteria:
        st.info("Preencha o que fizer sentido e clique em Buscar editais. Campos vazios ampliam a pesquisa.")
        return

    today = date.today()
    horizon_days = {
        "Hoje": 0, "Próximos 7 dias": 7, "Próximos 15 dias": 15, "Próximos 30 dias": 30,
        "Próximos 60 dias": 60, "Próximos 90 dias": 90,
    }
    closing_to = None
    if criteria["horizon"] in horizon_days:
        closing_to = (today + timedelta(days=horizon_days[criteria["horizon"]])).isoformat()
    order_map = {
        "Certame mais próximo": "certame", "Mais recentes": "recent",
        "Maior valor": "value_desc", "Menor valor": "value_asc",
    }
    # Diagnóstico transparente da busca: primeiro aplicamos filtros estruturais, depois
    # o tipo Produto/Serviço e por último a palavra-chave. Assim o cliente entende por
    # que 1.390 editais no catálogo podem virar 15 resultados sem imaginar que a busca falhou.
    structural_items = db.list_global_catalog(
        search="", states=criteria["states"], modalities=criteria["modalities"],
        srp=None if criteria["srp"] == "Todos" else criteria["srp"] == "Sim",
        minimum=criteria["minimum"], maximum=criteria["maximum"],
        closing_from=today.isoformat(), closing_to=closing_to, limit=10000,
        order_by=order_map[criteria["order"]],
    )
    nature_items = [item for item in structural_items if _nature_matches(item, criteria["nature"])]
    items = db.list_global_catalog(
        search=criteria["keyword"], states=criteria["states"], modalities=criteria["modalities"],
        srp=None if criteria["srp"] == "Todos" else criteria["srp"] == "Sim",
        minimum=criteria["minimum"], maximum=criteria["maximum"],
        closing_from=today.isoformat(), closing_to=closing_to, limit=10000,
        order_by=order_map[criteria["order"]],
    )
    items = [item for item in items if _nature_matches(item, criteria["nature"])]
    for item in items:
        item["nature"] = _opportunity_nature(item)
    if criteria.get("use_profile") and profile_ready:
        items = rank_opportunities(items, profile)

    catalog_total = db.global_catalog_count()
    st.caption(
        f"Catálogo: {catalog_total} · após prazo/UF/modalidade/valor: {len(structural_items)} · "
        f"tipo {criteria['nature']}: {len(nature_items)} · resultado da palavra-chave: {len(items)}"
    )

    st.markdown("### Resultado")
    st.caption(f"{len(items)} edital(is) encontrado(s). Ajuste qualquer filtro acima e pesquise novamente quando quiser.")
    if not items:
        st.info("Nenhum edital corresponde a esta combinação. Os filtros acima foram mantidos para você alterar somente o necessário.")
        return

    filter_description = (
        f'Texto: {criteria["keyword"] or "todos"}; tipo: {criteria["nature"]}; '
        f'UFs: {", ".join(criteria["states"]) if criteria["states"] else "todas"}; '
        f'modalidades: {", ".join(criteria["modalities"]) if criteria["modalities"] else "todas"}'
    )
    with st.expander("Exportar resultado"):
        e1, e2 = st.columns(2)
        e1.download_button(
            "Exportar Excel", catalog_excel(items, user["company_name"], filter_description),
            "editais_licitanexo.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
        e2.download_button(
            "Exportar PDF", catalog_pdf(items, user["company_name"], filter_description),
            "editais_licitanexo.pdf", "application/pdf", width="stretch",
        )

    per_page = 8
    total_pages = max((len(items) + per_page - 1) // per_page, 1)
    current_page = min(max(int(st.session_state.get("catalog_page", 1)), 1), total_pages)
    first = (current_page - 1) * per_page
    page_items = items[first:first + per_page]
    visible_controls = tuple(str(row.get("pncp_control_number") or "").strip() for row in page_items)
    item_preview_map = _cached_radar_item_summaries(visible_controls)

    for index in range(0, len(page_items), 2):
        columns = st.columns(2)
        for column, item in zip(columns, page_items[index:index + 2]):
            with column:
                with st.container(border=True):
                    if criteria.get("use_profile") and "_match_score" in item:
                        score = int(item.get("_match_score") or 0)
                        st.markdown(f"**✨ Aderência à sua empresa: {score}%**")
                        reasons = item.get("_match_reasons") or []
                        if reasons:
                            st.caption("Encontrado por: " + " · ".join(reasons[:3]))
                    st.markdown(f'#### {item.get("agency") or "Órgão não informado"}')
                    st.write(item.get("object") or "Objeto não informado")
                    m1, m2 = st.columns(2)
                    m1.metric("Valor", format_brl(item.get("estimated_value")))
                    deadline = item.get("closing_at")
                    try:
                        deadline_text = datetime.fromisoformat(str(deadline).replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M") if deadline else "Não informado"
                    except ValueError:
                        deadline_text = str(deadline)[:16].replace("T", " ") if deadline else "Não informado"
                    m2.metric("Fim das propostas", deadline_text)
                    st.caption(
                        f'{item.get("nature")} · {item.get("city") or "Município não informado"}/{item.get("state") or "--"} · '
                        f'{item.get("modality") or "Modalidade não informada"}'
                    )
                    source_name, portal_label = opportunity_source_and_portal(
                        item.get("source_name"), item.get("source_channel"), item.get("source_url")
                    )
                    st.caption(f"**Fonte:** {source_name} · **Portal de disputa:** {portal_label}")
                    control_number = str(item.get("pncp_control_number") or "").strip()
                    _render_radar_item_summary(
                        item,
                        item_preview_map.get(control_number, {
                            "items": [], "item_count": 0, "count_known": False,
                            "has_more": False, "items_error": "",
                        }),
                    )
                    if st.button("⭐ Salvar em Meus Editais", key=f'open_catalog_{item["id"]}', type="primary", width="stretch"):
                        try:
                            opportunity_id = db.add_global_catalog_item_to_pipeline(company_id, item["id"])
                            if opportunity_id:
                                st.session_state.pipeline_opportunity_id = opportunity_id
                                st.session_state["_navigation_request"] = "⭐ Meus Editais"
                                st.rerun()
                            st.success("Edital salvo.")
                        except Exception as error:
                            st.error(f"Não foi possível salvar este edital: {error}")
                    source_url = str(item.get("source_url") or "")
                    official_url = pncp_official_url(item.get("pncp_control_number"))
                    link_cols = st.columns(2) if source_url.startswith(("http://", "https://")) and official_url else [st]
                    if source_url.startswith(("http://", "https://")):
                        link_cols[0].link_button("🌐 Ir para o portal de disputa", source_url, width="stretch")
                    if official_url:
                        target = link_cols[1] if len(link_cols) > 1 else link_cols[0]
                        target.link_button("📄 Ver no PNCP", official_url, width="stretch")

    st.divider()
    nav1, nav2, nav3, nav4 = st.columns(4)
    if nav1.button("⏮ Primeira", disabled=current_page <= 1, width="stretch"):
        st.session_state.catalog_page = 1; st.rerun()
    if nav2.button("◀ Anterior", disabled=current_page <= 1, width="stretch"):
        st.session_state.catalog_page = current_page - 1; st.rerun()
    if nav3.button("Próxima ▶", disabled=current_page >= total_pages, width="stretch"):
        st.session_state.catalog_page = current_page + 1; st.rerun()
    if nav4.button("Última ⏭", disabled=current_page >= total_pages, width="stretch"):
        st.session_state.catalog_page = total_pages; st.rerun()
    st.caption(f"Página {current_page} de {total_pages}")


def essential_account_page(user):
    """Conta enxuta + exatamente as mesmas preferências que aparecem na busca."""
    account_page(user)
    st.divider()
    st.subheader("Preferências de busca")
    st.caption("Salve sua pesquisa padrão. Quando abrir Buscar Editais, esses campos já estarão prontos para você ajustar.")
    profile = db.get_company_profile(user["company_id"])

    activity_options = ["Produtos", "Serviços", "Produtos e serviços", "Todos"]
    srp_options = ["Todos", "Sim", "Não"]
    order_options = ["Certame mais próximo", "Mais recentes", "Maior valor", "Menor valor"]

    default_nature = profile.get("search_nature") or profile.get("activity_type") or "Produtos"
    if default_nature not in activity_options: default_nature = "Produtos"
    default_states = [x.strip().upper() for x in str(profile.get("service_states") or "").replace(";", ",").split(",") if x.strip().upper() in BRAZIL_STATES]
    default_modalities = [x.strip() for x in str(profile.get("search_modalities") or "").split("|") if x.strip() in MODALITIES]
    default_srp = profile.get("search_srp") if profile.get("search_srp") in srp_options else "Todos"
    default_order = profile.get("search_order") if profile.get("search_order") in order_options else "Certame mais próximo"

    with st.form("essential_search_profile", clear_on_submit=False, enter_to_submit=False):
        keyword = st.text_input(
            "O que você procura?", value=profile.get("search_keyword") or "",
            placeholder="Ex.: medicamentos, uniformes, manutenção de ar-condicionado",
        )
        c1, c2 = st.columns(2)
        nature = c1.selectbox("Tipo", activity_options, index=activity_options.index(default_nature))
        srp = c2.selectbox("Registro de preços", srp_options, index=srp_options.index(default_srp))
        states = st.multiselect("UFs", list(BRAZIL_STATES), default=default_states, placeholder="Vazio = Brasil inteiro")
        modalities = st.multiselect("Modalidades", list(MODALITIES.keys()), default=default_modalities, placeholder="Vazio = todas")
        d1, d2 = st.columns(2)
        min_value = d1.text_input("Valor mínimo", value="" if profile.get("search_minimum") is None else str(profile.get("search_minimum")))
        max_value = d2.text_input("Valor máximo", value="" if profile.get("search_maximum") is None else str(profile.get("search_maximum")))
        if st.form_submit_button("Salvar preferências", type="primary", width="stretch"):
            minimum = parse_brl(min_value) if min_value.strip() else None
            maximum = parse_brl(max_value) if max_value.strip() else None
            if min_value and minimum is None:
                st.error("O valor mínimo não pôde ser interpretado.")
            elif max_value and maximum is None:
                st.error("O valor máximo não pôde ser interpretado.")
            else:
                db.save_company_profile(
                    user["company_id"],
                    search_keyword=keyword.strip(), search_nature=nature,
                    service_states=", ".join(states), search_modalities="|".join(modalities),
                    search_srp=srp, search_horizon="Todos os abertos",
                    search_minimum=minimum, search_maximum=maximum, search_order="Mais recentes",
                )
                st.session_state.pop("radar_search_criteria", None)
                st.success("Preferências salvas.")


def dashboard_page(user):
    company_id = user["company_id"]
    rows = db.list_opportunities(company_id)
    active = [row for row in rows if row["stage"] not in ("Ganha", "Perdida", "Arquivada")]
    competition = db.competition_summary(company_id)
    calendar = db.participation_calendar(company_id)

    st.header(f"{_greeting(user)} 👋")
    phrase = st.session_state.get("motivational_phrase") or random.choice(MOTIVATIONAL_PHRASES)
    st.session_state.motivational_phrase = phrase
    now = _local_now()
    st.caption(f"{now.strftime('%d/%m/%Y')} · {now.strftime('%H:%M')} — {phrase}")
    with st.expander("❓ Como usar a Central"):
        st.write("Use esta tela como seu resumo do dia. Se houver um alerta, resolva primeiro. Depois veja o próximo certame ou abra a Jornada.")

    expired, expiring = _document_alerts(company_id)
    if expired:
        names = ", ".join(f"{name} ({expiry.strftime('%d/%m/%Y')})" for name, expiry in expired[:4])
        st.error(f"⚠️ Documento(s) vencido(s): {names}. Atualize o Passaporte.")
    elif expiring:
        names = ", ".join(f"{name} ({expiry.strftime('%d/%m/%Y')})" for name, expiry in expiring[:4])
        st.warning(f"Documento(s) vencendo em até 30 dias: {names}.")

    next_event = calendar[0] if calendar else None
    next_text = "Nenhum agendado"
    if next_event and next_event.get("certame"):
        try:
            next_text = datetime.fromisoformat(str(next_event["certame"]).replace("Z", "+00:00")).strftime("%d/%m %H:%M")
        except (TypeError, ValueError):
            next_text = str(next_event["certame"])[:16].replace("T", " ")

    st.markdown("### O que precisa de atenção hoje")
    c1, c2, c3 = st.columns(3)
    c1.metric("Licitações em andamento", len(active))
    c2.metric("Valor em disputa", format_brl(competition["total_value"]))
    c3.metric("Próximo certame", next_text)

    q1, q2, q3 = st.columns(3)
    if q1.button("🔎 Buscar oportunidade", width="stretch", type="primary"):
        st.session_state["_navigation_request"] = "Radar de Oportunidades"; st.rerun()
    if q2.button("📁 Abrir Jornada", width="stretch"):
        st.session_state["_navigation_request"] = "Meus Editais"; st.rerun()
    if q3.button("🏢 Atualizar Passaporte", width="stretch"):
        st.session_state["_navigation_request"] = "Passaporte da Empresa"; st.rerun()

    st.markdown("### Próximos certames")
    if calendar:
        table = pd.DataFrame(calendar[:10])
        table.rename(columns={"certame": "Data", "agency": "Órgão", "object": "Objeto", "quoted_value": "Proposta"}, inplace=True)
        table["Proposta"] = table["Proposta"].map(format_brl)
        st.dataframe(table[["Data", "Órgão", "Objeto", "Proposta"]], hide_index=True, width="stretch")
    else:
        st.info("Nenhuma participação com data definida. Na Jornada, marque Participar e informe a data do certame.")

def calendar_page(user):
    company_id = user["company_id"]
    st.markdown(
        """<style>
        .calendar-title {font-size:2rem;font-weight:850;line-height:1.1;color:#F7F9FC;margin:.15rem 0 .3rem;letter-spacing:-.02em;}
        .calendar-subtitle {color:#94A3B8;font-size:.96rem;margin-bottom:1.15rem;}
        .month-card {background:#FFFFFF;border:1px solid #E5EAF0;border-radius:18px;padding:1.1rem 1.15rem 1.2rem;box-shadow:0 10px 28px rgba(7,24,45,.09);color:#10243F;}
        .month-head {display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem;}
        .month-name {font-size:1.1rem;font-weight:850;letter-spacing:-.01em;}
        .month-count {font-size:.75rem;font-weight:750;color:#8B6412;background:#FFF4D5;border:1px solid #F2D58C;padding:.28rem .55rem;border-radius:999px;}
        .weekdays,.month-grid {display:grid;grid-template-columns:repeat(7,1fr);gap:5px;text-align:center;}
        .weekdays {color:#8896A8;font-size:.72rem;font-weight:800;margin-bottom:5px;text-transform:uppercase;}
        .day {height:38px;display:flex;align-items:center;justify-content:center;border-radius:10px;font-size:.86rem;color:#394A5E;}
        .day.event {background:#C99A2E;color:#FFF;font-weight:850;box-shadow:0 5px 12px rgba(201,154,46,.24);}
        .day.today {outline:2px solid #AAB6C4;outline-offset:-2px;font-weight:800;}
        .agenda-head {display:flex;align-items:flex-end;justify-content:space-between;margin:.1rem 0 .7rem;}
        .agenda-head h3 {font-size:1.35rem;margin:0;color:#F7F9FC;}
        .agenda-head span {font-size:.78rem;color:#94A3B8;}
        .agenda-card {border:1px solid #263B55;background:#102035;border-radius:14px;padding:.8rem .9rem;margin-bottom:.55rem;}
        .agenda-top {display:flex;gap:.7rem;align-items:flex-start;}
        .date-badge {flex:0 0 54px;background:#0B1728;border:1px solid #31465F;border-radius:11px;padding:.42rem .25rem;text-align:center;color:#F7F9FC;}
        .date-badge strong {display:block;color:#D7A52E;font-size:1.05rem;line-height:1.05;}
        .date-badge small {display:block;color:#AAB6C4;font-size:.7rem;margin-top:.15rem;text-transform:uppercase;}
        .agenda-agency {font-size:.91rem;font-weight:800;color:#F7F9FC;line-height:1.3;margin-bottom:.18rem;}
        .agenda-object {font-size:.81rem;color:#B8C3D1;line-height:1.35;}
        .agenda-meta {font-size:.72rem;color:#8190A3;margin-top:.32rem;}
        .notes-panel-title {font-size:1.35rem;font-weight:820;color:#F7F9FC;margin:1.35rem 0 .15rem;}
        .notes-panel-sub {font-size:.84rem;color:#94A3B8;margin-bottom:.7rem;}
        @media(max-width:768px){.calendar-title{font-size:1.6rem}.agenda-head h3{font-size:1.15rem}.day{height:34px}.month-card{padding:.85rem}}
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<style>
        .calendar-title,.agenda-head h3,.notes-panel-title{color:#293746 !important;font-weight:400 !important;}
        .calendar-subtitle,.agenda-head span,.notes-panel-sub{color:#667786 !important;}
        .month-card,.agenda-card,.date-badge{background:#FFFFFF !important;border-color:#DCE3E8 !important;box-shadow:none !important;color:#293746 !important;}
        .month-name,.month-count,.weekdays,.day,.agenda-agency,.agenda-object,.agenda-meta,.date-badge strong,.date-badge small{color:#293746 !important;font-weight:400 !important;}
        .month-count{background:#F4F7F9 !important;border-color:#DCE3E8 !important;}
        .day.event{background:#EAF2F3 !important;color:#293746 !important;box-shadow:none !important;}
        .day.today{outline:1px solid #9FB4BA !important;}
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="calendar-title">Calendário de certames</div>', unsafe_allow_html=True)
    st.markdown('<div class="calendar-subtitle">Veja rapidamente o que vem pela frente e mantenha seus lembretes em um só lugar.</div>', unsafe_allow_html=True)

    calendar_rows = db.essential_certame_calendar(company_id, date.today().isoformat(), limit=40)
    event_dates = []
    for row in calendar_rows:
        try:
            event_dates.append(datetime.fromisoformat(str(row.get("certame_at")).replace("Z", "+00:00")))
        except (TypeError, ValueError):
            pass

    focus = event_dates[0] if event_dates else _local_now()
    import calendar as _calendar
    cal = _calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(focus.year, focus.month)
    event_days = {d.day for d in event_dates if d.year == focus.year and d.month == focus.month}
    today = _local_now().date()
    month_names = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    weekday_names = ["D", "S", "T", "Q", "Q", "S", "S"]

    month_html = (
        '<div class="month-card"><div class="month-head">'
        f'<div class="month-name">{month_names[focus.month]} {focus.year}</div>'
        f'<div class="month-count">{len(calendar_rows)} próximo(s)</div></div>'
        '<div class="weekdays">' + ''.join(f'<span>{w}</span>' for w in weekday_names) + '</div>'
        '<div class="month-grid">'
    )
    for week in weeks:
        for day in week:
            if not day:
                month_html += '<span class="day"></span>'
                continue
            classes = ["day"]
            if day in event_days:
                classes.append("event")
            if today.year == focus.year and today.month == focus.month and today.day == day:
                classes.append("today")
            class_str = " ".join(classes)
            month_html += f'<span class="{class_str}">{day}</span>'
    month_html += '</div></div>'

    cal_col, agenda_col = st.columns([.82, 1.55], gap="large")
    with cal_col:
        st.markdown(month_html, unsafe_allow_html=True)
    with agenda_col:
        st.markdown(
            f'<div class="agenda-head"><h3>Próximos certames</h3><span>{len(calendar_rows)} agendado(s)</span></div>',
            unsafe_allow_html=True,
        )
        if calendar_rows:
            for row in calendar_rows[:6]:
                try:
                    event_dt = datetime.fromisoformat(str(row.get("certame_at")).replace("Z", "+00:00"))
                    badge_day = f"{event_dt.day:02d}"
                    badge_month = month_names[event_dt.month][:3]
                    time_label = event_dt.strftime("%H:%M")
                except (TypeError, ValueError):
                    badge_day, badge_month, time_label = "--", "---", ""
                agency = escape(str(row.get("agency") or "Órgão não informado"))
                obj = escape(str(row.get("object") or "Objeto não informado"))
                if len(obj) > 155:
                    obj = obj[:152].rstrip() + "..."
                city = escape(str(row.get("city") or ""))
                state = escape(str(row.get("state") or ""))
                modality = escape(str(row.get("modality") or ""))
                location = "/".join(part for part in (city, state) if part)
                meta = " · ".join(part for part in (time_label, modality, location) if part)
                card_html = f"""<div class="agenda-card"><div class="agenda-top">
                    <div class="date-badge"><strong>{badge_day}</strong><small>{badge_month}</small></div>
                    <div><div class="agenda-agency">{agency}</div><div class="agenda-object">{obj}</div>
                    <div class="agenda-meta">{meta}</div></div></div></div>"""
                st.markdown(card_html, unsafe_allow_html=True)
            if len(calendar_rows) > 6:
                st.caption(f"+ {len(calendar_rows) - 6} certame(s) futuro(s) registrados.")
        else:
            st.info("Nenhum certame agendado. Na Minha lista, escolha Vou participar e informe o dia e a hora do certame.")

    st.markdown('<div class="notes-panel-title">Anotações rápidas</div>', unsafe_allow_html=True)
    st.markdown('<div class="notes-panel-sub">Registre lembretes de operação sem transformar o LicitaNexo em um sistema pesado de tarefas.</div>', unsafe_allow_html=True)
    with st.form("essential_calendar_note_form", clear_on_submit=True):
        new_note = st.text_area(
            "Nova anotação",
            height=82,
            placeholder="Ex.: ligar para o fornecedor; conferir amostra; revisar o prazo do edital...",
        )
        add_note = st.form_submit_button("Adicionar anotação", type="primary", width="stretch")
        if add_note:
            if new_note.strip():
                db.add_essential_calendar_note(company_id, new_note)
                st.success("Anotação adicionada.")
                st.rerun()
            else:
                st.warning("Escreva a anotação antes de adicionar.")

    saved_notes = db.list_essential_calendar_notes(company_id)
    if not saved_notes:
        st.caption("Nenhuma anotação registrada ainda.")
    else:
        for note_row in saved_notes:
            with st.container(border=True):
                note_col, delete_col = st.columns([10, 1])
                with note_col:
                    st.write(note_row.get("note") or "")
                    try:
                        created = datetime.fromisoformat(str(note_row.get("created_at"))).strftime("%d/%m/%Y %H:%M")
                    except (TypeError, ValueError):
                        created = str(note_row.get("created_at") or "")[:16]
                    st.caption(created)
                with delete_col:
                    if st.button("🗑️", key=f"delete_calendar_note_{note_row['id']}", help="Apagar anotação"):
                        db.delete_essential_calendar_note(company_id, note_row["id"])
                        st.rerun()


def main():
    apply_brand()
    if "user" not in st.session_state:
        login_page()
        return
    user = st.session_state.user
    try:
        security.validate_session(st.session_state.get("security_session_token"))
    except SessionExpiredError as error:
        security.event("session_expired", user.get("email",""), _client_ip(), False, str(error))
        st.session_state.clear()
        st.warning(str(error))
        login_page()
        return
    if "motivational_phrase" not in st.session_state:
        st.session_state.motivational_phrase = random.choice(MOTIVATIONAL_PHRASES)
    if not db.legal_is_current(user):
        legal_acceptance_page(user)
        return
    allowed, access_message, account = db.subscription_access(user["company_id"])
    admin_section = None
    account_label = escape(str(user.get("name") or user.get("email") or "Minha conta").split()[0])
    st.markdown(
        f'<div class="ln-app-topbar"><span class="ln-app-topbar-menu">☰</span>'
        f'<span class="ln-app-topbar-account">{account_label}</span></div>',
        unsafe_allow_html=True,
    )
    with st.sidebar:
        if LOGO_PATH.exists():
            logo_data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
            st.markdown(
                f'<div class="ln-sidebar-brand"><img src="data:image/png;base64,{logo_data}" alt="LicitaNexo"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="ln-sidebar-brand"><span class="ln-sidebar-brand-text">LicitaNexo</span></div>', unsafe_allow_html=True)

        if _is_admin_user(user):
            pending = _cached_pending_access_requests()
            page = "Administração"
            st.caption(f"Ambiente: {ENVIRONMENT}")
            st.markdown("##### SALA DE CONTROLE")
            admin_section = st.radio(
                "Funções administrativas",
                ADMIN_SECTIONS,
                format_func=lambda value: ADMIN_SECTION_LABELS[value],
                key="admin_sidebar_section",
                label_visibility="collapsed",
            )
        else:
            explore_pages = [
                "Início", "Buscar licitações", "Por Estado", "Por Cidade",
                "Por Modalidade", "Por site de disputa", "Filtro avançado", "Em destaque",
            ]
            work_pages = ["Minha lista", "Calendário"]
            account_pages = ["Preferências", "Radar de licitações", "Suporte", "Minha conta"]
            pages = [*explore_pages, *work_pages, *account_pages]
            if not allowed:
                explore_pages, work_pages = [], []
                account_pages = ["Suporte", "Minha conta"]
                pages = account_pages

            requested_page = st.session_state.pop("_navigation_request", None)
            if requested_page in pages:
                st.session_state["main_navigation"] = requested_page
            if st.session_state.get("main_navigation") not in pages:
                st.session_state["main_navigation"] = pages[0]
            page = st.session_state["main_navigation"]

            nav_icons = {
                "Início": ":material/home:", "Buscar licitações": ":material/search:",
                "Por Estado": ":material/map:", "Por Cidade": ":material/location_on:",
                "Por Modalidade": ":material/category:", "Por site de disputa": ":material/language:",
                "Filtro avançado": ":material/filter_alt:", "Em destaque": ":material/trending_up:",
                "Minha lista": ":material/bookmark:", "Calendário": ":material/calendar_month:",
                "Preferências": ":material/tune:", "Radar de licitações": ":material/radar:",
                "Suporte": ":material/help_center:", "Minha conta": ":material/account_circle:",
            }

            def _nav_group(title, options, group_key):
                nonlocal page
                if not options:
                    return
                st.caption(title)
                for index, option in enumerate(options):
                    selected = page == option
                    if st.button(
                        option, icon=nav_icons.get(option), key=f"nav_{group_key}_{index}",
                        type="primary" if selected else "secondary", width="stretch",
                    ):
                        st.session_state["main_navigation"] = option
                        st.rerun()

            _nav_group("EXPLORAR", explore_pages, "explore")
            _nav_group("MINHA ÁREA", work_pages, "work")
            _nav_group("MINHA CONTA", account_pages, "account")

            guide_page = {
                "Buscar licitações": "🔎 Buscar Editais",
                "Calendário": "📅 Calendário",
                "Suporte": "💬 Suporte",
                "Minha conta": "👤 Minha Conta",
            }.get(page, page)
            if guide_page in {"📅 Calendário", "🔎 Buscar Editais", "💬 Suporte", "👤 Minha Conta"}:
                render_sidebar_guides(guide_page)


        if st.button("Sair", icon=":material/logout:", key="sidebar_logout", width="stretch"):
            security.revoke_session(st.session_state.get("security_session_token"))
            security.event("logout", user.get("email", ""), _client_ip(), True, f'user_id={user.get("id", "")}')
            st.session_state.clear()
            st.rerun()

    if page == "Início":
        if LOGO_PATH.exists():
            st.markdown('<div class="ln-home-color-logo">', unsafe_allow_html=True)
            st.image(str(LOGO_PATH), width=190)
            st.markdown('</div>', unsafe_allow_html=True)
        essential_home_page(db, user)
    elif page == "Buscar licitações":
        essential_search_page(db, user, usage)
    elif page == "Por Estado":
        essential_state_page(db, user)
    elif page == "Por Cidade":
        essential_city_page(db, user)
    elif page == "Por Modalidade":
        essential_modality_page(db, user)
    elif page == "Por site de disputa":
        essential_portal_page(db, user)
    elif page == "Filtro avançado":
        essential_advanced_search_page(db, user)
    elif page == "Em destaque":
        essential_top50_page(db, user)
    elif page == "Minha lista":
        essential_my_list_page(db, user)
    elif page == "Calendário":
        calendar_page(user)
    elif page == "Preferências":
        essential_preferences_page(db, user)
    elif page == "Radar de licitações":
        essential_radar_page(db, user)
    elif page == "Suporte":
        support_page(user)
    elif page == "Minha conta":
        essential_account_page(user)
    else:
        admin_page(user, admin_section or "Visão geral")


main()

