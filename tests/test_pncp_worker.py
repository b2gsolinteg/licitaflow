import unittest
from contextlib import contextmanager
from datetime import date
from unittest.mock import patch

import requests

from scripts.pncp_sync_worker import SyncWindow, resolve_sync_window, run_sync_cycle
from src.pncp import PncpClient, PncpTemporaryError


class ResolveDb:
    def __init__(self, pending=None, anchor=None, count=1):
        self.pending = pending
        self.anchor = anchor
        self.count = count

    def latest_incomplete_global_sync_period(self, source):
        return self.pending

    def last_successful_sync_run(self, sources):
        return self.anchor

    def global_catalog_count(self):
        return self.count


class FakeRunDb:
    def __init__(self):
        self.finished = None
        self.calls = []

    @contextmanager
    def sync_run_scope(self, source):
        self.calls.append(("start", source))
        yield "run-1"

    def finish_sync_run(self, run_id, status, pages, records, errors):
        self.finished = (run_id, status, pages, records, errors)

    def get_global_checkpoint(self, *args, **kwargs):
        return None

    def save_global_checkpoint(self, *args, **kwargs):
        self.calls.append(("checkpoint", args, kwargs))

    def upsert_global_catalog_page(self, items):
        return len(items)


class PartialClient:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.sync_calls = []
        PartialClient.instances.append(self)

    def fetch_modalities(self):
        return {"Dispensa de licitação": 8, "Pregão eletrônico": 6}

    def sync(self, *args, **kwargs):
        self.sync_calls.append((args, kwargs))
        return {
            "pages": 3,
            "received": 150,
            "saved": 150,
            "partial": True,
            "errors": ["página 4: erro 503 após 4 tentativas"],
        }


class PncpWorkerTests(unittest.TestCase):
    def test_resolve_pending_checkpoint_keeps_original_range(self):
        db = ResolveDb(
            pending={
                "publication_day": "update:range:2026-08-10:2026-08-12",
                "period_start": "2026-08-10",
                "period_end": "2026-08-12",
            }
        )
        window = resolve_sync_window(db, today=date(2026, 8, 13))
        self.assertTrue(window.resumed)
        self.assertEqual(window.mode, "update")
        self.assertEqual(window.start_date, date(2026, 8, 10))
        self.assertEqual(window.end_date, date(2026, 8, 12))

    def test_resolve_new_cycle_overlaps_one_day(self):
        db = ResolveDb(
            anchor={"finished_at": "2026-08-12T18:30:00", "started_at": "2026-08-12T18:00:00"}
        )
        window = resolve_sync_window(db, today=date(2026, 8, 13))
        self.assertFalse(window.resumed)
        self.assertEqual(window.mode, "update")
        self.assertEqual(window.start_date, date(2026, 8, 11))
        self.assertEqual(window.end_date, date(2026, 8, 13))

    def test_pncp_sync_retries_failed_page_from_same_checkpoint(self):
        client = PncpClient(page_delay=0, max_attempts=1)
        requested_pages = []
        checkpoints = []

        def fail_page(*args):
            requested_pages.append(args[-1])
            raise PncpTemporaryError("erro 503")

        client.fetch_page = fail_page
        stats = client.sync(
            date(2026, 8, 10),
            date(2026, 8, 12),
            6,
            "",
            checkpoint_getter=lambda key: {
                "completed": 0,
                "next_page": 7,
                "items_saved": 300,
            },
            page_saver=lambda items: len(items),
            checkpoint_saver=lambda *args: checkpoints.append(args),
        )

        self.assertEqual(requested_pages, [7])
        self.assertTrue(stats["partial"])
        self.assertEqual(checkpoints[-1][1], 7)
        self.assertFalse(checkpoints[-1][2])

    def test_get_retries_timeout_four_times_without_real_sleep(self):
        client = PncpClient(timeout=1, page_delay=0, max_attempts=4)

        class TimeoutSession:
            def __init__(self):
                self.calls = 0

            def get(self, *args, **kwargs):
                self.calls += 1
                raise requests.Timeout("simulado")

        session = TimeoutSession()
        client.session = session
        with patch("src.pncp.time.sleep", return_value=None):
            with self.assertRaises(PncpTemporaryError) as ctx:
                client._get("https://example.invalid", {})

        self.assertEqual(session.calls, 4)
        self.assertIn("após 4 tentativas", str(ctx.exception))

    def test_worker_stops_after_first_partial_modality(self):
        db = FakeRunDb()
        window = SyncWindow(
            mode="update",
            start_date=date(2026, 8, 11),
            end_date=date(2026, 8, 12),
            period_start="2026-08-11",
            period_end="2026-08-12",
            resumed=False,
        )
        PartialClient.instances.clear()
        with patch("scripts.pncp_sync_worker.PncpClient", PartialClient):
            result = run_sync_cycle(db, window, max_pages_per_modality=10)

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["pages"], 3)
        self.assertEqual(len(PartialClient.instances[0].sync_calls), 1)
        self.assertEqual(db.finished[1], "partial")


if __name__ == "__main__":
    unittest.main()
