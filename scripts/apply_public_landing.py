from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"

IMPORT_ANCHOR = "from src.logging_setup import configure_logging"
LEGACY_IMPORT = "from src.public_landing import render_public_landing"
IMPORT_LINE = "from src.public_landing_exact import render_public_landing"

PUBLIC_GATE = '''    if "user" not in st.session_state and not st.query_params.get("auth"):
        render_public_landing(LOGO_PATH)
        return

'''


def _replace_import(source: str) -> tuple[str, bool]:
    changed = False

    if LEGACY_IMPORT in source:
        source = source.replace(LEGACY_IMPORT, IMPORT_LINE, 1)
        changed = True
    elif IMPORT_LINE not in source:
        if IMPORT_ANCHOR not in source:
            raise RuntimeError("ponto de importação não encontrado")
        source = source.replace(
            IMPORT_ANCHOR,
            f"{IMPORT_ANCHOR}\n{IMPORT_LINE}",
            1,
        )
        changed = True

    return source, changed


def _insert_public_gate(source: str) -> tuple[str, bool]:
    if PUBLIC_GATE in source:
        return source, False

    match = re.search(r"(?m)^def main\(\):\s*$", source)
    if not match:
        raise RuntimeError("def main() não encontrado")

    insert_at = match.end()
    source = source[:insert_at] + "\n" + PUBLIC_GATE + source[insert_at:]
    return source, True


def main() -> int:
    if not APP_PATH.exists():
        print(f"ERRO: app.py não encontrado em {APP_PATH}")
        return 1

    original = APP_PATH.read_text(encoding="utf-8")
    source = original

    try:
        source, import_changed = _replace_import(source)
        source, gate_changed = _insert_public_gate(source)
    except RuntimeError as error:
        print(f"ERRO: {error}. Nenhuma alteração foi feita.")
        return 2

    if source == original:
        print("OK: integração da landing aprovada já está aplicada.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / f"app.py.before-public-landing-v3.{stamp}.bak"
    shutil.copy2(APP_PATH, backup)
    APP_PATH.write_text(source, encoding="utf-8")

    print("OK: landing aprovada integrada com isolamento de CSS.")
    print(f"Backup criado: {backup.name}")
    if import_changed:
        print("Import atualizado para src.public_landing_exact.")
    if gate_changed:
        print("Gate público inserido imediatamente após def main().")
    print("O restante do main() foi preservado sem reescrita.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
