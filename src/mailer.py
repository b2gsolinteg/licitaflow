import os
import smtplib
import ssl
from email.message import EmailMessage


class MailError(RuntimeError):
    pass


def mail_config():
    return {
        "host": os.getenv("LICITANEXO_SMTP_HOST", "").strip(),
        "port": int(os.getenv("LICITANEXO_SMTP_PORT", "587") or 587),
        "user": os.getenv("LICITANEXO_SMTP_USER", "").strip(),
        "password": os.getenv("LICITANEXO_SMTP_PASSWORD", ""),
        "from_email": os.getenv("LICITANEXO_FROM_EMAIL", "").strip(),
        "from_name": os.getenv("LICITANEXO_FROM_NAME", "B2G SaaS").strip() or "B2G SaaS",
        "use_tls": os.getenv("LICITANEXO_SMTP_TLS", "1").strip().lower() in {"1", "true", "yes", "sim"},
        "app_url": os.getenv("LICITANEXO_APP_URL", "").strip().rstrip("/"),
    }


def is_configured():
    cfg = mail_config()
    return bool(cfg["host"] and cfg["user"] and cfg["password"] and cfg["from_email"])


def _send(to_email, subject, text):
    cfg = mail_config()
    if not is_configured():
        raise MailError("O envio de e-mail ainda não foi configurado.")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f'{cfg["from_name"]} <{cfg["from_email"]}>'
    msg["To"] = to_email
    msg.set_content(text)
    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as smtp:
            if cfg["use_tls"]:
                smtp.starttls(context=ssl.create_default_context())
            smtp.login(cfg["user"], cfg["password"])
            smtp.send_message(msg)
    except Exception as exc:
        raise MailError(f"Falha ao enviar e-mail: {exc}") from exc


def send_invitation(to_email, name, code, trial_days):
    cfg = mail_config()
    activation_hint = (
        f'Abra {cfg["app_url"]} e escolha “Ativar convite”.\n\n' if cfg["app_url"] else
        'Abra o LicitaNexo e escolha “Ativar convite”.\n\n'
    )
    text = (
        f"Olá, {name}.\n\n"
        "Sua solicitação de acesso ao LicitaNexo foi aprovada pela B2G SaaS.\n\n"
        f"{activation_hint}"
        f"Código de ativação: {code}\n"
        f"Período de teste: {trial_days} dia(s).\n\n"
        "Você criará sua própria senha durante a ativação. A B2G SaaS nunca envia senhas por e-mail.\n\n"
        "LicitaNexo — seu departamento de licitações em um único lugar.\n"
        "B2G SaaS · Business to Growth"
    )
    _send(to_email, "Seu acesso ao LicitaNexo foi aprovado", text)


def send_recovery_code(to_email, name, code):
    cfg = mail_config()
    recovery_hint = (
        f'Abra {cfg["app_url"]} e escolha “Recuperar senha”.\n\n' if cfg["app_url"] else
        'Abra o LicitaNexo e escolha “Recuperar senha”.\n\n'
    )
    text = (
        f"Olá, {name}.\n\n"
        "Recebemos uma solicitação para redefinir a senha da sua conta LicitaNexo.\n\n"
        f"{recovery_hint}"
        f"Código de recuperação: {code}\n"
        "O código expira em 30 minutos.\n\n"
        "Se você não solicitou a redefinição, ignore esta mensagem.\n\n"
        "B2G SaaS · Business to Growth"
    )
    _send(to_email, "Recuperação de senha · LicitaNexo", text)


def send_test_email(to_email):
    _send(
        to_email,
        "Teste de e-mail · LicitaNexo",
        "Configuração de e-mail validada com sucesso.\n\nB2G SaaS · Business to Growth",
    )
