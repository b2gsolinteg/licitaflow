import importlib.util
import unittest
from pathlib import Path


RUNTIME_PATH = Path(__file__).parents[1] / "src" / "db_runtime.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location("db_runtime_under_test", RUNTIME_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PostgresMonthUsageCompatibilityTests(unittest.TestCase):
    def test_both_month_boundaries_cast_text_timestamp_column(self):
        runtime = load_runtime()
        sql = runtime.translate_sql("""
            SELECT COALESCE(SUM(units),0) AS units
            FROM usage_events
            WHERE company_id=?
              AND created_at >= datetime('now','start of month')
              AND created_at < datetime('now','start of month','+1 month')
        """)

        self.assertEqual(sql.count("CAST(created_at AS TIMESTAMP)"), 2)
        self.assertIn("date_trunc('month', CURRENT_TIMESTAMP)", sql)
        self.assertIn("INTERVAL '1 month'", sql)
        self.assertEqual(sql.count("%s"), 1)

    def test_admin_month_summary_uses_same_translation(self):
        runtime = load_runtime()
        sql = runtime.translate_sql("""
            SELECT company_id FROM usage_events
            WHERE created_at >= datetime('now','start of month')
              AND created_at < datetime('now','start of month','+1 month')
        """)

        self.assertEqual(sql.count("CAST(created_at AS TIMESTAMP)"), 2)


if __name__ == "__main__":
    unittest.main()

