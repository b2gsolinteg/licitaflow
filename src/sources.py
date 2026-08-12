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
