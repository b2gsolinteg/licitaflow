import ast
import unittest
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
APP_SOURCE = APP_PATH.read_text(encoding="utf-8")


class InviteRecoveryUiTests(unittest.TestCase):
    def test_app_is_valid_python(self):
        ast.parse(APP_SOURCE)

    def test_public_password_recovery_has_request_and_reset_steps(self):
        self.assertIn(
            'st.form("password_recovery_request", clear_on_submit=False, enter_to_submit=False)',
            APP_SOURCE,
        )
        self.assertIn('db.request_password_reset(normalized_email)', APP_SOURCE)
        self.assertIn(
            'st.form("password_recovery_reset", clear_on_submit=False, enter_to_submit=False)',
            APP_SOURCE,
        )
        self.assertIn(
            'db.reset_password(normalized_email, recovery_code, new_password)',
            APP_SOURCE,
        )
        self.assertIn('len(str(new_password or "")) < 8', APP_SOURCE)
        self.assertIn('new_password != new_password_confirmation', APP_SOURCE)

    def test_admin_can_regenerate_and_view_pending_invitation_code(self):
        self.assertIn('"admin_invitation_codes"', APP_SOURCE)
        self.assertIn('"Gerar novo código para este convite"', APP_SOURCE)
        self.assertIn(
            'code = db.approve_access_request(\n'
            '                        selected_request["id"], trial_days=selected_trial_days,',
            APP_SOURCE,
        )
        self.assertIn('"O código original não pode ser recuperado', APP_SOURCE)


if __name__ == "__main__":
    unittest.main()
