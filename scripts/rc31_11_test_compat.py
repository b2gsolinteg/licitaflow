from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"anchor ausente em {path}: {old}")
    p.write_text(text.replace(old, new), encoding="utf-8")


for path in (
    "tests/test_rc31_6_essential.py",
    "tests/test_rc31_9_simple_discovery.py",
    "tests/test_rc31_10_modern_filters.py",
):
    replace(path, 'APP_VERSION = "1.0 Essential RC31.10"', 'APP_VERSION = "1.0 Essential RC31.11"')

replace(
    "tests/test_rc31_8_clean_essential.py",
    'self.assertIn("Licitações sem complicação.", login)',
    'self.assertIn("Encontre oportunidades para vender ao governo.", login)',
)
