import sqlite3
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.support import SupportError, SupportService


class _Database:
    def __init__(self, path):
        self.path = path
        with self.connect() as conn:
            conn.executescript("""
                PRAGMA foreign_keys=ON;
                CREATE TABLE companies(id TEXT PRIMARY KEY, name TEXT NOT NULL);
                CREATE TABLE users(
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL, name TEXT NOT NULL,
                    email TEXT NOT NULL, FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                CREATE TABLE assisted_requests(
                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL, user_id TEXT NOT NULL,
                    request_type TEXT NOT NULL, title TEXT NOT NULL, details TEXT NOT NULL DEFAULT '',
                    urgency TEXT NOT NULL DEFAULT 'Normal', status TEXT NOT NULL DEFAULT 'Recebida',
                    admin_notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def create_assisted_request(self, company_id, user_id, request_type, title, details, urgency):
        request_id = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO assisted_requests VALUES(?,?,?,?,?,?,?,'Recebida','',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
                (request_id, company_id, user_id, request_type, title, details, urgency),
            )
        return request_id

    def list_assisted_requests(self, company_id=None):
        sql = "SELECT * FROM assisted_requests"
        params = []
        if company_id:
            sql += " WHERE company_id=?"
            params.append(company_id)
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def update_assisted_request(self, request_id, status, admin_notes=""):
        with self.connect() as conn:
            conn.execute(
                "UPDATE assisted_requests SET status=?, admin_notes=? WHERE id=?",
                (status, admin_notes, request_id),
            )


class SupportServiceTests(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.path = handle.name
        self.db = _Database(self.path)
        with self.db.connect() as conn:
            conn.execute("INSERT INTO companies VALUES('c1','Empresa 1')")
            conn.execute("INSERT INTO companies VALUES('c2','Empresa 2')")
            conn.execute("INSERT INTO users VALUES('u1','c1','Cliente','cliente@example.com')")
            conn.execute("INSERT INTO users VALUES('u2','c2','Outro','outro@example.com')")
            conn.execute("INSERT INTO users VALUES('admin','c1','Suporte','admin@example.com')")
        self.service = SupportService(self.db)
        self.user = {"id": "u1", "company_id": "c1"}

    def tearDown(self):
        Path(self.path).unlink(missing_ok=True)

    def test_conversation_and_replies(self):
        request_id = self.service.create_conversation(
            self.user, "Dúvida operacional", "Preciso de ajuda", "Mensagem inicial"
        )
        self.service.add_message(request_id, "admin", "admin", "Olá, vamos ajudar.")
        self.service.add_message(request_id, "u1", "user", "Obrigado!", company_id="c1")
        messages = self.service.list_messages(request_id, company_id="c1")
        self.assertEqual([m["body"] for m in messages], ["Olá, vamos ajudar.", "Obrigado!"])
        self.assertEqual(self.service.list_conversations("c1")[0]["status"], "Recebida")

    def test_company_isolation(self):
        request_id = self.service.create_conversation(
            self.user, "Dúvida operacional", "Ajuda", "Mensagem"
        )
        with self.assertRaises(SupportError):
            self.service.add_message(request_id, "u2", "user", "Intrusão", company_id="c2")
        self.assertEqual(self.service.list_messages(request_id, company_id="c2"), [])

    def test_rejects_empty_and_long_messages(self):
        request_id = self.service.create_conversation(
            self.user, "Dúvida operacional", "Ajuda", "Mensagem"
        )
        with self.assertRaises(SupportError):
            self.service.add_message(request_id, "u1", "user", "   ", company_id="c1")
        with self.assertRaises(SupportError):
            self.service.add_message(request_id, "u1", "user", "x" * 5001, company_id="c1")
        with self.assertRaises(SupportError):
            self.service.create_conversation(
                self.user, "Dúvida operacional", "Ajuda", "   "
            )


if __name__ == "__main__":
    unittest.main()
