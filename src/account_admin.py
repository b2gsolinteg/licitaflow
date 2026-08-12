import json
import sqlite3
from .db_runtime import connect_runtime, using_postgres
from datetime import datetime, timezone


class AccountAdminError(RuntimeError):
    pass


class AccountAdminService:
    """Administrative lifecycle for customer accounts.

    Hard delete is intentionally avoided. Deactivation immediately blocks access,
    while permanent purge requires an already-deactivated account and preserves
    a minimal audit/tombstone so the operation remains traceable.
    """

    def __init__(self, database_path):
        self.path = str(database_path)
        
        if not using_postgres():
            self.ensure_schema()

    def connect(self):
        return connect_runtime(self.path)

    def ensure_schema(self):
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS account_admin_audit(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT NOT NULL,
                    company_name TEXT NOT NULL DEFAULT '',
                    action TEXT NOT NULL,
                    actor_email TEXT NOT NULL DEFAULT '',
                    reason TEXT NOT NULL DEFAULT '',
                    details TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_account_admin_audit_company
                    ON account_admin_audit(company_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS deleted_company_tombstones(
                    company_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL DEFAULT '',
                    cnpj TEXT NOT NULL DEFAULT '',
                    deleted_by TEXT NOT NULL DEFAULT '',
                    reason TEXT NOT NULL DEFAULT '',
                    deleted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def _company(self, conn, company_id):
        row = conn.execute(
            "SELECT * FROM companies WHERE id=?", (str(company_id),)
        ).fetchone()
        if not row:
            raise AccountAdminError("Conta não encontrada.")
        return row

    def deactivate(self, company_id, actor_email, reason):
        reason = str(reason or "").strip()
        if len(reason) < 5:
            raise AccountAdminError("Informe o motivo da desativação.")
        with self.connect() as conn:
            company = self._company(conn, company_id)
            conn.execute(
                "UPDATE companies SET subscription_status='suspended' WHERE id=?",
                (str(company_id),),
            )
            conn.execute("""
                INSERT INTO account_admin_audit(
                    company_id,company_name,action,actor_email,reason,details
                ) VALUES (?,?, 'deactivated', ?, ?, ?)
            """, (
                str(company_id), company["name"], str(actor_email or "").lower(),
                reason, "Acesso suspenso; dados preservados.",
            ))
        return True

    def reactivate(self, company_id, actor_email):
        with self.connect() as conn:
            company = self._company(conn, company_id)
            conn.execute(
                "UPDATE companies SET subscription_status='active' WHERE id=?",
                (str(company_id),),
            )
            conn.execute("""
                INSERT INTO account_admin_audit(
                    company_id,company_name,action,actor_email,reason,details
                ) VALUES (?,?, 'reactivated', ?, '', ?)
            """, (
                str(company_id), company["name"], str(actor_email or "").lower(),
                "Conta reativada pelo administrador.",
            ))
        return True

    def purge(self, company_id, actor_email, reason, confirmation):
        reason = str(reason or "").strip()
        if len(reason) < 10:
            raise AccountAdminError("Para exclusão definitiva, informe um motivo com pelo menos 10 caracteres.")
        with self.connect() as conn:
            company = self._company(conn, company_id)
            if str(company["subscription_status"] or "").lower() != "suspended":
                raise AccountAdminError("Desative a conta antes da exclusão definitiva.")
            expected = f"EXCLUIR {company['name']}".strip()
            if str(confirmation or "").strip() != expected:
                raise AccountAdminError(f'Digite exatamente: {expected}')

            # Audit snapshot before deletion.
            cnpj = ""
            try:
                profile = conn.execute(
                    "SELECT * FROM company_profiles WHERE company_id=?",
                    (str(company_id),),
                ).fetchone()
                if profile and "cnpj" in profile.keys():
                    cnpj = str(profile["cnpj"] or "")
            except sqlite3.Error:
                pass

            # Explicit order covers old tables whose FK was created without CASCADE.
            tables = [
                "billing_events", "billing_checkouts", "commercial_subscriptions",
                "assisted_requests", "password_reset_requests", "edital_findings",
                "edital_analyses", "calendar_events", "price_references",
                "opportunity_quote_items", "opportunity_documents",
                "opportunity_checklist", "opportunity_tasks", "opportunity_details",
                "opportunities", "pncp_catalog", "source_sync_checkpoints",
                "sync_checkpoints", "company_profiles", "users",
            ]
            for table in tables:
                try:
                    conn.execute(f"DELETE FROM {table} WHERE company_id=?", (str(company_id),))
                except sqlite3.OperationalError:
                    # Some installations may not have every historical table/column.
                    pass

            # Keep access/trial claims outside the purge when possible: they are
            # anti-abuse/commercial history and prevent a deleted customer from
            # receiving another free trial.
            try:
                conn.execute(
                    "DELETE FROM access_requests WHERE company_id=?",
                    (str(company_id),),
                )
            except sqlite3.OperationalError:
                pass

            conn.execute("""
                INSERT INTO deleted_company_tombstones(
                    company_id,company_name,cnpj,deleted_by,reason,deleted_at
                ) VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(company_id) DO UPDATE SET
                    company_name=excluded.company_name,cnpj=excluded.cnpj,
                    deleted_by=excluded.deleted_by,reason=excluded.reason,
                    deleted_at=CURRENT_TIMESTAMP
            """, (
                str(company_id), company["name"], cnpj,
                str(actor_email or "").lower(), reason,
            ))
            conn.execute("""
                INSERT INTO account_admin_audit(
                    company_id,company_name,action,actor_email,reason,details
                ) VALUES (?,?, 'purged', ?, ?, ?)
            """, (
                str(company_id), company["name"], str(actor_email or "").lower(),
                reason, "Dados operacionais removidos; trilha mínima de auditoria preservada.",
            ))
            conn.execute("DELETE FROM companies WHERE id=?", (str(company_id),))
        return True

    def audit(self, limit=200):
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("""
                SELECT * FROM account_admin_audit
                ORDER BY created_at DESC, id DESC LIMIT ?
            """, (int(limit),)).fetchall()]
