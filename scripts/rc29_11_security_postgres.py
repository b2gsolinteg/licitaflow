from __future__ import annotations

import getpass
import os

try:
    import psycopg
except ImportError as exc:
    raise RuntimeError(
        "Driver PostgreSQL ausente. Instale com: "
        r".\.venv\Scripts\python.exe -m pip install psycopg[binary]"
    ) from exc


SCHEMA = "licitanexo"


def connect():
    host = os.getenv(
        "LICITANEXO_PGHOST",
        "aws-0-sa-east-1.pooler.supabase.com",
    )
    port = int(os.getenv("LICITANEXO_PGPORT", "5432"))
    dbname = os.getenv("LICITANEXO_PGDATABASE", "postgres")
    user = os.getenv(
        "LICITANEXO_PGUSER",
        "postgres.lbpuxozymtlvoccsucrf",
    )
    password = getpass.getpass("Senha Supabase: ")

    return psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode="require",
        connect_timeout=12,
    )


def main() -> int:
    print("=" * 68)
    print("LicitaNexo - migração segura das tabelas de segurança")
    print("=" * 68)
    print("Operação: somente CREATE IF NOT EXISTS.")
    print("Nenhuma tabela existente será apagada.")
    print()

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"')
            cur.execute(f'SET search_path TO "{SCHEMA}", public')

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS security_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    subject TEXT NOT NULL DEFAULT '',
                    ip_hash TEXT NOT NULL DEFAULT '',
                    success INTEGER NOT NULL DEFAULT 0,
                    details TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_security_events_type_time
                ON security_events(event_type, created_at DESC)
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS security_rate_limits (
                    bucket TEXT PRIMARY KEY,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    window_started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    blocked_until TIMESTAMPTZ,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS security_sessions (
                    token_hash TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL DEFAULT '',
                    user_id TEXT NOT NULL DEFAULT '',
                    issued_at TIMESTAMPTZ NOT NULL,
                    last_seen_at TIMESTAMPTZ NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    revoked_at TIMESTAMPTZ
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_security_sessions_user
                ON security_sessions(user_id, revoked_at, expires_at)
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS security_backup_audit (
                    id BIGSERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    size_bytes BIGINT NOT NULL,
                    integrity_status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_name IN (
                    'security_events',
                    'security_rate_limits',
                    'security_sessions',
                    'security_backup_audit'
                  )
                ORDER BY table_name
                """,
                (SCHEMA,),
            )
            found = [row[0] for row in cur.fetchall()]

        conn.commit()

    expected = {
        "security_events",
        "security_rate_limits",
        "security_sessions",
        "security_backup_audit",
    }

    if set(found) != expected:
        print("[FAIL] Nem todas as tabelas foram encontradas.")
        print("Encontradas:", ", ".join(found) or "(nenhuma)")
        return 1

    print("[PASS] security_backup_audit")
    print("[PASS] security_events")
    print("[PASS] security_rate_limits")
    print("[PASS] security_sessions")
    print()
    print("SECURITY_POSTGRES_MIGRATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
