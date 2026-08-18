import unittest
from pathlib import Path

from src.pncp_items import PncpItemsError, fetch_contract_items_preview
from src.radar_items import fetch_radar_item_summaries


ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "data": [
                {
                    "numeroItem": index,
                    "descricao": f"Produto {index}",
                    "quantidade": 10 * index,
                    "unidadeMedida": "UN",
                    "valorUnitarioEstimado": 5.5 * index,
                }
                for index in range(1, 5)
            ],
            "totalElementos": 17,
        }


class FakeSession:
    headers = {}

    def get(self, url, params=None, timeout=None):
        assert params["pagina"] == 1
        assert params["tamanhoPagina"] == 4
        assert timeout <= 10
        return FakeResponse()


class RadarItemPreviewTests(unittest.TestCase):
    def test_preview_uses_only_first_page_and_exposes_total(self):
        pack = fetch_contract_items_preview(
            "12345678000199-1-10/2026", limit=4, timeout=5, session=FakeSession()
        )
        self.assertEqual(4, len(pack["items"]))
        self.assertEqual(17, pack["item_count"])
        self.assertTrue(pack["count_known"])
        self.assertTrue(pack["has_more"])
        self.assertEqual("Produto 1", pack["items"][0]["description"])

    def test_batch_keeps_other_cards_when_one_preview_fails(self):
        def fake_fetch(control, limit=4):
            if control == "B":
                raise PncpItemsError("falha isolada")
            return {
                "items": [{"description": f"Item {control}"}],
                "item_count": 9,
                "count_known": True,
                "has_more": True,
                "items_error": "",
            }

        result = fetch_radar_item_summaries(
            ["A", "B", "C"], max_workers=3, preview_items=4, fetcher=fake_fetch
        )
        self.assertEqual("Item A", result["A"]["items"][0]["description"])
        self.assertEqual("Item C", result["C"]["items"][0]["description"])
        self.assertIn("falha isolada", result["B"]["items_error"])


class Rc315FastUxContracts(unittest.TestCase):
    def test_search_renders_open_item_summary_before_actions(self):
        source = ROOT.joinpath("app.py").read_text(encoding="utf-8")
        self.assertIn("📦 Itens da licitação", source)
        self.assertIn("_cached_radar_item_summaries", source)
        self.assertIn("_render_radar_item_summary", source)
        self.assertIn("per_page = 8", source)
        self.assertIn("Ver todos os itens", source)

    def test_sidebar_navigation_fills_available_width(self):
        source = ROOT.joinpath("app.py").read_text(encoding="utf-8")
        self.assertIn("MENU LATERAL TOTALMENTE PREENCHIDO", source)
        self.assertIn('label:has(input:checked)', source)
        self.assertIn("width:100% !important", source)
        self.assertIn("min-height:100vh !important", source)

    def test_version_remains_in_rc31_line(self):
        source = ROOT.joinpath("src", "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.', source)


if __name__ == "__main__":
    unittest.main()
