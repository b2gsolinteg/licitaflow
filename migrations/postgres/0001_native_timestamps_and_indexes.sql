DO $$
DECLARE
    item RECORD;
    current_type TEXT;
    current_default TEXT;
BEGIN
    -- Converte somente colunas existentes que ainda são TEXT. Valores inválidos
    -- fazem a migration falhar de forma explícita, evitando corrupção silenciosa.
    FOR item IN
        SELECT * FROM (VALUES
            ('companies','trial_started_at',TRUE),
            ('companies','trial_ends_at',TRUE),
            ('companies','subscription_ends_at',TRUE),
            ('companies','created_at',FALSE),
            ('users','terms_accepted_at',TRUE),
            ('users','privacy_accepted_at',TRUE),
            ('users','created_at',FALSE),
            ('users','last_login_at',TRUE),
            ('access_requests','created_at',FALSE),
            ('access_requests','updated_at',FALSE),
            ('access_requests','invitation_expires_at',TRUE),
            ('access_requests','activated_at',TRUE),
            ('password_reset_requests','requested_at',FALSE),
            ('password_reset_requests','expires_at',TRUE),
            ('password_reset_requests','code_generated_at',TRUE),
            ('password_reset_requests','used_at',TRUE),
            ('security_events','created_at',FALSE),
            ('security_rate_limits','window_started_at',FALSE),
            ('security_rate_limits','blocked_until',TRUE),
            ('security_rate_limits','updated_at',FALSE),
            ('security_sessions','issued_at',FALSE),
            ('security_sessions','last_seen_at',FALSE),
            ('security_sessions','expires_at',FALSE),
            ('security_sessions','revoked_at',TRUE),
            ('security_backup_audit','created_at',FALSE),
            ('usage_settings','updated_at',FALSE),
            ('usage_company_limits','updated_at',FALSE),
            ('usage_events','created_at',FALSE),
            ('commercial_subscriptions','trial_started_at',TRUE),
            ('commercial_subscriptions','trial_ends_at',TRUE),
            ('commercial_subscriptions','current_period_start',TRUE),
            ('commercial_subscriptions','current_period_end',TRUE),
            ('commercial_subscriptions','updated_at',FALSE),
            ('billing_checkouts','created_at',FALSE),
            ('billing_checkouts','updated_at',FALSE),
            ('billing_events','created_at',FALSE),
            ('assisted_requests','created_at',FALSE),
            ('assisted_requests','updated_at',FALSE),
            ('assisted_request_messages','created_at',FALSE),
            ('assisted_request_messages','read_at',TRUE),
            ('opportunities','published_at',TRUE),
            ('opportunities','opening_at',TRUE),
            ('opportunities','closing_at',TRUE),
            ('opportunities','created_at',FALSE),
            ('opportunities','updated_at',FALSE),
            ('pncp_catalog','published_at',TRUE),
            ('pncp_catalog','opening_at',TRUE),
            ('pncp_catalog','closing_at',TRUE),
            ('pncp_catalog','first_seen_at',FALSE),
            ('pncp_catalog','last_seen_at',FALSE),
            ('global_pncp_catalog','published_at',TRUE),
            ('global_pncp_catalog','opening_at',TRUE),
            ('global_pncp_catalog','closing_at',TRUE),
            ('global_pncp_catalog','first_seen_at',FALSE),
            ('global_pncp_catalog','last_seen_at',FALSE)
        ) AS values_list(table_name, column_name, nullable_column)
    LOOP
        SELECT data_type, column_default
        INTO current_type, current_default
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = item.table_name
          AND column_name = item.column_name;

        IF current_type = 'text' THEN
            IF current_default IS NOT NULL THEN
                EXECUTE format(
                    'ALTER TABLE %I ALTER COLUMN %I DROP DEFAULT',
                    item.table_name,
                    item.column_name
                );
            END IF;

            IF item.nullable_column THEN
                EXECUTE format(
                    'ALTER TABLE %I ALTER COLUMN %I TYPE TIMESTAMPTZ USING NULLIF(BTRIM(%I), '''')::timestamptz',
                    item.table_name,
                    item.column_name,
                    item.column_name
                );
            ELSE
                EXECUTE format(
                    'ALTER TABLE %I ALTER COLUMN %I TYPE TIMESTAMPTZ USING %I::timestamptz',
                    item.table_name,
                    item.column_name,
                    item.column_name
                );
            END IF;

            IF current_default IS NOT NULL THEN
                EXECUTE format(
                    'ALTER TABLE %I ALTER COLUMN %I SET DEFAULT CURRENT_TIMESTAMP',
                    item.table_name,
                    item.column_name
                );
            END IF;
        END IF;
    END LOOP;

    IF to_regclass('usage_events') IS NOT NULL THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_usage_events_company_event_created ON usage_events(company_id,event_type,created_at DESC)';
    END IF;
    IF to_regclass('security_sessions') IS NOT NULL THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_security_sessions_active ON security_sessions(user_id,expires_at DESC) WHERE revoked_at IS NULL';
    END IF;
    IF to_regclass('security_events') IS NOT NULL THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_security_events_failed_created ON security_events(created_at DESC) WHERE success=0';
    END IF;
    IF to_regclass('access_requests') IS NOT NULL THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_access_requests_email_status ON access_requests(email,status)';
    END IF;
    IF to_regclass('password_reset_requests') IS NOT NULL THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_password_reset_user_status ON password_reset_requests(user_id,status,requested_at DESC)';
    END IF;
    IF to_regclass('assisted_request_messages') IS NOT NULL THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_support_messages_request_created ON assisted_request_messages(request_id,created_at)';
    END IF;
    IF to_regclass('billing_checkouts') IS NOT NULL THEN
        EXECUTE format(
            'CREATE UNIQUE INDEX IF NOT EXISTS ux_billing_provider_id ON billing_checkouts(provider_id) WHERE provider_id <> %L',
            ''
        );
        EXECUTE 'CREATE INDEX IF NOT EXISTS ix_billing_local_status_created ON billing_checkouts(local_status,created_at DESC)';
    END IF;
END
$$;
