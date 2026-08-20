from __future__ import annotations

import math
import statistics
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable

from .db_runtime import using_postgres
from .mei_portals import portal_access_info
from .pncp_items import PncpItemsError, fetch_contract_items
from .public_prices import ComprasGovPriceClient, PublicPriceError, normalize_brand
from .sources import opportunity_source_and_portal, pncp_official_url


BRAZIL_REGIONS = {
    "Norte": ("AC", "AP", "AM", "PA", "RO", "RR", "TO"),
    "Nordeste": ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"),
    "Centro-Oeste": ("DF", "GO", "MT", "MS"),
    "Sudeste": ("ES", "MG", "RJ", "SP"),
    "Sul": ("PR", "RS", "SC"),
}

BRAZIL_STATES = tuple(sorted({state for states in BRAZIL_REGIONS.values() for state in states}))

CATEGORY_RULES = {
    "Alimentos e bebidas": ("alimento", "cafe", "café", "agua mineral", "água mineral", "leite", "carne", "fruta", "hortifruti"),
    "Limpeza e higiene": ("limpeza", "detergente", "desinfetante", "papel toalha", "higiene", "sabonete", "alcool", "álcool"),
    "Papelaria e escritório": ("papel", "caneta", "escritorio", "escritório", "toner", "cartucho", "pasta", "expediente"),
    "Construção e materiais": ("construcao", "construção", "cimento", "tijolo", "tinta", "hidraul", "eletric", "ferragem"),
    "Informática": ("computador", "notebook", "informatica", "informática", "impressora", "software", "monitor"),
    "Uniformes e vestuário": ("uniforme", "camiseta", "vestuario", "vestuário", "calcado", "calçado", "tecido"),
    "Saúde": ("medicamento", "hospital", "saude", "saúde", "seringa", "luva", "curativo", "farmac"),
    "Ferramentas": ("ferramenta", "furadeira", "parafusadeira", "chave", "broca", "alicate"),
    "Artesanato": ("artesanato", "barbante", "cola branca", "guache", "eva", "linha", "tecido"),
}


def states_for_region(region: str | None) -> tuple[str, ...]:
    return BRAZIL_REGIONS.get(str(region or "").strip(), ())


def infer_category(text: str | None) -> str:
    normalized = str(text or "").casefold()
    for category, terms in CATEGORY_RULES.items():
        if any(term.casefold() in normalized for term in terms):
            return category
    return "Outros"


def _dict_rows(rows) -> list[dict]:
    return [dict(row) for row in rows]


class MeiCatalogService:
    """Consulta enxuta sobre o catálogo global já sincronizado pelo LicitaNexo Pro."""

    def __init__(self, db):
        self.db = db

    def search(
        self,
        *,
        region: str = "",
        states: Iterable[str] | None = None,
        city: str = "",
        modalities: Iterable[str] | None = None,
        keyword: str = "",
        limit: int = 120,
    ) -> list[dict]:
        selected_states = {str(value).strip().upper() for value in (states or []) if str(value).strip()}
        selected_states.update(states_for_region(region))
        selected_states.intersection_update(BRAZIL_STATES)
        selected_modalities = [str(value).strip() for value in (modalities or []) if str(value).strip()]
        city = str(city or "").strip()
        keyword = str(keyword or "").strip()
        clauses = ["(closing_at IS NULL OR closing_at >= ?)"]
        now = datetime.now(timezone.utc)
        params: list[object] = [now if using_postgres() else now.isoformat(timespec="seconds")]

        if selected_states:
            placeholders = ",".join("?" for _ in selected_states)
            clauses.append(f"state IN ({placeholders})")
            params.extend(sorted(selected_states))
        if city:
            clauses.append("search_fold(city) LIKE ?")
            params.append(f"%{self.db._search_fold(city)}%")
        if selected_modalities:
            placeholders = ",".join("?" for _ in selected_modalities)
            clauses.append(f"modality IN ({placeholders})")
            params.extend(selected_modalities)
        if keyword:
            terms = [part.strip() for part in keyword.replace(";", ",").split(",") if part.strip()]
            if terms:
                keyword_clauses = []
                for term in terms[:6]:
                    keyword_clauses.append(
                        "(search_fold(object) LIKE ? OR search_fold(agency) LIKE ? OR search_fold(city) LIKE ?)"
                    )
                    folded = f"%{self.db._search_fold(term)}%"
                    params.extend((folded, folded, folded))
                clauses.append("(" + " OR ".join(keyword_clauses) + ")")

        sql = f"""
            SELECT id, pncp_control_number, agency, city, state, modality,
                   published_at, opening_at, closing_at, object, estimated_value,
                   source_url, srp, source_name, source_channel
              FROM global_pncp_catalog
             WHERE {' AND '.join(clauses)}
             ORDER BY CASE WHEN closing_at IS NULL THEN 1 ELSE 0 END,
                      closing_at ASC, published_at DESC
             LIMIT ?
        """
        params.append(max(1, min(int(limit), 500)))
        with self.db.connect() as conn:
            rows = _dict_rows(conn.execute(sql, tuple(params)).fetchall())
        for row in rows:
            row["category"] = infer_category(row.get("object"))
            source, portal = opportunity_source_and_portal(
                row.get("source_name"), row.get("source_channel"), row.get("source_url")
            )
            access = portal_access_info(portal)
            row.update({
                "source_label": source,
                "portal": portal,
                "portal_access": access.label,
                "portal_access_tone": access.tone,
                "portal_access_detail": access.detail,
                "portal_verified_at": access.verified_at,
                "pncp_url": pncp_official_url(row.get("pncp_control_number")),
            })
        return rows

    def counts_by_state(self) -> dict[str, int]:
        now = datetime.now(timezone.utc)
        value = now if using_postgres() else now.isoformat(timespec="seconds")
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT state, COUNT(*) AS total
                  FROM global_pncp_catalog
                 WHERE (closing_at IS NULL OR closing_at >= ?)
                   AND state <> ''
                 GROUP BY state
                 ORDER BY state
                """,
                (value,),
            ).fetchall()
        return {str(row["state"]): int(row["total"] or 0) for row in rows}

    def counts_by_region(self) -> dict[str, int]:
        state_counts = self.counts_by_state()
        return {
            region: sum(state_counts.get(state, 0) for state in states)
            for region, states in BRAZIL_REGIONS.items()
        }


def enrich_with_items(
    opportunities: list[dict],
    *,
    fetcher: Callable[[str], list[dict]] = fetch_contract_items,
    max_workers: int = 4,
    max_items: int = 5,
) -> list[dict]:
    """Busca itens apenas para a página visível, em paralelo e sem quebrar a busca."""
    result = [dict(item) for item in opportunities]
    by_control = {
        str(item.get("pncp_control_number") or ""): item
        for item in result
        if str(item.get("pncp_control_number") or "")
    }
    if not by_control:
        return result

    with ThreadPoolExecutor(max_workers=max(1, min(int(max_workers), 6))) as executor:
        futures = {executor.submit(fetcher, control): control for control in by_control}
        for future in as_completed(futures):
            control = futures[future]
            target = by_control[control]
            try:
                items = future.result() or []
                target["items"] = items[: max(1, int(max_items))]
                target["item_count"] = len(items)
                target["items_error"] = ""
                if target["category"] == "Outros" and items:
                    target["category"] = infer_category(" ".join(str(row.get("description") or "") for row in items))
            except (PncpItemsError, RuntimeError, ValueError) as exc:
                target["items"] = []
                target["item_count"] = 0
                target["items_error"] = str(exc)
            except Exception:
                target["items"] = []
                target["item_count"] = 0
                target["items_error"] = "Itens temporariamente indisponíveis."
    return result


def _valid_prices(rows: Iterable[dict]) -> list[dict]:
    valid = []
    for row in rows:
        try:
            price = float(row.get("homologated_unit_value") or 0)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(price) or price <= 0:
            continue
        item = dict(row)
        item["homologated_unit_value"] = price
        valid.append(item)
    return valid


def summarize_price_history(rows: Iterable[dict]) -> dict:
    valid = _valid_prices(rows)
    prices = [row["homologated_unit_value"] for row in valid]
    if not prices:
        return {
            "count": 0,
            "average": None,
            "median": None,
            "minimum": None,
            "maximum": None,
            "last_price": None,
            "last_date": None,
            "brands": [],
            "suppliers": [],
            "rows": [],
        }

    dated = sorted(valid, key=lambda row: str(row.get("published_at") or ""), reverse=True)
    brand_counter = Counter(
        normalize_brand(row.get("brand"))
        for row in valid
        if normalize_brand(row.get("brand")) != "Não informada"
    )
    supplier_counter = Counter(
        str(row.get("supplier") or "").strip()
        for row in valid
        if str(row.get("supplier") or "").strip()
    )
    latest = dated[0]
    return {
        "count": len(prices),
        "average": statistics.fmean(prices),
        "median": statistics.median(prices),
        "minimum": min(prices),
        "maximum": max(prices),
        "last_price": latest["homologated_unit_value"],
        "last_date": latest.get("published_at"),
        "brands": [{"name": name, "count": count} for name, count in brand_counter.most_common(6)],
        "suppliers": [{"name": name, "count": count} for name, count in supplier_counter.most_common(6)],
        "rows": dated,
    }


def fetch_price_history_for_item(
    item: dict,
    *,
    state: str = "",
    months: int = 18,
    client: ComprasGovPriceClient | None = None,
) -> dict:
    """Consulta histórico homologado oficial no Compras.gov sob demanda."""
    price_client = client or ComprasGovPriceClient(timeout=35)
    catalog_code = str(item.get("catalog_code") or "").strip()
    catalog_description = str(item.get("description") or "").strip()
    catalog_source = "PNCP"

    if not catalog_code and catalog_description:
        candidates = price_client.search_catalog(catalog_description[:120], kind="Material", limit=8)
        if candidates:
            catalog_code = str(candidates[0].get("code") or "").strip()
            catalog_description = str(candidates[0].get("description") or catalog_description)
            catalog_source = str(candidates[0].get("catalog_source") or "Compras.gov")

    if not catalog_code:
        return {
            "available": False,
            "reason": "Este item não possui código CATMAT/CATSER suficiente para consultar preços históricos automaticamente.",
            "catalog_code": "",
            "catalog_description": catalog_description,
            "summary": summarize_price_history([]),
        }

    start = date.today() - timedelta(days=max(1, int(months)) * 30)
    try:
        rows = price_client.fetch_prices(
            catalog_code,
            state=str(state or "").upper(),
            kind="Material",
            start_date=start.isoformat(),
            max_pages=12,
        )
    except PublicPriceError as exc:
        return {
            "available": False,
            "reason": str(exc),
            "catalog_code": catalog_code,
            "catalog_description": catalog_description,
            "catalog_source": catalog_source,
            "summary": summarize_price_history([]),
        }
    return {
        "available": bool(rows),
        "reason": "" if rows else "Nenhuma compra homologada recente foi encontrada para este código.",
        "catalog_code": catalog_code,
        "catalog_description": catalog_description,
        "catalog_source": catalog_source,
        "summary": summarize_price_history(rows),
    }
