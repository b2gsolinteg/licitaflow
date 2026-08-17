from __future__ import annotations

import uuid

from .db_runtime import using_postgres


def _number(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def ensure_sqlite_pricing_schema(db) -> None:
    if using_postgres():
        return
    with db.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS opportunity_item_suppliers (
                id TEXT PRIMARY KEY,
                quote_item_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                company_id TEXT NOT NULL,
                supplier_name TEXT NOT NULL,
                unit_cost REAL NOT NULL DEFAULT 0,
                freight_unit REAL NOT NULL DEFAULT 0,
                taxes_unit REAL NOT NULL DEFAULT 0,
                other_unit_costs REAL NOT NULL DEFAULT 0,
                lead_time_days INTEGER,
                notes TEXT NOT NULL DEFAULT '',
                is_selected INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(quote_item_id) REFERENCES opportunity_quote_items(id) ON DELETE CASCADE,
                FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_item_suppliers_item ON opportunity_item_suppliers(company_id, quote_item_id, unit_cost)"
        )


def list_suppliers(db, company_id: str, quote_item_id: str) -> list[dict]:
    ensure_sqlite_pricing_schema(db)
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT * FROM opportunity_item_suppliers
            WHERE company_id=? AND quote_item_id=?
            ORDER BY is_selected DESC, unit_cost ASC, created_at ASC
        """, (company_id, quote_item_id)).fetchall()
    return [dict(row) for row in rows]


def add_supplier(db, company_id: str, quote_item_id: str, supplier_name: str, unit_cost: float,
                 freight_unit: float = 0, taxes_unit: float = 0, other_unit_costs: float = 0,
                 lead_time_days: int | None = None, notes: str = "") -> str:
    supplier_name = str(supplier_name or "").strip()
    if not supplier_name:
        raise ValueError("Informe o fornecedor.")
    if _number(unit_cost) < 0:
        raise ValueError("O preço de custo não pode ser negativo.")
    ensure_sqlite_pricing_schema(db)
    supplier_id = str(uuid.uuid4())
    with db.connect() as conn:
        item = conn.execute(
            "SELECT id, opportunity_id, company_id FROM opportunity_quote_items WHERE id=? AND company_id=?",
            (quote_item_id, company_id),
        ).fetchone()
        if not item:
            raise ValueError("Item de proposta não encontrado.")
        has_selected = conn.execute(
            "SELECT 1 FROM opportunity_item_suppliers WHERE company_id=? AND quote_item_id=? AND is_selected=1 LIMIT 1",
            (company_id, quote_item_id),
        ).fetchone()
        selected = 0 if has_selected else 1
        conn.execute("""
            INSERT INTO opportunity_item_suppliers(
                id, quote_item_id, opportunity_id, company_id, supplier_name,
                unit_cost, freight_unit, taxes_unit, other_unit_costs,
                lead_time_days, notes, is_selected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            supplier_id, quote_item_id, item["opportunity_id"], company_id, supplier_name,
            _number(unit_cost), _number(freight_unit), _number(taxes_unit), _number(other_unit_costs),
            None if lead_time_days in (None, "") else int(lead_time_days), str(notes or "").strip(), selected,
        ))
        if selected:
            conn.execute("""
                UPDATE opportunity_quote_items
                SET supplier=?, unit_cost=?, freight=?, taxes=?, other_costs=?
                WHERE id=? AND company_id=?
            """, (
                supplier_name, _number(unit_cost), _number(freight_unit),
                _number(taxes_unit), _number(other_unit_costs), quote_item_id, company_id,
            ))
    return supplier_id


def select_supplier(db, company_id: str, quote_item_id: str, supplier_id: str) -> None:
    ensure_sqlite_pricing_schema(db)
    with db.connect() as conn:
        supplier = conn.execute("""
            SELECT * FROM opportunity_item_suppliers
            WHERE id=? AND company_id=? AND quote_item_id=?
        """, (supplier_id, company_id, quote_item_id)).fetchone()
        if not supplier:
            raise ValueError("Fornecedor não encontrado para este item.")
        conn.execute(
            "UPDATE opportunity_item_suppliers SET is_selected=0, updated_at=CURRENT_TIMESTAMP WHERE company_id=? AND quote_item_id=?",
            (company_id, quote_item_id),
        )
        conn.execute(
            "UPDATE opportunity_item_suppliers SET is_selected=1, updated_at=CURRENT_TIMESTAMP WHERE id=? AND company_id=?",
            (supplier_id, company_id),
        )
        conn.execute("""
            UPDATE opportunity_quote_items
            SET supplier=?, unit_cost=?, freight=?, taxes=?, other_costs=?
            WHERE id=? AND company_id=?
        """, (
            supplier["supplier_name"], _number(supplier["unit_cost"]),
            _number(supplier["freight_unit"]), _number(supplier["taxes_unit"]),
            _number(supplier["other_unit_costs"]), quote_item_id, company_id,
        ))


def delete_supplier(db, company_id: str, quote_item_id: str, supplier_id: str) -> None:
    ensure_sqlite_pricing_schema(db)
    with db.connect() as conn:
        row = conn.execute(
            "SELECT is_selected FROM opportunity_item_suppliers WHERE id=? AND company_id=? AND quote_item_id=?",
            (supplier_id, company_id, quote_item_id),
        ).fetchone()
        if not row:
            return
        was_selected = bool(row["is_selected"])
        conn.execute(
            "DELETE FROM opportunity_item_suppliers WHERE id=? AND company_id=? AND quote_item_id=?",
            (supplier_id, company_id, quote_item_id),
        )
        if was_selected:
            next_row = conn.execute("""
                SELECT * FROM opportunity_item_suppliers
                WHERE company_id=? AND quote_item_id=?
                ORDER BY unit_cost ASC, created_at ASC LIMIT 1
            """, (company_id, quote_item_id)).fetchone()
            if next_row:
                conn.execute(
                    "UPDATE opportunity_item_suppliers SET is_selected=1, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (next_row["id"],),
                )
                conn.execute("""
                    UPDATE opportunity_quote_items
                    SET supplier=?, unit_cost=?, freight=?, taxes=?, other_costs=?
                    WHERE id=? AND company_id=?
                """, (
                    next_row["supplier_name"], _number(next_row["unit_cost"]),
                    _number(next_row["freight_unit"]), _number(next_row["taxes_unit"]),
                    _number(next_row["other_unit_costs"]), quote_item_id, company_id,
                ))
            else:
                conn.execute("""
                    UPDATE opportunity_quote_items
                    SET supplier='', unit_cost=0, freight=0, taxes=0, other_costs=0
                    WHERE id=? AND company_id=?
                """, (quote_item_id, company_id))


def item_financials(item: dict) -> dict:
    quantity = max(_number(item.get("quantity")), 0)
    edital_price = max(_number(item.get("edital_price")), 0)
    sale_price = max(_number(item.get("sale_price")), 0)
    cost_unit = sum(max(_number(item.get(field)), 0) for field in (
        "unit_cost", "freight", "taxes", "other_costs", "commission",
    ))
    revenue = quantity * sale_price
    total_cost = quantity * cost_unit
    profit = revenue - total_cost
    margin_pct = (profit / revenue * 100) if revenue > 0 else 0.0
    edital_total = quantity * edital_price
    discount_pct = ((edital_price - sale_price) / edital_price * 100) if edital_price > 0 and sale_price > 0 else 0.0
    return {
        "quantity": quantity,
        "edital_price": edital_price,
        "sale_price": sale_price,
        "cost_unit": cost_unit,
        "revenue": revenue,
        "total_cost": total_cost,
        "profit": profit,
        "margin_pct": margin_pct,
        "edital_total": edital_total,
        "discount_pct": discount_pct,
    }


def pricing_summary(items: list[dict]) -> dict:
    values = [item_financials(item) for item in items]
    revenue = sum(row["revenue"] for row in values)
    total_cost = sum(row["total_cost"] for row in values)
    profit = revenue - total_cost
    edital_total = sum(row["edital_total"] for row in values)
    margin_pct = (profit / revenue * 100) if revenue > 0 else 0.0
    return {
        "items": len(items),
        "edital_total": edital_total,
        "revenue": revenue,
        "total_cost": total_cost,
        "profit": profit,
        "margin_pct": margin_pct,
    }
