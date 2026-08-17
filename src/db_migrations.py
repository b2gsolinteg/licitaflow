from __future__ import annotations

import hashlib
import os
from pathlib import Path

from .db_runtime import postgres_schema, using_postgres


MIGRATION_LOCK_ID = 74291031
MIGRATION_TABLE = "schema_migrations"


class MigrationError(RuntimeError):
    pass


def _migration_directory(project_root=None):
    root = Path(project_root) if project_root else Path(__file__).resolve().parents[1]
    return root / "migrations" / "postgres"


def _migration_files(project_root=None):
    directory = _migration_directory(project_root)
    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.glob("*.sql")
        if path.is_file() and not path.name.startswith("_")
    )


def _checksum(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _connect():
    try:
        import psycopg
    except ImportError as exc:
        raise MigrationError(
            "Driver PostgreSQL ausente: instale psycopg[binary]."
        ) from exc

    dsn = os.getenv("DATABASE_URL", "").strip()
    if dsn:
        return psycopg.connect(dsn, connect_timeout=12)
    return psycopg.connect(
        host=os.environ["LICITANEXO_PGHOST"],
        port=int(os.getenv("LICITANEXO_PGPORT", "5432")),
        dbname=os.getenv("LICITANEXO_PGDATABASE", "postgres"),
        user=os.environ["LICITANEXO_PGUSER"],
        password=os.environ["LICITANEXO_PGPASSWORD"],
        sslmode=os.getenv("LICITANEXO_PGSSLMODE", "require"),
        connect_timeout=12,
    )


def _prepare(connection):
    schema = postgres_schema()
    quoted = schema.replace('"', '""')
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{quoted}"')
        cursor.execute(f'SET search_path TO "{quoted}", public')
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE}(
                version TEXT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    connection.commit()


def migration_status(project_root=None):
    if not using_postgres():
        return {"backend": "sqlite", "applied": [], "pending": []}

    files = _migration_files(project_root)
    with _connect() as connection:
        _prepare(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT version, checksum, applied_at FROM {MIGRATION_TABLE} ORDER BY version"
            )
            applied_rows = cursor.fetchall()

    applied = {
        str(version): {
            "version": str(version),
            "checksum": str(checksum),
            "applied_at": applied_at,
        }
        for version, checksum, applied_at in applied_rows
    }
    pending = []
    for path in files:
        content = path.read_text(encoding="utf-8")
        checksum = _checksum(content)
        existing = applied.get(path.name)
        if existing and existing["checksum"] != checksum:
            raise MigrationError(
                f"Migration {path.name} foi alterada após aplicada. "
                "Crie uma nova migration em vez de editar o histórico."
            )
        if not existing:
            pending.append(path.name)

    return {
        "backend": "postgres",
        "applied": list(applied.values()),
        "pending": pending,
    }


def run_postgres_migrations(project_root=None):
    if not using_postgres():
        return {"backend": "sqlite", "applied_now": [], "pending": []}

    files = _migration_files(project_root)
    applied_now = []

    with _connect() as connection:
        _prepare(connection)
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_ID,))
        connection.commit()
        try:
            for path in files:
                content = path.read_text(encoding="utf-8")
                checksum = _checksum(content)
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT checksum FROM {MIGRATION_TABLE} WHERE version=%s",
                        (path.name,),
                    )
                    row = cursor.fetchone()
                if row:
                    if str(row[0]) != checksum:
                        raise MigrationError(
                            f"Migration {path.name} já aplicada possui checksum diferente."
                        )
                    continue

                try:
                    with connection.cursor() as cursor:
                        cursor.execute(content)
                        cursor.execute(
                            f"INSERT INTO {MIGRATION_TABLE}(version,checksum) VALUES (%s,%s)",
                            (path.name, checksum),
                        )
                    connection.commit()
                except Exception as exc:
                    connection.rollback()
                    raise MigrationError(
                        f"Falha ao aplicar migration {path.name}: {exc}"
                    ) from exc
                applied_now.append(path.name)
        finally:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_ID,))
                connection.commit()
            except Exception:
                connection.rollback()

    status = migration_status(project_root)
    return {
        "backend": "postgres",
        "applied_now": applied_now,
        "pending": status["pending"],
    }
