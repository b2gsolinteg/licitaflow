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
LANDING_IMPORT = "from src.public_landing_exact import render_public_landing"
AUTH_IMPORT = "from src.public_auth import render_public_auth"

OLD_PUBLIC_GATE = '''    if "user" not in st.session_state and not st.query_params.get("auth"):
        render_public_landing(LOGO_PATH)
        return

'''

PUBLIC_GATE = '''    if "user" not in st.session_state:
        if st.query_params.get("auth"):
            render_public_auth(
                db=db,
                security=security,
                conversion=conversion,
                commercial=commercial,
                client_ip_getter=_client_ip,
                motivational_phrases=MOTIVATIONAL_PHRASES,
            )
        else:
            render_public_landing(LOGO_PATH)
        return

'''


def _replace_imports(source: str) -> tuple[str, bool]:
    changed = False

    if LEGACY_IMPORT in source:
        source = source.replace(LEGACY_IMPORT, LANDING_IMPORT, 1)
        changed = True
    elif LANDING_IMPORT not in source:
        if IMPORT_ANCHOR not in source:
            raise RuntimeError("ponto de importação não encontrado")
        source = source.replace(IMPORT_ANCHOR, f"{IMPORT_ANCHOR}\n{LANDING_IMPORT}", 1)
        changed = True

    if AUTH_IMPORT not in source:
        anchor = LANDING_IMPORT if LANDING_IMPORT in source else IMPORT_ANCHOR
        source = source.replace(anchor, f"{anchor}\n{AUTH_IMPORT}", 1)
        changed = True

    return source, changed


def _install_public_gate(source: str) -> tuple[str, bool]:
    if PUBLIC_GATE in source:
        return source, False

    if OLD_PUBLIC_GATE in source:
        return source.replace(OLD_PUBLIC_GATE, PUBLIC_GATE, 1), True

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
        source, import_changed = _replace_imports(source)
        source, gate_changed = _install_public_gate(source)
    except RuntimeError as error:
        print(f"ERRO: {error}. Nenhuma alteração foi feita.")
        return 2

    if source == original:
        print("OK: nova home e autenticação pública já estão integradas.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / f"app.py.before-home-login-redesign.{stamp}.bak"
    shutil.copy2(APP_PATH, backup)
    APP_PATH.write_text(source, encoding="utf-8")

    print("OK: nova home e autenticação pública integradas.")
    print(f"Backup criado: {backup.name}")
    if import_changed:
        print("Imports públicos atualizados.")
    if gate_changed:
        print("Gate público atualizado para home e login isolados do tema interno.")
    print("O restante do app.py foi preservado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
