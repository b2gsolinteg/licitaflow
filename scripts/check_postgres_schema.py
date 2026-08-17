from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db_migrations import MigrationError, migration_status
from src.db_runtime import connect_runtime, postgres_schema, using_postgres


EXPECTED_TIMESTAMPS = {
    ("security_events", "created_at"),
    ("security_rate_limits", "window_started_at"),
    ("security_rate_limits", "blocked_until"),
    ("security_rate_limits", "updated_at"),
    ("security_sessions", "issued_at"),
    ("security_sessions", "last_seen_at"),
    ("security_sessions", "expires_at"),
    ("security_sessions", "revoked_at"),
    ("usage_events", "created_at"),
    ("billing_checkouts", "created_at"),
    ("billing_checkouts", "updated_at"),
    ("company_profiles", "cnpj_card_uploaded_at"),
    ("company_document_uploads", "created_at"),
    ("opportunity_item_suppliers", "created_at"),
    ("opportunity_item_suppliers", "updated_at"),
}


def main() -> int:
    if not using_postgres():
        print("POSTGRES_SCHEMA_CHECK=SKIP backend=sqlite")
        return 0

    strict = os.getenv("LICITANEXO_SCHEMA_STRICT", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "sim",
    }

    try:
        status = migration_status(ROOT)
    except MigrationError as exc:
        print(f"POSTGRES_SCHEMA_CHECK=FAIL\n{exc}", file=sys.stderr)
        return 1

    if status.get("pending"):
        print(
            "POSTGRES_SCHEMA_CHECK=FAIL pending=" + ",".join(status["pending"]),
            file=sys.stderr,
        )
        return 1

    with connect_runtime(ROOT / "data" / "schema-check.db") as connection:
        rows = connection.execute(
            """
            SELECT table_name,column_name,data_type
            FROM information_schema.columns
            WHERE table_schema=?
            """,
            (postgres_schema(),),
        ).fetchall()

    types = {
        (str(row["table_name"]), str(row["column_name"])): str(row["data_type"])
        for row in rows
    }
    failures = []
    warnings = []
    for key in sorted(EXPECTED_TIMESTAMPS):
        data_type = types.get(key)
        if data_type is None:
            message = f"{key[0]}.{key[1]} ausente"
            (failures if strict else warnings).append(message)
        elif data_type != "timestamp with time zone":
            failures.append(f"{key[0]}.{key[1]}={data_type}")

    payload = {
        "schema": postgres_schema(),
        "strict": strict,
        "warnings": warnings,
        "failures": failures,
        "migrations": len(status.get("applied") or []),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if failures:
        print("POSTGRES_SCHEMA_CHECK=FAIL", file=sys.stderr)
        return 1
    print("POSTGRES_SCHEMA_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
