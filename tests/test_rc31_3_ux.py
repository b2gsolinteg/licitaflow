import io
import unittest
from pathlib import Path

from pypdf import PdfReader

from src.help_guides import GUIDES, full_manual_pdf, guide_pdf


ROOT = Path(__file__).resolve().parents[1]


class HelpGuidePdfTests(unittest.TestCase):
    def test_each_user_screen_generates_valid_pdf(self):
        self.assertGreaterEqual(len(GUIDES), 7)
        for page, guide in GUIDES.items():
            payload = guide_pdf(page)
            self.assertTrue(payload.startswith(b"%PDF"), page)
            reader = PdfReader(io.BytesIO(payload))
            self.assertGreaterEqual(len(reader.pages), 1, page)
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
            self.assertIn("LicitaNexo", text)
            self.assertTrue(guide["title"].split(" - ")[0].split()[0] in text)

    def test_full_manual_has_all_sections(self):
        payload = full_manual_pdf()
        self.assertTrue(payload.startswith(b"%PDF"))
        reader = PdfReader(io.BytesIO(payload))
        self.assertGreaterEqual(len(reader.pages), len(GUIDES))


class Rc313UxContracts(unittest.TestCase):
    def test_auth_forms_do_not_submit_on_enter(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        for form_name in (
            "login", "access_request", "activate_invitation",
            "password_recovery_request", "password_recovery_reset",
        ):
            self.assertIn(
                f'with st.form("{form_name}", clear_on_submit=False, enter_to_submit=False):',
                source,
            )

    def test_sidebar_exposes_guide_for_current_screen(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("from src.help_guides import render_sidebar_guides", source)
        self.assertIn("render_sidebar_guides(page)", source)

    def test_supplier_comparison_is_not_markdown_money_cards(self):
        source = (ROOT / "src" / "pricing_ui.py").read_text(encoding="utf-8")
        self.assertIn("comparison_rows", source)
        self.assertIn("st.dataframe(", source)
        self.assertIn('"Margem possível"', source)
        self.assertIn('"Situação"', source)
        self.assertNotIn("row_values.markdown", source)

    def test_manual_opportunity_form_does_not_clear_on_enter(self):
        source = (ROOT / "src" / "pipeline_ui.py").read_text(encoding="utf-8")
        self.assertIn(
            'with st.form("manual_opportunity", clear_on_submit=False, enter_to_submit=False):',
            source,
        )

    def test_version_is_rc31_3(self):
        source = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.3"', source)


if __name__ == "__main__":
    unittest.main()
