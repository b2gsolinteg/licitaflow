import hashlib
import secrets
import sqlite3
from .db_runtime import connect_runtime, using_postgres
from datetime import datetime, timezone
from pathlib import Path

class SecurityError(RuntimeError): pass
class RateLimitError(SecurityError): pass
class SessionExpiredError(SecurityError): pass

class SecurityService:
    LOGIN_MAX_FAILURES=5
    LOGIN_WINDOW_MINUTES=15
    LOGIN_BLOCK_MINUTES=15
    REQUEST_MAX_ATTEMPTS=10
    REQUEST_WINDOW_MINUTES=60
    SESSION_IDLE_MINUTES=60
    SESSION_ABSOLUTE_HOURS=8

    def __init__(self,database_path,project_root=None):
        self.path=str(database_path)
        self.project_root=Path(project_root) if project_root else Path(self.path).parent
        
        if not using_postgres():
            self.ensure_schema()

    def connect(self):
        return connect_runtime(self.path)

    def ensure_schema(self):
        with self.connect() as c:
            c.executescript("""
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
            """)

    @staticmethod
    def normalize_email(v): return str(v or "").strip().lower()
    @staticmethod
    def _sha(v): return hashlib.sha256(str(v or "").encode("utf-8")).hexdigest()
    def ip_hash(self,ip):
        v=str(ip or "").strip()
        return self._sha(v)[:24] if v else ""
    def _bucket(self,purpose,subject="",ip=""):
        return f"{purpose}:{self._sha(f'{purpose}|{self.normalize_email(subject)}|{self.ip_hash(ip)}')[:32]}"

    def _event_tx(self,c,event_type,subject="",ip="",success=False,details=""):
        c.execute("""INSERT INTO security_events(event_type,subject,ip_hash,success,details)
                     VALUES (?,?,?,?,?)""",
                  (str(event_type),self.normalize_email(subject),self.ip_hash(ip),
                   1 if success else 0,str(details or "")[:1000]))

    def event(self,event_type,subject="",ip="",success=False,details=""):
        with self.connect() as c:self._event_tx(c,event_type,subject,ip,success,details)

    def _check_bucket(self,c,bucket,window_minutes):
        row=c.execute("SELECT * FROM security_rate_limits WHERE bucket=?",(bucket,)).fetchone()
        if row and row["blocked_until"]:
            if c.execute("SELECT datetime(?)>datetime('now')",(row["blocked_until"],)).fetchone()[0]:
                raise RateLimitError("Muitas tentativas em sequência. Aguarde alguns minutos e tente novamente.")
        if row:
            expired=c.execute("""SELECT datetime(window_started_at,?)<=datetime('now')
                                 FROM security_rate_limits WHERE bucket=?""",
                              (f"+{int(window_minutes)} minutes",bucket)).fetchone()[0]
            if expired:
                c.execute("""UPDATE security_rate_limits SET attempts=0,
                             window_started_at=CURRENT_TIMESTAMP,blocked_until=NULL,
                             updated_at=CURRENT_TIMESTAMP WHERE bucket=?""",(bucket,))

    def precheck(self,purpose,subject="",ip=""):
        window=self.LOGIN_WINDOW_MINUTES if purpose=="login" else self.REQUEST_WINDOW_MINUTES
        with self.connect() as c:self._check_bucket(c,self._bucket(purpose,subject,ip),window)
        return True

    def register_attempt(self,purpose,subject="",ip="",success=False):
        if purpose=="login":
            max_attempts,window,block=self.LOGIN_MAX_FAILURES,self.LOGIN_WINDOW_MINUTES,self.LOGIN_BLOCK_MINUTES
        elif purpose=="access_request":
            max_attempts,window,block=self.REQUEST_MAX_ATTEMPTS,self.REQUEST_WINDOW_MINUTES,self.LOGIN_BLOCK_MINUTES
        else:
            max_attempts,window,block=20,60,15
        bucket=self._bucket(purpose,subject,ip)
        should_block=False
        with self.connect() as c:
            self._check_bucket(c,bucket,window)
            if success:
                c.execute("DELETE FROM security_rate_limits WHERE bucket=?",(bucket,))
                self._event_tx(c,f"{purpose}_success",subject,ip,True)
                return
            c.execute("""INSERT INTO security_rate_limits(bucket,attempts,window_started_at,updated_at)
                         VALUES (?,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
                         ON CONFLICT(bucket) DO UPDATE SET attempts=security_rate_limits.attempts+1,
                         updated_at=CURRENT_TIMESTAMP""",(bucket,))
            attempts=int(c.execute("SELECT attempts FROM security_rate_limits WHERE bucket=?",(bucket,)).fetchone()[0])
            if attempts>=max_attempts:
                c.execute("""UPDATE security_rate_limits SET blocked_until=datetime('now',?),
                             updated_at=CURRENT_TIMESTAMP WHERE bucket=?""",
                          (f"+{int(block)} minutes",bucket))
                should_block=True
            self._event_tx(c,f"{purpose}_failure",subject,ip,False,f"attempts={attempts}")
        if should_block:
            raise RateLimitError("Muitas tentativas em sequência. O acesso foi temporariamente protegido.")

    def create_session(self,company_id,user_id):
        token=secrets.token_urlsafe(32); th=self._sha(token)
        with self.connect() as c:
            c.execute("""INSERT INTO security_sessions(token_hash,company_id,user_id,issued_at,last_seen_at,expires_at)
                         VALUES (?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,datetime('now',?))""",
                      (th,str(company_id or ""),str(user_id or ""),f"+{self.SESSION_ABSOLUTE_HOURS} hours"))
        return token

    def validate_session(self,token):
        if not token: raise SessionExpiredError("Sessão inválida.")
        th=self._sha(token)
        with self.connect() as c:
            r=c.execute("SELECT * FROM security_sessions WHERE token_hash=?",(th,)).fetchone()
            if not r or r["revoked_at"]: raise SessionExpiredError("Sessão encerrada.")
            abs_exp=c.execute("SELECT datetime(?)<=datetime('now')",(r["expires_at"],)).fetchone()[0]
            idle_exp=c.execute("SELECT datetime(?,?)<=datetime('now')",(r["last_seen_at"],f"+{self.SESSION_IDLE_MINUTES} minutes")).fetchone()[0]
            if abs_exp or idle_exp:
                c.execute("UPDATE security_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE token_hash=?",(th,))
                raise SessionExpiredError("Sua sessão expirou por segurança. Entre novamente.")
            c.execute("UPDATE security_sessions SET last_seen_at=CURRENT_TIMESTAMP WHERE token_hash=?",(th,))
        return True

    def revoke_session(self,token):
        if not token:return
        with self.connect() as c:c.execute("UPDATE security_sessions SET revoked_at=CURRENT_TIMESTAMP WHERE token_hash=?",(self._sha(token),))

    def metrics(self):
        with self.connect() as c:
            return {
              "failed_24h":int(c.execute("SELECT COUNT(*) FROM security_events WHERE success=0 AND created_at>=datetime('now','-24 hours')").fetchone()[0]),
              "blocked":int(c.execute("SELECT COUNT(*) FROM security_rate_limits WHERE blocked_until IS NOT NULL AND datetime(blocked_until)>datetime('now')").fetchone()[0]),
              "active_sessions":int(c.execute("SELECT COUNT(*) FROM security_sessions WHERE revoked_at IS NULL AND datetime(expires_at)>datetime('now')").fetchone()[0]),
              "verified_backups":int(c.execute("SELECT COUNT(*) FROM security_backup_audit WHERE integrity_status='ok'").fetchone()[0]),
            }

    def recent_events(self,limit=300):
        with self.connect() as c:return [dict(r) for r in c.execute("SELECT * FROM security_events ORDER BY created_at DESC,id DESC LIMIT ?",(int(limit),)).fetchall()]

    def create_verified_backup(self):
        if using_postgres():
            raise SecurityError(
                "No modo PostgreSQL, o backup deve ser feito no Supabase/pg_dump. "
                "O backup SQLite local foi desativado para evitar uma falsa sensação de proteção."
            )
        d=self.project_root/"backups"; d.mkdir(parents=True,exist_ok=True)
        target=d/f"licitanexo_rc25_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.sqlite3"
        s=sqlite3.connect(self.path,timeout=30); t=sqlite3.connect(str(target),timeout=30)
        try:s.backup(t)
        finally:t.close(); s.close()
        chk=sqlite3.connect(str(target),timeout=30)
        try:integrity=str(chk.execute("PRAGMA integrity_check").fetchone()[0])
        finally:chk.close()
        status="ok" if integrity.lower()=="ok" else integrity[:80]
        size=target.stat().st_size
        with self.connect() as c:c.execute("INSERT INTO security_backup_audit(filename,size_bytes,integrity_status) VALUES (?,?,?)",(target.name,int(size),status))
        if status!="ok":raise SecurityError(f"Backup criado, mas a verificação retornou: {status}")
        return {"path":str(target),"filename":target.name,"size_bytes":int(size),"integrity_status":status}

    def backup_history(self,limit=50):
        with self.connect() as c:return [dict(r) for r in c.execute("SELECT * FROM security_backup_audit ORDER BY created_at DESC,id DESC LIMIT ?",(int(limit),)).fetchall()]
