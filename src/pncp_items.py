from __future__ import annotations

import time
import uuid
from decimal import Decimal, InvalidOperation

import requests

from .db_runtime import using_postgres
from .sources import parse_pncp_control_number


PNCP_DATA_URL = "https://pncp.gov.br/api/pncp/v1"


class PncpItemsError(RuntimeError):
    pass


def _number(value) -> float:
    try:
        return float(Decimal(str(value if value is not None else 0)))
    except (InvalidOperation, ValueError, TypeError):
        return 0.0


def _normalize_item(raw: dict, control_number: str) -> dict:
    number = raw.get("numeroItem") or raw.get("numero") or raw.get("item")
    description = str(raw.get("descricao") or raw.get("descricaoItem") or "").strip()
    complement = str(raw.get("informacaoComplementar") or "").strip()
    if complement and complement.lower() not in description.lower():
        description = f"{description} — {complement}" if description else complement
    quantity = max(_number(raw.get("quantidade")), 0)
    unit = str(raw.get("unidadeMedida") or raw.get("unidade") or "").strip()
    confidential = bool(raw.get("orcamentoSigiloso"))
    unit_price = 0.0 if confidential else max(_number(raw.get("valorUnitarioEstimado")), 0)
    total = 0.0 if confidential else max(_number(raw.get("valorTotal")), 0)
    if unit_price <= 0 and quantity > 0 and total > 0:
        unit_price = total / quantity
    return {
        "number": str(number or "").strip(),
        "description": description or f"Item {number or ''}".strip(),
        "quantity": quantity or 1.0,
        "unit_measure": unit,
        "unit_price": unit_price,
        "total": total,
        "confidential": confidential,
        "material_or_service": str(raw.get("materialOuServicoNome") or "").strip(),
        "judgment": str(raw.get("criterioJulgamentoNome") or "").strip(),
        "catalog_code": str(raw.get("catalogoCodigoItem") or "").strip(),
        "source_reference": f"pncp:{control_number}:{number}",
    }


def fetch_contract_items(control_number: str, *, timeout: int = 20, page_size: int = 200, session=None) -> list[dict]:
    parsed = parse_pncp_control_number(control_number)
    if not parsed:
        raise PncpItemsError("Este edital não possui um número de controle PNCP válido para consultar os itens oficiais.")
    cnpj, year, sequence = parsed
    client = session or requests.Session()
    if session is None:
        client.headers.update({
            "User-Agent": "LicitaNexo/1.0 (+b2gsolucoesintegradas@gmail.com)",
            "Accept": "application/json",
        })
    endpoint = f"{PNCP_DATA_URL}/orgaos/{cnpj}/compras/{year}/{sequence}/itens"
    result: list[dict] = []
    seen = set()
    page = 1
    size = max(10, min(int(page_size), 500))

    while page <= 50:
        response = None
        last_error = None
        for attempt in range(3):
            try:
                response = client.get(
                    endpoint,
                    params={"pagina": page, "tamanhoPagina": size},
                    timeout=timeout,
                )
                if response.status_code == 204:
                    return result
                if response.status_code in {429, 500, 502, 503, 504}:
                    last_error = f"PNCP respondeu {response.status_code}"
                    time.sleep(min(2 ** attempt, 4))
                    continue
                response.raise_for_status()
                break
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                last_error = str(exc)
                if attempt < 2:
                    time.sleep(min(2 ** attempt, 4))
        if response is None or response.status_code >= 400:
            raise PncpItemsError(f"Não foi possível consultar os itens oficiais no PNCP. {last_error or ''}".strip())

        try:
            payload = response.json()
        except ValueError as exc:
            raise PncpItemsError("O PNCP retornou uma resposta de itens em formato inesperado.") from exc

        if isinstance(payload, list):
            raw_items = payload
            total_pages = 1
        elif isinstance(payload, dict):
            raw_items = payload.get("itens") or payload.get("data") or payload.get("items") or []
            total_pages = int(payload.get("totalPaginas") or payload.get("totalPages") or 0)
        else:
            raw_items = []
            total_pages = 0

        if not isinstance(raw_items, list):
            raise PncpItemsError("O PNCP não devolveu a lista de itens no formato esperado.")
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            normalized = _normalize_item(raw, control_number)
            key = normalized["source_reference"]
            if key in seen:
                continue
            seen.add(key)
            result.append(normalized)

        if total_pages and page >= total_pages:
            break
        if not total_pages and len(raw_items) < size:
            break
        if not raw_items:
            break
        page += 1
    return result



def fetch_contract_items_preview(
    control_number: str,
    *,
    limit: int = 4,
    timeout: int = 7,
    session=None,
) -> dict:
    """Busca apenas a primeira página de itens para cards de pesquisa rápida.

    Diferente de ``fetch_contract_items``, esta função não percorre todas as páginas.
    O objetivo é manter o Radar responsivo e exibir um resumo oficial do PNCP antes
    de o usuário decidir abrir ou salvar a oportunidade.
    """
    parsed = parse_pncp_control_number(control_number)
    if not parsed:
        raise PncpItemsError("Número de controle PNCP inválido para consultar os itens.")
    cnpj, year, sequence = parsed
    client = session or requests.Session()
    if session is None:
        client.headers.update({
            "User-Agent": "LicitaNexo/1.0 (+b2gsolucoesintegradas@gmail.com)",
            "Accept": "application/json",
        })
    endpoint = f"{PNCP_DATA_URL}/orgaos/{cnpj}/compras/{year}/{sequence}/itens"
    size = max(1, min(int(limit or 4), 20))
    response = None
    last_error = None

    # Preview não pode transformar a busca em uma espera longa. Faz no máximo
    # uma repetição curta para erros transitórios e devolve falha isolada por card.
    for attempt in range(2):
        try:
            response = client.get(
                endpoint,
                params={"pagina": 1, "tamanhoPagina": size},
                timeout=max(2, int(timeout)),
            )
            if response.status_code == 204:
                return {
                    "items": [], "item_count": 0, "count_known": True,
                    "has_more": False, "items_error": "",
                }
            if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                last_error = f"PNCP respondeu {response.status_code}"
                time.sleep(0.35)
                continue
            response.raise_for_status()
            break
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            last_error = str(exc)
            if attempt == 0:
                time.sleep(0.25)

    if response is None or response.status_code >= 400:
        raise PncpItemsError(
            f"Itens temporariamente indisponíveis no PNCP. {last_error or ''}".strip()
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise PncpItemsError("O PNCP retornou os itens em formato inesperado.") from exc

    total_value = None
    if isinstance(payload, list):
        raw_items = payload
        total_value = len(raw_items)
    elif isinstance(payload, dict):
        raw_items = payload.get("itens") or payload.get("data") or payload.get("items") or []
        for key in (
            "totalRegistros", "totalElementos", "totalItems", "total",
            "quantidadeRegistros", "totalCount",
        ):
            if payload.get(key) is not None:
                total_value = payload.get(key)
                break
    else:
        raw_items = []

    if not isinstance(raw_items, list):
        raise PncpItemsError("O PNCP não devolveu a lista de itens no formato esperado.")

    normalized = []
    seen = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        item = _normalize_item(raw, control_number)
        if item["source_reference"] in seen:
            continue
        seen.add(item["source_reference"])
        normalized.append(item)
        if len(normalized) >= size:
            break

    count_known = total_value is not None
    try:
        total = max(int(total_value), len(normalized)) if count_known else len(normalized)
    except (TypeError, ValueError):
        total = len(normalized)
        count_known = False
    has_more = total > len(normalized) if count_known else len(raw_items) >= size
    return {
        "items": normalized,
        "item_count": total,
        "count_known": count_known,
        "has_more": has_more,
        "items_error": "",
    }


def fetch_contract_documents(control_number: str, *, timeout: int = 20, session=None) -> list[dict]:
    parsed = parse_pncp_control_number(control_number)
    if not parsed:
        return []
    cnpj, year, sequence = parsed
    client = session or requests.Session()
    if session is None:
        client.headers.update({
            "User-Agent": "LicitaNexo/1.0 (+b2gsolucoesintegradas@gmail.com)",
            "Accept": "application/json",
        })
    endpoint = f"{PNCP_DATA_URL}/orgaos/{cnpj}/compras/{year}/{sequence}/arquivos"
    try:
        response = client.get(endpoint, timeout=timeout)
        if response.status_code == 204:
            return []
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise PncpItemsError(f"Não foi possível consultar os documentos oficiais do PNCP: {exc}") from exc
    raw_documents = payload if isinstance(payload, list) else (
        payload.get("documentos") or payload.get("data") or payload.get("arquivos") or []
        if isinstance(payload, dict) else []
    )
    documents = []
    for raw in raw_documents:
        if not isinstance(raw, dict):
            continue
        url = str(raw.get("url") or raw.get("urlDocumento") or "").strip()
        documents.append({
            "title": str(raw.get("titulo") or raw.get("nome") or raw.get("tipoDocumentoNome") or "Documento").strip(),
            "type": str(raw.get("tipoDocumentoNome") or "").strip(),
            "url": url,
            "published_at": str(raw.get("dataPublicacaoPncp") or raw.get("dataPublicacao") or "").strip(),
        })
    return documents


def ensure_sqlite_quote_source_schema(db) -> None:
    if using_postgres():
        return
    with db.connect() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(opportunity_quote_items)").fetchall()}
        additions = {
            "unit_measure": "TEXT NOT NULL DEFAULT ''",
            "source_kind": "TEXT NOT NULL DEFAULT 'manual'",
            "source_reference": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE opportunity_quote_items ADD COLUMN {name} {definition}")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_quote_items_source ON opportunity_quote_items(company_id, opportunity_id, source_reference)"
        )


def import_contract_items(db, company_id: str, opportunity_id: str, control_number: str, items: list[dict]) -> dict:
    ensure_sqlite_quote_source_schema(db)
    imported = 0
    skipped = 0
    confidential = 0
    with db.connect() as conn:
        opportunity = conn.execute(
            "SELECT id FROM opportunities WHERE id=? AND company_id=?",
            (opportunity_id, company_id),
        ).fetchone()
        if not opportunity:
            raise ValueError("Edital não encontrado para esta empresa.")
        existing = {
            str(row["source_reference"] or "")
            for row in conn.execute(
                "SELECT source_reference FROM opportunity_quote_items WHERE company_id=? AND opportunity_id=?",
                (company_id, opportunity_id),
            ).fetchall()
            if str(row["source_reference"] or "")
        }
        for item in items:
            reference = str(item.get("source_reference") or "").strip()
            if reference and reference in existing:
                skipped += 1
                continue
            if item.get("confidential"):
                confidential += 1
            conn.execute("""
                INSERT INTO opportunity_quote_items(
                    id, opportunity_id, company_id, description, quantity,
                    unit_cost, freight, taxes, other_costs, sale_price, supplier,
                    lot_number, edital_price, commission, unit_measure, source_kind, source_reference
                ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, 0, '', ?, ?, 0, ?, 'pncp', ?)
            """, (
                str(uuid.uuid4()), opportunity_id, company_id,
                str(item.get("description") or "Item PNCP").strip()[:4000],
                max(_number(item.get("quantity")), 0.0001),
                str(item.get("number") or "").strip()[:80],
                max(_number(item.get("unit_price")), 0),
                str(item.get("unit_measure") or "").strip()[:80],
                reference,
            ))
            if reference:
                existing.add(reference)
            imported += 1
    return {"imported": imported, "skipped": skipped, "confidential": confidential}
