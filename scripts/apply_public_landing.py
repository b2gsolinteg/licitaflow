from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"

IMPORT_ANCHOR = "from src.logging_setup import configure_logging"
LEGACY_IMPORT = "from src.public_landing import render_public_landing"
IMPORT_LINE = "from src.public_landing_exact import render_public_landing"

ORIGINAL_MAIN = '''def main():
    apply_brand()
    if "user" not in st.session_state:
        login_page()
        return
'''

PATCHED_MAIN_V1 = '''def main():
    apply_brand()
    if "user" not in st.session_state:
        if st.query_params.get("auth"):
            login_page()
        else:
            render_public_landing(LOGO_PATH)
        return
'''

DESIRED_MAIN = '''def main():
    if "user" not in st.session_state and not st.query_params.get("auth"):
        render_public_landing(LOGO_PATH)
        return

    apply_brand()
    if "user" not in st.session_state:
        login_page()
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


def _replace_main(source: str) -> tuple[str, bool]:
    if DESIRED_MAIN in source:
        return source, False
    if PATCHED_MAIN_V1 in source:
        return source.replace(PATCHED_MAIN_V1, DESIRED_MAIN, 1), True
    if ORIGINAL_MAIN in source:
        return source.replace(ORIGINAL_MAIN, DESIRED_MAIN, 1), True
    raise RuntimeError("bloco main() compatível não encontrado")


def main() -> int:
    if not APP_PATH.exists():
        print(f"ERRO: app.py não encontrado em {APP_PATH}")
        return 1

    original = APP_PATH.read_text(encoding="utf-8")
    source = original

    try:
        source, import_changed = _replace_import(source)
        source, main_changed = _replace_main(source)
    except RuntimeError as error:
        print(f"ERRO: {error}. Nenhuma alteração foi feita.")
        return 2

    if source == original:
        print("OK: integração da landing aprovada já está aplicada.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / f"app.py.before-public-landing-v2.{stamp}.bak"
    shutil.copy2(APP_PATH, backup)
    APP_PATH.write_text(source, encoding="utf-8")

    print("OK: landing aprovada integrada com isolamento de CSS.")
    print(f"Backup criado: {backup.name}")
    if import_changed:
        print("Import atualizado para src.public_landing_exact.")
    if main_changed:
        print("A home pública agora é renderizada antes do tema interno do app.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
