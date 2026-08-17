from pathlib import Path

catalog_path = Path("src/mei_catalog.py")
source = catalog_path.read_text(encoding="utf-8")
replacements = {
    'params.append(f"%{city.casefold()}%")': 'params.append(f"%{self.db._search_fold(city)}%")',
    'folded = f"%{term.casefold()}%"': 'folded = f"%{self.db._search_fold(term)}%"',
}
for old, new in replacements.items():
    if source.count(old) != 1:
        raise SystemExit(f"Trecho esperado não encontrado uma única vez: {old}")
    source = source.replace(old, new)
catalog_path.write_text(source, encoding="utf-8")

test_path = Path("tests/test_mei_catalog.py")
test = test_path.read_text(encoding="utf-8")
for old, new in (
    ('"Prefeitura de Londrina",\n                    "Londrina",', '"Prefeitura de São José dos Pinhais",\n                    "São José dos Pinhais",'),
    ('rows = self.service.search(region="Sul", city="Londrina", keyword="")', 'rows = self.service.search(region="Sul", city="São José dos Pinhais", keyword="")'),
    ('self.assertEqual("Londrina", rows[0]["city"])', 'self.assertEqual("São José dos Pinhais", rows[0]["city"])'),
):
    if test.count(old) != 1:
        raise SystemExit(f"Trecho de teste esperado não encontrado uma única vez: {old}")
    test = test.replace(old, new)
test_path.write_text(test, encoding="utf-8")
print("Busca MEI com acentos endurecida")
