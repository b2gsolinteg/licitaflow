import json
import sqlite3
from .db_runtime import connect_runtime, using_postgres
from datetime import datetime, timezone


class ConversionService:
    """RC24 · Funil, trial, ativação e retenção sem depender de um provedor externo."""

    def __init__(self, database_path):
        self.path = str(database_path)
        
        if not using_postgres():
            self.ensure_schema()

    def connect(self):
        return connect_runtime(self.path)

    def ensure_schema(self):
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversion_events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT NOT NULL DEFAULT '',
                    user_id TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_conversion_events_company
                    ON conversion_events(company_id, event_type, created_at DESC);

                CREATE TABLE IF NOT EXISTS conversion_action_queue(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT NOT NULL DEFAULT '',
                    action_type TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'normal',
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    dedupe_key TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                );
                CREATE INDEX IF NOT EXISTS ix_conversion_actions_status
                    ON conversion_action_queue(status, priority, created_at DESC);
            """)

    def record_event(self, event_type, company_id="", user_id="", details=None):
        payload = json.dumps(details or {}, ensure_ascii=False, separators=(",", ":"))
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO conversion_events(company_id,user_id,event_type,details)
                VALUES (?,?,?,?)
            """, (
                str(company_id or ""), str(user_id or ""), str(event_type), payload[:4000],
            ))

    def _table_exists(self, conn, table):
        # PRAGMA table_info é atendido nativamente pelo SQLite e traduzido pelo
        # PostgresCompatConnection para information_schema.columns. Assim evitamos
        # consultar sqlite_master em produção PostgreSQL.
        return bool(conn.execute(f"PRAGMA table_info({table})").fetchone())

    def _columns(self, conn, table):
        if not self._table_exists(conn, table):
            return set()
        return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}

    def funnel(self):
        result = {
            "requests": 0, "activated": 0, "trials": 0, "engaged": 0,
            "checkout": 0, "paid": 0,
        }
        with self.connect() as conn:
            if self._table_exists(conn, "access_requests"):
                cols = self._columns(conn, "access_requests")
                result["requests"] = int(conn.execute(
                    "SELECT COUNT(*) FROM access_requests"
                ).fetchone()[0])
                if "status" in cols:
                    result["activated"] = int(conn.execute(
                        "SELECT COUNT(*) FROM access_requests WHERE status='activated'"
                    ).fetchone()[0])

            if self._table_exists(conn, "companies"):
                cols = self._columns(conn, "companies")
                if "subscription_status" in cols:
                    result["trials"] = int(conn.execute("""
                        SELECT COUNT(*) FROM companies
                        WHERE lower(COALESCE(subscription_status,''))='trialing'
                    """).fetchone()[0])
                    result["paid"] = int(conn.execute("""
                        SELECT COUNT(*) FROM companies
                        WHERE lower(COALESCE(subscription_status,''))='active'
                    """).fetchone()[0])

            if self._table_exists(conn, "usage_events"):
                result["engaged"] = int(conn.execute("""
                    SELECT COUNT(DISTINCT company_id) FROM usage_events
                    WHERE event_type IN ('search','analysis')
                """).fetchone()[0])

            if self._table_exists(conn, "billing_checkouts"):
                result["checkout"] = int(conn.execute(
                    "SELECT COUNT(DISTINCT company_id) FROM billing_checkouts"
                ).fetchone()[0])

            # commercial_subscriptions is the strongest source when RC21 is active.
            if self._table_exists(conn, "commercial_subscriptions"):
                cols = self._columns(conn, "commercial_subscriptions")
                if "status" in cols:
                    commercial_paid = int(conn.execute("""
                        SELECT COUNT(*) FROM commercial_subscriptions
                        WHERE lower(COALESCE(status,''))='active'
                    """).fetchone()[0])
                    result["paid"] = max(result["paid"], commercial_paid)
        return result

    def _last_usage_map(self, conn):
        if not self._table_exists(conn, "usage_events"):
            return {}
        rows = conn.execute("""
            SELECT company_id, MAX(created_at) AS last_usage,
                   SUM(CASE WHEN event_type='search' THEN units ELSE 0 END) AS searches,
                   SUM(CASE WHEN event_type='analysis' THEN units ELSE 0 END) AS analyses
            FROM usage_events GROUP BY company_id
        """).fetchall()
        return {str(r["company_id"]): dict(r) for r in rows}

    def _checkout_map(self, conn):
        if not self._table_exists(conn, "billing_checkouts"):
            return {}
        rows = conn.execute("""
            SELECT company_id, MAX(created_at) AS last_checkout,
                   MAX(CASE WHEN local_status='active' THEN 1 ELSE 0 END) AS has_active,
                   MAX(CASE WHEN local_status='pending' THEN 1 ELSE 0 END) AS has_pending
            FROM billing_checkouts GROUP BY company_id
        """).fetchall()
        return {str(r["company_id"]): dict(r) for r in rows}

    def customer_health(self):
        with self.connect() as conn:
            if not self._table_exists(conn, "companies"):
                return []
            ccols = self._columns(conn, "companies")
            needed = {"id", "name"}
            if not needed.issubset(ccols):
                return []

            select = ["id", "name"]
            for col in ("subscription_status", "trial_ends_at", "subscription_ends_at", "plan"):
                if col in ccols:
                    select.append(col)
            companies = conn.execute(
                f"SELECT {','.join(select)} FROM companies ORDER BY name"
            ).fetchall()

            usage_map = self._last_usage_map(conn)
            checkout_map = self._checkout_map(conn)

            user_map = {}
            if self._table_exists(conn, "users"):
                ucols = self._columns(conn, "users")
                if "company_id" in ucols:
                    pieces = ["company_id"]
                    pieces.append("MAX(last_login_at) AS last_login" if "last_login_at" in ucols else "NULL AS last_login")
                    pieces.append("MAX(email) AS email" if "email" in ucols else "'' AS email")
                    rows = conn.execute(
                        f"SELECT {','.join(pieces)} FROM users GROUP BY company_id"
                    ).fetchall()
                    user_map = {str(r["company_id"]): dict(r) for r in rows}

        today = datetime.now(timezone.utc).date()
        output = []
        for c in companies:
            item = dict(c)
            cid = str(item["id"])
            status = str(item.get("subscription_status") or "").lower()
            trial_end = item.get("trial_ends_at")
            days_left = None
            if trial_end:
                try:
                    parsed = datetime.fromisoformat(str(trial_end).replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    days_left = (parsed.date() - today).days
                except (ValueError, TypeError):
                    pass

            usage = usage_map.get(cid, {})
            checkout = checkout_map.get(cid, {})
            user = user_map.get(cid, {})
            searches = int(usage.get("searches") or 0)
            analyses = int(usage.get("analyses") or 0)
            last_activity = usage.get("last_usage") or user.get("last_login")
            health = "normal"
            action = ""
            priority = "normal"

            if status == "trialing":
                if searches + analyses == 0:
                    health, action, priority = (
                        "sem ativação",
                        "Ajudar o cliente a realizar a primeira busca e primeira análise.",
                        "high",
                    )
                if days_left is not None and days_left <= 2:
                    health, priority = "trial vencendo", "high"
                    action = (
                        "Trial termina hoje/amanhã; realizar contato comercial."
                        if days_left >= 0 else "Trial expirado; tratar recuperação ou encerramento."
                    )
                if checkout.get("has_pending"):
                    health, action, priority = (
                        "checkout pendente",
                        "Cliente iniciou pagamento; acompanhar confirmação.",
                        "high",
                    )
            elif status == "active":
                # SQLite-style timestamp strings compare well enough after parsing.
                stale = False
                if last_activity:
                    try:
                        dt = datetime.fromisoformat(str(last_activity).replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        stale = (datetime.now(timezone.utc) - dt).days >= 7
                    except (ValueError, TypeError):
                        stale = False
                if stale:
                    health, action, priority = (
                        "risco de retenção",
                        "Assinante sem atividade há 7+ dias; fazer contato de sucesso do cliente.",
                        "normal",
                    )

            output.append({
                "company_id": cid,
                "company_name": item.get("name") or cid,
                "email": user.get("email") or "",
                "status": status or "não definido",
                "days_left": days_left,
                "searches": searches,
                "analyses": analyses,
                "last_activity": last_activity,
                "health": health,
                "recommended_action": action,
                "priority": priority,
                "has_pending_checkout": bool(checkout.get("has_pending")),
            })
        return output

    def refresh_action_queue(self):
        health = self.customer_health()
        created = 0
        with self.connect() as conn:
            for item in health:
                if not item["recommended_action"]:
                    continue
                # Reopen at most one task of each category/company/day.
                today = datetime.now(timezone.utc).date().isoformat()
                key = f'{item["company_id"]}:{item["health"]}:{today}'
                try:
                    conn.execute("""
                        INSERT INTO conversion_action_queue(
                            company_id,action_type,priority,title,details,dedupe_key,status
                        ) VALUES (?,?,?,?,?,?,'open')
                    """, (
                        item["company_id"], item["health"], item["priority"],
                        item["company_name"], item["recommended_action"], key,
                    ))
                    created += 1
                except sqlite3.IntegrityError:
                    pass
        return created

    def actions(self, status="open", limit=300):
        with self.connect() as conn:
            if status == "all":
                rows = conn.execute("""
                    SELECT * FROM conversion_action_queue
                    ORDER BY CASE priority WHEN 'high' THEN 0 ELSE 1 END,
                             created_at DESC LIMIT ?
                """, (int(limit),)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM conversion_action_queue WHERE status=?
                    ORDER BY CASE priority WHEN 'high' THEN 0 ELSE 1 END,
                             created_at DESC LIMIT ?
                """, (str(status), int(limit))).fetchall()
        return [dict(r) for r in rows]

    def complete_action(self, action_id):
        with self.connect() as conn:
            conn.execute("""
                UPDATE conversion_action_queue
                SET status='done', completed_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (int(action_id),))

    @staticmethod
    def trial_message(days_left):
        if days_left is None:
            return ""
        if days_left < 0:
            return "Seu período gratuito terminou."
        if days_left == 0:
            return "Seu período gratuito termina hoje."
        if days_left == 1:
            return "Resta 1 dia do seu período gratuito."
        return f"Restam {days_left} dias do seu período gratuito."
