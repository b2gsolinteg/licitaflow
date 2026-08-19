from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ValueLoginHomeContracts(unittest.TestCase):
    def test_essential_price_is_2990(self):
        config = (ROOT / "src" / "config.py").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("ESSENTIAL_PRICE_CENTS = 2990", config)
        self.assertIn("R$ 29,90", app)
        self.assertNotIn("R$ 49,90", app)
        self.assertNotIn("menos de R$1", app.lower())

    def test_home_leads_with_beginner_value_and_open_items(self):
        text = (ROOT / "src" / "essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn("Descubra o que o governo está comprando.", text)
        self.assertIn("Você não precisa adivinhar o que vender", text)
        self.assertIn("itens da compra já na tela", text)
        self.assertIn("documento por documento", text)

    def test_login_explains_the_product_without_overpromising(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("Encontre oportunidades para vender ao governo.", app)
        self.assertIn("Editais com os itens da compra já abertos na busca", app)
        self.assertIn("Pesquisa simples em todo o Brasil", app)
        self.assertNotIn("sem estoque", app.lower())

    def test_sidebar_keeps_professional_icons_with_muted_palette(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('icon=nav_icons.get(option)', app)
        self.assertIn('background:#E9F3EE !important', app)
        self.assertIn('background:#F0ECF4 !important', app)


if __name__ == "__main__":
    unittest.main()
