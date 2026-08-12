"""Worker independente do Streamlit para atualizar o catálogo PNCP.

Foi desenhado para rodar em GitHub Actions (ou outro scheduler) sem depender de
sessão web. Reutiliza o mesmo checkpoint persistente do app, portanto uma execução
interrompida continua da página salva na próxima rodada.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import database_path
from src.database import Database
from src.db_runtime import using_postgres
from src.pncp import MODALITIES, PncpClient


CHECKPOINT_SOURCE = "PNCP_INCREMENTAL"
RUN_SOURCES = ["PNCP_INCREMENTAL", "PNCP_INCREMENTAL_RESUME", "PNCP_FULL", "PNCP"]
ADVISORY_LOCK_ID = 74291029


@dataclass(frozen=True)
class SyncWindow:
    mode: str
    start_date: date
    end_date: date
    period_start: str
    period_end: str
    resumed: bool


class WorkerAlreadyRunning(RuntimeError):
    pass


def _parse_datetime(value) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def resolve_sync_window(db: Database, today: date | None = None) -> SyncWindow:
    """Retoma um checkpoint pendente; caso contrário abre uma janela incremental."""
    today = today or date.today()
    pending = db.latest_incomplete_global_sync_period(CHECKPOINT_SOURCE)
    if pending:
        key = str(pending.get("publication_day") or "")
        mode = PncpClient.checkpoint_mode_from_key(key)
        parsed = PncpClient.parse_range_checkpoint_key(key)
        if mode not in {"publication", "update"} or not parsed:
            raise RuntimeError("Checkpoint incremental PNCP inválido; execução automática abortada.")
        start_date, end_date = parsed
        return SyncWindow(
            mode=mode,
            start_date=start_date,
            end_date=end_date,
            period_start=str(pending.get("period_start") or start_date.isoformat()),
            period_end=str(pending.get("period_end") or end_date.isoformat()),
            resumed=True,
        )

    anchor = db.last_successful_sync_run(RUN_SOURCES)
    if not anchor:
        if db.global_catalog_count() == 0:
            raise RuntimeError("Catálogo vazio: execute a carga completa inicial antes do worker incremental.")
        raise RuntimeError(
            "Catálogo possui dados, mas não há sincronização concluída para servir de marco incremental."
        )

    raw_anchor = anchor.get("finished_at") or anchor.get("started_at")
    anchor_dt = _parse_datetime(raw_anchor)
    start_date = anchor_dt.date() - timedelta(days=1)
    end_date = today
    return SyncWindow(
        mode="update",
        start_date=start_date,
        end_date=end_date,
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        resumed=False,
    )


def ordered_modalities(client: PncpClient):
    """Mesma prioridade da interface administrativa, com fallback local."""
    modalities = client.fetch_modalities()
    priority_codes = [8, 6, 4, 12, 9]
    by_code = {int(code): name for name, code in modalities.items()}
    local_by_code = {int(code): name for name, code in MODALITIES.items()}
    ordered = []
    used = set()
    for code in priority_codes:
        ordered.append((by_code.get(code) or local_by_code.get(code) or str(code), code))
        used.add(code)
    for name, code in modalities.items():
        code = int(code)
        if code not in used:
            ordered.append((name, code))
            used.add(code)
    return ordered


@contextmanager
def worker_lock(db: Database):
    """Evita duas instâncias do worker simultâneas no PostgreSQL."""
    if not using_postgres():
        yield
        return

    conn = db.connect()
    acquired = False
    try:
        acquired = bool(
            conn.execute("SELECT pg_try_advisory_lock(?)", (ADVISORY_LOCK_ID,)).fetchone()[0]
        )
        if not acquired:
            raise WorkerAlreadyRunning("Já existe uma atualização PNCP automática em execução.")
        yield
    finally:
        if acquired:
            try:
                conn.execute("SELECT pg_advisory_unlock(?)", (ADVISORY_LOCK_ID,))
            except Exception:
                pass
        conn.close()


def run_sync_cycle(
    db: Database,
    window: SyncWindow,
    *,
    timeout: int = 30,
    page_delay: float = 0.25,
    max_attempts: int = 4,
    max_pages_per_modality: int = 120,
):
    """Executa uma rodada limitada; checkpoint permite continuar na próxima hora."""
    client = PncpClient(
        mode=window.mode,
        timeout=timeout,
        page_delay=page_delay,
        max_attempts=max_attempts,
    )
    modalities = ordered_modalities(client)
    totals = {"pages": 0, "received": 0, "saved": 0, "errors": []}
    partial = False

    with db.sync_run_scope(CHECKPOINT_SOURCE) as run_id:
        for name, code in modalities:
            print(f"PNCP modalidade={name} code={code}", flush=True)
            stats = client.sync(
                window.start_date,
                window.end_date,
                code,
                "",
                checkpoint_getter=lambda key, c=code: db.get_global_checkpoint(
                    c,
                    "",
                    key,
                    source=CHECKPOINT_SOURCE,
                    period_start=window.period_start,
                    period_end=window.period_end,
                ),
                page_saver=db.upsert_global_catalog_page,
                checkpoint_saver=lambda key, page, completed, saved, error, c=code: db.save_global_checkpoint(
                    c,
                    "",
                    key,
                    page,
                    completed,
                    saved,
                    error,
                    source=CHECKPOINT_SOURCE,
                    period_start=window.period_start,
                    period_end=window.period_end,
                ),
                max_pages_per_run=max_pages_per_modality,
            )
            totals["pages"] += int(stats.get("pages") or 0)
            totals["received"] += int(stats.get("received") or 0)
            totals["saved"] += int(stats.get("saved") or 0)
            totals["errors"].extend(stats.get("errors") or [])

            if stats.get("partial") or stats.get("errors"):
                partial = True
                break

        status = "partial" if partial or totals["errors"] else "success"
        db.finish_sync_run(
            run_id,
            status,
            totals["pages"],
            totals["saved"],
            " | ".join(str(error) for error in totals["errors"]),
        )

    totals["status"] = status
    return totals


def main() -> int:
    db = Database(database_path(ROOT))
    timeout = max(5, int(os.getenv("PNCP_WORKER_TIMEOUT", "30")))
    max_attempts = max(1, int(os.getenv("PNCP_WORKER_MAX_ATTEMPTS", "4")))
    max_pages = max(1, int(os.getenv("PNCP_WORKER_MAX_PAGES_PER_MODALITY", "120")))
    page_delay = max(0.0, float(os.getenv("PNCP_WORKER_PAGE_DELAY", "0.25")))

    try:
        with worker_lock(db):
            window = resolve_sync_window(db)
            print(
                "PNCP_WORKER_START "
                f"mode={window.mode} start={window.start_date} end={window.end_date} "
                f"resumed={window.resumed}",
                flush=True,
            )
            result = run_sync_cycle(
                db,
                window,
                timeout=timeout,
                page_delay=page_delay,
                max_attempts=max_attempts,
                max_pages_per_modality=max_pages,
            )
            print(
                "PNCP_WORKER_END "
                f"status={result['status']} pages={result['pages']} "
                f"received={result['received']} saved={result['saved']} "
                f"errors={len(result['errors'])}",
                flush=True,
            )
            # Partial é estado esperado e retomável. O workflow termina com sucesso
            # para permitir a próxima execução agendada, que continuará do checkpoint.
            return 0
    except WorkerAlreadyRunning as error:
        print(f"PNCP_WORKER_SKIP {error}", flush=True)
        return 0
    except Exception as error:
        print(f"PNCP_WORKER_ERROR {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
