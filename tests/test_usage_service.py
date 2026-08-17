import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


os.environ.setdefault("LICITANEXO_DB_BACKEND", "sqlite")

from src.usage import UsageLimitError, UsageService, _month_bounds_utc


class UsageServiceTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.path = Path(handle.name)
        self.usage = UsageService(self.path)

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_sqlite_month_bounds_are_lexicographically_safe(self):
        start, end = _month_bounds_utc(datetime(2026, 8, 16, tzinfo=timezone.utc))
        self.assertEqual(start, "2026-08-01 00:00:00+00:00")
        self.assertEqual(end, "2026-09-01 00:00:00+00:00")

    def test_month_usage_excludes_old_events(self):
        self.usage.record_analysis("c1", "u1", "edital.pdf", pages=8)
        old = datetime.now(timezone.utc) - timedelta(days=70)
        with self.usage.connect() as connection:
            connection.execute(
                """
                INSERT INTO usage_events(
                    company_id,user_id,event_type,units,estimated_cost_cents,metadata,created_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    "c1",
                    "u1",
                    "analysis",
                    7,
                    0,
                    "{}",
                    old.strftime("%Y-%m-%d %H:%M:%S+00:00"),
                ),
            )
        result = self.usage.month_usage("c1", "analysis")
        self.assertEqual(result["units"], 1)

    def test_company_limit_blocks_after_reaching_quota(self):
        self.usage.set_company_policy("c1", analysis_limit=1, estimated_cost_cents=0)
        self.assertTrue(self.usage.assert_analysis_allowed("c1")["allowed"])
        self.usage.record_analysis("c1", "u1", "edital.pdf")
        with self.assertRaises(UsageLimitError):
            self.usage.assert_analysis_allowed("c1")


if __name__ == "__main__":
    unittest.main()
