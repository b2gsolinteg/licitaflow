from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db_migrations import MigrationError, run_postgres_migrations


def main() -> int:
    try:
        result = run_postgres_migrations(ROOT)
    except MigrationError as exc:
        print(f"POSTGRES_MIGRATIONS=FAIL\n{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    if result.get("pending"):
        print("POSTGRES_MIGRATIONS=FAIL", file=sys.stderr)
        return 1
    print("POSTGRES_MIGRATIONS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
