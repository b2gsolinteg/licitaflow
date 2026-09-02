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


INCREMENTAL_CHECKPOINT_SOURCE = "PNCP_INCREMENTAL"
FULL_CHECKPOINT_SOURCE = "PNCP_FULL_OPEN"
RUN_SOURCES = ["PNCP_INCREMENTAL", "PNCP_INCREMENTAL_RESUME", "PNCP_FULL", "PNCP"]
ADVISORY_LOCK_ID = 74291029


@dataclass(frozen=True)
class SyncWindow:
    mode: str
    start_date: date
    end_date: date
    period_start: str
    period_end: str
    checkpoint_source: str
    run_source: str
    resumed: bool


class WorkerAlreadyRunning(RuntimeError):
    pass


def _parse_datetime(value) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def resolve_sync_window(db: Database, today: date | None = None) -> SyncWindow:
    """Retoma um checkpoint pendente; caso contrário abre uma janela incremental."""
    today = today or date.today()

    # A reconciliação completa solicitada no painel tem prioridade. O worker
    # continua pelos checkpoints até todas as modalidades terminarem.
    full_pending = db.latest_incomplete_global_sync_period(FULL_CHECKPOINT_SOURCE)
    if full_pending:
        key = str(full_pending.get("publication_day") or "")
        mode = PncpClient.checkpoint_mode_from_key(key)
        parsed = PncpClient.parse_range_checkpoint_key(key)
        if mode != "open_proposals" or not parsed:
            raise RuntimeError("Checkpoint de reconciliação completa PNCP inválido.")
        start_date, end_date = parsed
        return SyncWindow(
            mode=mode,
            start_date=start_date,
            end_date=end_date,
            period_start=str(full_pending.get("period_start") or start_date.isoformat()),
            period_end=str(full_pending.get("period_end") or end_date.isoformat()),
            checkpoint_source=FULL_CHECKPOINT_SOURCE,
            run_source="PNCP_FULL",
            resumed=True,
        )

    pending = db.latest_incomplete_global_sync_period(INCREMENTAL_CHECKPOINT_SOURCE)

    if pending:
        key = str(pending.get("publication_day") or "")
        mode = PncpClient.checkpoint_mode_from_key(key)
        parsed = PncpClient.parse_range_checkpoint_key(key)

        if mode not in {"publication", "update"} or not parsed:
            raise RuntimeError(
                "Checkpoint incremental PNCP inválido; execução automática abortada."
            )

        start_date, end_date = parsed

        return SyncWindow(
            mode=mode,
            start_date=start_date,
            end_date=end_date,
            period_start=str(
                pending.get("period_start") or start_date.isoformat()
            ),
            period_end=str(
                pending.get("period_end") or end_date.isoformat()
            ),
            checkpoint_source=INCREMENTAL_CHECKPOINT_SOURCE,
            run_source="PNCP_INCREMENTAL",
            resumed=True,
        )

    anchor = db.last_successful_sync_run(RUN_SOURCES)

    if not anchor:
        if db.global_catalog_count() == 0:
            raise RuntimeError(
                "Catálogo vazio: execute a carga completa inicial antes do worker incremental."
            )

        catalog_anchor = db.last_catalog_update()
        if not catalog_anchor:
            raise RuntimeError(
                "Catálogo possui dados, mas não há marco confiável "
                "para iniciar a sincronização incremental."
            )

        anchor = {
            "finished_at": catalog_anchor,
            "started_at": catalog_anchor,
        }

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
        checkpoint_source=INCREMENTAL_CHECKPOINT_SOURCE,
        run_source="PNCP_INCREMENTAL",
        resumed=False,
    )


def schedule_full_reconciliation(
    db: Database,
    today: date | None = None,
    horizon_days: int = 60,
) -> bool:
    """Cria a reconciliação semanal sem reiniciar um trabalho pendente."""
    if db.latest_incomplete_global_sync_period(FULL_CHECKPOINT_SOURCE):
        return False

    start_date = today or date.today()
    end_date = start_date + timedelta(days=max(1, int(horizon_days)))
    checkpoint_key = (
        f"open_proposals:range:{start_date.isoformat()}:{end_date.isoformat()}"
    )

    for modality_code in sorted({int(code) for code in MODALITIES.values()}):
        db.save_global_checkpoint(
            modality_code,
            "",
            checkpoint_key,
            1,
            False,
            0,
            "",
            source=FULL_CHECKPOINT_SOURCE,
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat(),
        )

    return True


def ordered_modalities(client: PncpClient):
    """Mesma prioridade da interface administrativa, com fallback local."""
    modalities = client.fetch_modalities()

    priority_codes = [8, 6, 4, 12, 9]

    by_code = {
        int(code): name
        for name, code in modalities.items()
    }

    local_by_code = {
        int(code): name
        for name, code in MODALITIES.items()
    }

    ordered = []
    used = set()

    for code in priority_codes:
        ordered.append(
            (
                by_code.get(code)
                or local_by_code.get(code)
                or str(code),
                code,
            )
        )
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
            conn.execute(
                "SELECT pg_try_advisory_lock(?)",
                (ADVISORY_LOCK_ID,),
            ).fetchone()[0]
        )

        if not acquired:
            raise WorkerAlreadyRunning(
                "Já existe uma atualização PNCP automática em execução."
            )

        yield

    finally:
        if acquired:
            try:
                conn.execute(
                    "SELECT pg_advisory_unlock(?)",
                    (ADVISORY_LOCK_ID,),
                )
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
    max_consecutive_empty_failures: int | None = None,
):
    """Executa uma rodada limitada; checkpoint permite continuar na próxima hora."""
    client = PncpClient(
        mode=window.mode,
        timeout=timeout,
        page_delay=page_delay,
        max_attempts=max_attempts,
    )

    modalities = ordered_modalities(client)

    totals = {
        "pages": 0,
        "received": 0,
        "saved": 0,
        "errors": [],
    }

    partial = False
    consecutive_empty_failures = 0

    with db.sync_run_scope(window.run_source) as run_id:
        for name, code in modalities:
            print(
                f"PNCP modalidade={name} code={code}",
                flush=True,
            )

            stats = client.sync(
                window.start_date,
                window.end_date,
                code,
                "",
                checkpoint_getter=lambda key, c=code: db.get_global_checkpoint(
                    c,
                    "",
                    key,
                    source=window.checkpoint_source,
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
                    source=window.checkpoint_source,
                    period_start=window.period_start,
                    period_end=window.period_end,
                ),
                max_pages_per_run=max_pages_per_modality,
            )

            totals["pages"] += int(
                stats.get("pages") or 0
            )

            totals["received"] += int(
                stats.get("received") or 0
            )

            totals["saved"] += int(
                stats.get("saved") or 0
            )

            errors = [
                str(error)
                for error in (stats.get("errors") or [])
            ]

            totals["errors"].extend(errors)

            no_progress_failure = bool(errors) and (
                int(stats.get("pages") or 0) == 0
                and int(stats.get("received") or 0) == 0
            )

            if no_progress_failure:
                consecutive_empty_failures += 1
            else:
                consecutive_empty_failures = 0

            for error in errors:
                detail = " ".join(error.split())

                print(
                    "PNCP_WORKER_ERROR_DETAIL "
                    f"modalidade={name} "
                    f"code={code} "
                    f"detail={detail}",
                    flush=True,
                )

            if stats.get("partial") or errors:
                partial = True
                # Um 429 pede parada imediata. Timeout/5xx fica salvo no
                # checkpoint, mas não bloqueia as modalidades seguintes.
                if any("429" in error for error in errors):
                    break

                if (
                    max_consecutive_empty_failures
                    and consecutive_empty_failures >= max_consecutive_empty_failures
                ):
                    print(
                        "PNCP_WORKER_FAIL_FAST "
                        f"consecutive_empty_failures={consecutive_empty_failures}",
                        flush=True,
                    )
                    break

                continue

        status = (
            "partial"
            if partial or totals["errors"]
            else "success"
        )

        db.finish_sync_run(
            run_id,
            status,
            totals["pages"],
            totals["saved"],
            " | ".join(
                str(error)
                for error in totals["errors"]
            ),
        )

    totals["status"] = status

    return totals


def main() -> int:
    db = Database(database_path(ROOT))

    timeout = max(
        5,
        int(
            os.getenv(
                "PNCP_WORKER_TIMEOUT",
                "30",
            )
        ),
    )

    max_attempts = max(
        1,
        int(
            os.getenv(
                "PNCP_WORKER_MAX_ATTEMPTS",
                "4",
            )
        ),
    )

    max_pages = max(
        1,
        int(
            os.getenv(
                "PNCP_WORKER_MAX_PAGES_PER_MODALITY",
                "120",
            )
        ),
    )

    page_delay = max(
        0.0,
        float(
            os.getenv(
                "PNCP_WORKER_PAGE_DELAY",
                "0.25",
            )
        ),
    )

    max_consecutive_empty_failures = max(
        1,
        int(
            os.getenv(
                "PNCP_WORKER_MAX_CONSECUTIVE_EMPTY_FAILURES",
                "3",
            )
        ),
    )

    try:
        with worker_lock(db):
            if os.getenv("PNCP_AUTO_FULL_RECONCILE", "0") == "1":
                created = schedule_full_reconciliation(
                    db,
                    horizon_days=int(os.getenv("PNCP_FULL_HORIZON_DAYS", "60")),
                )
                print(
                    "PNCP_FULL_AUTO_SCHEDULE " + ("created" if created else "already_pending"),
                    flush=True,
                )

            window = resolve_sync_window(db)

            if not window.resumed:
                cleared = db.clear_completed_global_sync_period(
                    window.checkpoint_source,
                    window.period_start,
                    window.period_end,
                )
                print(
                    f"PNCP_CHECKPOINT_RESET cleared={cleared}",
                    flush=True,
                )

            print(
                "PNCP_WORKER_START "
                f"mode={window.mode} "
                f"start={window.start_date} "
                f"end={window.end_date} "
                f"resumed={window.resumed} "
                f"timeout={timeout}s "
                f"max_attempts={max_attempts} "
                f"page_delay={page_delay}s "
                f"max_pages_per_modality={max_pages} "
                f"fail_fast_after={max_consecutive_empty_failures}",
                flush=True,
            )

            if window.mode == "open_proposals":
                timeout = max(timeout, int(os.getenv("PNCP_FULL_TIMEOUT", "60")))
                max_attempts = max(max_attempts, int(os.getenv("PNCP_FULL_MAX_ATTEMPTS", "6")))
                page_delay = max(page_delay, float(os.getenv("PNCP_FULL_PAGE_DELAY", "1.8")))

            result = run_sync_cycle(
                db,
                window,
                timeout=timeout,
                page_delay=page_delay,
                max_attempts=max_attempts,
                max_pages_per_modality=max_pages,
                max_consecutive_empty_failures=max_consecutive_empty_failures,
            )

            print(
                "PNCP_WORKER_END "
                f"status={result['status']} "
                f"pages={result['pages']} "
                f"received={result['received']} "
                f"saved={result['saved']} "
                f"errors={len(result['errors'])}",
                flush=True,
            )

            # Partial é estado esperado e retomável.
            # O workflow termina com sucesso para permitir
            # a próxima execução agendada, que continuará
            # do checkpoint salvo.
            return 0

    except WorkerAlreadyRunning as error:
        print(
            f"PNCP_WORKER_SKIP {error}",
            flush=True,
        )
        return 0

    except Exception as error:
        print(
            f"PNCP_WORKER_ERROR {type(error).__name__}: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
