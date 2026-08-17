import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArchitectureContractTests(unittest.TestCase):
    def test_streamlit_entrypoint_does_not_import_postgres_driver(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertNotIn("psycopg", imported)
        self.assertNotIn("psycopg_pool", imported)

    def test_critical_services_do_not_use_sqlite_datetime_functions(self):
        for relative in ("src/security_rc25.py", "src/usage.py", "src/billing.py"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("datetime('now'", source, relative)
            self.assertNotIn('datetime("now"', source, relative)

    def test_postgres_schema_is_owned_by_migrations(self):
        support_source = (ROOT / "src/support.py").read_text(encoding="utf-8")
        self.assertIn("if not using_postgres():", support_source)
        migrations = sorted((ROOT / "migrations/postgres").glob("*.sql"))
        self.assertGreaterEqual(len(migrations), 2)
        self.assertTrue(any(path.name.startswith("0002_support") for path in migrations))

    def test_login_does_not_offer_unimplemented_remember_me(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('st.checkbox("Lembrar de mim"', source)
        self.assertIn('href="?auth=recovery"', source)

    def test_sidebar_css_patch_is_not_duplicated(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        marker = "LICITANEXO - PATCH MENU LATERAL"
        self.assertEqual(source.count(marker), 1)

    def test_versioned_migration_tool_has_checksum_and_lock(self):
        source = (ROOT / "src/db_migrations.py").read_text(encoding="utf-8")
        self.assertIn("sha256", source)
        self.assertIn("pg_advisory_lock", source)
        self.assertIn("schema_migrations", source)


if __name__ == "__main__":
    unittest.main()
