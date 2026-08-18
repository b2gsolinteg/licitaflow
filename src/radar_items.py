from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from .pncp_items import PncpItemsError, fetch_contract_items_preview


def fetch_radar_item_summaries(
    control_numbers,
    *,
    max_workers: int = 6,
    preview_items: int = 4,
    fetcher=fetch_contract_items_preview,
) -> dict[str, dict]:
    """Busca previews dos itens em paralelo sem deixar uma falha quebrar o Radar."""
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

    workers = max(1, min(int(max_workers or 1), 8, len(controls)))
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
                    "items": list(pack.get("items") or [])[: max(1, int(preview_items))],
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
