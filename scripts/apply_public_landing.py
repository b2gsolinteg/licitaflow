from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"

IMPORT_ANCHOR = "from src.logging_setup import configure_logging"
SHELL_IMPORT = "from src.public_shell import render_public_landing, render_public_auth"
LEGACY_IMPORTS = (
    "from src.public_landing import render_public_landing",
    "from src.public_landing_exact import render_public_landing",
    "from src.public_auth import render_public_auth",
)

GATE_MARKER = "# PUBLIC_SHELL_GATE_V4"
PUBLIC_GATE = '''    # PUBLIC_SHELL_GATE_V4
    # Este gate precisa ser a primeira lógica de main(): impede que a home/login públicos
    # herdem apply_brand() e impede ?auth=... de cair no login_page() legado.
    if "user" not in st.session_state:
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
    for legacy in LEGACY_IMPORTS:
        line = legacy + "\n"
        if line in source:
            source = source.replace(line, "", 1)
            changed = True

    if SHELL_IMPORT not in source:
        if IMPORT_ANCHOR not in source:
            raise RuntimeError("ponto de importação não encontrado")
        source = source.replace(IMPORT_ANCHOR, f"{IMPORT_ANCHOR}\n{SHELL_IMPORT}", 1)
        changed = True

    return source, changed


def _install_public_gate(source: str) -> tuple[str, bool]:
    match = re.search(r"(?m)^def main\(\):\s*$", source)
    if not match:
        raise RuntimeError("def main() não encontrado")

    insert_at = match.end()
    immediate_region = source[insert_at:insert_at + 900]

    # Só considera instalado se o gate V4 estiver imediatamente no início de main().
    # Gates antigos podem permanecer mais abaixo sem efeito; o V4 retorna antes deles.
    if GATE_MARKER in immediate_region:
        return source, False

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
        print("OK: gate público V4 já está instalado antes do login legado.")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / f"app.py.before-public-shell-v4.{stamp}.bak"
    shutil.copy2(APP_PATH, backup)
    APP_PATH.write_text(source, encoding="utf-8")

    print("OK: home e login públicos isolados do tema/login legado.")
    print(f"Backup criado: {backup.name}")
    if import_changed:
        print("Import público atualizado para src.public_shell.")
    if gate_changed:
        print("Gate V4 inserido como primeira lógica de main().")
    print("O login antigo permanece no arquivo apenas como fallback interno, mas não recebe mais ?auth=...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
