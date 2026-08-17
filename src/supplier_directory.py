from __future__ import annotations

import uuid
from collections import defaultdict

from .db_runtime import using_postgres


def ensure_sqlite_supplier_schema(db) -> None:
    if using_postgres():
        return
    with db.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS company_suppliers (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL,
                name TEXT NOT NULL,
                cnpj TEXT NOT NULL DEFAULT '',
                contact_name TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL DEFAULT '',
                payment_terms TEXT NOT NULL DEFAULT '',
                default_lead_time_days INTEGER,
                notes TEXT NOT NULL DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_id, name),
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_company_suppliers_company ON company_suppliers(company_id, active, name)"
        )


def list_company_suppliers(db, company_id: str, *, active_only: bool = True) -> list[dict]:
    ensure_sqlite_supplier_schema(db)
    where = " AND active=1" if active_only else ""
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM company_suppliers WHERE company_id=?{where} ORDER BY name COLLATE NOCASE",
            (company_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_company_supplier(db, company_id: str, supplier_id: str) -> dict | None:
    ensure_sqlite_supplier_schema(db)
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM company_suppliers WHERE company_id=? AND id=?",
            (company_id, supplier_id),
        ).fetchone()
    return dict(row) if row else None


def save_company_supplier(
    db,
    company_id: str,
    name: str,
    *,
    supplier_id: str | None = None,
    cnpj: str = "",
    contact_name: str = "",
    phone: str = "",
    email: str = "",
    city: str = "",
    state: str = "",
    payment_terms: str = "",
    default_lead_time_days: int | None = None,
    notes: str = "",
    active: bool = True,
) -> str:
    ensure_sqlite_supplier_schema(db)
    clean_name = " ".join(str(name or "").split()).strip()
    if not clean_name:
        raise ValueError("Informe o nome do fornecedor.")
    clean_state = str(state or "").strip().upper()[:2]
    clean_email = str(email or "").strip().lower()
    lead_time = None if default_lead_time_days in (None, "") else max(int(default_lead_time_days), 0)

    with db.connect() as conn:
        if supplier_id:
            existing = conn.execute(
                "SELECT id FROM company_suppliers WHERE company_id=? AND id=?",
                (company_id, supplier_id),
            ).fetchone()
            if not existing:
                raise ValueError("Fornecedor não encontrado.")
            conn.execute("""
                UPDATE company_suppliers
                SET name=?, cnpj=?, contact_name=?, phone=?, email=?, city=?, state=?,
                    payment_terms=?, default_lead_time_days=?, notes=?, active=?, updated_at=CURRENT_TIMESTAMP
                WHERE company_id=? AND id=?
            """, (
                clean_name, str(cnpj or "").strip(), str(contact_name or "").strip(),
                str(phone or "").strip(), clean_email, str(city or "").strip(), clean_state,
                str(payment_terms or "").strip(), lead_time, str(notes or "").strip(),
                1 if active else 0, company_id, supplier_id,
            ))
            return supplier_id

        by_name = conn.execute(
            "SELECT id FROM company_suppliers WHERE company_id=? AND LOWER(name)=LOWER(?) LIMIT 1",
            (company_id, clean_name),
        ).fetchone()
        if by_name:
            supplier_id = by_name["id"]
            conn.execute("""
                UPDATE company_suppliers
                SET cnpj=CASE WHEN ?<>'' THEN ? ELSE cnpj END,
                    contact_name=CASE WHEN ?<>'' THEN ? ELSE contact_name END,
                    phone=CASE WHEN ?<>'' THEN ? ELSE phone END,
                    email=CASE WHEN ?<>'' THEN ? ELSE email END,
                    city=CASE WHEN ?<>'' THEN ? ELSE city END,
                    state=CASE WHEN ?<>'' THEN ? ELSE state END,
                    payment_terms=CASE WHEN ?<>'' THEN ? ELSE payment_terms END,
                    default_lead_time_days=COALESCE(?, default_lead_time_days),
                    notes=CASE WHEN ?<>'' THEN ? ELSE notes END,
                    active=1, updated_at=CURRENT_TIMESTAMP
                WHERE company_id=? AND id=?
            """, (
                str(cnpj or "").strip(), str(cnpj or "").strip(),
                str(contact_name or "").strip(), str(contact_name or "").strip(),
                str(phone or "").strip(), str(phone or "").strip(),
                clean_email, clean_email,
                str(city or "").strip(), str(city or "").strip(),
                clean_state, clean_state,
                str(payment_terms or "").strip(), str(payment_terms or "").strip(),
                lead_time,
                str(notes or "").strip(), str(notes or "").strip(),
                company_id, supplier_id,
            ))
            return supplier_id

        supplier_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO company_suppliers(
                id, company_id, name, cnpj, contact_name, phone, email, city, state,
                payment_terms, default_lead_time_days, notes, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            supplier_id, company_id, clean_name, str(cnpj or "").strip(),
            str(contact_name or "").strip(), str(phone or "").strip(), clean_email,
            str(city or "").strip(), clean_state, str(payment_terms or "").strip(),
            lead_time, str(notes or "").strip(), 1 if active else 0,
        ))
        return supplier_id


def ensure_company_supplier(db, company_id: str, name: str, **fields) -> str:
    return save_company_supplier(db, company_id, name, **fields)


def set_company_supplier_active(db, company_id: str, supplier_id: str, active: bool) -> None:
    ensure_sqlite_supplier_schema(db)
    with db.connect() as conn:
        result = conn.execute(
            "UPDATE company_suppliers SET active=?, updated_at=CURRENT_TIMESTAMP WHERE company_id=? AND id=?",
            (1 if active else 0, company_id, supplier_id),
        )
        if result.rowcount == 0:
            raise ValueError("Fornecedor não encontrado.")


def list_opportunity_supplier_quotes(db, company_id: str, opportunity_id: str) -> dict[str, list[dict]]:
    """Busca todas as cotações do edital em uma única ida ao banco, evitando N+1."""
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT * FROM opportunity_item_suppliers
            WHERE company_id=? AND opportunity_id=?
            ORDER BY quote_item_id, is_selected DESC, unit_cost ASC, created_at ASC
        """, (company_id, opportunity_id)).fetchall()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        item = dict(row)
        grouped[str(item["quote_item_id"])].append(item)
    return dict(grouped)


def recent_supplier_quotes(db, company_id: str, supplier_name: str, limit: int = 8) -> list[dict]:
    clean_name = " ".join(str(supplier_name or "").split()).strip()
    if not clean_name:
        return []
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT s.*, q.description, q.lot_number, o.agency, o.pncp_control_number
            FROM opportunity_item_suppliers s
            JOIN opportunity_quote_items q ON q.id=s.quote_item_id AND q.company_id=s.company_id
            JOIN opportunities o ON o.id=s.opportunity_id AND o.company_id=s.company_id
            WHERE s.company_id=? AND LOWER(s.supplier_name)=LOWER(?)
            ORDER BY s.created_at DESC
            LIMIT ?
        """, (company_id, clean_name, max(1, min(int(limit), 50)))).fetchall()
    return [dict(row) for row in rows]
