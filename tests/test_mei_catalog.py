import os
import tempfile
import unittest
from pathlib import Path

from src.database import Database
from src.mei_catalog import (
    MeiCatalogService,
    enrich_with_items,
    fetch_price_history_for_item,
    states_for_region,
    summarize_price_history,
)
from src.mei_portals import portal_access_info


class FakePriceClient:
    def search_catalog(self, query, kind="Material", limit=8):
        return [{"code": 123, "description": "BARBANTE ALGODAO", "catalog_source": "Compras.gov"}]

    def fetch_prices(self, catalog_code, state="", kind="Material", start_date=None, max_pages=12):
        return [
            {"homologated_unit_value": 12.0, "published_at": "2026-08-01", "brand": "Circulo", "supplier": "Fornecedor 1"},
            {"homologated_unit_value": 14.0, "published_at": "2026-07-01", "brand": "Circulo", "supplier": "Fornecedor 2"},
            {"homologated_unit_value": 10.0, "published_at": "2026-06-01", "brand": "EuroRoma", "supplier": "Fornecedor 1"},
        ]


class MeiCatalogTests(unittest.TestCase):
    def setUp(self):
        self.previous_backend = os.environ.get("LICITANEXO_DB_BACKEND")
        os.environ["LICITANEXO_DB_BACKEND"] = "sqlite"
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "licitanexo.db")
        self.service = MeiCatalogService(self.db)
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT INTO global_pncp_catalog(
                    id,pncp_control_number,agency,city,state,modality,published_at,
                    opening_at,closing_at,object,estimated_value,source_url,srp,
                    source_name,source_channel
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "1", "12345678000199-1-10/2026", "Prefeitura de São José dos Pinhais",
                    "São José dos Pinhais", "PR", "Pregão eletrônico", "2026-08-10T12:00:00",
                    "2026-08-18T10:00:00", "2099-08-20T10:00:00",
                    "Aquisição de materiais de artesanato e barbante",
                    36070.44, "https://www.gov.br/compras/", 0, "Compras.gov", "PNCP",
                ),
            )
            conn.execute(
                """
                INSERT INTO global_pncp_catalog(
                    id,pncp_control_number,agency,city,state,modality,published_at,
                    opening_at,closing_at,object,estimated_value,source_url,srp,
                    source_name,source_channel
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "2", "12345678000199-1-11/2026", "Prefeitura de Recife",
                    "Recife", "PE", "Dispensa de licitação", "2026-08-11T12:00:00",
                    "2026-08-19T10:00:00", "2099-08-21T10:00:00",
                    "Aquisição de material de limpeza", 9000.0,
                    "https://bll.org.br/", 0, "BLL Compras", "PNCP",
                ),
            )

    def tearDown(self):
        self.tmp.cleanup()
        if self.previous_backend is None:
            os.environ.pop("LICITANEXO_DB_BACKEND", None)
        else:
            os.environ["LICITANEXO_DB_BACKEND"] = self.previous_backend

    def test_region_and_city_filters_do_not_require_keyword(self):
        self.assertIn("PR", states_for_region("Sul"))
        rows = self.service.search(region="Sul", city="São José dos Pinhais", keyword="")
        self.assertEqual(1, len(rows))
        self.assertEqual("São José dos Pinhais", rows[0]["city"])
        self.assertEqual("Compras.gov", rows[0]["portal"])
        self.assertEqual("Gratuito", rows[0]["portal_access"])

    def test_paid_or_conditional_portals_are_not_called_free(self):
        self.assertNotEqual("Gratuito", portal_access_info("BLL Compras").label)
        self.assertNotEqual("Gratuito", portal_access_info("BNC Compras").label)
        self.assertEqual("Verificar condições", portal_access_info("Portal desconhecido").label)

    def test_item_enrichment_is_resilient_and_exposes_products(self):
        opportunities = [{"pncp_control_number": "A", "category": "Outros"}]

        def fake_fetcher(control):
            self.assertEqual("A", control)
            return [{
                "description": "Barbante de algodão",
                "quantity": 500,
                "unit_measure": "rolo",
                "unit_price": 14.8,
                "catalog_code": "123",
                "source_reference": "pncp:A:1",
            }]

        enriched = enrich_with_items(opportunities, fetcher=fake_fetcher, max_workers=1, max_items=5)
        self.assertEqual(1, enriched[0]["item_count"])
        self.assertEqual("Barbante de algodão", enriched[0]["items"][0]["description"])
        self.assertEqual("Artesanato", enriched[0]["category"])

    def test_price_summary_uses_homologated_values_and_brand_counts(self):
        summary = summarize_price_history([
            {"homologated_unit_value": 10, "published_at": "2026-06-01", "brand": "EuroRoma", "supplier": "Fornecedor 1"},
            {"homologated_unit_value": 14, "published_at": "2026-07-01", "brand": "Circulo", "supplier": "Fornecedor 2"},
            {"homologated_unit_value": 12, "published_at": "2026-08-01", "brand": "Circulo", "supplier": "Fornecedor 1"},
        ])
        self.assertEqual(3, summary["count"])
        self.assertEqual(12, summary["median"])
        self.assertEqual(10, summary["minimum"])
        self.assertEqual(14, summary["maximum"])
        self.assertEqual(12, summary["last_price"])
        self.assertEqual("Circulo", summary["brands"][0]["name"])
        self.assertEqual(2, summary["brands"][0]["count"])

    def test_price_history_can_discover_catalog_code_without_user_profile(self):
        result = fetch_price_history_for_item(
            {"description": "barbante algodão", "catalog_code": ""},
            state="PR",
            client=FakePriceClient(),
        )
        self.assertTrue(result["available"])
        self.assertEqual("123", result["catalog_code"])
        self.assertEqual(12, result["summary"]["median"])


class MeiAppContracts(unittest.TestCase):
    def test_mei_entrypoint_is_separate_from_pro(self):
        source = Path(__file__).resolve().parents[1].joinpath("mei_app.py").read_text(encoding="utf-8")
        self.assertIn('MEI_PRICE = "R$ 29,90/mês"', source)
        self.assertNotIn("from app import", source)
        self.assertIn("Brasil inteiro", source)
        self.assertIn("Ver preço real do governo", source)
        self.assertIn("Portal da disputa", source)

    def test_removed_features_are_not_mei_navigation(self):
        source = Path(__file__).resolve().parents[1].joinpath("mei_app.py").read_text(encoding="utf-8")
        for forbidden in ("Jornada", "Precificação", "Tutoriais de participação", "Perfil da empresa"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
