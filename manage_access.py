"""Utilitário local de emergência para administrar o acesso à LicitaNexo."""

import argparse
from datetime import datetime
from getpass import getpass
from pathlib import Path

from src.config import database_path
from src.database import Database


RESET_CONFIRMATION = "APAGAR TUDO E REINICIAR"


def reset_password(db_path):
    db = Database(db_path)
    users = db.local_recovery_users()
    if not users:
        print("Nenhuma conta foi encontrada neste banco de dados.")
        return 1
    print("Contas encontradas neste computador:")
    for user in users:
        print(f'- {user["email"]} | {user["name"]} | {user["company_name"]}')
    print("\nRedefinição local de senha")
    email = input("E-mail da conta: ").strip()
    password = getpass("Nova senha (mínimo de 8 caracteres): ")
    confirmation = getpass("Confirme a nova senha: ")
    if password != confirmation:
        print("As senhas não coincidem. Nenhuma alteração foi feita.")
        return 1
    try:
        db.set_password_by_email_for_local_recovery(email, password)
    except ValueError as error:
        print(f"Não foi possível alterar: {error}")
        return 1
    print("Senha alterada com sucesso. Abra a LicitaNexo e entre com o e-mail informado.")
    return 0


def clean_start(db_path):
    print("ATENÇÃO: esta operação inicia um banco vazio.")
    print("Contas, editais, pipeline e solicitações atuais sairão do sistema.")
    print("O banco antigo será guardado automaticamente na pasta data\\backups.")
    confirmation = input(f'Para continuar, digite exatamente: {RESET_CONFIRMATION}\n> ').strip()
    if confirmation != RESET_CONFIRMATION:
        print("Confirmação incorreta. Nenhuma alteração foi feita.")
        return 1

    company = input("Nome da empresa [B2G]: ").strip() or "B2G"
    name = input("Nome do administrador [Ricardo Cruz]: ").strip() or "Ricardo Cruz"
    email = input("E-mail administrador [b2gsolucoesintegradas@gmail.com]: ").strip().lower()
    email = email or "b2gsolucoesintegradas@gmail.com"
    password = getpass("Crie a senha administrativa (mínimo de 8 caracteres): ")
    password_confirmation = getpass("Confirme a senha administrativa: ")
    if password != password_confirmation:
        print("As senhas não coincidem. Nenhuma alteração foi feita.")
        return 1
    if db_path.name != "licitaflow.db":
        print("Caminho do banco inesperado. Operação cancelada por segurança.")
        return 1

    active_sidecars = [Path(str(db_path) + suffix) for suffix in ("-journal", "-wal", "-shm")]
    if any(path.exists() for path in active_sidecars):
        print("O banco parece estar em uso. Feche o Streamlit com Ctrl+C e tente novamente.")
        return 1

    backup_path = None
    if db_path.exists():
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"licitaflow_antes_reinicio_{stamp}.db"
        db_path.replace(backup_path)

    try:
        db = Database(db_path)
        db.register(company, name, email, password)
    except Exception:
        if db_path.exists():
            db_path.unlink()
        if backup_path and backup_path.exists():
            backup_path.replace(db_path)
        print("Não foi possível criar o novo banco. O banco anterior foi restaurado.")
        raise

    print("\nLicitaNexo reiniciada com sucesso.")
    print(f"Empresa: {company}")
    print(f"Administrador: {email}")
    if backup_path:
        print(f"Backup anterior: {backup_path}")
    print("Agora configure LICITANEXO_ADMIN_EMAILS com esse e-mail e inicie o aplicativo.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Administração local de acesso da LicitaNexo")
    parser.add_argument(
        "operation", nargs="?", choices=("reset-password", "clean-start"),
        default="reset-password",
        help="reset-password redefine uma senha; clean-start reinicia todos os dados",
    )
    args = parser.parse_args()
    db_path = database_path(Path(__file__).parent)
    if args.operation == "clean-start":
        return clean_start(db_path)
    return reset_password(db_path)


if __name__ == "__main__":
    raise SystemExit(main())
