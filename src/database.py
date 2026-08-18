import sqlite3
import re
import hashlib
import secrets
import shutil
import uuid
import unicodedata
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .config import APP_VERSION, LEGAL_VERSION, TRIAL_DAYS
from .db_runtime import ClosingSQLiteConnection, connect_runtime, using_postgres
from .security import hash_password, verify_password
from .pncp import canonical_modality_name


def _timestamp_not_expired(value, *, allow_missing=False):
    """Compare SQLite text or PostgreSQL timestamps without mixing SQL types."""
    if value is None or not str(value).strip():
        return allow_missing
    try:
        if isinstance(value, datetime):
            expires_at = value
        else:
            expires_at = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        now = datetime.now(expires_at.tzinfo) if expires_at.tzinfo else datetime.now()
        return expires_at >= now
    except (TypeError, ValueError):
        return False


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        # O schema PostgreSQL foi criado/validado pela RC27.
        # Não execute migrações DDL SQLite contra PostgreSQL.
        if not using_postgres():
            self._backup_before_migration(path)
            self.ensure_schema()
            self.ensure_local_admin()
            self._record_schema_version()

    def _existing_schema_version(self):
        if not Path(self.path).exists():
            return None
        try:
            with sqlite3.connect(self.path, timeout=10, factory=ClosingSQLiteConnection) as conn:
                exists = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='system_meta'"
                ).fetchone()
                if not exists:
                    return None
                row = conn.execute("SELECT value FROM system_meta WHERE key='app_version'").fetchone()
                return row[0] if row else None
        except sqlite3.Error:
            return None

    def _backup_before_migration(self, path: Path):
        if not path.exists() or path.stat().st_size == 0:
            return
        if self._existing_schema_version() == APP_VERSION:
            return
        backup_dir = path.parent.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        safe_version = APP_VERSION.replace(" ", "_").replace("/", "-")
        destination = backup_dir / f"licitaflow_pre_{safe_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            shutil.copy2(path, destination)
        except OSError:
            # Falha de backup não deve impedir a inicialização do MVP, mas a cópia manual
            # continua recomendada antes de mudanças estruturais importantes.
            pass

    def _record_schema_version(self):
        with self.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO system_meta(key, value, updated_at) VALUES ('app_version', ?, CURRENT_TIMESTAMP)", (APP_VERSION,))

    @staticmethod
    def _search_fold(value):
        normalized = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()

    def connect(self):
        return connect_runtime(self.path, search_fold=self._search_fold)

    def ensure_schema(self):
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'Essencial',
                    subscription_status TEXT NOT NULL DEFAULT 'trialing',
                    trial_started_at TEXT,
                    trial_ends_at TEXT,
                    subscription_ends_at TEXT,
                    billing_customer_id TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'owner',
                    terms_version TEXT NOT NULL DEFAULT '',
                    terms_accepted_at TEXT,
                    privacy_accepted_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE IF NOT EXISTS opportunities (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    pncp_control_number TEXT, agency TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT '',
                    modality TEXT NOT NULL DEFAULT '', published_at TEXT,
                    opening_at TEXT, closing_at TEXT, object TEXT NOT NULL DEFAULT '',
                    estimated_value REAL, source_url TEXT NOT NULL DEFAULT '',
                    srp INTEGER NOT NULL DEFAULT 0,
                    source_name TEXT NOT NULL DEFAULT 'PNCP',
                    source_channel TEXT NOT NULL DEFAULT 'PNCP',
                    stage TEXT NOT NULL DEFAULT 'Oportunidade',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id),
                    UNIQUE(company_id, pncp_control_number)
                );
                CREATE TABLE IF NOT EXISTS pncp_catalog (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    pncp_control_number TEXT NOT NULL,
                    agency TEXT NOT NULL DEFAULT '', city TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT '', modality TEXT NOT NULL DEFAULT '',
                    published_at TEXT, opening_at TEXT, closing_at TEXT,
                    object TEXT NOT NULL DEFAULT '', estimated_value REAL,
                    source_url TEXT NOT NULL DEFAULT '',
                    srp INTEGER NOT NULL DEFAULT 0,
                    source_name TEXT NOT NULL DEFAULT 'PNCP',
                    source_channel TEXT NOT NULL DEFAULT 'PNCP',
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id),
                    UNIQUE(company_id, pncp_control_number)
                );
                CREATE TABLE IF NOT EXISTS sync_checkpoints (
                    company_id TEXT NOT NULL, modality_code INTEGER NOT NULL,
                    state TEXT NOT NULL DEFAULT '', publication_day TEXT NOT NULL,
                    next_page INTEGER NOT NULL DEFAULT 1,
                    completed INTEGER NOT NULL DEFAULT 0,
                    items_saved INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(company_id, modality_code, state, publication_day),
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE IF NOT EXISTS source_sync_checkpoints (
                    company_id TEXT NOT NULL, source TEXT NOT NULL,
                    modality_code INTEGER NOT NULL, state TEXT NOT NULL DEFAULT '',
                    period_start TEXT NOT NULL, period_end TEXT NOT NULL,
                    publication_day TEXT NOT NULL, next_page INTEGER NOT NULL DEFAULT 1,
                    completed INTEGER NOT NULL DEFAULT 0,
                    items_saved INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(company_id, source, modality_code, state, period_start, period_end, publication_day),
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE IF NOT EXISTS global_pncp_catalog (
                    id TEXT PRIMARY KEY, pncp_control_number TEXT NOT NULL UNIQUE,
                    agency TEXT NOT NULL DEFAULT '', city TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT '', modality TEXT NOT NULL DEFAULT '',
                    published_at TEXT, opening_at TEXT, closing_at TEXT,
                    object TEXT NOT NULL DEFAULT '', estimated_value REAL,
                    source_url TEXT NOT NULL DEFAULT '', srp INTEGER NOT NULL DEFAULT 0,
                    source_name TEXT NOT NULL DEFAULT 'PNCP',
                    source_channel TEXT NOT NULL DEFAULT 'PNCP',
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS global_sync_checkpoints (
                    source TEXT NOT NULL, modality_code INTEGER NOT NULL,
                    state TEXT NOT NULL DEFAULT '', period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL, publication_day TEXT NOT NULL,
                    next_page INTEGER NOT NULL DEFAULT 1, completed INTEGER NOT NULL DEFAULT 0,
                    items_saved INTEGER NOT NULL DEFAULT 0, last_error TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(source, modality_code, state, period_start, period_end, publication_day)
                );
                CREATE TABLE IF NOT EXISTS sync_runs (
                    id TEXT PRIMARY KEY, source TEXT NOT NULL DEFAULT 'PNCP',
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, finished_at TEXT,
                    status TEXT NOT NULL DEFAULT 'running', pages INTEGER NOT NULL DEFAULT 0,
                    records INTEGER NOT NULL DEFAULT 0, errors TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_global_catalog_state ON global_pncp_catalog(state);
                CREATE INDEX IF NOT EXISTS idx_global_catalog_modality ON global_pncp_catalog(modality);
                CREATE INDEX IF NOT EXISTS idx_global_catalog_dates ON global_pncp_catalog(closing_at, published_at);
                CREATE INDEX IF NOT EXISTS idx_global_catalog_value ON global_pncp_catalog(estimated_value);
                CREATE TABLE IF NOT EXISTS access_requests (
                    id TEXT PRIMARY KEY, company_name TEXT NOT NULL,
                    name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
                    whatsapp TEXT NOT NULL DEFAULT '', segment TEXT NOT NULL DEFAULT '',
                    challenge TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'pending',
                    invitation_hash TEXT NOT NULL DEFAULT '', contacted_at TEXT,
                    invited_at TEXT, activated_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS assisted_requests (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    request_type TEXT NOT NULL, title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '', urgency TEXT NOT NULL DEFAULT 'Normal',
                    status TEXT NOT NULL DEFAULT 'Recebida', admin_notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS password_reset_requests (
                    id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'requested',
                    code_hash TEXT NOT NULL DEFAULT '', expires_at TEXT,
                    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    code_generated_at TEXT, used_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS company_profiles (
                    company_id TEXT PRIMARY KEY,
                    has_technical_certificate INTEGER NOT NULL DEFAULT 0,
                    has_balance_sheet INTEGER NOT NULL DEFAULT 0,
                    accepts_price_registration INTEGER NOT NULL DEFAULT 1,
                    activity_type TEXT NOT NULL DEFAULT 'Produtos',
                    has_technical_manager INTEGER NOT NULL DEFAULT 0,
                    accepts_samples INTEGER NOT NULL DEFAULT 1,
                    accepts_site_visit INTEGER NOT NULL DEFAULT 1,
                    service_states TEXT NOT NULL DEFAULT '',
                    max_contract_value REAL,
                    notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS company_documents (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    category TEXT NOT NULL, document_type TEXT NOT NULL,
                    applicable TEXT NOT NULL DEFAULT 'Não informado',
                    status TEXT NOT NULL DEFAULT 'Não informado',
                    expiry_date TEXT, issuer TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    UNIQUE(company_id, document_type)
                );
                CREATE TABLE IF NOT EXISTS edital_analyses (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    opportunity_id TEXT, filename TEXT NOT NULL,
                    compatibility_score INTEGER NOT NULL DEFAULT 0,
                    pages_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS edital_findings (
                    id TEXT PRIMARY KEY, analysis_id TEXT NOT NULL, company_id TEXT NOT NULL,
                    severity TEXT NOT NULL, category TEXT NOT NULL,
                    title TEXT NOT NULL, evidence TEXT NOT NULL DEFAULT '',
                    page_number INTEGER, recommended_action TEXT NOT NULL DEFAULT '',
                    confirmed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(analysis_id) REFERENCES edital_analyses(id) ON DELETE CASCADE,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    opportunity_id TEXT, title TEXT NOT NULL,
                    event_type TEXT NOT NULL DEFAULT 'Tarefa', event_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pendente', source TEXT NOT NULL DEFAULT 'Manual',
                    evidence TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS essential_calendar_notes (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    note TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS price_references (
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    opportunity_id TEXT, query TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL DEFAULT '', agency TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT '',
                    quantity REAL, unit TEXT NOT NULL DEFAULT '',
                    estimated_unit_value REAL, homologated_unit_value REAL,
                    supplier TEXT NOT NULL DEFAULT '', brand TEXT NOT NULL DEFAULT '',
                    source_url TEXT NOT NULL DEFAULT '', published_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS opportunity_details (
                    opportunity_id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                    decision TEXT NOT NULL DEFAULT 'Analisar',
                    next_action TEXT NOT NULL DEFAULT '', deadline TEXT,
                    responsible TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
                    our_bid REAL, winning_bid REAL, contract_value REAL,
                    winner TEXT NOT NULL DEFAULT '', loss_reason TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE IF NOT EXISTS opportunity_tasks (
                    id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, company_id TEXT NOT NULL,
                    title TEXT NOT NULL, due_date TEXT, priority TEXT NOT NULL DEFAULT 'Normal',
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE IF NOT EXISTS opportunity_checklist (
                    id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, company_id TEXT NOT NULL,
                    title TEXT NOT NULL, position INTEGER NOT NULL DEFAULT 0,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE IF NOT EXISTS opportunity_documents (
                    id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, company_id TEXT NOT NULL,
                    name TEXT NOT NULL, expiry_date TEXT,
                    status TEXT NOT NULL DEFAULT 'Pendente', notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE IF NOT EXISTS opportunity_quote_items (
                    id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, company_id TEXT NOT NULL,
                    description TEXT NOT NULL, quantity REAL NOT NULL DEFAULT 1,
                    unit_cost REAL NOT NULL DEFAULT 0, freight REAL NOT NULL DEFAULT 0,
                    taxes REAL NOT NULL DEFAULT 0, other_costs REAL NOT NULL DEFAULT 0,
                    sale_price REAL NOT NULL DEFAULT 0, supplier TEXT NOT NULL DEFAULT '',
                    lot_number TEXT NOT NULL DEFAULT '', edital_price REAL NOT NULL DEFAULT 0,
                    commission REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE INDEX IF NOT EXISTS ix_opportunity_company
                    ON opportunities(company_id, stage);
                CREATE INDEX IF NOT EXISTS ix_catalog_company_date
                    ON pncp_catalog(company_id, published_at DESC);
                CREATE INDEX IF NOT EXISTS ix_catalog_company_state
                    ON pncp_catalog(company_id, state, modality);
                CREATE INDEX IF NOT EXISTS ix_tasks_opportunity
                    ON opportunity_tasks(company_id, opportunity_id, completed);
                CREATE INDEX IF NOT EXISTS ix_checklist_opportunity
                    ON opportunity_checklist(company_id, opportunity_id, position);
                CREATE INDEX IF NOT EXISTS ix_password_reset_status
                    ON password_reset_requests(status, requested_at DESC);
                CREATE INDEX IF NOT EXISTS ix_findings_company
                    ON edital_findings(company_id, analysis_id, severity);
                CREATE INDEX IF NOT EXISTS ix_calendar_company_date
                    ON calendar_events(company_id, event_at);
                CREATE INDEX IF NOT EXISTS ix_prices_company_query
                    ON price_references(company_id, query, created_at DESC);
                CREATE INDEX IF NOT EXISTS ix_assisted_company_status
                    ON assisted_requests(company_id, status, created_at DESC);
                CREATE TABLE IF NOT EXISTS system_meta (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS email_events (
                    id TEXT PRIMARY KEY, event_type TEXT NOT NULL, recipient TEXT NOT NULL,
                    status TEXT NOT NULL, details TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_email_events_created
                    ON email_events(created_at DESC);

                CREATE TABLE IF NOT EXISTS trial_attempts (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL DEFAULT '',
                    cnpj TEXT NOT NULL DEFAULT '',
                    ip_hash TEXT NOT NULL DEFAULT '',
                    ip_masked TEXT NOT NULL DEFAULT '',
                    outcome TEXT NOT NULL DEFAULT 'allowed',
                    risk_score INTEGER NOT NULL DEFAULT 0,
                    reasons TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_trial_attempts_email ON trial_attempts(email);
                CREATE INDEX IF NOT EXISTS ix_trial_attempts_cnpj ON trial_attempts(cnpj);
                CREATE INDEX IF NOT EXISTS ix_trial_attempts_ip ON trial_attempts(ip_hash);
                CREATE INDEX IF NOT EXISTS ix_trial_attempts_created ON trial_attempts(created_at DESC);

                CREATE TABLE IF NOT EXISTS payments (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    amount REAL NOT NULL DEFAULT 0,
                    method TEXT NOT NULL DEFAULT 'PIX',
                    billing_cycle TEXT NOT NULL DEFAULT 'Mensal',
                    status TEXT NOT NULL DEFAULT 'pending',
                    external_id TEXT NOT NULL DEFAULT '',
                    due_at TEXT,
                    paid_at TEXT,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS ix_payments_company ON payments(company_id);
                CREATE INDEX IF NOT EXISTS ix_payments_status ON payments(status);
                CREATE INDEX IF NOT EXISTS ix_payments_created ON payments(created_at DESC);

                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    actor TEXT NOT NULL DEFAULT 'system',
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL DEFAULT '',
                    entity_id TEXT NOT NULL DEFAULT '',
                    details TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_audit_events_created ON audit_events(created_at DESC);

                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    campaign_type TEXT NOT NULL DEFAULT 'coupon',
                    owner_name TEXT NOT NULL DEFAULT '',
                    benefit_type TEXT NOT NULL DEFAULT 'percent',
                    benefit_value REAL NOT NULL DEFAULT 0,
                    max_uses INTEGER NOT NULL DEFAULT 0,
                    per_cnpj_limit INTEGER NOT NULL DEFAULT 1,
                    valid_from TEXT,
                    valid_until TEXT,
                    allowed_cycles TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_campaigns_code ON campaigns(code);

                CREATE TABLE IF NOT EXISTS campaign_uses (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    email TEXT NOT NULL DEFAULT '',
                    cnpj TEXT NOT NULL DEFAULT '',
                    access_request_id TEXT NOT NULL DEFAULT '',
                    company_id TEXT NOT NULL DEFAULT '',
                    payment_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'lead',
                    benefit_value REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS ix_campaign_uses_campaign ON campaign_uses(campaign_id);
                CREATE INDEX IF NOT EXISTS ix_campaign_uses_cnpj ON campaign_uses(cnpj);
            """)
            self._ensure_column(conn, "opportunities", "source_name", "TEXT NOT NULL DEFAULT 'PNCP'")
            self._ensure_column(conn, "opportunities", "source_channel", "TEXT NOT NULL DEFAULT 'PNCP'")
            self._ensure_column(conn, "opportunities", "closing_at", "TEXT")
            self._ensure_column(conn, "opportunities", "srp", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(conn, "pncp_catalog", "source_name", "TEXT NOT NULL DEFAULT 'PNCP'")
            self._ensure_column(conn, "pncp_catalog", "source_channel", "TEXT NOT NULL DEFAULT 'PNCP'")
            self._ensure_column(conn, "pncp_catalog", "closing_at", "TEXT")
            self._ensure_column(conn, "pncp_catalog", "srp", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(conn, "companies", "plan", "TEXT NOT NULL DEFAULT 'Essencial'")
            self._ensure_column(conn, "companies", "subscription_status", "TEXT NOT NULL DEFAULT 'trialing'")
            self._ensure_column(conn, "companies", "trial_started_at", "TEXT")
            self._ensure_column(conn, "companies", "trial_ends_at", "TEXT")
            self._ensure_column(conn, "companies", "subscription_ends_at", "TEXT")
            self._ensure_column(conn, "companies", "billing_customer_id", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "companies", "cnpj", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "companies", "billing_email", "TEXT NOT NULL DEFAULT ''")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_companies_cnpj "
                "ON companies(cnpj) WHERE cnpj<>''"
            )
            self._ensure_column(conn, "users", "terms_version", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "users", "terms_accepted_at", "TEXT")
            self._ensure_column(conn, "users", "privacy_accepted_at", "TEXT")
            self._ensure_column(conn, "users", "last_login_at", "TEXT")
            self._ensure_column(conn, "access_requests", "job_title", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "access_requests", "cnpj", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "access_requests", "how_heard", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "access_requests", "admin_notes", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "access_requests", "approved_trial_days", f"INTEGER NOT NULL DEFAULT {TRIAL_DAYS}")
            self._ensure_column(conn, "access_requests", "invitation_expires_at", "TEXT")
            self._ensure_column(conn, "access_requests", "request_ip_hash", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "access_requests", "request_ip_masked", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "access_requests", "risk_score", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(conn, "access_requests", "risk_status", "TEXT NOT NULL DEFAULT 'normal'")
            self._ensure_column(conn, "access_requests", "risk_reasons", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "access_requests", "campaign_code", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "opportunity_details", "certame_at", "TEXT")
            self._ensure_column(conn, "opportunity_quote_items", "lot_number", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "opportunity_quote_items", "edital_price", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(conn, "opportunity_quote_items", "commission", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(conn, "company_profiles", "legal_name", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "trade_name", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "cnpj", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "company_size", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "cnaes", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "offerings", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "interest_keywords", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "procurement_interests", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "brands", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "business_model", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "delivery_days", "INTEGER")
            self._ensure_column(conn, "company_profiles", "delivery_structure", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "technical_certificate_details", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "balance_sheet_year", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "technical_manager_details", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "desired_margin", "REAL NOT NULL DEFAULT 15")
            # Preferências do LicitaNexo Essential. São apenas atalhos para a busca;
            # não transformam a conta em um cadastro complexo.
            self._ensure_column(conn, "company_profiles", "search_keyword", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "search_nature", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "search_modalities", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "company_profiles", "search_srp", "TEXT NOT NULL DEFAULT 'Todos'")
            self._ensure_column(conn, "company_profiles", "search_horizon", "TEXT NOT NULL DEFAULT 'Próximos 30 dias'")
            self._ensure_column(conn, "company_profiles", "search_minimum", "REAL")
            self._ensure_column(conn, "company_profiles", "search_maximum", "REAL")
            self._ensure_column(conn, "company_profiles", "search_order", "TEXT NOT NULL DEFAULT 'Certame mais próximo'")
            self._ensure_column(conn, "price_references", "catalog_code", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "price_references", "purchase_id", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "price_references", "item_number", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "price_references", "source_type", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "price_references", "brand_normalized", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "price_references", "supplier_tax_id", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "price_references", "procurement_form", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "price_references", "evidence_excerpt", "TEXT NOT NULL DEFAULT ''")
            conn.execute("""
                INSERT OR IGNORE INTO global_pncp_catalog(
                    id, pncp_control_number, agency, city, state, modality, published_at, opening_at,
                    closing_at, object, estimated_value, source_url, srp, source_name, source_channel,
                    first_seen_at, last_seen_at
                )
                SELECT lower(hex(randomblob(16))), pncp_control_number, agency, city, state, modality,
                       published_at, opening_at, closing_at, object, estimated_value, source_url, srp,
                       source_name, source_channel, MIN(first_seen_at), MAX(last_seen_at)
                FROM pncp_catalog WHERE trim(pncp_control_number)<>'' GROUP BY pncp_control_number
            """)
            self._ensure_column(conn, "price_references", "page_number", "INTEGER")
            conn.execute("UPDATE companies SET trial_started_at=CURRENT_TIMESTAMP WHERE trial_started_at IS NULL")
            conn.execute(
                "UPDATE companies SET trial_ends_at=datetime('now', ?) WHERE trial_ends_at IS NULL",
                (f"+{TRIAL_DAYS} days",),
            )
            conn.execute("UPDATE opportunities SET stage='Nova oportunidade' WHERE stage='Oportunidade'")
            # Normaliza rótulos históricos do PNCP (ex.: “Pregão - Eletrônico”) para
            # os mesmos nomes apresentados nos filtros do Radar.
            modality_aliases = {
                "Pregão - Eletrônico": "Pregão eletrônico",
                "Pregão - Presencial": "Pregão presencial",
                "Concorrência - Eletrônica": "Concorrência eletrônica",
                "Concorrência - Presencial": "Concorrência presencial",
                "Leilão - Eletrônico": "Leilão eletrônico",
                "Leilão - Presencial": "Leilão presencial",
                "Diálogo Competitivo": "Diálogo competitivo",
                "Dispensa": "Dispensa de licitação",
                "Dispensa de Licitação": "Dispensa de licitação",
            }
            for old_name, new_name in modality_aliases.items():
                conn.execute("UPDATE pncp_catalog SET modality=? WHERE modality=?", (new_name, old_name))
                conn.execute("UPDATE global_pncp_catalog SET modality=? WHERE modality=?", (new_name, old_name))
                conn.execute("UPDATE opportunities SET modality=? WHERE modality=?", (new_name, old_name))

    def create_assisted_request(self, company_id, user_id, request_type, title, details="", urgency="Normal"):
        request_type = str(request_type or "").strip()
        title = str(title or "").strip()
        if not request_type or not title:
            raise ValueError("Informe o tipo e descreva brevemente o pedido.")
        allowed_urgencies = {"Normal", "Alta", "Urgente"}
        urgency = urgency if urgency in allowed_urgencies else "Normal"
        request_id = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO assisted_requests(
                    id, company_id, user_id, request_type, title, details, urgency
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (request_id, company_id, user_id, request_type, title,
                    str(details or "").strip(), urgency))
        return request_id

    def list_assisted_requests(self, company_id=None):
        sql = """
            SELECT r.*, u.name AS user_name, u.email AS user_email, c.name AS company_name
            FROM assisted_requests r
            JOIN users u ON u.id=r.user_id
            JOIN companies c ON c.id=r.company_id
        """
        params = []
        if company_id:
            sql += " WHERE r.company_id=?"
            params.append(company_id)
        sql += " ORDER BY CASE r.status WHEN 'Recebida' THEN 0 WHEN 'Em atendimento' THEN 1 ELSE 2 END, r.created_at DESC"
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def update_assisted_request(self, request_id, status, admin_notes=""):
        allowed = {"Recebida", "Em atendimento", "Concluída", "Cancelada"}
        if status not in allowed:
            raise ValueError("Situação de atendimento inválida.")
        with self.connect() as conn:
            conn.execute("""
                UPDATE assisted_requests SET status=?, admin_notes=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (status, str(admin_notes or "").strip(), request_id))

    @staticmethod
    def _ensure_column(conn, table, column, definition):
        columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    @staticmethod
    def normalize_cnpj(value):
        return re.sub(r"\D", "", str(value or ""))

    @classmethod
    def validate_cnpj(cls, value):
        cnpj = cls.normalize_cnpj(value)
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        def digit(base, weights):
            total = sum(int(n) * w for n, w in zip(base, weights))
            remainder = total % 11
            return "0" if remainder < 2 else str(11 - remainder)
        d1 = digit(cnpj[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
        d2 = digit(cnpj[:12] + d1, [6,5,4,3,2,9,8,7,6,5,4,3,2])
        return cnpj[-2:] == d1 + d2

    @staticmethod
    def _ip_hash(value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        return hashlib.sha256(("LicitaNexo|trial|" + raw).encode("utf-8")).hexdigest()

    @staticmethod
    def _mask_ip(value):
        raw = str(value or "").strip()
        if not raw:
            return ""
        if ":" in raw:
            parts = raw.split(":")
            return ":".join(parts[:3]) + ":…"
        parts = raw.split(".")
        if len(parts) == 4:
            return ".".join(parts[:2] + ["x", "x"])
        return "registrado"

    def _record_trial_attempt(self, conn, email, cnpj, client_ip, outcome, score, reasons):
        conn.execute("""
            INSERT INTO trial_attempts(
                id, email, cnpj, ip_hash, ip_masked, outcome, risk_score, reasons
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), str(email or "").strip().lower(), self.normalize_cnpj(cnpj),
            self._ip_hash(client_ip), self._mask_ip(client_ip), outcome, int(score or 0),
            " | ".join(str(r) for r in (reasons or []))[:1200],
        ))

    def assess_trial_request(self, email, cnpj, client_ip=""):
        normalized_email = str(email or "").strip().lower()
        normalized_cnpj = self.normalize_cnpj(cnpj)
        if not self.validate_cnpj(normalized_cnpj):
            raise ValueError("Informe um CNPJ válido.")
        reasons = []
        score = 0
        outcome = "allowed"
        ip_hash = self._ip_hash(client_ip)
        with self.connect() as conn:
            if conn.execute("SELECT 1 FROM users WHERE email=?", (normalized_email,)).fetchone():
                reasons.append("E-mail já possui conta")
                score = 100
                outcome = "blocked"
            company = conn.execute(
                "SELECT id FROM companies WHERE cnpj=? AND cnpj<>'' LIMIT 1", (normalized_cnpj,)
            ).fetchone()
            if company:
                reasons.append("CNPJ já utilizou ou possui conta")
                score = 100
                outcome = "blocked"
            prior = conn.execute("""
                SELECT status, email FROM access_requests
                WHERE cnpj=? AND cnpj<>'' ORDER BY created_at DESC LIMIT 1
            """, (normalized_cnpj,)).fetchone()
            if prior and prior["email"] != normalized_email:
                if prior["status"] in {"invited", "activated"}:
                    reasons.append("CNPJ já possui convite/ativação")
                    score = 100
                    outcome = "blocked"
                else:
                    reasons.append("CNPJ já possui solicitação com outro e-mail")
                    score += 55
            if ip_hash:
                row = conn.execute("""
                    SELECT COUNT(DISTINCT cnpj) AS total
                    FROM trial_attempts
                    WHERE ip_hash=? AND cnpj<>'' AND cnpj<>?
                      AND created_at >= datetime('now','-30 days')
                """, (ip_hash, normalized_cnpj)).fetchone()
                distinct_cnpjs = int(row["total"] or 0)
                if distinct_cnpjs >= 4:
                    reasons.append(f"IP relacionado a {distinct_cnpjs} outros CNPJs em 30 dias")
                    score += 70
                elif distinct_cnpjs >= 2:
                    reasons.append(f"IP relacionado a {distinct_cnpjs} outros CNPJs em 30 dias")
                    score += 50
                elif distinct_cnpjs == 1:
                    reasons.append("IP já apareceu em outro CNPJ recentemente")
                    score += 20
        if outcome != "blocked" and score >= 50:
            outcome = "review"
        return {
            "email": normalized_email, "cnpj": normalized_cnpj, "score": min(score, 100),
            "outcome": outcome, "reasons": reasons,
            "ip_hash": ip_hash, "ip_masked": self._mask_ip(client_ip),
        }

    def list_trial_attempts(self, limit=200):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("""
                SELECT * FROM trial_attempts
                ORDER BY created_at DESC LIMIT ?
            """, (int(limit),)).fetchall()]

    def record_audit(self, action, entity_type="", entity_id="", details="", actor="admin"):
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO audit_events(id, actor, action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), actor, action, entity_type, str(entity_id or ""),
                  str(details or "")[:1500]))

    def list_audit_events(self, limit=200):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("""
                SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?
            """, (int(limit),)).fetchall()]

    def record_payment(self, company_id, amount, method, billing_cycle, status="pending",
                       external_id="", due_at=None, paid_at=None, notes=""):
        allowed_methods = {"PIX", "Cartão", "Boleto", "Transferência"}
        allowed_status = {"pending", "paid", "failed", "refunded", "canceled"}
        if method not in allowed_methods:
            raise ValueError("Forma de pagamento inválida.")
        if status not in allowed_status:
            raise ValueError("Status de pagamento inválido.")
        payment_id = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO payments(
                    id, company_id, amount, method, billing_cycle, status,
                    external_id, due_at, paid_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (payment_id, company_id, float(amount or 0), method, billing_cycle, status,
                  str(external_id or ""), due_at, paid_at, str(notes or "")))
        self.record_audit("payment_recorded", "payment", payment_id,
                          f"{method} · {billing_cycle} · {status} · R$ {float(amount or 0):.2f}")
        return payment_id

    def list_payments(self, limit=300):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("""
                SELECT p.*, c.name AS company_name, c.cnpj
                FROM payments p JOIN companies c ON c.id=p.company_id
                ORDER BY p.created_at DESC LIMIT ?
            """, (int(limit),)).fetchall()]

    def control_room_stats(self):
        with self.connect() as conn:
            paid = conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid'"
            ).fetchone()[0]
            return {
                "companies": int(conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]),
                "users": int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]),
                "pending_requests": int(conn.execute(
                    "SELECT COUNT(*) FROM access_requests WHERE status IN ('pending','contacted')"
                ).fetchone()[0]),
                "active_trials": int(conn.execute(
                    "SELECT COUNT(*) FROM companies WHERE subscription_status='trialing' "
                    "AND trial_ends_at >= CURRENT_TIMESTAMP"
                ).fetchone()[0]),
                "active_subscriptions": int(conn.execute(
                    "SELECT COUNT(*) FROM companies WHERE subscription_status IN ('active','grace')"
                ).fetchone()[0]),
                "risk_reviews": int(conn.execute(
                    "SELECT COUNT(*) FROM access_requests WHERE risk_status='review' "
                    "AND status IN ('pending','contacted')"
                ).fetchone()[0]),
                "paid_total": float(paid or 0),
            }


    @staticmethod
    def normalize_campaign_code(value):
        return re.sub(r"[^A-Z0-9_-]", "", str(value or "").strip().upper())[:40]

    def create_campaign(self, code, name, campaign_type="coupon", owner_name="",
                        benefit_type="percent", benefit_value=0, max_uses=0,
                        valid_from=None, valid_until=None, allowed_cycles="", notes=""):
        code = self.normalize_campaign_code(code)
        if len(code) < 3:
            raise ValueError("O código deve ter ao menos 3 caracteres.")
        if not str(name or "").strip():
            raise ValueError("Informe o nome da campanha.")
        if campaign_type not in {"coupon","referral"}:
            raise ValueError("Tipo de campanha inválido.")
        if benefit_type not in {"percent","fixed","none"}:
            raise ValueError("Tipo de benefício inválido.")
        value=float(benefit_value or 0)
        if benefit_type=="percent" and not 0 <= value <= 100:
            raise ValueError("Percentual deve ficar entre 0 e 100.")
        cid=str(uuid.uuid4())
        with self.connect() as conn:
            try:
                conn.execute("""
                    INSERT INTO campaigns(
                        id, code, name, campaign_type, owner_name, benefit_type,
                        benefit_value, max_uses, per_cnpj_limit, valid_from,
                        valid_until, allowed_cycles, active, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 1, ?)
                """,(cid,code,str(name).strip(),campaign_type,str(owner_name or "").strip(),
                     benefit_type,value,max(0,int(max_uses or 0)),valid_from,valid_until,
                     str(allowed_cycles or "").strip(),str(notes or "").strip()))
            except sqlite3.IntegrityError as e:
                raise ValueError("Já existe uma campanha com esse código.") from e
        self.record_audit("campaign_created","campaign",cid,f"Código {code}")
        return cid

    def list_campaigns(self, include_inactive=True):
        sql = """
            SELECT c.*,
                   COUNT(u.id) AS uses_count,
                   SUM(CASE WHEN u.status IN ('activated','paid') THEN 1 ELSE 0 END) AS conversions
            FROM campaigns c LEFT JOIN campaign_uses u ON u.campaign_id=c.id
        """
        if not include_inactive:
            sql += " WHERE c.active=1"
        sql += " GROUP BY c.id ORDER BY c.created_at DESC"
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql).fetchall()]

    def set_campaign_active(self, campaign_id, active):
        with self.connect() as conn:
            conn.execute("UPDATE campaigns SET active=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                         (1 if active else 0,campaign_id))
        self.record_audit("campaign_status","campaign",campaign_id,"Ativa" if active else "Inativa")

    def validate_campaign_code(self, code, cnpj=""):
        code=self.normalize_campaign_code(code)
        if not code:
            return None
        cnpj=self.normalize_cnpj(cnpj)
        now=datetime.utcnow().isoformat(timespec="seconds")
        with self.connect() as conn:
            row=conn.execute("SELECT * FROM campaigns WHERE code=? AND active=1",(code,)).fetchone()
            if not row:
                raise ValueError("Código de indicação ou cupom inválido/inativo.")
            c=dict(row)
            if c.get("valid_from") and str(c["valid_from"]) > now:
                raise ValueError("Este código ainda não está válido.")
            if c.get("valid_until") and str(c["valid_until"]) < now:
                raise ValueError("Este código expirou.")
            max_uses=int(c.get("max_uses") or 0)
            if max_uses:
                used=conn.execute("SELECT COUNT(*) FROM campaign_uses WHERE campaign_id=?",(c["id"],)).fetchone()[0]
                if int(used or 0)>=max_uses:
                    raise ValueError("Este código atingiu o limite de utilizações.")
            if cnpj:
                used=conn.execute("SELECT COUNT(*) FROM campaign_uses WHERE campaign_id=? AND cnpj=?",
                                  (c["id"],cnpj)).fetchone()[0]
                if int(used or 0) >= int(c.get("per_cnpj_limit") or 1):
                    raise ValueError("Este código já foi utilizado por este CNPJ.")
        return c

    def record_campaign_use(self, campaign, email, cnpj, access_request_id="", company_id="", status="lead"):
        if not campaign:
            return None
        uid=str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO campaign_uses(
                    id,campaign_id,code,email,cnpj,access_request_id,company_id,status,benefit_value
                ) VALUES (?,?,?,?,?,?,?,?,?)
            """,(uid,campaign["id"],campaign["code"],str(email or "").strip().lower(),
                 self.normalize_cnpj(cnpj),str(access_request_id or ""),str(company_id or ""),
                 status,float(campaign.get("benefit_value") or 0)))
        return uid

    def campaign_uses(self, limit=500):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT u.*,c.name AS campaign_name,c.campaign_type,c.owner_name,c.benefit_type
                FROM campaign_uses u JOIN campaigns c ON c.id=u.campaign_id
                ORDER BY u.created_at DESC LIMIT ?
            """,(int(limit),)).fetchall()]

    def register(self, company_name, name, email, password):
        if not all(str(value).strip() for value in (company_name, name, email)):
            raise ValueError("Preencha empresa, nome e e-mail.")
        company_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
        normalized_email = email.strip().lower()
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO companies(
                    id, name, trial_started_at, trial_ends_at
                ) VALUES (?, ?, CURRENT_TIMESTAMP, datetime('now', ?))
            """, (company_id, company_name.strip(), f"+{TRIAL_DAYS} days"))
            conn.execute(
                "INSERT INTO users(id, company_id, name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
                (user_id, company_id, name.strip(), normalized_email, hash_password(password)),
            )
        return self.authenticate(normalized_email, password)

    def ensure_local_admin(self):
        """Preserva o administrador local em instalações existentes do MVP.

        Se ainda não houver nenhum usuário com papel admin, promove somente a conta
        mais antiga. Em produção, ADMIN_EMAILS continua sendo o mecanismo recomendado
        para bootstrap explícito.
        """
        with self.connect() as conn:
            has_admin = conn.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone()
            if has_admin:
                return
            oldest = conn.execute("SELECT id FROM users ORDER BY created_at ASC, rowid ASC LIMIT 1").fetchone()
            if oldest:
                conn.execute("UPDATE users SET role='admin' WHERE id=?", (oldest["id"],))

    def user_is_admin(self, user):
        return bool(user and str(user.get("role") or "").lower() == "admin")

    def request_access(self, company_name, name, email, whatsapp, segment="", challenge="",
                       job_title="", cnpj="", how_heard="", client_ip="", campaign_code=""):
        values = [str(value or "").strip() for value in (company_name, name, email, whatsapp, cnpj)]
        if not all(values):
            raise ValueError("Preencha empresa, CNPJ, nome, e-mail e WhatsApp.")
        company_name, name, normalized_email, whatsapp, raw_cnpj = values
        normalized_email = normalized_email.lower()
        risk = self.assess_trial_request(normalized_email, raw_cnpj, client_ip)
        campaign = self.validate_campaign_code(campaign_code, risk["cnpj"]) if campaign_code else None
        request_id = str(uuid.uuid4())

        with self.connect() as conn:
            self._record_trial_attempt(
                conn, normalized_email, risk["cnpj"], client_ip,
                risk["outcome"], risk["score"], risk["reasons"]
            )
            if risk["outcome"] == "blocked":
                raise ValueError(
                    "Não foi possível liberar automaticamente um novo período gratuito "
                    "para estes dados. Entre em contato com o atendimento."
                )
            conn.execute("""
                INSERT INTO access_requests(
                    id, company_name, name, email, whatsapp, segment, challenge,
                    job_title, cnpj, how_heard, request_ip_hash, request_ip_masked,
                    risk_score, risk_status, risk_reasons, campaign_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    company_name=excluded.company_name, name=excluded.name,
                    whatsapp=excluded.whatsapp, segment=excluded.segment,
                    challenge=excluded.challenge, job_title=excluded.job_title,
                    cnpj=excluded.cnpj, how_heard=excluded.how_heard,
                    request_ip_hash=excluded.request_ip_hash,
                    request_ip_masked=excluded.request_ip_masked,
                    risk_score=excluded.risk_score,
                    risk_status=excluded.risk_status,
                    risk_reasons=excluded.risk_reasons,
                    campaign_code=excluded.campaign_code,
                    status=CASE WHEN access_requests.status='activated' THEN 'activated' ELSE 'pending' END,
                    invitation_hash=CASE WHEN access_requests.status='activated' THEN access_requests.invitation_hash ELSE '' END,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                request_id, company_name, name, normalized_email, whatsapp,
                str(segment or "").strip(), str(challenge or "").strip(),
                str(job_title or "").strip(), risk["cnpj"], str(how_heard or "").strip(),
                risk["ip_hash"], risk["ip_masked"], risk["score"], risk["outcome"],
                " | ".join(risk["reasons"])[:1200],
                self.normalize_campaign_code(campaign_code),
            ))
        if campaign:
            self.record_campaign_use(
                campaign, normalized_email, risk["cnpj"],
                access_request_id=request_id, status="lead"
            )
        self.record_audit(
            "access_request", "access_request", normalized_email,
            f"CNPJ {risk['cnpj']} · risco {risk['score']} · {risk['outcome']}",
            actor="public",
        )
        return risk


    def list_access_requests(self, status=""):
        sql = "SELECT * FROM access_requests"
        params = []
        if status:
            sql += " WHERE status=?"
            params.append(status)
        sql += " ORDER BY created_at DESC"
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def count_access_requests(self, statuses=("pending", "contacted")):
        statuses = tuple(statuses or ())
        if not statuses:
            return 0
        placeholders = ",".join("?" for _ in statuses)
        with self.connect() as conn:
            return int(conn.execute(
                f"SELECT COUNT(*) FROM access_requests WHERE status IN ({placeholders})", statuses
            ).fetchone()[0])

    def reject_access_request(self, request_id):
        with self.connect() as conn:
            conn.execute(
                "UPDATE access_requests SET status='rejected', invitation_hash='', updated_at=CURRENT_TIMESTAMP "
                "WHERE id=? AND status<>'activated'", (request_id,)
            )

    def mark_request_contacted(self, request_id):
        with self.connect() as conn:
            conn.execute("""
                UPDATE access_requests SET status='contacted', contacted_at=CURRENT_TIMESTAMP,
                    updated_at=CURRENT_TIMESTAMP WHERE id=? AND status<>'activated'
            """, (request_id,))

    def approve_access_request(self, request_id, trial_days=None, admin_notes=""):
        invitation_code = "NX-" + secrets.token_hex(4).upper()
        trial_days = max(int(trial_days or TRIAL_DAYS), 1)
        with self.connect() as conn:
            updated = conn.execute("""
                UPDATE access_requests SET status='invited', invitation_hash=?,
                    approved_trial_days=?, admin_notes=?,
                    invitation_expires_at=datetime('now', '+7 days'),
                    invited_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND status<>'activated'
            """, (hash_password(invitation_code), trial_days, str(admin_notes or '').strip(), request_id)).rowcount
        if not updated:
            raise ValueError("Solicitação indisponível para convite.")
        return invitation_code

    def activate_invitation(self, email, invitation_code, password):
        normalized_email = str(email or "").strip().lower()
        code = str(invitation_code or "").strip().upper()
        with self.connect() as conn:
            request = conn.execute("""
                SELECT * FROM access_requests WHERE email=? AND status='invited'
            """, (normalized_email,)).fetchone()
            if request and not _timestamp_not_expired(
                request["invitation_expires_at"], allow_missing=True
            ):
                request = None
            if not request or not verify_password(code, request["invitation_hash"]):
                raise ValueError("E-mail ou código de convite inválido.")
            if conn.execute("SELECT 1 FROM users WHERE email=?", (normalized_email,)).fetchone():
                raise ValueError("Este e-mail já possui uma conta.")
            normalized_cnpj = self.normalize_cnpj(request["cnpj"])
            if normalized_cnpj and conn.execute(
                "SELECT 1 FROM companies WHERE cnpj=? LIMIT 1", (normalized_cnpj,)
            ).fetchone():
                raise ValueError(
                    "Este CNPJ já possui uma empresa ativada no LicitaNexo. "
                    "Não é possível iniciar um novo período gratuito."
                )
            password_hash = hash_password(password)
            company_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
            conn.execute("""
                INSERT INTO companies(id, name, cnpj, billing_email, trial_started_at, trial_ends_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, datetime('now', ?))
            """, (
                company_id, request["company_name"], normalized_cnpj,
                normalized_email, f"+{int(request['approved_trial_days'] or TRIAL_DAYS)} days"
            ))
            conn.execute("""
                INSERT INTO users(id, company_id, name, email, password_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, company_id, request["name"], normalized_email, password_hash))
            conn.execute("""
                UPDATE access_requests SET status='activated', activated_at=CURRENT_TIMESTAMP,
                    invitation_hash='', updated_at=CURRENT_TIMESTAMP WHERE id=?
            """, (request["id"],))
            if request["campaign_code"]:
                conn.execute("""
                    UPDATE campaign_uses
                    SET status='activated', company_id=?, updated_at=CURRENT_TIMESTAMP
                    WHERE access_request_id=? AND code=?
                """, (company_id, request["id"], request["campaign_code"]))
        return self.authenticate(normalized_email, password)

    def authenticate(self, email, password):
        normalized = email.strip().lower()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT u.*, c.name AS company_name FROM users u JOIN companies c ON c.id=u.company_id WHERE u.email=?",
                (normalized,),
            ).fetchone()
            if row and verify_password(password, row["password_hash"]):
                conn.execute("UPDATE users SET last_login_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
                updated = conn.execute(
                    "SELECT u.*, c.name AS company_name FROM users u JOIN companies c ON c.id=u.company_id WHERE u.id=?",
                    (row["id"],),
                ).fetchone()
                return dict(updated)
        return None

    def request_password_reset(self, email):
        """Register a recovery request without revealing whether the e-mail exists."""
        normalized_email = str(email or "").strip().lower()
        if not normalized_email:
            raise ValueError("Informe seu e-mail.")
        with self.connect() as conn:
            user = conn.execute("SELECT id FROM users WHERE email=?", (normalized_email,)).fetchone()
            if not user:
                return
            conn.execute(
                "UPDATE password_reset_requests SET status='superseded', code_hash='' "
                "WHERE user_id=? AND status IN ('requested', 'code_generated')",
                (user["id"],),
            )
            conn.execute(
                "INSERT INTO password_reset_requests(id, user_id) VALUES (?, ?)",
                (str(uuid.uuid4()), user["id"]),
            )

    def list_password_reset_requests(self):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("""
                SELECT r.*, u.name, u.email, c.name AS company_name
                FROM password_reset_requests r
                JOIN users u ON u.id=r.user_id
                JOIN companies c ON c.id=u.company_id
                WHERE r.status IN ('requested', 'code_generated')
                ORDER BY r.requested_at DESC
            """).fetchall()]

    def generate_password_reset_code(self, request_id):
        recovery_code = "NX-R-" + secrets.token_hex(4).upper()
        with self.connect() as conn:
            updated = conn.execute("""
                UPDATE password_reset_requests
                SET status='code_generated', code_hash=?,
                    expires_at=datetime('now', '+30 minutes'),
                    code_generated_at=CURRENT_TIMESTAMP
                WHERE id=? AND status IN ('requested', 'code_generated')
            """, (hash_password(recovery_code), request_id)).rowcount
        if not updated:
            raise ValueError("Solicitação de recuperação indisponível.")
        return recovery_code

    def reset_password(self, email, recovery_code, new_password):
        normalized_email = str(email or "").strip().lower()
        code = str(recovery_code or "").strip().upper()
        with self.connect() as conn:
            request = conn.execute("""
                SELECT r.*, u.id AS account_user_id
                FROM password_reset_requests r
                JOIN users u ON u.id=r.user_id
                WHERE u.email=? AND r.status='code_generated'
                ORDER BY r.code_generated_at DESC LIMIT 1
            """, (normalized_email,)).fetchone()
            if request and not _timestamp_not_expired(request["expires_at"]):
                request = None
            if not request or not verify_password(code, request["code_hash"]):
                raise ValueError("E-mail ou código de recuperação inválido ou expirado.")
            conn.execute(
                "UPDATE users SET password_hash=? WHERE id=?",
                (hash_password(new_password), request["account_user_id"]),
            )
            conn.execute("""
                UPDATE password_reset_requests
                SET status='used', code_hash='', used_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (request["id"],))

    def local_recovery_users(self):
        """Return local accounts for the server-owner recovery utility."""
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("""
                SELECT u.email, u.name, c.name AS company_name
                FROM users u JOIN companies c ON c.id=u.company_id
                ORDER BY u.email
            """).fetchall()]

    def set_password_by_email_for_local_recovery(self, email, new_password):
        """Reset a password from the local server console only."""
        normalized_email = str(email or "").strip().lower()
        with self.connect() as conn:
            updated = conn.execute(
                "UPDATE users SET password_hash=? WHERE email=?",
                (hash_password(new_password), normalized_email),
            ).rowcount
            if not updated:
                raise ValueError("Conta não encontrada para esse e-mail.")

    def get_user(self, company_id, user_id):
        with self.connect() as conn:
            row = conn.execute("""
                SELECT u.*, c.name AS company_name FROM users u
                JOIN companies c ON c.id=u.company_id
                WHERE u.id=? AND u.company_id=?
            """, (user_id, company_id)).fetchone()
        return dict(row) if row else None

    def accept_legal(self, company_id, user_id, terms_version=LEGAL_VERSION):
        with self.connect() as conn:
            conn.execute("""
                UPDATE users SET terms_version=?, terms_accepted_at=CURRENT_TIMESTAMP,
                    privacy_accepted_at=CURRENT_TIMESTAMP
                WHERE id=? AND company_id=?
            """, (terms_version, user_id, company_id))

    def legal_is_current(self, user, terms_version=LEGAL_VERSION):
        return bool(
            user and user.get("terms_version") == terms_version
            and user.get("terms_accepted_at") and user.get("privacy_accepted_at")
        )

    def get_company_account(self, company_id):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
        return dict(row) if row else None

    def subscription_access(self, company_id):
        account = self.get_company_account(company_id)
        if not account:
            return False, "Conta não encontrada", None
        status = account["subscription_status"]
        if status in {"active", "grace"}:
            return True, "Assinatura ativa", account
        if status == "trialing":
            with self.connect() as conn:
                active = conn.execute(
                    "SELECT datetime(?) >= CURRENT_TIMESTAMP", (account["trial_ends_at"],)
                ).fetchone()[0]
            if active:
                return True, "Período de teste", account
            return False, "Período de teste encerrado", account
        labels = {
            "past_due": "Pagamento pendente", "canceled": "Assinatura cancelada",
            "suspended": "Conta suspensa",
        }
        return False, labels.get(status, "Assinatura inativa"), account

    def list_companies_admin(self):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("""
                SELECT c.*, COUNT(u.id) AS users_count
                FROM companies c LEFT JOIN users u ON u.company_id=c.id
                GROUP BY c.id ORDER BY c.created_at DESC
            """).fetchall()]

    def update_company_subscription(self, company_id, plan, status, trial_ends_at=None,
                                    subscription_ends_at=None):
        allowed_statuses = {"trialing", "active", "grace", "past_due", "canceled", "suspended"}
        if status not in allowed_statuses:
            raise ValueError("Situação de assinatura inválida.")
        with self.connect() as conn:
            conn.execute("""
                UPDATE companies SET plan=?, subscription_status=?, trial_ends_at=?,
                    subscription_ends_at=? WHERE id=?
            """, (plan.strip() or "Essencial", status, trial_ends_at,
                    subscription_ends_at, company_id))
        self.record_audit(
            "subscription_updated", "company", company_id,
            f"Plano {plan.strip() or 'Essencial'} · status {status} · fim {subscription_ends_at or trial_ends_at or '-'}"
        )

    @staticmethod
    def _item_values(item):
        return (
            item.get("numeroControlePNCP") or "",
            item.get("orgao") or "", item.get("municipio") or "",
            item.get("uf") or "", canonical_modality_name(item.get("modalidade") or ""),
            item.get("publicacao"), item.get("abertura"), item.get("encerramento"),
            item.get("objeto") or "", item.get("valor"), item.get("link") or "",
            int(bool(item.get("srp"))),
            item.get("source_name") or "PNCP", item.get("source_channel") or "PNCP",
        )

    def upsert_catalog_page(self, company_id, items):
        saved = 0
        with self.connect() as conn:
            for item in items:
                values = self._item_values(item)
                control = values[0]
                if not control:
                    continue
                conn.execute("""
                    INSERT INTO pncp_catalog(
                        id, company_id, pncp_control_number, agency, city, state,
                        modality, published_at, opening_at, closing_at, object, estimated_value,
                        source_url, srp, source_name, source_channel
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(company_id, pncp_control_number) DO UPDATE SET
                        agency=excluded.agency, city=excluded.city, state=excluded.state,
                        modality=excluded.modality, published_at=excluded.published_at,
                        opening_at=excluded.opening_at, closing_at=excluded.closing_at,
                        object=excluded.object, srp=excluded.srp,
                        estimated_value=excluded.estimated_value,
                        source_url=CASE WHEN excluded.source_url<>'' THEN excluded.source_url ELSE pncp_catalog.source_url END,
                        source_name=excluded.source_name, source_channel=excluded.source_channel,
                        last_seen_at=CURRENT_TIMESTAMP
                """, (str(uuid.uuid4()), company_id, *values))
                saved += 1
        return saved

    def list_catalog(self, company_id, search="", state="", modality="", source_name="",
                     srp=None, minimum=None, maximum=None, limit=1000):
        sql = "SELECT * FROM pncp_catalog WHERE company_id=?"
        params = [company_id]
        if search.strip():
            words = [word.lower() for word in search.split() if word.strip()]
            for word in words:
                sql += " AND (lower(object) LIKE ? OR lower(agency) LIKE ? OR lower(city) LIKE ?)"
                term = f"%{word}%"
                params.extend([term, term, term])
        if state:
            sql += " AND state=?"
            params.append(state)
        if modality:
            sql += " AND modality=?"
            params.append(modality)
        if source_name:
            sql += " AND source_name=?"
            params.append(source_name)
        if srp is not None:
            sql += " AND srp=?"
            params.append(int(bool(srp)))
        if minimum is not None:
            sql += " AND estimated_value>=?"
            params.append(minimum)
        if maximum is not None:
            sql += " AND estimated_value<=?"
            params.append(maximum)
        sql += " ORDER BY published_at DESC, last_seen_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def catalog_filters(self, company_id):
        with self.connect() as conn:
            states = [row[0] for row in conn.execute(
                "SELECT DISTINCT state FROM pncp_catalog WHERE company_id=? AND state<>'' ORDER BY state", (company_id,)
            )]
            modalities = [row[0] for row in conn.execute(
                "SELECT DISTINCT modality FROM pncp_catalog WHERE company_id=? AND modality<>'' ORDER BY modality", (company_id,)
            )]
            sources = [row[0] for row in conn.execute(
                "SELECT DISTINCT source_name FROM pncp_catalog WHERE company_id=? AND source_name<>'' ORDER BY source_name",
                (company_id,),
            )]
        return states, modalities, sources

    def catalog_count(self, company_id):
        with self.connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM pncp_catalog WHERE company_id=?", (company_id,)).fetchone()[0]

    def clear_catalog(self, company_id):
        """Limpa apenas o Radar temporário; a Jornada permanece intacta."""
        with self.connect() as conn:
            conn.execute("DELETE FROM pncp_catalog WHERE company_id=?", (company_id,))
            conn.execute("DELETE FROM source_sync_checkpoints WHERE company_id=?", (company_id,))

    def get_checkpoint(self, company_id, modality_code, state, publication_day,
                       source="PNCP", period_start=None, period_end=None):
        period_start = period_start or publication_day
        period_end = period_end or publication_day
        with self.connect() as conn:
            row = conn.execute("""
                SELECT * FROM source_sync_checkpoints
                WHERE company_id=? AND source=? AND modality_code=? AND state=?
                  AND period_start=? AND period_end=? AND publication_day=?
            """, (company_id, source, modality_code, state or "", period_start,
                    period_end, publication_day)).fetchone()
        return dict(row) if row else None

    def save_checkpoint(self, company_id, modality_code, state, publication_day, next_page,
                        completed, items_saved, error="", source="PNCP",
                        period_start=None, period_end=None):
        period_start = period_start or publication_day
        period_end = period_end or publication_day
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO source_sync_checkpoints(
                    company_id, source, modality_code, state, period_start, period_end, publication_day,
                    next_page, completed, items_saved, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_id, source, modality_code, state, period_start, period_end, publication_day)
                DO UPDATE SET
                    next_page=excluded.next_page, completed=excluded.completed,
                    items_saved=excluded.items_saved, last_error=excluded.last_error,
                    updated_at=CURRENT_TIMESTAMP
            """, (company_id, source, modality_code, state or "", period_start, period_end, publication_day,
                    next_page, int(completed), items_saved, error[:500]))

    def reset_checkpoints(self, company_id, modality_code, state, start_day, end_day, source="PNCP"):
        with self.connect() as conn:
            conn.execute("""
                DELETE FROM source_sync_checkpoints
                WHERE company_id=? AND source=? AND modality_code=? AND state=?
                  AND period_start=? AND period_end=?
            """, (company_id, source, modality_code, state or "", start_day, end_day))

    def upsert_opportunity(self, company_id, item):
        (control, agency, city, state, modality, published, opening, closing, obj, value,
         link, srp, source_name, source_channel) = self._item_values(item)
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO opportunities(
                    id, company_id, pncp_control_number, agency, city, state, modality,
                    published_at, opening_at, closing_at, object, estimated_value, source_url,
                    srp, source_name, source_channel, stage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_id, pncp_control_number) DO UPDATE SET
                    agency=excluded.agency, city=excluded.city, state=excluded.state,
                    modality=excluded.modality, published_at=excluded.published_at,
                    opening_at=excluded.opening_at, closing_at=excluded.closing_at,
                    object=excluded.object, srp=excluded.srp,
                    estimated_value=excluded.estimated_value,
                    source_url=CASE WHEN excluded.source_url<>'' THEN excluded.source_url ELSE opportunities.source_url END,
                    source_name=excluded.source_name, source_channel=excluded.source_channel,
                    updated_at=CURRENT_TIMESTAMP
            """, (str(uuid.uuid4()), company_id, control or None, agency, city, state,
                    modality, published, opening, closing, obj, value, link, srp, source_name,
                    source_channel, "Nova oportunidade"))

    def add_manual_opportunity(self, company_id, agency, obj, city="", state="", modality="", estimated_value=None, certame_at=None, source_url=""):
        control = f"MANUAL-{uuid.uuid4()}"
        self.upsert_opportunity(company_id, {
            "numeroControlePNCP": control, "orgao": agency, "municipio": city, "uf": state,
            "modalidade": modality, "objeto": obj, "valor": estimated_value, "link": source_url,
            "source_name": "Cadastro manual", "source_channel": "Manual",
        })
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id FROM opportunities WHERE company_id=? AND pncp_control_number=?",
                (company_id, control),
            ).fetchone()
        if row and certame_at:
            self.ensure_opportunity_workspace(company_id, row["id"])
            self.update_details(company_id, row["id"], certame_at=certame_at)
        return row["id"] if row else None

    def add_catalog_to_pipeline(self, company_id, catalog_ids):
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM pncp_catalog WHERE company_id=? AND id IN ({','.join('?' for _ in catalog_ids)})",
                [company_id, *catalog_ids],
            ).fetchall() if catalog_ids else []
        for row in rows:
            self.upsert_opportunity(company_id, {
                "numeroControlePNCP": row["pncp_control_number"], "orgao": row["agency"],
                "municipio": row["city"], "uf": row["state"], "modalidade": row["modality"],
                "publicacao": row["published_at"], "abertura": row["opening_at"],
                "encerramento": row["closing_at"], "srp": bool(row["srp"]),
                "objeto": row["object"], "valor": row["estimated_value"], "link": row["source_url"],
                "source_name": row["source_name"], "source_channel": row["source_channel"],
            })
        return len(rows)

    def get_opportunity(self, company_id, opportunity_id):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM opportunities WHERE id=? AND company_id=?",
                (opportunity_id, company_id),
            ).fetchone()
        return dict(row) if row else None

    def delete_opportunity(self, company_id, opportunity_id):
        """Remove uma oportunidade da Jornada e seus dados vinculados."""
        with self.connect() as conn:
            cursor = conn.execute(
                "DELETE FROM opportunities WHERE id=? AND company_id=?",
                (opportunity_id, company_id),
            )
        return cursor.rowcount > 0

    def ensure_opportunity_workspace(self, company_id, opportunity_id):
        defaults = [
            "Ler o edital e anexos", "Conferir objeto e quantidades",
            "Verificar qualificação técnica", "Conferir certidões",
            "Confirmar capacidade de entrega", "Solicitar cotações",
            "Calcular preço e margem", "Preparar proposta",
            "Revisar documentação", "Confirmar envio da proposta",
        ]
        with self.connect() as conn:
            allowed = conn.execute(
                "SELECT 1 FROM opportunities WHERE id=? AND company_id=?", (opportunity_id, company_id)
            ).fetchone()
            if not allowed:
                return False
            conn.execute("""
                INSERT OR IGNORE INTO opportunity_details(opportunity_id, company_id)
                VALUES (?, ?)
            """, (opportunity_id, company_id))
            count = conn.execute(
                "SELECT COUNT(*) FROM opportunity_checklist WHERE opportunity_id=? AND company_id=?",
                (opportunity_id, company_id),
            ).fetchone()[0]
            if count == 0:
                conn.executemany("""
                    INSERT INTO opportunity_checklist(id, opportunity_id, company_id, title, position)
                    VALUES (?, ?, ?, ?, ?)
                """, [(str(uuid.uuid4()), opportunity_id, company_id, title, position)
                        for position, title in enumerate(defaults)])
        return True

    def get_details(self, company_id, opportunity_id):
        self.ensure_opportunity_workspace(company_id, opportunity_id)
        with self.connect() as conn:
            row = conn.execute("""
                SELECT * FROM opportunity_details WHERE opportunity_id=? AND company_id=?
            """, (opportunity_id, company_id)).fetchone()
        return dict(row) if row else None

    def update_details(self, company_id, opportunity_id, **fields):
        allowed = {
            "decision", "next_action", "deadline", "responsible", "notes", "certame_at",
            "our_bid", "winning_bid", "contract_value", "winner", "loss_reason",
        }
        clean = {key: value for key, value in fields.items() if key in allowed}
        if not clean:
            return
        self.ensure_opportunity_workspace(company_id, opportunity_id)
        assignments = ", ".join(f"{key}=?" for key in clean)
        with self.connect() as conn:
            conn.execute(
                f"UPDATE opportunity_details SET {assignments}, updated_at=CURRENT_TIMESTAMP "
                "WHERE opportunity_id=? AND company_id=?",
                [*clean.values(), opportunity_id, company_id],
            )

    def pipeline_summaries(self, company_id, search=""):
        sql = """
            SELECT o.*, d.next_action, d.deadline, d.responsible, d.decision, d.certame_at,
                (SELECT COUNT(*) FROM opportunity_checklist c
                 WHERE c.opportunity_id=o.id AND c.company_id=o.company_id) AS checklist_total,
                (SELECT COUNT(*) FROM opportunity_checklist c
                 WHERE c.opportunity_id=o.id AND c.company_id=o.company_id AND c.completed=1) AS checklist_done,
                (SELECT COUNT(*) FROM opportunity_tasks t
                 WHERE t.opportunity_id=o.id AND t.company_id=o.company_id AND t.completed=0) AS open_tasks
            FROM opportunities o
            LEFT JOIN opportunity_details d ON d.opportunity_id=o.id AND d.company_id=o.company_id
            WHERE o.company_id=?
        """
        params = [company_id]
        if search:
            sql += " AND (lower(o.object) LIKE ? OR lower(o.agency) LIKE ?)"
            term = f"%{search.lower()}%"
            params.extend([term, term])
        sql += " ORDER BY CASE WHEN d.certame_at IS NULL OR d.certame_at='' THEN 1 ELSE 0 END, d.certame_at, o.updated_at DESC"
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def _list_children(self, table, company_id, opportunity_id, order_by="created_at"):
        allowed = {
            "opportunity_tasks", "opportunity_checklist", "opportunity_documents",
            "opportunity_quote_items",
        }
        if table not in allowed:
            raise ValueError("Tabela inválida")
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(
                f"SELECT * FROM {table} WHERE opportunity_id=? AND company_id=? ORDER BY {order_by}",
                (opportunity_id, company_id),
            ).fetchall()]

    def list_tasks(self, company_id, opportunity_id):
        return self._list_children("opportunity_tasks", company_id, opportunity_id, "completed, due_date, created_at")

    def add_task(self, company_id, opportunity_id, title, due_date=None, priority="Normal"):
        if not title.strip():
            raise ValueError("Informe a tarefa.")
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO opportunity_tasks(id, opportunity_id, company_id, title, due_date, priority)
                SELECT ?, id, company_id, ?, ?, ? FROM opportunities WHERE id=? AND company_id=?
            """, (str(uuid.uuid4()), title.strip(), due_date, priority, opportunity_id, company_id))

    def list_checklist(self, company_id, opportunity_id):
        self.ensure_opportunity_workspace(company_id, opportunity_id)
        return self._list_children("opportunity_checklist", company_id, opportunity_id, "position, created_at")

    def add_checklist_item(self, company_id, opportunity_id, title):
        if not title.strip():
            raise ValueError("Informe o item.")
        with self.connect() as conn:
            position = conn.execute(
                "SELECT COALESCE(MAX(position), -1)+1 FROM opportunity_checklist WHERE opportunity_id=? AND company_id=?",
                (opportunity_id, company_id),
            ).fetchone()[0]
            conn.execute("""
                INSERT INTO opportunity_checklist(id, opportunity_id, company_id, title, position)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), opportunity_id, company_id, title.strip(), position))

    def set_child_completed(self, table, company_id, item_id, completed):
        if table not in {"opportunity_tasks", "opportunity_checklist"}:
            raise ValueError("Tabela inválida")
        with self.connect() as conn:
            conn.execute(
                f"UPDATE {table} SET completed=? WHERE id=? AND company_id=?",
                (int(completed), item_id, company_id),
            )

    def delete_child(self, table, company_id, item_id):
        if table not in {
            "opportunity_tasks", "opportunity_checklist", "opportunity_documents",
            "opportunity_quote_items",
        }:
            raise ValueError("Tabela inválida")
        with self.connect() as conn:
            conn.execute(f"DELETE FROM {table} WHERE id=? AND company_id=?", (item_id, company_id))

    def list_documents(self, company_id, opportunity_id):
        return self._list_children("opportunity_documents", company_id, opportunity_id, "expiry_date, created_at")

    def add_document(self, company_id, opportunity_id, name, expiry_date=None, status="Pendente", notes=""):
        if not name.strip():
            raise ValueError("Informe o documento.")
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO opportunity_documents(id, opportunity_id, company_id, name, expiry_date, status, notes)
                SELECT ?, id, company_id, ?, ?, ?, ? FROM opportunities WHERE id=? AND company_id=?
            """, (str(uuid.uuid4()), name.strip(), expiry_date, status, notes.strip(), opportunity_id, company_id))

    def list_quote_items(self, company_id, opportunity_id):
        return self._list_children("opportunity_quote_items", company_id, opportunity_id)

    def add_quote_item(self, company_id, opportunity_id, description, quantity, unit_cost,
                       freight, taxes, other_costs, sale_price, supplier="",
                       lot_number="", edital_price=0, commission=0):
        if not description.strip():
            raise ValueError("Informe a descrição do item.")
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO opportunity_quote_items(
                    id, opportunity_id, company_id, description, quantity, unit_cost,
                    freight, taxes, other_costs, sale_price, supplier, lot_number, edital_price, commission
                ) SELECT ?, id, company_id, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                  FROM opportunities WHERE id=? AND company_id=?
            """, (str(uuid.uuid4()), description.strip(), quantity, unit_cost, freight,
                    taxes, other_costs, sale_price, supplier.strip(), str(lot_number or "").strip(),
                    float(edital_price or 0), float(commission or 0), opportunity_id, company_id))


    def update_quote_item(self, company_id, item_id, description, quantity, unit_cost,
                          freight, taxes, other_costs, sale_price, supplier="",
                          lot_number="", edital_price=0, commission=0):
        if not description.strip():
            raise ValueError("Informe a descrição do item.")
        with self.connect() as conn:
            cursor = conn.execute("""
                UPDATE opportunity_quote_items
                   SET description=?, quantity=?, unit_cost=?, freight=?, taxes=?,
                       other_costs=?, sale_price=?, supplier=?, lot_number=?, edital_price=?, commission=?
                 WHERE id=? AND company_id=?
            """, (description.strip(), quantity, unit_cost, freight, taxes, other_costs,
                  sale_price, supplier.strip(), str(lot_number or "").strip(),
                  float(edital_price or 0), float(commission or 0), item_id, company_id))
            if cursor.rowcount == 0:
                raise ValueError("Lote/item não encontrado.")

    def won_financial_summary(self, company_id, year=None, month=None, days=None):
        conditions = ["o.company_id=?", "o.stage='Ganha'"]
        params = [company_id]
        if year:
            conditions.append("strftime('%Y', o.updated_at)=?")
            params.append(str(year))
        if month:
            conditions.append("strftime('%m', o.updated_at)=?")
            params.append(f"{int(month):02d}")
        if days:
            conditions.append("date(o.updated_at) >= date('now', ?)")
            params.append(f"-{int(days)} days")
        with self.connect() as conn:
            row = conn.execute(f"""
                SELECT COUNT(DISTINCT o.id) AS wins,
                       COALESCE(SUM(CASE WHEN d.contract_value > 0 THEN d.contract_value
                                         ELSE COALESCE(q.quoted_value, 0) END), 0) AS won_value
                  FROM opportunities o
                  LEFT JOIN opportunity_details d
                    ON d.opportunity_id=o.id AND d.company_id=o.company_id
                  LEFT JOIN (
                      SELECT opportunity_id, company_id,
                             SUM(quantity * sale_price) AS quoted_value
                        FROM opportunity_quote_items
                       GROUP BY opportunity_id, company_id
                  ) q ON q.opportunity_id=o.id AND q.company_id=o.company_id
                 WHERE {' AND '.join(conditions)}
            """, params).fetchone()
        return {"wins": int(row["wins"] or 0), "won_value": float(row["won_value"] or 0)}

    def loss_reason_summary(self, company_id, limit=5):
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT trim(d.loss_reason) AS reason, COUNT(*) AS total
                  FROM opportunities o
                  JOIN opportunity_details d
                    ON d.opportunity_id=o.id AND d.company_id=o.company_id
                 WHERE o.company_id=? AND o.stage='Perdida'
                   AND trim(COALESCE(d.loss_reason, ''))<>''
                 GROUP BY trim(d.loss_reason)
                 ORDER BY total DESC, reason
                 LIMIT ?
            """, (company_id, int(limit))).fetchall()
        return [dict(row) for row in rows]

    def competition_summary(self, company_id):
        with self.connect() as conn:
            row = conn.execute("""
                SELECT COALESCE(SUM(q.quantity * q.sale_price), 0) AS total_value,
                       COUNT(DISTINCT o.id) AS opportunities
                FROM opportunities o
                JOIN opportunity_details d
                  ON d.opportunity_id=o.id AND d.company_id=o.company_id
                LEFT JOIN opportunity_quote_items q
                  ON q.opportunity_id=o.id AND q.company_id=o.company_id
                WHERE o.company_id=? AND d.decision='Participar'
            """, (company_id,)).fetchone()
        return {"total_value": float(row["total_value"] or 0),
                "opportunities": int(row["opportunities"] or 0)}

    def participation_calendar(self, company_id):
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT o.id, o.agency, o.object, o.stage,
                       d.certame_at AS certame_at,
                       COALESCE(SUM(q.quantity * q.sale_price), 0) AS quoted_value
                FROM opportunities o
                JOIN opportunity_details d
                  ON d.opportunity_id=o.id AND d.company_id=o.company_id
                LEFT JOIN opportunity_quote_items q
                  ON q.opportunity_id=o.id AND q.company_id=o.company_id
                WHERE o.company_id=? AND d.decision='Participar'
                GROUP BY o.id, o.agency, o.object, o.stage, d.certame_at
                ORDER BY CASE WHEN certame_at IS NULL THEN 1 ELSE 0 END, certame_at
            """, (company_id,)).fetchall()
        result=[]
        for row in rows:
            value=dict(row)
            raw=value.pop("certame_at", None)
            if raw:
                try:
                    value["certame"] = datetime.fromisoformat(str(raw).replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
                except (TypeError, ValueError):
                    value["certame"] = str(raw)[:16].replace("T", " ")
            else:
                value["certame"] = "Não informada"
            value["quoted_value"] = float(value.get("quoted_value") or 0)
            result.append(value)
        return result

    def essential_certame_calendar(self, company_id, from_date=None, limit=20):
        """Calendário enxuto do Essential: qualquer edital salvo com data de certame informada."""
        sql = """
            SELECT o.id, o.agency, o.object, o.modality, o.city, o.state, d.certame_at
            FROM opportunities o
            JOIN opportunity_details d
              ON d.opportunity_id=o.id AND d.company_id=o.company_id
            WHERE o.company_id=? AND d.decision='Participar'
              AND d.certame_at IS NOT NULL AND d.certame_at<>''
        """
        params = [company_id]
        if from_date:
            sql += " AND substr(d.certame_at, 1, 10) >= ?"
            params.append(str(from_date)[:10])
        sql += " ORDER BY d.certame_at ASC LIMIT ?"
        params.append(int(limit))
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def add_essential_calendar_note(self, company_id, note):
        text = str(note or "").strip()
        if not text:
            return None
        note_id = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO essential_calendar_notes(id, company_id, note) VALUES (?, ?, ?)",
                (note_id, company_id, text),
            )
        return note_id

    def list_essential_calendar_notes(self, company_id, limit=100):
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, note, created_at FROM essential_calendar_notes WHERE company_id=? "
                "ORDER BY created_at DESC LIMIT ?",
                (company_id, int(limit)),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_essential_calendar_note(self, company_id, note_id):
        with self.connect() as conn:
            cur = conn.execute(
                "DELETE FROM essential_calendar_notes WHERE id=? AND company_id=?",
                (note_id, company_id),
            )
        return bool(cur.rowcount)

    def list_opportunities(self, company_id, search="", state=""):
        sql = "SELECT * FROM opportunities WHERE company_id=?"
        params = [company_id]
        if search:
            sql += " AND lower(object) LIKE ?"
            params.append(f"%{search.lower()}%")
        if state:
            sql += " AND state=?"
            params.append(state)
        sql += " ORDER BY published_at DESC, created_at DESC"
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def update_stage(self, company_id, opportunity_id, stage):
        with self.connect() as conn:
            conn.execute(
                "UPDATE opportunities SET stage=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND company_id=?",
                (stage, opportunity_id, company_id),
            )

    def get_company_profile(self, company_id):
        with self.connect() as conn:
            conn.execute("INSERT OR IGNORE INTO company_profiles(company_id) VALUES (?)", (company_id,))
            row = conn.execute("SELECT * FROM company_profiles WHERE company_id=?", (company_id,)).fetchone()
        return dict(row)

    def save_company_profile(self, company_id, **fields):
        allowed = {
            "has_technical_certificate", "has_balance_sheet", "accepts_price_registration",
            "activity_type", "has_technical_manager", "accepts_samples", "accepts_site_visit",
            "service_states", "max_contract_value", "notes", "legal_name", "trade_name",
            "cnpj", "company_size", "cnaes", "offerings", "interest_keywords", "procurement_interests", "brands", "business_model",
            "delivery_days", "delivery_structure", "technical_certificate_details",
            "balance_sheet_year", "technical_manager_details", "desired_margin",
            "search_keyword", "search_nature", "search_modalities", "search_srp",
            "search_horizon", "search_minimum", "search_maximum", "search_order",
        }
        clean = {key: value for key, value in fields.items() if key in allowed}
        self.get_company_profile(company_id)
        assignments = ", ".join(f"{key}=?" for key in clean)
        with self.connect() as conn:
            conn.execute(
                f"UPDATE company_profiles SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE company_id=?",
                [*clean.values(), company_id],
            )

    def list_company_documents(self, company_id):
        # Núcleo documental enxuto para ME/MEI/EPP. O edital continua sendo a referência
        # final e o usuário pode adicionar qualquer documento específico do seu mercado.
        defaults = [
            ("Empresa", "Contrato social e alterações"),
            ("Empresa", "Cartão CNPJ"),
            ("Regularidade", "Certidão conjunta federal e dívida ativa da União"),
            ("Regularidade", "Certidão estadual"),
            ("Regularidade", "Certidão municipal"),
            ("Regularidade", "Certificado de regularidade do FGTS"),
            ("Regularidade", "CNDT - débitos trabalhistas"),
            ("Econômico-financeira", "Balanço patrimonial e demonstrações contábeis"),
            ("Econômico-financeira", "Certidão negativa de falência ou recuperação judicial"),
            ("Capacidade técnica", "Atestado de capacidade técnica"),
            ("Cadastro", "Cadastro SICAF"),
        ]
        basic_names = [document for _, document in defaults]
        with self.connect() as conn:
            conn.executemany(
                """INSERT OR IGNORE INTO company_documents(
                    id, company_id, category, document_type
                ) VALUES (?, ?, ?, ?)""",
                [(str(uuid.uuid4()), company_id, category, document) for category, document in defaults],
            )
            placeholders = ",".join("?" for _ in basic_names)
            rows = conn.execute(
                f"""SELECT * FROM company_documents
                    WHERE company_id=? AND (
                        document_type IN ({placeholders})
                        OR category='Adicionado pela empresa'
                        OR applicable='Sim'
                    )
                    ORDER BY CASE WHEN category='Adicionado pela empresa' THEN 1 ELSE 0 END,
                             category, document_type""",
                [company_id, *basic_names],
            ).fetchall()
        return [dict(row) for row in rows]

    def add_company_document(self, company_id, document_type):
        document_type = str(document_type or "").strip()
        if not document_type:
            raise ValueError("Informe o nome do documento.")
        if len(document_type) > 140:
            raise ValueError("Use um nome de documento mais curto.")
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT id FROM company_documents WHERE company_id=? AND lower(document_type)=lower(?)",
                (company_id, document_type),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE company_documents SET category='Adicionado pela empresa', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (existing["id"],),
                )
                return existing["id"]
            document_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO company_documents(id, company_id, category, document_type)
                   VALUES (?, ?, 'Adicionado pela empresa', ?)""",
                (document_id, company_id, document_type),
            )
            return document_id

    def save_company_documents(self, company_id, rows):
        allowed_applicable = {"Sim", "Não", "Não informado"}
        allowed_status = {"Válido", "Vencido", "Em renovação", "Não possui", "Não se aplica", "Não informado"}
        with self.connect() as conn:
            for row in rows:
                document_type = str(row.get("document_type") or "").strip()
                if not document_type:
                    continue
                applicable = str(row.get("applicable") or "Não informado")
                status = str(row.get("status") or "Não informado")
                if applicable not in allowed_applicable:
                    applicable = "Não informado"
                if status not in allowed_status:
                    status = "Não informado"
                conn.execute(
                    """UPDATE company_documents SET applicable=?, status=?, expiry_date=?,
                       issuer=?, notes=?, updated_at=CURRENT_TIMESTAMP
                       WHERE company_id=? AND document_type=?""",
                    (applicable, status, row.get("expiry_date") or None,
                     str(row.get("issuer") or "").strip(), str(row.get("notes") or "").strip(),
                     company_id, document_type),
                )

    def save_edital_analysis(self, company_id, opportunity_id, filename, score, pages_count, findings):
        analysis_id = str(uuid.uuid4())
        with self.connect() as conn:
            if opportunity_id and not conn.execute(
                "SELECT 1 FROM opportunities WHERE id=? AND company_id=?", (opportunity_id, company_id)
            ).fetchone():
                raise ValueError("Oportunidade inválida para esta empresa.")
            conn.execute("""
                INSERT INTO edital_analyses(id, company_id, opportunity_id, filename,
                    compatibility_score, pages_count) VALUES (?, ?, ?, ?, ?, ?)
            """, (analysis_id, company_id, opportunity_id, filename, int(score), int(pages_count)))
            conn.executemany("""
                INSERT INTO edital_findings(id, analysis_id, company_id, severity, category,
                    title, evidence, page_number, recommended_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(
                str(uuid.uuid4()), analysis_id, company_id, finding["severity"], finding["category"],
                finding["title"], finding.get("evidence", ""), finding.get("page_number"),
                finding.get("recommended_action", ""),
            ) for finding in findings])
        return analysis_id

    def get_analysis(self, company_id, analysis_id):
        with self.connect() as conn:
            analysis = conn.execute(
                "SELECT * FROM edital_analyses WHERE id=? AND company_id=?", (analysis_id, company_id)
            ).fetchone()
            findings = conn.execute("""
                SELECT * FROM edital_findings WHERE analysis_id=? AND company_id=?
                ORDER BY CASE severity WHEN 'Vermelho' THEN 1 WHEN 'Amarelo' THEN 2 ELSE 3 END,
                         page_number, created_at
            """, (analysis_id, company_id)).fetchall()
        return (dict(analysis), [dict(row) for row in findings]) if analysis else (None, [])

    def list_analyses(self, company_id, opportunity_id=None):
        sql = """
            SELECT a.*, o.agency, o.object FROM edital_analyses a
            LEFT JOIN opportunities o ON o.id=a.opportunity_id AND o.company_id=a.company_id
            WHERE a.company_id=?
        """
        params = [company_id]
        if opportunity_id:
            sql += " AND a.opportunity_id=?"
            params.append(opportunity_id)
        sql += " ORDER BY a.created_at DESC"
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def add_analysis_actions_to_checklist(self, company_id, analysis_id):
        analysis, findings = self.get_analysis(company_id, analysis_id)
        if not analysis or not analysis.get("opportunity_id"):
            return 0
        opportunity_id = analysis["opportunity_id"]
        self.ensure_opportunity_workspace(company_id, opportunity_id)
        added = 0
        for finding in findings:
            if finding["severity"] not in {"Vermelho", "Amarelo"}:
                continue
            action = finding["recommended_action"] or f'Conferir: {finding["title"]}'
            with self.connect() as conn:
                exists = conn.execute("""
                    SELECT 1 FROM opportunity_checklist
                    WHERE company_id=? AND opportunity_id=? AND title=?
                """, (company_id, opportunity_id, action)).fetchone()
            if not exists:
                self.add_checklist_item(company_id, opportunity_id, action)
                added += 1
        return added

    def add_calendar_event(self, company_id, title, event_at, event_type="Tarefa",
                           opportunity_id=None, source="Manual", evidence=""):
        if not str(title or "").strip() or not event_at:
            raise ValueError("Informe título e data do evento.")
        with self.connect() as conn:
            if opportunity_id and not conn.execute(
                "SELECT 1 FROM opportunities WHERE id=? AND company_id=?", (opportunity_id, company_id)
            ).fetchone():
                raise ValueError("Oportunidade inválida.")
            conn.execute("""
                INSERT INTO calendar_events(id, company_id, opportunity_id, title, event_type,
                    event_at, source, evidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), company_id, opportunity_id, title.strip(), event_type,
                    event_at, source, evidence))

    def list_agenda(self, company_id, start_date, end_date):
        params = [company_id, start_date, end_date]
        with self.connect() as conn:
            manual = [dict(row) for row in conn.execute("""
                SELECT e.id, e.opportunity_id, e.title, e.event_type, e.event_at,
                    e.status, e.source, o.agency, o.object
                FROM calendar_events e LEFT JOIN opportunities o
                  ON o.id=e.opportunity_id AND o.company_id=e.company_id
                WHERE e.company_id=? AND date(e.event_at) BETWEEN date(?) AND date(?)
            """, params).fetchall()]
            openings = [dict(row) for row in conn.execute("""
                SELECT 'opening:'||id AS id, id AS opportunity_id,
                    'Abertura da sessão' AS title, 'Sessão' AS event_type,
                    opening_at AS event_at, 'Pendente' AS status, 'PNCP' AS source,
                    agency, object FROM opportunities
                WHERE company_id=? AND date(opening_at) BETWEEN date(?) AND date(?)
            """, params).fetchall()]
            closings = [dict(row) for row in conn.execute("""
                SELECT 'closing:'||id AS id, id AS opportunity_id,
                    'Encerramento das propostas' AS title, 'Proposta' AS event_type,
                    closing_at AS event_at, 'Pendente' AS status, 'PNCP' AS source,
                    agency, object FROM opportunities
                WHERE company_id=? AND date(closing_at) BETWEEN date(?) AND date(?)
            """, params).fetchall()]
            deadlines = [dict(row) for row in conn.execute("""
                SELECT 'deadline:'||o.id AS id, o.id AS opportunity_id,
                    COALESCE(NULLIF(d.next_action,''),'Prazo interno') AS title,
                    'Prazo interno' AS event_type, d.deadline AS event_at,
                    'Pendente' AS status, 'Jornada' AS source, o.agency, o.object
                FROM opportunity_details d JOIN opportunities o ON o.id=d.opportunity_id
                WHERE d.company_id=? AND date(d.deadline) BETWEEN date(?) AND date(?)
            """, params).fetchall()]
            tasks = [dict(row) for row in conn.execute("""
                SELECT 'task:'||t.id AS id, t.opportunity_id, t.title,
                    'Tarefa' AS event_type, t.due_date AS event_at,
                    CASE t.completed WHEN 1 THEN 'Concluído' ELSE 'Pendente' END AS status,
                    'Jornada' AS source, o.agency, o.object
                FROM opportunity_tasks t JOIN opportunities o ON o.id=t.opportunity_id
                WHERE t.company_id=? AND date(t.due_date) BETWEEN date(?) AND date(?)
            """, params).fetchall()]
            documents = [dict(row) for row in conn.execute("""
                SELECT 'doc:'||d.id AS id, d.opportunity_id,
                    'Vencimento: '||d.name AS title, 'Documento' AS event_type,
                    d.expiry_date AS event_at, d.status, 'Documentos' AS source,
                    o.agency, o.object
                FROM opportunity_documents d JOIN opportunities o ON o.id=d.opportunity_id
                WHERE d.company_id=? AND date(d.expiry_date) BETWEEN date(?) AND date(?)
            """, params).fetchall()]
        return sorted(manual + openings + closings + deadlines + tasks + documents,
                      key=lambda item: str(item.get("event_at") or ""))

    def save_price_references(self, company_id, query, references):
        with self.connect() as conn:
            for ref in references:
                # A pesquisa nasce a partir do catálogo do Radar. O id desse catálogo
                # não pertence à tabela opportunities e, portanto, não pode ser usado
                # como chave estrangeira da Jornada. Mantemos o vínculo somente quando
                # o identificador realmente pertence a uma oportunidade da empresa.
                opportunity_id = ref.get("opportunity_id")
                if opportunity_id and not conn.execute(
                    "SELECT 1 FROM opportunities WHERE id=? AND company_id=?",
                    (opportunity_id, company_id),
                ).fetchone():
                    opportunity_id = None
                duplicate = conn.execute("""
                    SELECT 1 FROM price_references
                    WHERE company_id=? AND catalog_code=? AND purchase_id=?
                      AND item_number=? AND homologated_unit_value=?
                    LIMIT 1
                """, (
                    company_id, str(ref.get("catalog_code", "")),
                    str(ref.get("purchase_id", "")), str(ref.get("item_number", "")),
                    ref.get("homologated_unit_value"),
                )).fetchone()
                if duplicate:
                    continue
                conn.execute("""
                    INSERT INTO price_references(id, company_id, opportunity_id, query,
                        description, agency, city, state, quantity, unit,
                        estimated_unit_value, homologated_unit_value, supplier, brand,
                        source_url, published_at, catalog_code, purchase_id, item_number,
                        source_type, brand_normalized, supplier_tax_id, procurement_form,
                        evidence_excerpt, page_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), company_id, opportunity_id, query.strip().lower(),
                        ref.get("description", ""), ref.get("agency", ""), ref.get("city", ""),
                        ref.get("state", ""), ref.get("quantity"), ref.get("unit", ""),
                        ref.get("estimated_unit_value"), ref.get("homologated_unit_value"),
                        ref.get("supplier", ""), ref.get("brand", ""), ref.get("source_url", ""),
                        ref.get("published_at"), ref.get("catalog_code", ""),
                        ref.get("purchase_id", ""), ref.get("item_number", ""),
                        ref.get("source_type", ""), ref.get("brand_normalized", ""),
                        ref.get("supplier_tax_id", ""), ref.get("procurement_form", ""),
                        ref.get("evidence", ""), ref.get("page_number")))

    def list_price_references(self, company_id, query="", limit=5000, start_date=None,
                              actual_only=False):
        sql = "SELECT * FROM price_references WHERE company_id=?"
        params = [company_id]
        if query.strip():
            sql += " AND (lower(description) LIKE ? OR lower(query) LIKE ?)"
            term = f"%{query.strip().lower()}%"
            params.extend([term, term])
        if start_date:
            sql += " AND date(published_at) >= date(?)"
            params.append(str(start_date)[:10])
        if actual_only:
            sql += " AND homologated_unit_value IS NOT NULL AND trim(supplier) <> ''"
        sql += " ORDER BY published_at DESC, created_at DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def export_pipeline_bundle(self, company_id):
        with self.connect() as conn:
            tables = {}
            tables["Pipeline"] = [dict(row) for row in conn.execute("""
                SELECT o.*, d.decision, d.next_action, d.deadline, d.responsible,
                    d.our_bid, d.winning_bid, d.contract_value, d.winner, d.loss_reason
                FROM opportunities o LEFT JOIN opportunity_details d
                  ON d.opportunity_id=o.id AND d.company_id=o.company_id
                WHERE o.company_id=? ORDER BY o.updated_at DESC
            """, (company_id,)).fetchall()]
            for label, table in (("Tarefas", "opportunity_tasks"),
                                 ("Documentos", "opportunity_documents"),
                                 ("Precos", "opportunity_quote_items")):
                tables[label] = [dict(row) for row in conn.execute(
                    f"SELECT * FROM {table} WHERE company_id=? ORDER BY created_at DESC", (company_id,)
                ).fetchall()]
        return tables


    # Catálogo público compartilhado entre todas as empresas.
    def upsert_global_catalog_page(self, items):
        saved = 0
        with self.connect() as conn:
            for item in items:
                values = self._item_values(item)
                control = values[0]
                if not control:
                    continue
                conn.execute("""
                    INSERT INTO global_pncp_catalog(
                        id, pncp_control_number, agency, city, state, modality, published_at, opening_at,
                        closing_at, object, estimated_value, source_url, srp, source_name, source_channel
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(pncp_control_number) DO UPDATE SET
                        agency=excluded.agency, city=excluded.city, state=excluded.state,
                        modality=excluded.modality, published_at=excluded.published_at,
                        opening_at=excluded.opening_at, closing_at=excluded.closing_at,
                        object=excluded.object, srp=excluded.srp, estimated_value=excluded.estimated_value,
                        source_url=CASE WHEN excluded.source_url<>'' THEN excluded.source_url ELSE global_pncp_catalog.source_url END,
                        source_name=excluded.source_name, source_channel=excluded.source_channel,
                        last_seen_at=CURRENT_TIMESTAMP
                """, (str(uuid.uuid4()), *values))
                saved += 1
        return saved


    def global_catalog_group_counts(self, column, closing_from=None):
        """Contagens leves para Estado/Cidade/Modalidade sem carregar o catálogo inteiro."""
        allowed = {"state", "city", "modality"}
        if column not in allowed:
            raise ValueError("Agrupamento de catálogo inválido.")
        sql = f"SELECT {column} AS label, COUNT(*) AS total FROM global_pncp_catalog WHERE trim({column})<>''"
        params = []
        if closing_from:
            sql += " AND (closing_at IS NULL OR date(closing_at)>=date(?))"
            params.append(str(closing_from)[:10])
        sql += f" GROUP BY {column} ORDER BY COUNT(*) DESC, {column} ASC"
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def global_catalog_quality_stats(self):
        """Diagnóstico simples para a Sala de Controle explicar o número exibido ao cliente."""
        with self.connect() as conn:
            row = conn.execute("""
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN closing_at IS NULL THEN 1 ELSE 0 END) AS without_deadline,
                       SUM(CASE WHEN closing_at IS NOT NULL AND date(closing_at) >= CURRENT_DATE THEN 1 ELSE 0 END) AS future_deadline,
                       SUM(CASE WHEN closing_at IS NOT NULL AND date(closing_at) < CURRENT_DATE THEN 1 ELSE 0 END) AS expired_deadline,
                       SUM(CASE WHEN trim(source_url)='' THEN 1 ELSE 0 END) AS without_portal_url,
                       SUM(CASE WHEN estimated_value IS NULL OR estimated_value<=0 THEN 1 ELSE 0 END) AS without_value
                FROM global_pncp_catalog
            """).fetchone()
        return {
            "total": int(row["total"] or 0),
            "without_deadline": int(row["without_deadline"] or 0),
            "future_deadline": int(row["future_deadline"] or 0),
            "expired_deadline": int(row["expired_deadline"] or 0),
            "without_portal_url": int(row["without_portal_url"] or 0),
            "without_value": int(row["without_value"] or 0),
        }

    def global_catalog_stats(self):
        with self.connect() as conn:
            row = conn.execute("""
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN date(first_seen_at)=CURRENT_DATE THEN 1 ELSE 0 END) AS new_today,
                       SUM(CASE WHEN date(last_seen_at)=CURRENT_DATE THEN 1 ELSE 0 END) AS seen_today,
                       SUM(CASE WHEN closing_at IS NOT NULL AND datetime(closing_at) >= CURRENT_TIMESTAMP THEN 1 ELSE 0 END) AS open_now
                FROM global_pncp_catalog
            """).fetchone()
        return {
            "total": int(row["total"] or 0),
            "new_today": int(row["new_today"] or 0),
            "seen_today": int(row["seen_today"] or 0),
            "open_now": int(row["open_now"] or 0),
        }

    def global_catalog_count(self):
        with self.connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM global_pncp_catalog").fetchone()[0])

    def global_catalog_modality_counts(self):
        """Resumo por modalidade, somando aliases históricos do PNCP.

        O portal pode devolver nomes diferentes para a mesma modalidade (por exemplo
        ``Dispensa`` e ``Dispensa de licitação``). A interface usa o nome canônico e
        soma todos os aliases para não esconder registros já existentes no catálogo.
        """
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT modality, COUNT(*) AS total FROM global_pncp_catalog "
                "WHERE trim(modality)<>'' GROUP BY modality ORDER BY total DESC"
            ).fetchall()
        counts = {}
        for row in rows:
            name = canonical_modality_name(row["modality"])
            if not name:
                continue
            counts[name] = counts.get(name, 0) + int(row["total"] or 0)
        return counts


    def global_catalog_modality_breakdown(self):
        """Distribuição completa do catálogo por modalidade, incluindo registros sem modalidade."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT modality, COUNT(*) AS total FROM global_pncp_catalog GROUP BY modality ORDER BY total DESC"
            ).fetchall()
        counts = {}
        for row in rows:
            raw = str(row["modality"] or "").strip()
            name = canonical_modality_name(raw) if raw else "Não informada"
            counts[name] = counts.get(name, 0) + int(row["total"] or 0)
        return counts

    def global_catalog_filters(self):
        with self.connect() as conn:
            states = [r[0] for r in conn.execute(
                "SELECT DISTINCT state FROM global_pncp_catalog WHERE state<>'' ORDER BY state"
            )]
            modalities = [r[0] for r in conn.execute(
                "SELECT DISTINCT modality FROM global_pncp_catalog WHERE modality<>'' ORDER BY modality"
            )]
        return states, modalities

    def list_global_catalog(self, search="", states=None, cities=None, modalities=None, srp=None, minimum=None,
                            maximum=None, closing_from=None, closing_to=None, limit=5000,
                            order_by="recent", portal_terms=None): 
        sql = "SELECT * FROM global_pncp_catalog WHERE 1=1"
        params = []
        portal_terms = [str(term or "").strip().lower() for term in (portal_terms or []) if str(term or "").strip()]
        if portal_terms:
            portal_clauses = []
            for term in portal_terms:
                portal_clauses.append("(lower(source_name) LIKE ? OR lower(source_url) LIKE ?)")
                like = f"%{term}%"
                params.extend([like, like])
            sql += " AND (" + " OR ".join(portal_clauses) + ")"
        if search.strip():
            # A caixa de busca aceita várias intenções separadas por vírgula/; ou quebra de linha.
            # Ex.: "medicamentos, uniformes, luvas" significa medicamentos OU uniformes OU luvas.
            # Dentro de uma intenção com mais de uma palavra, todas precisam aparecer em algum
            # campo pesquisável. Isso evita a busca impossível da versão anterior, que exigia
            # simultaneamente todas as palavras de categorias diferentes.
            groups = [
                group.strip() for group in re.split(r"[,;\n]+", search) if group.strip()
            ]
            if not groups:
                groups = [search.strip()]
            group_sql = []
            for group in groups[:20]:
                words = [w.lower() for w in group.split() if w.strip()]
                if not words:
                    continue
                word_sql = []
                for word in words[:10]:
                    # No Essential a palavra-chave representa aquilo que o usuário quer comprar/vender.
                    # Por isso pesquisamos o OBJETO da contratação; órgão e município já possuem
                    # filtros próprios e não devem gerar falsos positivos na busca comercial.
                    word_sql.append("search_fold(object) LIKE ?")
                    term = f"%{self._search_fold(word)}%"
                    params.append(term)
                group_sql.append("(" + " AND ".join(word_sql) + ")")
            if group_sql:
                sql += " AND (" + " OR ".join(group_sql) + ")"
        states = [s for s in (states or []) if s]
        if states:
            sql += f" AND state IN ({','.join('?' for _ in states)})"
            params.extend(states)
        cities = [str(city).strip() for city in (cities or []) if str(city).strip()]
        if cities:
            sql += " AND (" + " OR ".join("lower(city)=lower(?)" for _ in cities) + ")"
            params.extend(cities)
        modalities = [canonical_modality_name(m) for m in (modalities or []) if m]
        if modalities:
            # O PNCP pode armazenar a mesma modalidade com hífen, por exemplo
            # "Pregão - Eletrônico". Normalizamos a comparação no SQL para que o
            # filtro funcione também em catálogos coletados por versões anteriores.
            normalized_modalities = [m.lower().replace(" - ", " ").replace("-", " ") for m in modalities]
            normalized_expr = "lower(replace(replace(modality, ' - ', ' '), '-', ' '))"
            sql += f" AND {normalized_expr} IN ({','.join('?' for _ in normalized_modalities)})"
            params.extend(normalized_modalities)
        if srp is not None:
            sql += " AND srp=?"; params.append(int(bool(srp)))
        if minimum is not None:
            sql += " AND estimated_value>=?"; params.append(minimum)
        if maximum is not None:
            sql += " AND estimated_value<=?"; params.append(maximum)
        if closing_from:
            sql += " AND (closing_at IS NULL OR date(closing_at)>=date(?))"; params.append(str(closing_from)[:10])
        if closing_to:
            sql += " AND closing_at IS NOT NULL AND date(closing_at)<=date(?)"; params.append(str(closing_to)[:10])
        orders = {
            "recent": "published_at DESC, last_seen_at DESC",
            "certame": "CASE WHEN closing_at IS NULL THEN 1 ELSE 0 END, closing_at ASC",
            "value_desc": "estimated_value DESC",
            "value_asc": "estimated_value ASC",
        }
        sql += " ORDER BY " + orders.get(order_by, orders["recent"]) + " LIMIT ?"
        params.append(int(limit))
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def add_global_catalog_to_pipeline(self, company_id, catalog_ids):
        if not catalog_ids:
            return 0
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM global_pncp_catalog WHERE id IN ({','.join('?' for _ in catalog_ids)})",
                catalog_ids,
            ).fetchall()
        for row in rows:
            self.upsert_opportunity(company_id, {
                "numeroControlePNCP": row["pncp_control_number"], "orgao": row["agency"],
                "municipio": row["city"], "uf": row["state"], "modalidade": row["modality"],
                "publicacao": row["published_at"], "abertura": row["opening_at"],
                "encerramento": row["closing_at"], "srp": bool(row["srp"]),
                "objeto": row["object"], "valor": row["estimated_value"], "link": row["source_url"],
                "source_name": row["source_name"], "source_channel": row["source_channel"],
            })
        return len(rows)

    def add_global_catalog_item_to_pipeline(self, company_id, catalog_id):
        """Leva uma oportunidade do catálogo para a Jornada e devolve o id privado da empresa."""
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM global_pncp_catalog WHERE id=?", (catalog_id,)).fetchone()
        if not row:
            raise ValueError("Oportunidade não encontrada no catálogo.")
        self.upsert_opportunity(company_id, {
            "numeroControlePNCP": row["pncp_control_number"], "orgao": row["agency"],
            "municipio": row["city"], "uf": row["state"], "modalidade": row["modality"],
            "publicacao": row["published_at"], "abertura": row["opening_at"],
            "encerramento": row["closing_at"], "srp": bool(row["srp"]),
            "objeto": row["object"], "valor": row["estimated_value"], "link": row["source_url"],
            "source_name": row["source_name"], "source_channel": row["source_channel"],
        })
        with self.connect() as conn:
            opportunity = conn.execute(
                "SELECT id FROM opportunities WHERE company_id=? AND pncp_control_number=? LIMIT 1",
                (company_id, row["pncp_control_number"]),
            ).fetchone()
        if not opportunity:
            raise ValueError("Não foi possível abrir esta oportunidade na Jornada.")
        self.ensure_opportunity_workspace(company_id, opportunity["id"])
        return opportunity["id"]

    def get_global_checkpoint(self, modality_code, state, publication_day, source="PNCP_INCREMENTAL",
                              period_start="", period_end=""):
        with self.connect() as conn:
            row = conn.execute("""
                SELECT * FROM global_sync_checkpoints WHERE source=? AND modality_code=? AND state=?
                AND period_start=? AND period_end=? AND publication_day=?
            """, (source, modality_code, state or "", period_start, period_end, publication_day)).fetchone()
        return dict(row) if row else None

    def save_global_checkpoint(self, modality_code, state, publication_day, next_page, completed,
                               items_saved, last_error, source="PNCP_INCREMENTAL", period_start="", period_end=""):
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO global_sync_checkpoints(source, modality_code, state, period_start, period_end,
                    publication_day, next_page, completed, items_saved, last_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, modality_code, state, period_start, period_end, publication_day) DO UPDATE SET
                    next_page=excluded.next_page, completed=excluded.completed, items_saved=excluded.items_saved,
                    last_error=excluded.last_error, updated_at=CURRENT_TIMESTAMP
            """, (source, modality_code, state or "", period_start, period_end, publication_day,
                    next_page, int(bool(completed)), items_saved, last_error or ""))

    def latest_incomplete_global_sync_period(self, source="PNCP_INCREMENTAL"):
        source = str(source or "").strip()
        if not source:
            raise ValueError("Informe a fonte da sincronização.")

        with self.connect() as conn:
            row = conn.execute("""
                SELECT period_start, period_end, publication_day, updated_at
                FROM global_sync_checkpoints
                WHERE source=? AND completed=0
                ORDER BY updated_at DESC, period_end DESC, period_start DESC
                LIMIT 1
            """, (source,)).fetchone()

        return dict(row) if row else None
    def mark_stale_sync_runs(self, cutoff):
        cutoff_text = str(cutoff or "").strip()
        try:
            cutoff_dt = datetime.fromisoformat(cutoff_text)
        except (TypeError, ValueError) as error:
            raise ValueError("Informe um cutoff de data/hora valido.") from error

        cutoff_text = cutoff_dt.strftime("%Y-%m-%d %H:%M:%S")
        message = "Execucao interrompida antes da conclusao; encerrada automaticamente."

        with self.connect() as conn:
            row = conn.execute(
                """SELECT COUNT(*) AS total
                   FROM sync_runs
                   WHERE status='running' AND started_at < ?""",
                (cutoff_text,),
            ).fetchone()
            total = int(row["total"] or 0)

            if total:
                conn.execute(
                    """UPDATE sync_runs
                       SET finished_at=CURRENT_TIMESTAMP,
                           status='error',
                           errors=CASE
                               WHEN COALESCE(errors, '')='' THEN ?
                               ELSE errors || ' | ' || ?
                           END
                       WHERE status='running' AND started_at < ?""",
                    (message, message, cutoff_text),
                )

        return total

    @contextmanager
    def sync_run_scope(self, source="PNCP"):
        run_id = self.start_sync_run(source)
        try:
            yield run_id
        except Exception as error:
            try:
                with self.connect() as conn:
                    conn.execute(
                        """UPDATE sync_runs
                           SET finished_at=CURRENT_TIMESTAMP,
                               status='error',
                               errors=?
                           WHERE id=? AND status='running'""",
                        (f"{type(error).__name__}: {error}", run_id),
                    )
            except Exception:
                # O erro original da sincronizacao tem prioridade.
                # Uma falha ao registrar o status sera tratada posteriormente
                # pela rotina de limpeza de execucoes interrompidas.
                pass
            raise

    def start_sync_run(self, source="PNCP"):
        run_id = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute("INSERT INTO sync_runs(id, source) VALUES (?, ?)", (run_id, source))
        return run_id

    def finish_sync_run(self, run_id, status, pages=0, records=0, errors=""):
        with self.connect() as conn:
            conn.execute("""UPDATE sync_runs SET finished_at=CURRENT_TIMESTAMP, status=?, pages=?, records=?, errors=?
                            WHERE id=?""", (status, pages, records, errors or "", run_id))

    def list_sync_runs(self, limit=20):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM sync_runs ORDER BY started_at DESC LIMIT ?", (int(limit),)
            ).fetchall()]

    def last_successful_sync_run(self, sources=None):
        """Retorna a sincronização concluída mais recente entre as fontes informadas."""
        source_list = [str(value) for value in (sources or []) if str(value).strip()]
        sql = "SELECT * FROM sync_runs WHERE status='success'"
        params = []
        if source_list:
            sql += f" AND source IN ({','.join('?' for _ in source_list)})"
            params.extend(source_list)
        sql += " ORDER BY COALESCE(finished_at, started_at) DESC LIMIT 1"
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def last_catalog_update(self):
        with self.connect() as conn:
            row = conn.execute("SELECT MAX(last_seen_at) FROM global_pncp_catalog").fetchone()
        return row[0] if row and row[0] else None

    def get_access_request(self, request_id):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM access_requests WHERE id=?", (request_id,)).fetchone()
        return dict(row) if row else None

    def record_email_event(self, event_type, recipient, status, details=""):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO email_events(id, event_type, recipient, status, details) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), event_type, str(recipient or '').strip().lower(), status, str(details or '')[:1000]),
            )

    def list_email_events(self, limit=50):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM email_events ORDER BY created_at DESC LIMIT ?", (int(limit),)
            ).fetchall()]

    def crm_accounts(self):
        with self.connect() as conn:
            active = [dict(row) for row in conn.execute("""
                SELECT c.id AS company_id, c.name AS company_name, c.plan, c.subscription_status,
                       c.trial_started_at, c.trial_ends_at, c.subscription_ends_at, c.created_at,
                       u.name, u.email, u.role, u.last_login_at
                FROM companies c JOIN users u ON u.company_id=c.id
                WHERE u.role IN ('owner','admin')
                ORDER BY c.created_at DESC
            """).fetchall()]
            requests = [dict(row) for row in conn.execute("""
                SELECT id, company_name, name, email, whatsapp, segment, job_title, cnpj, how_heard,
                       status, approved_trial_days, created_at, contacted_at, invited_at, activated_at
                FROM access_requests ORDER BY created_at DESC
            """).fetchall()]
        return active, requests

    def system_stats(self):
        with self.connect() as conn:
            return {
                "companies": int(conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]),
                "users": int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]),
                "pending_requests": int(conn.execute("SELECT COUNT(*) FROM access_requests WHERE status IN ('pending','contacted')").fetchone()[0]),
                "active_trials": int(conn.execute("SELECT COUNT(*) FROM companies WHERE subscription_status='trialing' AND trial_ends_at >= CURRENT_TIMESTAMP").fetchone()[0]),
            }






