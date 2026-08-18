from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from .pncp_items import PncpItemsError, fetch_contract_items_preview


def fetch_radar_item_summaries(
    control_numbers,
    *,
    max_workers: int = 4,
    preview_items: int = 20,
    fetcher=fetch_contract_items_preview,
) -> dict[str, dict]:
    """Busca até 20 itens por oportunidade em paralelo sem deixar uma falha quebrar a pesquisa.

    O Essential privilegia leitura rápida no próprio resultado. A chamada continua limitada à
    primeira página de cada contratação; listas maiores só são carregadas quando o usuário pede.
    """
    controls = list(dict.fromkeys(
        str(value or "").strip() for value in control_numbers if str(value or "").strip()
    ))
    result = {
        control: {
            "items": [], "item_count": 0, "count_known": False,
            "has_more": False, "items_error": "",
        }
        for control in controls
    }
    if not controls:
        return result

    preview_items = max(1, min(int(preview_items or 20), 20))
    workers = max(1, min(int(max_workers or 1), 6, len(controls)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(fetcher, control, limit=preview_items): control
            for control in controls
        }
        for future in as_completed(futures):
            control = futures[future]
            try:
                pack = future.result() or {}
                result[control] = {
                    "items": list(pack.get("items") or [])[:preview_items],
                    "item_count": int(pack.get("item_count") or 0),
                    "count_known": bool(pack.get("count_known")),
                    "has_more": bool(pack.get("has_more")),
                    "items_error": str(pack.get("items_error") or ""),
                }
            except (PncpItemsError, RuntimeError, ValueError) as exc:
                result[control]["items_error"] = str(exc)
            except Exception:
                result[control]["items_error"] = "Itens temporariamente indisponíveis."
    return result
