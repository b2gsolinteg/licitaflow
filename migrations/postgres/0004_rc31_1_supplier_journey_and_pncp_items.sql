-- RC31.1 · fornecedores permanentes, jornada e origem estruturada dos itens.
-- Migration aditiva e retrocompatível com RC31.0.

CREATE TABLE IF NOT EXISTS company_suppliers (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    cnpj TEXT NOT NULL DEFAULT '',
    contact_name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT '',
    payment_terms TEXT NOT NULL DEFAULT '',
    default_lead_time_days INTEGER,
    notes TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, name)
);
CREATE INDEX IF NOT EXISTS ix_company_suppliers_company
    ON company_suppliers(company_id, active, name);

CREATE TABLE IF NOT EXISTS opportunity_journey_steps (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    opportunity_id TEXT NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    step_key TEXT NOT NULL,
    title TEXT NOT NULL,
    is_done INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, opportunity_id, step_key)
);
CREATE INDEX IF NOT EXISTS ix_opportunity_journey_company
    ON opportunity_journey_steps(company_id, opportunity_id, sort_order);

DO $$
BEGIN
    IF to_regclass('opportunity_quote_items') IS NOT NULL THEN
        ALTER TABLE opportunity_quote_items ADD COLUMN IF NOT EXISTS unit_measure TEXT NOT NULL DEFAULT '';
        ALTER TABLE opportunity_quote_items ADD COLUMN IF NOT EXISTS source_kind TEXT NOT NULL DEFAULT 'manual';
        ALTER TABLE opportunity_quote_items ADD COLUMN IF NOT EXISTS source_reference TEXT NOT NULL DEFAULT '';
        CREATE INDEX IF NOT EXISTS ix_quote_items_source
            ON opportunity_quote_items(company_id, opportunity_id, source_reference);
    END IF;
END
$$;
