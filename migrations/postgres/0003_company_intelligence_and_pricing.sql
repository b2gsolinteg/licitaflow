-- Perfil empresarial, cofre documental e múltiplos fornecedores por item.
-- A migration é aditiva e retrocompatível com o RC30.0.

CREATE TABLE IF NOT EXISTS company_profiles (
    company_id TEXT PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
    has_technical_certificate INTEGER NOT NULL DEFAULT 0,
    has_balance_sheet INTEGER NOT NULL DEFAULT 0,
    accepts_price_registration INTEGER NOT NULL DEFAULT 1,
    activity_type TEXT NOT NULL DEFAULT 'Produtos',
    has_technical_manager INTEGER NOT NULL DEFAULT 0,
    accepts_samples INTEGER NOT NULL DEFAULT 1,
    accepts_site_visit INTEGER NOT NULL DEFAULT 1,
    service_states TEXT NOT NULL DEFAULT '',
    max_contract_value DOUBLE PRECISION,
    notes TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS legal_name TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS trade_name TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS cnpj TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS company_size TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS cnaes TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS offerings TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS interest_keywords TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS procurement_interests TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS brands TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS business_model TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS delivery_days INTEGER;
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS delivery_structure TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS technical_certificate_details TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS balance_sheet_year TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS technical_manager_details TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS desired_margin DOUBLE PRECISION NOT NULL DEFAULT 15;
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS search_keyword TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS search_nature TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS search_modalities TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS search_srp TEXT NOT NULL DEFAULT 'Todos';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS search_horizon TEXT NOT NULL DEFAULT 'Próximos 30 dias';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS search_minimum DOUBLE PRECISION;
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS search_maximum DOUBLE PRECISION;
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS search_order TEXT NOT NULL DEFAULT 'Certame mais próximo';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS excluded_keywords TEXT NOT NULL DEFAULT '';
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS profile_search_enabled INTEGER NOT NULL DEFAULT 1;
ALTER TABLE company_profiles ADD COLUMN IF NOT EXISTS cnpj_card_uploaded_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS company_documents (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    document_type TEXT NOT NULL,
    applicable TEXT NOT NULL DEFAULT 'Não informado',
    status TEXT NOT NULL DEFAULT 'Não informado',
    expiry_date TEXT,
    issuer TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, document_type)
);
CREATE INDEX IF NOT EXISTS ix_company_documents_company ON company_documents(company_id, status, document_type);

CREATE TABLE IF NOT EXISTS company_document_uploads (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT '',
    content_base64 TEXT NOT NULL,
    size_bytes BIGINT NOT NULL DEFAULT 0,
    sha256 TEXT NOT NULL,
    extracted_text TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_company_document_uploads_company
    ON company_document_uploads(company_id, document_type, created_at DESC);

DO $$
BEGIN
    IF to_regclass('opportunities') IS NOT NULL AND to_regclass('opportunity_quote_items') IS NULL THEN
        EXECUTE $sql$
            CREATE TABLE opportunity_quote_items (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                quantity DOUBLE PRECISION NOT NULL DEFAULT 1,
                unit_cost DOUBLE PRECISION NOT NULL DEFAULT 0,
                freight DOUBLE PRECISION NOT NULL DEFAULT 0,
                taxes DOUBLE PRECISION NOT NULL DEFAULT 0,
                other_costs DOUBLE PRECISION NOT NULL DEFAULT 0,
                sale_price DOUBLE PRECISION NOT NULL DEFAULT 0,
                supplier TEXT NOT NULL DEFAULT '',
                lot_number TEXT NOT NULL DEFAULT '',
                edital_price DOUBLE PRECISION NOT NULL DEFAULT 0,
                commission DOUBLE PRECISION NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        $sql$;
    END IF;
END
$$;

DO $$
BEGIN
    IF to_regclass('opportunity_quote_items') IS NOT NULL THEN
        ALTER TABLE opportunity_quote_items ADD COLUMN IF NOT EXISTS lot_number TEXT NOT NULL DEFAULT '';
        ALTER TABLE opportunity_quote_items ADD COLUMN IF NOT EXISTS edital_price DOUBLE PRECISION NOT NULL DEFAULT 0;
        ALTER TABLE opportunity_quote_items ADD COLUMN IF NOT EXISTS commission DOUBLE PRECISION NOT NULL DEFAULT 0;
    END IF;
END
$$;

DO $$
BEGIN
    IF to_regclass('opportunity_quote_items') IS NOT NULL THEN
        EXECUTE $sql$
            CREATE TABLE IF NOT EXISTS opportunity_item_suppliers (
                id TEXT PRIMARY KEY,
                quote_item_id TEXT NOT NULL REFERENCES opportunity_quote_items(id) ON DELETE CASCADE,
                opportunity_id TEXT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                supplier_name TEXT NOT NULL,
                unit_cost DOUBLE PRECISION NOT NULL DEFAULT 0,
                freight_unit DOUBLE PRECISION NOT NULL DEFAULT 0,
                taxes_unit DOUBLE PRECISION NOT NULL DEFAULT 0,
                other_unit_costs DOUBLE PRECISION NOT NULL DEFAULT 0,
                lead_time_days INTEGER,
                notes TEXT NOT NULL DEFAULT '',
                is_selected INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        $sql$;
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_item_suppliers_item ON opportunity_item_suppliers(company_id, quote_item_id, unit_cost)';
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_item_suppliers_opportunity ON opportunity_item_suppliers(company_id, opportunity_id)';
    END IF;
END
$$;
