from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortalAccess:
    label: str
    tone: str
    detail: str
    verified_at: str = "2026-08-17"


# Cadastro conservador. Quando o custo depende de modalidade, plano ou êxito,
# o LicitaNexo não simplifica para apenas "grátis" ou "pago".
PORTAL_ACCESS = {
    "Compras.gov": PortalAccess(
        label="Gratuito",
        tone="free",
        detail="Cadastro/SICAF e participação no ambiente federal sem taxa do portal.",
    ),
    "BLL Compras": PortalAccess(
        label="Cadastro grátis · pode haver cobrança",
        tone="conditional",
        detail="A BLL oferece cadastro sem custo com cobrança por êxito ou plano periódico.",
    ),
    "BNC Compras": PortalAccess(
        label="Cadastro grátis · participação com plano",
        tone="paid",
        detail="O cadastro é gratuito; a participação exige plano/cobrança da plataforma.",
    ),
    "Portal de Compras Públicas": PortalAccess(
        label="Cadastro básico grátis · planos disponíveis",
        tone="conditional",
        detail="Há acesso básico gratuito, mas participações/serviços podem depender do plano.",
    ),
    "LicitaNET": PortalAccess(
        label="Participação com plano",
        tone="paid",
        detail="A plataforma comercializa planos de acesso para fornecedores participarem.",
    ),
    "BBMNET": PortalAccess(
        label="Participação com cobrança",
        tone="paid",
        detail="O fornecedor escolhe plano periódico ou modalidade/edital para participar.",
    ),
}


def portal_access_info(portal_name: str | None) -> PortalAccess:
    name = str(portal_name or "").strip()
    if name in PORTAL_ACCESS:
        return PORTAL_ACCESS[name]
    return PortalAccess(
        label="Verificar condições",
        tone="unknown",
        detail="O LicitaNexo ainda não confirmou publicamente as condições deste portal.",
    )
