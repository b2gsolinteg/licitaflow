import io
import tempfile
import unittest
from pathlib import Path

from reportlab.pdfgen import canvas

from src.company_intelligence import (
    document_readiness,
    extract_cnpj_card,
    get_extended_profile,
    rank_opportunities,
    save_extended_profile,
)
from src.database import Database
from src.pricing import add_supplier, item_financials, list_suppliers, select_supplier


class CompanyIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "licitaflow.db")
        self.user = self.db.register("Empresa Teste", "Cliente", "cliente@example.com", "senha-forte")
        self.company_id = self.user["company_id"]

    def tearDown(self):
        self.temp.cleanup()

    def test_profile_ranks_matching_opportunities_without_hiding_others(self):
        save_extended_profile(
            self.db,
            self.company_id,
            offerings="papel A4, material de escritório, toner",
            interest_keywords="papel A4, papelaria",
            procurement_interests="fornecimento de material de expediente",
            service_states="SP, PR",
            excluded_keywords="obra pesada",
            profile_search_enabled=True,
        )
        profile = get_extended_profile(self.db, self.company_id)
        items = [
            {"id": "1", "object": "Aquisição de papel A4 e material de expediente", "state": "SP", "agency": "Prefeitura"},
            {"id": "2", "object": "Contratação de manutenção de elevadores", "state": "SP", "agency": "Câmara"},
            {"id": "3", "object": "Execução de obra pesada em rodovia", "state": "PR", "agency": "Estado"},
        ]
        ranked = rank_opportunities(items, profile)
        self.assertEqual([row["id"] for row in ranked], ["1", "2", "3"])
        self.assertGreater(ranked[0]["_match_score"], ranked[1]["_match_score"])
        self.assertEqual(next(row for row in ranked if row["id"] == "3")["_match_score"], 0)
        self.assertEqual(len(ranked), 3)

    def test_cnpj_pdf_extraction_reads_core_fields(self):
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer)
        lines = [
            "NÚMERO DE INSCRIÇÃO",
            "11.222.333/0001-81",
            "NOME EMPRESARIAL",
            "EMPRESA TESTE COMERCIO LTDA",
            "TÍTULO DO ESTABELECIMENTO (NOME DE FANTASIA)",
            "EMPRESA TESTE",
            "CÓDIGO E DESCRIÇÃO DA ATIVIDADE ECONÔMICA PRINCIPAL",
            "47.51-2-01 - Comércio varejista especializado",
        ]
        y = 800
        for line in lines:
            pdf.drawString(50, y, line)
            y -= 24
        pdf.save()
        parsed = extract_cnpj_card("cartao.pdf", "application/pdf", buffer.getvalue())
        self.assertEqual(parsed["cnpj"], "11222333000181")
        self.assertIn("EMPRESA TESTE COMERCIO LTDA", parsed["legal_name"])
        self.assertIn("47.51-2-01", parsed["cnaes"])

    def test_document_readiness_flags_expired_and_ready_documents(self):
        documents = [
            {"document_type": "Certificado de regularidade do FGTS", "status": "Válido", "expiry_date": "2099-12-31"},
            {"document_type": "CNDT - débitos trabalhistas", "status": "Vencido", "expiry_date": "2020-01-01"},
        ]
        findings = [
            {"title": "Regularidade FGTS", "evidence": "Apresentar certificado de regularidade do FGTS"},
            {"title": "CNDT", "evidence": "Exigida certidão negativa de débitos trabalhistas"},
        ]
        readiness = document_readiness(documents, findings)
        by_name = {row["document_type"]: row["state"] for row in readiness}
        self.assertEqual(by_name["Certificado de regularidade do FGTS"], "ready")
        self.assertEqual(by_name["CNDT - débitos trabalhistas"], "expired")

    def test_multiple_suppliers_feed_selected_item_cost_and_margin(self):
        self.db.upsert_opportunity(self.company_id, {
            "numeroControlePNCP": "TESTE-1",
            "orgao": "Prefeitura",
            "municipio": "São Paulo",
            "uf": "SP",
            "modalidade": "Pregão eletrônico",
            "objeto": "Aquisição de papel A4",
            "valor": 10000,
            "link": "",
        })
        opportunity = self.db.list_opportunities(self.company_id)[0]
        self.db.add_quote_item(
            self.company_id, opportunity["id"], "Papel A4", 100, 0, 0, 0, 0,
            27.90, "", lot_number="1", edital_price=32.00, commission=0,
        )
        item = self.db.list_quote_items(self.company_id, opportunity["id"])[0]
        first = add_supplier(self.db, self.company_id, item["id"], "Fornecedor A", 21.40, 0.50)
        second = add_supplier(self.db, self.company_id, item["id"], "Fornecedor B", 20.85, 0.40)
        suppliers = list_suppliers(self.db, self.company_id, item["id"])
        self.assertEqual(len(suppliers), 2)
        self.assertTrue(next(row for row in suppliers if row["id"] == first)["is_selected"])
        select_supplier(self.db, self.company_id, item["id"], second)
        refreshed = self.db.list_quote_items(self.company_id, opportunity["id"])[0]
        self.assertEqual(refreshed["supplier"], "Fornecedor B")
        self.assertAlmostEqual(float(refreshed["unit_cost"]), 20.85, places=2)
        metrics = item_financials(refreshed)
        self.assertGreater(metrics["profit"], 0)
        self.assertGreater(metrics["margin_pct"], 0)


if __name__ == "__main__":
    unittest.main()
