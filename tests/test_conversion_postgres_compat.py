import unittest

from src.conversion import ConversionService


class _Cursor:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows if rows is not None else ([] if row is None else [row])

    def fetchone(self):
        return self._row

    def fetchall(self):
        return list(self._rows)


class _FakeConnection:
    def __init__(self, existing=True):
        self.existing = existing
        self.statements = []

    def execute(self, statement, params=None):
        self.statements.append((str(statement), params))
        if str(statement).startswith("PRAGMA table_info("):
            row = {"name": "id"} if self.existing else None
            rows = [{"name": "id"}, {"name": "status"}] if self.existing else []
            return _Cursor(row=row, rows=rows)
        raise AssertionError(f"SQL inesperado: {statement}")


class ConversionPostgresCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.service = object.__new__(ConversionService)
        self.service.path = ":memory:"

    def test_table_exists_uses_pragma_compatibility_layer(self):
        conn = _FakeConnection(existing=True)
        self.assertTrue(self.service._table_exists(conn, "companies"))
        self.assertEqual("PRAGMA table_info(companies)", conn.statements[0][0])
        self.assertNotIn("sqlite_master", conn.statements[0][0])

    def test_columns_reuses_compatible_metadata_query(self):
        conn = _FakeConnection(existing=True)
        self.assertEqual({"id", "status"}, self.service._columns(conn, "companies"))
        self.assertTrue(all("sqlite_master" not in sql for sql, _ in conn.statements))

    def test_missing_table_returns_false_without_sqlite_master(self):
        conn = _FakeConnection(existing=False)
        self.assertFalse(self.service._table_exists(conn, "missing"))
        self.assertEqual("PRAGMA table_info(missing)", conn.statements[0][0])


if __name__ == "__main__":
    unittest.main()
