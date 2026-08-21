from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class ModernFilters(unittest.TestCase):
    def test_filters(self):
        s=(ROOT/"src"/"essential_discovery.py").read_text(encoding="utf-8")
        self.assertIn('"Sul": ("PR", "RS", "SC")', s)
        self.assertIn('NATURE_OPTIONS = ("Todos", "Produtos", "Serviços")', s)
        self.assertIn('SRP_OPTIONS = ("Todos", "Com registro de preços", "Sem registro de preços")', s)
        self.assertIn('states=_effective_states(criteria)', s)
        self.assertIn('srp=_srp_query_value', s)
    def test_modern_nav(self):
        a=(ROOT/"app.py").read_text(encoding="utf-8")
        self.assertIn('"Minha lista": ":material/bookmark:"', a)
        self.assertIn('"Buscar licitações": ":material/search:"', a)
        self.assertNotIn('"❤️ Minha lista"', a)
    def test_version(self):
        c=(ROOT/"src"/"config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.19"', c)
if __name__ == "__main__": unittest.main()
