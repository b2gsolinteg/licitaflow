import os
import re
import sqlite3
import threading
import time
from pathlib import Path


def backend_name():
    explicit=os.getenv("LICITANEXO_DB_BACKEND","").strip().lower()
    if explicit in {"postgres","postgresql"}: return "postgres"
    if explicit=="sqlite": return "sqlite"
    if os.getenv("DATABASE_URL","").strip(): return "postgres"
    return "sqlite"


def using_postgres():
    return backend_name()=="postgres"


def postgres_schema():
    value=os.getenv("LICITANEXO_DB_SCHEMA","licitanexo").strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",value):
        raise RuntimeError("LICITANEXO_DB_SCHEMA inválido.")
    return value


def _replace_qmarks(sql):
    out=[]; quote=None; i=0
    while i<len(sql):
        ch=sql[i]
        if quote:
            out.append(ch)
            if ch==quote:
                if i+1<len(sql) and sql[i+1]==quote:
                    out.append(sql[i+1]); i+=1
                else: quote=None
        else:
            if ch in ("'",'"'):
                quote=ch; out.append(ch)
            elif ch=='?': out.append('%s')
            else: out.append(ch)
        i+=1
    return ''.join(out)


def translate_sql(statement):
    s=str(statement)
    # Funções SQLite usadas pelo Database completo.
    s=re.sub(r"strftime\('%Y',\s*([^\)]+)\)", r"TO_CHAR(CAST(\1 AS TIMESTAMP), 'YYYY')", s, flags=re.I)
    s=re.sub(r"strftime\('%m',\s*([^\)]+)\)", r"TO_CHAR(CAST(\1 AS TIMESTAMP), 'MM')", s, flags=re.I)

    def _fold_expr(match):
        expr=match.group(1)
        return (
            "LOWER(translate(CAST("+expr+" AS TEXT), "
            "'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç', "
            "'AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'))"
        )
    s=re.sub(r"search_fold\(([^()]+)\)", _fold_expr, s, flags=re.I)
    # SQLite metadata query is handled separately by CompatConnection.execute.
    # Date/time functions: columns remain TEXT in RC27 to preserve application semantics.
    replacements=[
      (r"datetime\('now','start of month','\+1 month'\)", "(date_trunc('month', CURRENT_TIMESTAMP) + INTERVAL '1 month')"),
      (r"datetime\('now','start of month'\)", "date_trunc('month', CURRENT_TIMESTAMP)"),
      (r"datetime\('now',\s*'([+-]\d+)\s+(seconds?|minutes?|hours?|days?|months?|years?)'\)",
       r"(CURRENT_TIMESTAMP + INTERVAL '\1 \2')"),
      (r"datetime\('now',\s*%s\)", "(CURRENT_TIMESTAMP + (%s)::interval)"),
      (r"datetime\(([^,()]+),\s*%s\)", r"(CAST(\1 AS TIMESTAMP) + (%s)::interval)"),
      (r"datetime\(([^()]+)\)", r"CAST(\1 AS TIMESTAMP)"),
      (r"date\(([^()]+)\)", r"CAST(\1 AS DATE)"),
    ]
    s=_replace_qmarks(s)
    for pattern,repl in replacements:
        s=re.sub(pattern,repl,s,flags=re.I)

    # Known timestamp TEXT comparisons that SQLite accepted implicitly.
    for col in ("created_at","updated_at","expires_at","trial_ends_at","window_started_at","last_seen_at","requested_at"):
        s=re.sub(rf"\b{col}\b\s*(>=|<=|>|<)\s*(date_trunc\(|\(CURRENT_TIMESTAMP|CURRENT_TIMESTAMP|CAST\()",
                 rf"CAST({col} AS TIMESTAMP) \1 \2",s,flags=re.I)

    # SQLite INSERT OR IGNORE -> PostgreSQL ON CONFLICT DO NOTHING.
    ignore=bool(re.search(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b",s,flags=re.I))
    s=re.sub(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b","INSERT INTO",s,flags=re.I)
    if ignore and not re.search(r"\bON\s+CONFLICT\b",s,flags=re.I):
        s=s.rstrip().rstrip(';')+" ON CONFLICT DO NOTHING"
    return s


class CompatRow(tuple):
    def __new__(cls, values, columns):
        obj=super().__new__(cls,values); obj._columns=tuple(columns); obj._map={c:i for i,c in enumerate(columns)}; return obj
    def __getitem__(self,key):
        if isinstance(key,str): return super().__getitem__(self._map[key])
        return super().__getitem__(key)
    def keys(self): return list(self._columns)
    def __iter__(self): return super().__iter__()


class MemoryCursor:
    def __init__(self,rows): self._rows=list(rows); self._pos=0; self.rowcount=len(self._rows)
    def fetchone(self):
        if self._pos>=len(self._rows): return None
        r=self._rows[self._pos]; self._pos+=1; return r
    def fetchall(self):
        rows=self._rows[self._pos:]; self._pos=len(self._rows); return rows
    def __iter__(self): return iter(self.fetchall())


class CompatCursor:
    def __init__(self,raw): self.raw=raw
    @property
    def rowcount(self): return self.raw.rowcount
    def execute(self,statement,params=None):
        try:
            self.raw.execute(translate_sql(statement),params or ())
        except Exception as exc: _raise_compat(exc)
        return self
    def executemany(self,statement,seq):
        try:self.raw.executemany(translate_sql(statement),seq)
        except Exception as exc:_raise_compat(exc)
        return self
    def _row(self,row):
        if row is None:return None
        cols=[d.name for d in self.raw.description] if self.raw.description else []
        return CompatRow(row,cols)
    def fetchone(self): return self._row(self.raw.fetchone())
    def fetchall(self): return [self._row(r) for r in self.raw.fetchall()]
    def __iter__(self):
        for r in self.raw: yield self._row(r)
    def close(self): return self.raw.close()


def _raise_compat(exc):
    try:
        import psycopg
        if isinstance(exc,psycopg.IntegrityError): raise sqlite3.IntegrityError(str(exc)) from exc
        if isinstance(exc,psycopg.Error): raise sqlite3.OperationalError(str(exc)) from exc
    except ImportError: pass
    raise exc


class PostgresCompatConnection:
    def __init__(self,raw,lease=None): self.raw=raw; self._lease=lease; self._closed=False
    def cursor(self): return CompatCursor(self.raw.cursor())
    def execute(self,statement,params=None):
        stmt=str(statement).strip()
        m=re.fullmatch(r"PRAGMA\s+table_info\(([^)]+)\)",stmt,flags=re.I)
        if m:
            table=m.group(1).strip().strip('"`[]')
            cur=self.raw.cursor()
            cur.execute("""SELECT ordinal_position-1 AS cid,column_name AS name,
                           data_type AS type,CASE WHEN is_nullable='NO' THEN 1 ELSE 0 END AS notnull,
                           column_default AS dflt_value,0 AS pk
                           FROM information_schema.columns
                           WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position""",
                        (postgres_schema(),table))
            rows=[]
            for r in cur.fetchall(): rows.append(CompatRow(r,["cid","name","type","notnull","dflt_value","pk"]))
            cur.close(); return MemoryCursor(rows)
        if stmt.upper().startswith('PRAGMA '): return MemoryCursor([])
        cur=self.cursor(); return cur.execute(statement,params)
    def executemany(self,statement,seq): return self.cursor().executemany(statement,seq)
    def executescript(self,script):
        # RC27 owns schema migrations in PostgreSQL. Runtime services must not recreate SQLite DDL.
        return self
    def commit(self): return self.raw.commit()
    def rollback(self): return self.raw.rollback()
    def close(self):
        if self._closed:return None
        self._closed=True
        if self._lease is not None:return self._lease.__exit__(None,None,None)
        return self.raw.close()
    def __enter__(self): return self
    def __exit__(self,typ,val,tb):
        if self._closed:return False
        self._closed=True
        if self._lease is not None:return self._lease.__exit__(typ,val,tb)
        if typ is None:self.raw.commit()
        else:self.raw.rollback()
        self.raw.close(); return False


_PG_AUTH_BLOCKED_UNTIL = 0.0
_PG_AUTH_BLOCKED_REASON = ""
_PG_POOL = None
_PG_POOL_KEY = None
_PG_POOL_LOCK = threading.Lock()

def _looks_like_auth_failure(exc):
    text=str(exc).lower()
    return any(token in text for token in (
        "password authentication failed",
        "too many authentication failures",
        "ecircuitbreaker",
        "authentication failed",
    ))

def _pg_config():
    dsn=os.getenv("DATABASE_URL","").strip()
    if dsn:
        return dsn, {"connect_timeout":12}
    return "", {
        "host":os.environ["LICITANEXO_PGHOST"],
        "port":int(os.getenv("LICITANEXO_PGPORT","5432")),
        "dbname":os.getenv("LICITANEXO_PGDATABASE","postgres"),
        "user":os.environ["LICITANEXO_PGUSER"],
        "password":os.environ["LICITANEXO_PGPASSWORD"],
        "sslmode":"require",
        "connect_timeout":12,
    }


def _configure_pg_connection(raw):
    schema=postgres_schema()
    with raw.cursor() as cur:
        cur.execute('SET search_path TO "'+schema.replace('"','""')+'", public')
    raw.commit()


def _pg_pool():
    global _PG_POOL, _PG_POOL_KEY, _PG_AUTH_BLOCKED_UNTIL, _PG_AUTH_BLOCKED_REASON
    if time.monotonic() < _PG_AUTH_BLOCKED_UNTIL:
        remaining=max(1,int(_PG_AUTH_BLOCKED_UNTIL-time.monotonic()))
        raise sqlite3.OperationalError(
            f"PostgreSQL bloqueado após falha de autenticação. Aguarde {remaining}s. "
            f"{_PG_AUTH_BLOCKED_REASON}"
        )
    try:
        from psycopg_pool import ConnectionPool
    except ImportError as exc:
        raise RuntimeError("Pool PostgreSQL ausente: pip install psycopg-pool") from exc
    dsn,kwargs=_pg_config()
    pool_key=(dsn,tuple(sorted(kwargs.items())),postgres_schema())
    if _PG_POOL is not None and _PG_POOL_KEY==pool_key:
        return _PG_POOL
    with _PG_POOL_LOCK:
        if _PG_POOL is not None and _PG_POOL_KEY==pool_key:
            return _PG_POOL
        previous=_PG_POOL
        try:
            min_size=max(1,int(os.getenv("LICITANEXO_PG_POOL_MIN","1")))
            max_size=max(min_size,int(os.getenv("LICITANEXO_PG_POOL_MAX","6")))
            pool=ConnectionPool(
                conninfo=dsn,
                kwargs=kwargs,
                min_size=min_size,
                max_size=max_size,
                timeout=float(os.getenv("LICITANEXO_PG_POOL_TIMEOUT","12")),
                max_idle=float(os.getenv("LICITANEXO_PG_POOL_MAX_IDLE","300")),
                max_lifetime=float(os.getenv("LICITANEXO_PG_POOL_MAX_LIFETIME","1800")),
                configure=_configure_pg_connection,
                open=False,
            )
            pool.open(wait=True,timeout=12)
        except Exception as exc:
            if _looks_like_auth_failure(exc):
                _PG_AUTH_BLOCKED_UNTIL=time.monotonic()+300
                _PG_AUTH_BLOCKED_REASON=str(exc).splitlines()[0][:240]
            raise
        _PG_POOL=pool
        _PG_POOL_KEY=pool_key
        if previous is not None:
            try:previous.close()
            except Exception:pass
        return pool


def _pg_connect():
    global _PG_AUTH_BLOCKED_UNTIL, _PG_AUTH_BLOCKED_REASON
    if time.monotonic() < _PG_AUTH_BLOCKED_UNTIL:
        remaining=max(1, int(_PG_AUTH_BLOCKED_UNTIL-time.monotonic()))
        raise sqlite3.OperationalError(
            f"PostgreSQL bloqueado após falha de autenticação. Aguarde {remaining}s. "
            f"{_PG_AUTH_BLOCKED_REASON}"
        )
    try:
        pool=_pg_pool()
        lease=pool.connection(timeout=float(os.getenv("LICITANEXO_PG_POOL_TIMEOUT","12")))
        raw=lease.__enter__()
    except Exception as exc:
        if _looks_like_auth_failure(exc):
            _PG_AUTH_BLOCKED_UNTIL=time.monotonic()+300
            _PG_AUTH_BLOCKED_REASON=str(exc).splitlines()[0][:240]
        raise
    return PostgresCompatConnection(raw,lease=lease)


class ClosingSQLiteConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect_runtime(sqlite_path, search_fold=None):
    if using_postgres(): return _pg_connect()
    path=Path(sqlite_path); path.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(str(path),timeout=30,factory=ClosingSQLiteConnection); c.row_factory=sqlite3.Row
    if search_fold is not None:
        c.create_function("search_fold", 1, search_fold)
    c.execute("PRAGMA foreign_keys=ON"); c.execute("PRAGMA busy_timeout=30000")
    return c
