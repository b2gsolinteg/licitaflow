import ast
from pathlib import Path
import unittest


class InvitationActivationUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_path = Path(__file__).resolve().parents[1] / "app.py"
        cls.source = cls.app_path.read_text(encoding="utf-8")

    def test_app_remains_valid_python(self):
        ast.parse(self.source)

    def test_invitation_tab_renders_and_submits_activation_form(self):
        self.assertIn('with st.form("activate_invitation"):', self.source)
        self.assertIn('"Código de acesso"', self.source)
        self.assertIn('"Confirme sua senha"', self.source)
        self.assertIn("db.activate_invitation(", self.source)


if __name__ == "__main__":
    unittest.main()
