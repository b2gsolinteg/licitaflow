import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .db_runtime import connect_runtime, using_postgres


class SecurityError(RuntimeError):
    pass


class RateLimitError(SecurityError):
    pass


class SessionExpiredError(SecurityError):
    pass


def _utcnow():
    return datetime.now(timezone.utc)


def _parse_timestamp(value):
    if value is None or not str(value).strip():
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timestamp_value(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


class SecurityService:
    LOGIN_MAX_FAILURES = 5
    LOGIN_WINDOW_MINUTES = 15
    LOGIN_BLOCK_MINUTES = 15
    REQUEST_MAX_ATTEMPTS = 10
    REQUEST_WINDOW_MINUTES = 60
    SESSION_IDLE_MINUTES = 60
    SESSION_ABSOLUTE_HOURS = 8

    def __init__(self, database_path, project_root=None):
        self.path = str(database_path)
        self.project_root = Path(project_root) if project_root else Path(self.path).parent
        if not using_postgres():
            self.ensure_schema()

    def connect(self):
        return connect_runtime(self.path)

    def ensure_schema(self):
        with self.connect() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS security_events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,
                  subject TEXT NOT NULL DEFAULT '',ip_hash TEXT NOT NULL DEFAULT '',
                  success INTEGER NOT NULL DEFAULT 0,details TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS ix_security_events_type_time ON security_events(event_type,created_at DESC);
                CREATE TABLE IF NOT EXISTS security_rate_limits(
                  bucket TEXT PRIMARY KEY,attempts INTEGER NOT NULL DEFAULT 0,
                  window_started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  blocked_until TEXT,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS security_sessions(
                  token_hash TEXT PRIMARY KEY,company_id TEXT NOT NULL DEFAULT '',
                  user_id TEXT NOT NULL DEFAULT '',issued_at TEXT NOT NULL,
                  last_seen_at TEXT NOT NULL,expires_at TEXT NOT NULL,revoked_at TEXT);
                CREATE INDEX IF NOT EXISTS ix_security_sessions_user ON security_sessions(user_id,revoked_at,expires_at);
                CREATE TABLE IF NOT EXISTS security_backup_audit(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,filename TEXT NOT NULL,
                  size_bytes INTEGER NOT NULL,integrity_status TEXT NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                """
            )

    @staticmethod
    def normalize_email(value):
        return str(value or "").strip().lower()

    @staticmethod
    def _sha(value):
        return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()

    def ip_hash(self, ip):
        value = str(ip or "").strip()
        return self._sha(value)[:24] if value else ""

    def _bucket(self, purpose, subject="", ip=""):
        material = f"{purpose}|{self.normalize_email(subject)}|{self.ip_hash(ip)}"
        return f"{purpose}:{self._sha(material)[:32]}"

    def _event_tx(self, connection, event_type, subject="", ip="", success=False, details=""):
        connection.execute(
            """
            INSERT INTO security_events(event_type,subject,ip_hash,success,details)
            VALUES (?,?,?,?,?)
            """,
            (
                str(event_type),
                self.normalize_email(subject),
                self.ip_hash(ip),
                1 if success else 0,
                str(details or "")[:1000],
            ),
        )

    def event(self, event_type, subject="", ip="", success=False, details=""):
        with self.connect() as connection:
            self._event_tx(connection, event_type, subject, ip, success, details)

    def _check_bucket(self, connection, bucket, window_minutes):
        row = connection.execute(
            "SELECT * FROM security_rate_limits WHERE bucket=?", (bucket,)
        ).fetchone()
        if not row:
            return

        now = _utcnow()
        blocked_until = _parse_timestamp(row["blocked_until"])
        if blocked_until and blocked_until > now:
            raise RateLimitError(
                "Muitas tentativas em sequência. Aguarde alguns minutos e tente novamente."
            )

        window_started = _parse_timestamp(row["window_started_at"])
        if not window_started or window_started + timedelta(minutes=int(window_minutes)) <= now:
            timestamp = _timestamp_value(now)
            connection.execute(
                """
                UPDATE security_rate_limits
                SET attempts=0, window_started_at=?, blocked_until=NULL, updated_at=?
                WHERE bucket=?
                """,
                (timestamp, timestamp, bucket),
            )

    def precheck(self, purpose, subject="", ip=""):
        window = self.LOGIN_WINDOW_MINUTES if purpose == "login" else self.REQUEST_WINDOW_MINUTES
        with self.connect() as connection:
            self._check_bucket(connection, self._bucket(purpose, subject, ip), window)
        return True

    def register_attempt(self, purpose, subject="", ip="", success=False):
        if purpose == "login":
            max_attempts = self.LOGIN_MAX_FAILURES
            window = self.LOGIN_WINDOW_MINUTES
            block = self.LOGIN_BLOCK_MINUTES
        elif purpose == "access_request":
            max_attempts = self.REQUEST_MAX_ATTEMPTS
            window = self.REQUEST_WINDOW_MINUTES
            block = self.LOGIN_BLOCK_MINUTES
        else:
            max_attempts, window, block = 20, 60, 15

        bucket = self._bucket(purpose, subject, ip)
        should_block = False
        now = _utcnow()
        now_value = _timestamp_value(now)

        with self.connect() as connection:
            self._check_bucket(connection, bucket, window)
            if success:
                connection.execute("DELETE FROM security_rate_limits WHERE bucket=?", (bucket,))
                self._event_tx(connection, f"{purpose}_success", subject, ip, True)
                return

            connection.execute(
                """
                INSERT INTO security_rate_limits(bucket,attempts,window_started_at,updated_at)
                VALUES (?,1,?,?)
                ON CONFLICT(bucket) DO UPDATE SET
                    attempts=security_rate_limits.attempts+1,
                    updated_at=excluded.updated_at
                """,
                (bucket, now_value, now_value),
            )
            attempts = int(
                connection.execute(
                    "SELECT attempts FROM security_rate_limits WHERE bucket=?", (bucket,)
                ).fetchone()[0]
            )
            if attempts >= max_attempts:
                blocked_until = _timestamp_value(now + timedelta(minutes=int(block)))
                connection.execute(
                    """
                    UPDATE security_rate_limits
                    SET blocked_until=?, updated_at=?
                    WHERE bucket=?
                    """,
                    (blocked_until, now_value, bucket),
                )
                should_block = True
            self._event_tx(
                connection,
                f"{purpose}_failure",
                subject,
                ip,
                False,
                f"attempts={attempts}",
            )

        if should_block:
            raise RateLimitError(
                "Muitas tentativas em sequência. O acesso foi temporariamente protegido."
            )

    def create_session(self, company_id, user_id):
        token = secrets.token_urlsafe(32)
        token_hash = self._sha(token)
        issued_at = _utcnow()
        expires_at = issued_at + timedelta(hours=self.SESSION_ABSOLUTE_HOURS)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO security_sessions(
                    token_hash,company_id,user_id,issued_at,last_seen_at,expires_at
                ) VALUES (?,?,?,?,?,?)
                """,
                (
                    token_hash,
                    str(company_id or ""),
                    str(user_id or ""),
                    _timestamp_value(issued_at),
                    _timestamp_value(issued_at),
                    _timestamp_value(expires_at),
                ),
            )
        return token

    def validate_session(self, token):
        if not token:
            raise SessionExpiredError("Sessão inválida.")

        token_hash = self._sha(token)
        now = _utcnow()
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM security_sessions WHERE token_hash=?", (token_hash,)
            ).fetchone()
            if not row or row["revoked_at"]:
                raise SessionExpiredError("Sessão encerrada.")

            absolute_expiry = _parse_timestamp(row["expires_at"])
            last_seen = _parse_timestamp(row["last_seen_at"])
            idle_expiry = (
                last_seen + timedelta(minutes=self.SESSION_IDLE_MINUTES)
                if last_seen
                else now
            )
            if not absolute_expiry or absolute_expiry <= now or idle_expiry <= now:
                connection.execute(
                    "UPDATE security_sessions SET revoked_at=? WHERE token_hash=?",
                    (_timestamp_value(now), token_hash),
                )
                raise SessionExpiredError("Sua sessão expirou por segurança. Entre novamente.")

            # A sessão continua validada em toda execução completa, porém o heartbeat
            # só grava no banco quando passou pelo menos 60s. Fragments de UI não precisam
            # escrever no PostgreSQL a cada interação de preço/fornecedor.
            if not last_seen or (now - last_seen).total_seconds() >= 60:
                connection.execute(
                    "UPDATE security_sessions SET last_seen_at=? WHERE token_hash=?",
                    (_timestamp_value(now), token_hash),
                )
        return True

    def revoke_session(self, token):
        if not token:
            return
        with self.connect() as connection:
            connection.execute(
                "UPDATE security_sessions SET revoked_at=? WHERE token_hash=?",
                (_timestamp_value(_utcnow()), self._sha(token)),
            )

    def metrics(self):
        now = _utcnow()
        since = now - timedelta(hours=24)
        with self.connect() as connection:
            failed_rows = connection.execute(
                "SELECT created_at FROM security_events WHERE success=0"
            ).fetchall()
            blocked_rows = connection.execute(
                "SELECT blocked_until FROM security_rate_limits WHERE blocked_until IS NOT NULL"
            ).fetchall()
            session_rows = connection.execute(
                "SELECT last_seen_at,expires_at,revoked_at FROM security_sessions WHERE revoked_at IS NULL"
            ).fetchall()
            verified_backups = int(
                connection.execute(
                    "SELECT COUNT(*) FROM security_backup_audit WHERE integrity_status='ok'"
                ).fetchone()[0]
            )

        failed_24h = 0
        for row in failed_rows:
            try:
                created_at = _parse_timestamp(row["created_at"])
            except (TypeError, ValueError):
                continue
            if created_at and created_at >= since:
                failed_24h += 1

        blocked = 0
        for row in blocked_rows:
            try:
                blocked_until = _parse_timestamp(row["blocked_until"])
            except (TypeError, ValueError):
                continue
            if blocked_until and blocked_until > now:
                blocked += 1

        active_sessions = 0
        for row in session_rows:
            try:
                expires_at = _parse_timestamp(row["expires_at"])
                last_seen = _parse_timestamp(row["last_seen_at"])
            except (TypeError, ValueError):
                continue
            if not expires_at or not last_seen:
                continue
            if expires_at > now and last_seen + timedelta(minutes=self.SESSION_IDLE_MINUTES) > now:
                active_sessions += 1

        return {
            "failed_24h": failed_24h,
            "blocked": blocked,
            "active_sessions": active_sessions,
            "verified_backups": verified_backups,
        }

    def recent_events(self, limit=300):
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM security_events ORDER BY created_at DESC,id DESC LIMIT ?",
                    (int(limit),),
                ).fetchall()
            ]

    def create_verified_backup(self):
        if using_postgres():
            raise SecurityError(
                "No modo PostgreSQL, o backup deve ser feito no Supabase/pg_dump. "
                "O backup SQLite local foi desativado para evitar uma falsa sensação de proteção."
            )
        directory = self.project_root / "backups"
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"licitanexo_rc25_{_utcnow().strftime('%Y%m%d_%H%M%S')}.sqlite3"
        source = sqlite3.connect(self.path, timeout=30)
        destination = sqlite3.connect(str(target), timeout=30)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        check = sqlite3.connect(str(target), timeout=30)
        try:
            integrity = str(check.execute("PRAGMA integrity_check").fetchone()[0])
        finally:
            check.close()
        status = "ok" if integrity.lower() == "ok" else integrity[:80]
        size = target.stat().st_size
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO security_backup_audit(filename,size_bytes,integrity_status)
                VALUES (?,?,?)
                """,
                (target.name, int(size), status),
            )
        if status != "ok":
            raise SecurityError(f"Backup criado, mas a verificação retornou: {status}")
        return {
            "path": str(target),
            "filename": target.name,
            "size_bytes": int(size),
            "integrity_status": status,
        }

    def backup_history(self, limit=50):
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM security_backup_audit ORDER BY created_at DESC,id DESC LIMIT ?",
                    (int(limit),),
                ).fetchall()
            ]
