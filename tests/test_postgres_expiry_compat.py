import ast
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


DATABASE_PATH = Path(__file__).parents[1] / "src" / "database.py"


def load_expiry_helper():
    source = DATABASE_PATH.read_text(encoding="utf-8")
    module = ast.parse(source)
    helper = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "_timestamp_not_expired"
    )
    namespace = {"datetime": datetime}
    exec(compile(ast.Module(body=[helper], type_ignores=[]), str(DATABASE_PATH), "exec"), namespace)
    return namespace["_timestamp_not_expired"], source


class PostgresExpiryCompatibilityTests(unittest.TestCase):
    def test_helper_accepts_sqlite_text_and_postgres_datetime(self):
        helper, _ = load_expiry_helper()
        future_aware = datetime.now(timezone.utc) + timedelta(minutes=5)
        future_naive = datetime.now() + timedelta(minutes=5)
        past_aware = datetime.now(timezone.utc) - timedelta(minutes=5)

        self.assertTrue(helper(future_aware))
        self.assertTrue(helper(future_naive.isoformat(sep=" ")))
        self.assertFalse(helper(past_aware))
        self.assertFalse(helper("invalid timestamp"))
        self.assertTrue(helper(None, allow_missing=True))
        self.assertFalse(helper(None))

    def test_expiry_comparison_is_not_executed_by_sql(self):
        _, source = load_expiry_helper()
        self.assertNotIn("invitation_expires_at >= CURRENT_TIMESTAMP", source)
        self.assertNotIn("r.expires_at >= CURRENT_TIMESTAMP", source)


if __name__ == "__main__":
    unittest.main()
