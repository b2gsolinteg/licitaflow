import os
from pathlib import Path


APP_NAME = "LicitaNexo"
APP_VERSION = "1.0 Essential RC31.8"
APP_TAGLINE = "Simples para começar. Útil para vencer."
COMPANY_SIGNATURE = "Powered by B2G SaaS · Business to Growth"
APP_POSITIONING = "Seu departamento de licitações em um único lugar."
ENVIRONMENT = os.getenv("LICITANEXO_ENV", "production").strip().lower() or "production"
LEGAL_VERSION = os.getenv("LICITANEXO_LEGAL_VERSION", "2026-08-v1")
TRIAL_DAYS = max(int(os.getenv("LICITANEXO_TRIAL_DAYS", "7")), 1)
SUPPORT_EMAIL = os.getenv("LICITANEXO_SUPPORT_EMAIL", "suporte@licitanexo.com.br")
ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.getenv("LICITANEXO_ADMIN_EMAILS", "").split(",")
    if email.strip()
}
PUBLIC_PRICES_ENABLED = os.getenv("LICITANEXO_PUBLIC_PRICES_ENABLED", "0").strip().lower() in {
    "1", "true", "yes", "sim",
}


def database_path(project_root: Path) -> Path:
    data_directory = Path(os.getenv("LICITANEXO_DATA_DIR", project_root / "data"))
    return data_directory / "licitaflow.db"


def is_admin(email: str) -> bool:
    return str(email or "").strip().lower() in ADMIN_EMAILS


# RC20 · Fundação Comercial
ESSENTIAL_PRICE_CENTS = 4990
COMMERCIAL_PLAN = "ESSENTIAL"

# RC21 · Pagamentos e Assinaturas
BILLING_PROVIDER = "mercadopago"

# RC23 · Consumo e IA
DEFAULT_ESSENTIAL_ANALYSIS_LIMIT = 15

# RC25 · Segurança + Compliance
SECURITY_SESSION_IDLE_MINUTES = 60
SECURITY_SESSION_ABSOLUTE_HOURS = 8

# RC31.5 · UX: Radar rápido com resumo de itens e navegação lateral preenchida.
