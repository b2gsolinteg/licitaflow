import ast
from pathlib import Path
import unittest


class OptionalHelpBootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
        cls.source = source
        cls.tree = ast.parse(source)

    def test_help_guides_is_not_a_top_level_dependency(self):
        direct = [
            node for node in self.tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "src.help_guides"
        ]
        self.assertEqual([], direct)

    def test_help_loader_is_guarded(self):
        functions = [
            node for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "render_sidebar_guides"
        ]
        self.assertEqual(1, len(functions))
        guarded = any(isinstance(node, ast.Try) for node in ast.walk(functions[0]))
        self.assertTrue(guarded)
        self.assertIn("Guia PDF temporariamente indisponível", self.source)


if __name__ == "__main__":
    unittest.main()
