from __future__ import annotations

import uuid

from .db_runtime import using_postgres
from .pricing import item_financials


DEFAULT_STEPS = (
    ("analysis", "Analisar edital e anexos", 10),
    ("documents", "Conferir documentação exigida", 20),
    ("suppliers", "Cotar todos os itens", 30),
    ("pricing", "Definir preço de participação", 40),
    ("margin", "Revisar margem, frete, impostos e riscos", 50),
    ("proposal", "Preparar proposta e declarações", 60),
    ("submit", "Enviar proposta no portal", 70),
    ("session", "Acompanhar sessão / disputa", 80),
)


def ensure_sqlite_journey_schema(db) -> None:
    if using_postgres():
        return
    with db.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS opportunity_journey_steps (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL,
                opportunity_id TEXT NOT NULL,
                step_key TEXT NOT NULL,
                title TEXT NOT NULL,
                is_done INTEGER NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_id, opportunity_id, step_key),
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_opportunity_journey_company ON opportunity_journey_steps(company_id, opportunity_id, sort_order)"
        )


def ensure_journey(db, company_id: str, opportunity_id: str) -> None:
    ensure_sqlite_journey_schema(db)
    with db.connect() as conn:
        for step_key, title, sort_order in DEFAULT_STEPS:
            conn.execute("""
                INSERT INTO opportunity_journey_steps(id,company_id,opportunity_id,step_key,title,sort_order)
                VALUES (?,?,?,?,?,?)
                ON CONFLICT(company_id,opportunity_id,step_key) DO NOTHING
            """, (str(uuid.uuid4()), company_id, opportunity_id, step_key, title, sort_order))


def list_journey_steps(db, company_id: str, opportunity_id: str) -> list[dict]:
    ensure_journey(db, company_id, opportunity_id)
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT * FROM opportunity_journey_steps
            WHERE company_id=? AND opportunity_id=?
            ORDER BY sort_order, created_at, title
        """, (company_id, opportunity_id)).fetchall()
    return [dict(row) for row in rows]


def set_step_done(db, company_id: str, opportunity_id: str, step_id: str, done: bool) -> None:
    ensure_sqlite_journey_schema(db)
    with db.connect() as conn:
        result = conn.execute("""
            UPDATE opportunity_journey_steps
            SET is_done=?, updated_at=CURRENT_TIMESTAMP
            WHERE company_id=? AND opportunity_id=? AND id=?
        """, (1 if done else 0, company_id, opportunity_id, step_id))
        if result.rowcount == 0:
            raise ValueError("Etapa da jornada não encontrada.")


def add_custom_step(db, company_id: str, opportunity_id: str, title: str) -> str:
    ensure_journey(db, company_id, opportunity_id)
    clean = " ".join(str(title or "").split()).strip()
    if not clean:
        raise ValueError("Descreva a tarefa.")
    step_id = str(uuid.uuid4())
    step_key = f"custom:{step_id}"
    with db.connect() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order),80) FROM opportunity_journey_steps WHERE company_id=? AND opportunity_id=?",
            (company_id, opportunity_id),
        ).fetchone()
        sort_order = int(row[0] or 80) + 10
        conn.execute("""
            INSERT INTO opportunity_journey_steps(id,company_id,opportunity_id,step_key,title,sort_order)
            VALUES (?,?,?,?,?,?)
        """, (step_id, company_id, opportunity_id, step_key, clean, sort_order))
    return step_id


def delete_custom_step(db, company_id: str, opportunity_id: str, step_id: str) -> None:
    ensure_sqlite_journey_schema(db)
    with db.connect() as conn:
        row = conn.execute(
            "SELECT step_key FROM opportunity_journey_steps WHERE company_id=? AND opportunity_id=? AND id=?",
            (company_id, opportunity_id, step_id),
        ).fetchone()
        if not row or not str(row["step_key"]).startswith("custom:"):
            return
        conn.execute(
            "DELETE FROM opportunity_journey_steps WHERE company_id=? AND opportunity_id=? AND id=?",
            (company_id, opportunity_id, step_id),
        )


def automatic_status(db, company_id: str, opportunity_id: str) -> dict[str, bool]:
    try:
        analyses = db.list_analyses(company_id, opportunity_id)
    except Exception:
        analyses = []
    try:
        items = db.list_quote_items(company_id, opportunity_id)
    except Exception:
        items = []
    has_items = bool(items)
    suppliers_done = has_items and all(
        str(item.get("supplier") or "").strip() or float(item.get("unit_cost") or 0) > 0
        for item in items
    )
    pricing_done = has_items and all(float(item.get("sale_price") or 0) > 0 for item in items)
    positive_margin = pricing_done and suppliers_done and all(item_financials(item)["profit"] >= 0 for item in items)
    return {
        "analysis": bool(analyses),
        "suppliers": suppliers_done,
        "pricing": pricing_done,
        "margin_positive": positive_margin,
    }


def sync_automatic_completion(db, company_id: str, opportunity_id: str) -> dict[str, bool]:
    status = automatic_status(db, company_id, opportunity_id)
    ensure_journey(db, company_id, opportunity_id)
    with db.connect() as conn:
        for step_key in ("analysis", "suppliers", "pricing"):
            if status.get(step_key):
                conn.execute("""
                    UPDATE opportunity_journey_steps
                    SET is_done=1, updated_at=CURRENT_TIMESTAMP
                    WHERE company_id=? AND opportunity_id=? AND step_key=? AND is_done=0
                """, (company_id, opportunity_id, step_key))
    return status


def journey_progress(steps: list[dict]) -> dict:
    total = len(steps)
    done = sum(bool(int(step.get("is_done") or 0)) for step in steps)
    return {
        "total": total,
        "done": done,
        "ratio": (done / total) if total else 0.0,
        "percent": round((done / total * 100) if total else 0),
    }
