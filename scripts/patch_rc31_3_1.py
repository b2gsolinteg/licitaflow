from pathlib import Path

APP = Path("app.py")
CONFIG = Path("src/config.py")
TEST = Path("tests/test_optional_help_boot.py")

app = APP.read_text(encoding="utf-8")
old_import = "from src.help_guides import render_sidebar_guides\n"
new_loader = '''def render_sidebar_guides(page: str) -> None:\n    \"\"\"Carrega a ajuda sob demanda; falha do PDF nunca derruba o app.\"\"\"\n    try:\n        import src as _src  # garante o pacote-pai em reruns/hot reload do Streamlit\n        from src.help_guides import render_sidebar_guides as _render_sidebar_guides\n        _render_sidebar_guides(page)\n    except Exception:\n        st.caption(\"📘 Guia PDF temporariamente indisponível.\")\n\n'''
if app.count(old_import) != 1:
    raise SystemExit(f"esperado 1 import direto de help_guides; encontrado {app.count(old_import)}")
app = app.replace(old_import, new_loader, 1)
APP.write_text(app, encoding="utf-8")

config = CONFIG.read_text(encoding="utf-8")
old_version = 'APP_VERSION = "1.0 Essential RC31.3"'
new_version = 'APP_VERSION = "1.0 Essential RC31.3.1"'
if config.count(old_version) != 1:
    raise SystemExit("versão RC31.3 não encontrada exatamente uma vez")
CONFIG.write_text(config.replace(old_version, new_version, 1), encoding="utf-8")

TEST.write_text('''import ast\nfrom pathlib import Path\nimport unittest\n\n\nclass OptionalHelpBootTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")\n        cls.source = source\n        cls.tree = ast.parse(source)\n\n    def test_help_guides_is_not_a_top_level_dependency(self):\n        direct = [\n            node for node in self.tree.body\n            if isinstance(node, ast.ImportFrom) and node.module == "src.help_guides"\n        ]\n        self.assertEqual([], direct)\n\n    def test_help_loader_is_guarded(self):\n        functions = [\n            node for node in self.tree.body\n            if isinstance(node, ast.FunctionDef) and node.name == "render_sidebar_guides"\n        ]\n        self.assertEqual(1, len(functions))\n        guarded = any(isinstance(node, ast.Try) for node in ast.walk(functions[0]))\n        self.assertTrue(guarded)\n        self.assertIn("Guia PDF temporariamente indisponível", self.source)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

print("RC31.3.1 patch aplicado")
