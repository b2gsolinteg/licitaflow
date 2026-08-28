from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"

IMPORT_ANCHOR = "from src.logging_setup import configure_logging"
IMPORT_LINE = "from src.public_landing import render_public_landing"

OLD_MAIN = '''    if "user" not in st.session_state:
        login_page()
        return
'''

NEW_MAIN = '''    if "user" not in st.session_state:
        if st.query_params.get("auth"):
            login_page()
        else:
            render_public_landing(LOGO_PATH)
        return
'''


def main() -> int:
    if not APP_PATH.exists():
        print(f"ERRO: app.py não encontrado em {APP_PATH}")
        return 1

    source = APP_PATH.read_text(encoding="utf-8")
    original = source

    if IMPORT_LINE not in source:
        if IMPORT_ANCHOR not in source:
            print("ERRO: ponto de importação não encontrado. Nenhuma alteração foi feita.")
            return 2
        source = source.replace(
            IMPORT_ANCHOR,
            f"{IMPORT_ANCHOR}\n{IMPORT_LINE}",
            1,
        )

    if NEW_MAIN not in source:
        if OLD_MAIN not in source:
            print("ERRO: bloco de autenticação em main() não encontrado. Nenhuma alteração foi feita.")
            return 3
        source = source.replace(OLD_MAIN, NEW_MAIN, 1)

    if source == original:
        print("OK: a landing pública já está aplicada.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / f"app.py.before-public-landing.{stamp}.bak"
    shutil.copy2(APP_PATH, backup)
    APP_PATH.write_text(source, encoding="utf-8")

    print("OK: landing pública aplicada com sucesso.")
    print(f"Backup criado: {backup.name}")
    print("Se o Streamlit estiver aberto, ele recarregará automaticamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
