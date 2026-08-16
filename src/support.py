"""Serviço de conversas de suporte do LicitaNexo.

Evolui os pedidos de atendimento já existentes para uma conversa assíncrona,
mantendo compatibilidade com registros criados antes desta funcionalidade.
"""

import uuid
from datetime import datetime, timezone


class SupportError(ValueError):
    pass


class SupportService:
    ALLOWED_ROLES = {"user", "admin"}
    ALLOWED_STATUSES = {"Recebida", "Em atendimento", "Concluída", "Cancelada"}

    def __init__(self, database):
        self.database = database
        self.ensure_schema()

    def ensure_schema(self):
        statements = (
            """
            CREATE TABLE IF NOT EXISTS assisted_request_messages(
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                sender_user_id TEXT NOT NULL,
                sender_role TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                FOREIGN KEY(request_id) REFERENCES assisted_requests(id) ON DELETE CASCADE,
                FOREIGN KEY(sender_user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_assisted_request_messages_request
            ON assisted_request_messages(request_id, created_at)
            """,
        )
        with self.database.connect() as conn:
            for statement in statements:
                conn.execute(statement)

    def create_conversation(self, user, request_type, title, body="", urgency="Normal"):
        if not user or not user.get("id") or not user.get("company_id"):
            raise SupportError("Usuário não identificado.")
        body = str(body or "").strip()
        if not body:
            raise SupportError("Descreva como podemos ajudar.")
        if len(body) > 5000:
            raise SupportError("A mensagem deve ter no máximo 5.000 caracteres.")
        return self.database.create_assisted_request(
            user["company_id"], user["id"], request_type, title, body, urgency
        )

    def list_conversations(self, company_id=None):
        return self.database.list_assisted_requests(company_id)

    def list_messages(self, request_id, company_id=None):
        request_id = str(request_id or "").strip()
        if not request_id:
            return []
        sql = """
            SELECT m.*, u.name AS sender_name, u.email AS sender_email
            FROM assisted_request_messages m
            JOIN assisted_requests r ON r.id=m.request_id
            JOIN users u ON u.id=m.sender_user_id
            WHERE m.request_id=?
        """
        params = [request_id]
        if company_id:
            sql += " AND r.company_id=?"
            params.append(company_id)
        sql += " ORDER BY m.created_at ASC, m.id ASC"
        with self.database.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def add_message(self, request_id, sender_user_id, sender_role, body, company_id=None):
        request_id = str(request_id or "").strip()
        sender_user_id = str(sender_user_id or "").strip()
        sender_role = str(sender_role or "").strip().lower()
        body = str(body or "").strip()
        if sender_role not in self.ALLOWED_ROLES:
            raise SupportError("Tipo de remetente inválido.")
        if not request_id or not sender_user_id or not body:
            raise SupportError("Digite uma mensagem antes de enviar.")
        if len(body) > 5000:
            raise SupportError("A mensagem deve ter no máximo 5.000 caracteres.")

        with self.database.connect() as conn:
            sql = "SELECT id, company_id FROM assisted_requests WHERE id=?"
            params = [request_id]
            if company_id:
                sql += " AND company_id=?"
                params.append(company_id)
            request = conn.execute(sql, params).fetchone()
            if not request:
                raise SupportError("Atendimento não encontrado.")
            sender = conn.execute(
                "SELECT id, company_id FROM users WHERE id=?", (sender_user_id,)
            ).fetchone()
            if not sender:
                raise SupportError("Remetente não encontrado.")
            if sender_role == "user" and sender["company_id"] != request["company_id"]:
                raise SupportError("Você não pode responder a este atendimento.")

            conn.execute(
                """
                INSERT INTO assisted_request_messages(
                    id, request_id, sender_user_id, sender_role, body, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()), request_id, sender_user_id, sender_role, body,
                    datetime.now(timezone.utc).isoformat(timespec="microseconds"),
                ),
            )
            if sender_role == "user":
                conn.execute(
                    """
                    UPDATE assisted_requests
                    SET status='Recebida', updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (request_id,),
                )
            else:
                conn.execute(
                    """
                    UPDATE assisted_requests
                    SET status=CASE WHEN status='Recebida' THEN 'Em atendimento' ELSE status END,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (request_id,),
                )

    def update_status(self, request_id, status):
        if status not in self.ALLOWED_STATUSES:
            raise SupportError("Situação de atendimento inválida.")
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE assisted_requests
                SET status=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (status, request_id),
            )
