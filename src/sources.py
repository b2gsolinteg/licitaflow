import re


def parse_pncp_control_number(value):
    """Return (CNPJ, year, sequence) for numeric or alphanumeric CNPJ controls."""
    match = re.fullmatch(
        r"([A-Z0-9]{14})-1-(\d+)/(\d{4})",
        str(value or "").strip().upper(),
    )
    if not match:
        return None
    cnpj, sequence, year = match.groups()
    return cnpj, int(year), int(sequence)


PORTAL_ALIASES = (
    (("BLL",), "BLL Compras"),
    (("BNC", "BOLSA NACIONAL DE COMPRAS"), "BNC Compras"),
    (("BBMNET", "BOLSA BRASILEIRA DE MERCADORIAS"), "BBMNET"),
    (("LICITANET",), "LicitaNET"),
    (("M2A",), "M2A Compras"),
    (("PORTAL DE COMPRAS PUBLICAS", "PORTAL DE COMPRAS PÚBLICAS"), "Portal de Compras Públicas"),
    (("COMPRAS.GOV", "COMPRASNET", "SIASG", "GOV.BR/COMPRAS"), "Compras.gov"),
    (("BANCO DO BRASIL", "LICITACOES-E", "LICITAÇÕES-E", "LICITACOES-E.COM.BR"), "Licitações-e / Banco do Brasil"),
    (("BEC-SP", "BEC.SP.GOV.BR", "BOLSA ELETRONICA DE COMPRAS", "BOLSA ELETRÔNICA DE COMPRAS"), "BEC-SP"),
)


# O Essential precisa responder a uma dúvida prática de quem está começando:
# "vou pagar para usar o portal da disputa?". A classificação abaixo é deliberadamente
# conservadora. Portais públicos conhecidos são marcados como gratuitos; portais privados
# recebem "pode exigir pagamento", porque planos e regras comerciais podem mudar.
PORTAL_ACCESS = {
    "Compras.gov": {
        "status": "free",
        "label": "Gratuito",
        "detail": "Portal público. O acesso ao portal é gratuito; cadastro gov.br/SICAF pode ser necessário para participar.",
    },
    "BEC-SP": {
        "status": "free",
        "label": "Gratuito",
        "detail": "Portal público. Pode exigir cadastro/habilitação do fornecedor, sem tratá-lo como assinatura comercial do portal.",
    },
    "BLL Compras": {
        "status": "may_charge",
        "label": "Pode ser pago",
        "detail": "Portal privado. Confirme cadastro, plano, taxa ou condição comercial vigente antes de participar.",
    },
    "BNC Compras": {
        "status": "may_charge",
        "label": "Pode ser pago",
        "detail": "Portal privado. Confirme cadastro, plano, taxa ou condição comercial vigente antes de participar.",
    },
    "BBMNET": {
        "status": "may_charge",
        "label": "Pode ser pago",
        "detail": "Portal privado. Confirme cadastro, plano, taxa ou condição comercial vigente antes de participar.",
    },
    "LicitaNET": {
        "status": "may_charge",
        "label": "Pode ser pago",
        "detail": "Portal privado. Confirme cadastro, plano, taxa ou condição comercial vigente antes de participar.",
    },
    "M2A Compras": {
        "status": "may_charge",
        "label": "Pode ser pago",
        "detail": "Portal privado. Confirme cadastro, plano, taxa ou condição comercial vigente antes de participar.",
    },
    "Portal de Compras Públicas": {
        "status": "may_charge",
        "label": "Pode ser pago",
        "detail": "Portal privado. Confirme cadastro, plano, taxa ou condição comercial vigente antes de participar.",
    },
    "Licitações-e / Banco do Brasil": {
        "status": "check",
        "label": "Consultar condições",
        "detail": "As condições de credenciamento e uso podem variar. Confirme no portal antes de participar.",
    },
}


def normalize_portal_name(value, fallback="PNCP"):
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return fallback
    upper = text.upper()
    for needles, label in PORTAL_ALIASES:
        if any(needle in upper for needle in needles):
            return label
    return fallback


def infer_portal_name(user_name=None, source_url=None):
    combined = f"{user_name or ''} {source_url or ''}".strip()
    label = normalize_portal_name(combined, fallback="")
    if label:
        return label
    return "Outro portal"


def portal_access_info(portal_name):
    """Return beginner-friendly access guidance for the dispute portal.

    Unknown portals are never guessed as free or paid. This keeps the UI useful without
    turning a commercial condition that may change into a false guarantee.
    """
    portal = str(portal_name or "").strip()
    if portal in {"", "Não identificado", "Não informado", "Outro portal", "PNCP"}:
        return {
            "status": "unknown",
            "label": "Não identificado",
            "detail": "Consultar edital.",
        }
    return PORTAL_ACCESS.get(portal, {
        "status": "check",
        "label": "Consultar condições",
        "detail": "Confirme cadastro, eventual taxa e condições de acesso diretamente no portal antes de participar.",
    })


def source_label(source_name, source_channel):
    name = source_name or "PNCP"
    if source_channel == "Compras.gov API":
        return f"{name} — API oficial"
    if source_channel == "PNCP":
        return "PNCP" if name == "PNCP" else f"{name} — via PNCP"
    return name
COMPRASGOV_MODALITY_BY_PNCP = {
    4: 3,   # Concorrência eletrônica -> Concorrência
    6: 5,   # Pregão eletrônico -> Pregão
    8: 6,   # Dispensa de licitação
    9: 7,   # Inexigibilidade
    12: 12, # Credenciamento
}


def pncp_official_url(control_number):
    """Monta a página pública do edital no PNCP quando o número de controle é válido."""
    parsed = parse_pncp_control_number(control_number)
    if not parsed:
        return ""
    cnpj, year, sequence = parsed
    return f"https://pncp.gov.br/app/editais/{cnpj}/{year}/{sequence}"


def opportunity_source_and_portal(source_name=None, source_channel=None, source_url=None):
    """Separa a origem capturada pelo LicitaNexo do ambiente de disputa.

    Registros históricos da RC14-RC17 podem ter gravado o portal em source_name
    mesmo quando chegaram via PNCP. Esta função mantém compatibilidade sem
    reescrever o banco do cliente.
    """
    channel = " ".join(str(source_channel or "").split()).strip()
    raw_name = " ".join(str(source_name or "").split()).strip()
    url = str(source_url or "").strip()
    upper_channel = channel.upper()

    if upper_channel in {"PNCP", "PNCP_OPEN", "PNCP_DISPENSA_FALLBACK"}:
        source = "PNCP"
        portal = infer_portal_name(raw_name, url)
        if portal in {"Outro portal", "PNCP"}:
            portal = "Não identificado"
        return source, portal

    if channel == "Compras.gov API":
        return "Compras.gov", "Compras.gov"
    if upper_channel == "MANUAL" or raw_name.lower() == "cadastro manual":
        return "Cadastro manual", "Não informado"

    source = raw_name or channel or "Não identificada"
    portal = infer_portal_name(raw_name, url)
    if portal == "Outro portal":
        portal = "Não identificado"
    return source, portal
