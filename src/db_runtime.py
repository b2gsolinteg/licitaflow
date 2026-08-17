import os
import re
import sqlite3
import threading
import time
from pathlib import Path


def backend_name():
    explicit = os.getenv("LICITANEXO_DB_BACKEND", "").strip().lower()
    if explicit in {"postgres", "postgresql"}:
        return "postgres"
    if explicit == "sqlite":
        return "sqlite"
    if os.getenv("DATABASE_URL", "").strip():
        return "postgres"
    return "sqlite"


def using_postgres():
    return backend_name() == "postgres"


def postgres_schema():
    value = os.getenv("LICITANEXO_DB_SCHEMA", "licitanexo").strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise RuntimeError("LICITANEXO_DB_SCHEMA inválido.")
    return value


def _replace_qmarks(sql):
    out = []
    quote = None
    index = 0
    while index < len(sql):
        char = sql[index]
        if quote:
            out.append(char)
            if char == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    out.append(sql[index + 1])
                    index += 1
                else:
                    quote = None
        else:
            if char in ("'", '"'):
                quote = char
                out.append(char)
            elif char == "?":
                out.append("%s")
            else:
                out.append(char)
        index += 1
    return "".join(out)


def translate_sql(statement):
    """Compatibilidade temporária para SQL legado escrito originalmente para SQLite.

    Código novo deve preferir SQL comum aos dois bancos ou parâmetros calculados em
    Python. Esta função permanece para permitir a migração incremental do Database
    histórico sem interromper o produto.
    """
    sql = str(statement)
    sql = re.sub(
        r"strftime\('%Y',\s*([^\)]+)\)",
        r"TO_CHAR(CAST(\1 AS TIMESTAMP), 'YYYY')",
        sql,
        flags=re.I,
    )
    sql = re.sub(
        r"strftime\('%m',\s*([^\)]+)\)",
        r"TO_CHAR(CAST(\1 AS TIMESTAMP), 'MM')",
        sql,
        flags=re.I,
    )

    def _fold_expr(match):
        expression = match.group(1)
        return (
            "LOWER(translate(CAST(" + expression + " AS TEXT), "
            "'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç', "
            "'AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'))"
        )

    sql = re.sub(r"search_fold\(([^()]+)\)", _fold_expr, sql, flags=re.I)

    replacements = [
        (
            r"datetime\('now','start of month','\+1 month'\)",
            "(date_trunc('month', CURRENT_TIMESTAMP) + INTERVAL '1 month')",
        ),
        (
            r"datetime\('now','start of month'\)",
            "date_trunc('month', CURRENT_TIMESTAMP)",
        ),
        (
            r"datetime\('now',\s*'([+-]\d+)\s+(seconds?|minutes?|hours?|days?|months?|years?)'\)",
            r"(CURRENT_TIMESTAMP + INTERVAL '\1 \2')",
        ),
        (
            r"datetime\('now',\s*%s\)",
            "(CURRENT_TIMESTAMP + (%s)::interval)",
        ),
        (
            r"datetime\(([^,()]+),\s*%s\)",
            r"(CAST(\1 AS TIMESTAMP) + (%s)::interval)",
        ),
        (r"datetime\(([^()]+)\)", r"CAST(\1 AS TIMESTAMP)"),
        (r"date\(([^()]+)\)", r"CAST(\1 AS DATE)"),
    ]

    sql = _replace_qmarks(sql)
    for pattern, replacement in replacements:
        sql = re.sub(pattern, replacement, sql, flags=re.I)

    timestamp_columns = (
        "created_at",
        "updated_at",
        "expires_at",
        "trial_ends_at",
        "trial_started_at",
        "subscription_ends_at",
        "window_started_at",
        "last_seen_at",
        "requested_at",
        "issued_at",
        "blocked_until",
        "invitation_expires_at",
        "code_generated_at",
        "current_period_start",
        "current_period_end",
    )
    for column in timestamp_columns:
        sql = re.sub(
            rf"\b{column}\b\s*(>=|<=|>|<)\s*(date_trunc\(|\(date_trunc\(|\(CURRENT_TIMESTAMP|CURRENT_TIMESTAMP|CAST\()",
            rf"CAST({column} AS TIMESTAMP) \1 \2",
            sql,
            flags=re.I,
        )

    insert_ignore = bool(
        re.search(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", sql, flags=re.I)
    )
    sql = re.sub(
        r"\bINSERT\s+OR\s+IGNORE\s+INTO\b",
        "INSERT INTO",
        sql,
        flags=re.I,
    )
    if insert_ignore and not re.search(r"\bON\s+CONFLICT\b", sql, flags=re.I):
        sql = sql.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    return sql


class CompatRow(tuple):
    def __new__(cls, values, columns):
        obj = super().__new__(cls, values)
        obj._columns = tuple(columns)
        obj._map = {column: index for index, column in enumerate(columns)}
        return obj

    def __getitem__(self, key):
        if isinstance(key, str):
            return super().__getitem__(self._map[key])
        return super().__getitem__(key)

    def keys(self):
        return list(self._columns)

    def __iter__(self):
        return super().__iter__()


class MemoryCursor:
    def __init__(self, rows):
        self._rows = list(rows)
        self._pos = 0
        self.rowcount = len(self._rows)

    def fetchone(self):
        if self._pos >= len(self._rows):
            return None
        row = self._rows[self._pos]
        self._pos += 1
        return row

    def fetchall(self):
        rows = self._rows[self._pos :]
        self._pos = len(self._rows)
        return rows

    def __iter__(self):
        return iter(self.fetchall())


class CompatCursor:
    def __init__(self, raw):
        self.raw = raw

    @property
    def rowcount(self):
        return self.raw.rowcount

    def execute(self, statement, params=None):
        try:
            self.raw.execute(translate_sql(statement), params or ())
        except Exception as exc:
            _raise_compat(exc)
        return self

    def executemany(self, statement, seq):
        try:
            self.raw.executemany(translate_sql(statement), seq)
        except Exception as exc:
            _raise_compat(exc)
        return self

    def _row(self, row):
        if row is None:
            return None
        columns = [description.name for description in self.raw.description] if self.raw.description else []
        return CompatRow(row, columns)

    def fetchone(self):
        return self._row(self.raw.fetchone())

    def fetchall(self):
        return [self._row(row) for row in self.raw.fetchall()]

    def __iter__(self):
        for row in self.raw:
            yield self._row(row)

    def close(self):
        return self.raw.close()


def _raise_compat(exc):
    try:
        import psycopg

        if isinstance(exc, psycopg.IntegrityError):
            raise sqlite3.IntegrityError(str(exc)) from exc
        if isinstance(exc, psycopg.Error):
            raise sqlite3.OperationalError(str(exc)) from exc
    except ImportError:
        pass
    raise exc


class PostgresCompatConnection:
    def __init__(self, raw, lease=None):
        self.raw = raw
        self._lease = lease
        self._closed = False

    def cursor(self):
        return CompatCursor(self.raw.cursor())

    def execute(self, statement, params=None):
        statement_text = str(statement).strip()
        metadata_match = re.fullmatch(
            r"PRAGMA\s+table_info\(([^)]+)\)",
            statement_text,
            flags=re.I,
        )
        if metadata_match:
            table = metadata_match.group(1).strip().strip('"`[]')
            cursor = self.raw.cursor()
            cursor.execute(
                """
                SELECT ordinal_position-1 AS cid,column_name AS name,
                       data_type AS type,CASE WHEN is_nullable='NO' THEN 1 ELSE 0 END AS notnull,
                       column_default AS dflt_value,0 AS pk
                FROM information_schema.columns
                WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position
                """,
                (postgres_schema(), table),
            )
            rows = [
                CompatRow(
                    row,
                    ["cid", "name", "type", "notnull", "dflt_value", "pk"],
                )
                for row in cursor.fetchall()
            ]
            cursor.close()
            return MemoryCursor(rows)
        if statement_text.upper().startswith("PRAGMA "):
            return MemoryCursor([])
        cursor = self.cursor()
        return cursor.execute(statement, params)

    def executemany(self, statement, seq):
        return self.cursor().executemany(statement, seq)

    def executescript(self, script):
        # O schema PostgreSQL é controlado por migrations versionadas. Nunca execute
        # DDL SQLite automaticamente contra produção.
        return self

    def commit(self):
        return self.raw.commit()

    def rollback(self):
        return self.raw.rollback()

    def close(self):
        if self._closed:
            return None
        self._closed = True
        if self._lease is not None:
            return self._lease.__exit__(None, None, None)
        return self.raw.close()

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        if self._closed:
            return False
        self._closed = True
        if self._lease is not None:
            return self._lease.__exit__(typ, value, traceback)
        if typ is None:
            self.raw.commit()
        else:
            self.raw.rollback()
        self.raw.close()
        return False


_PG_AUTH_BLOCKED_UNTIL = 0.0
_PG_AUTH_BLOCKED_REASON = ""
_PG_POOL = None
_PG_POOL_KEY = None
_PG_POOL_LOCK = threading.Lock()


def _looks_like_auth_failure(exc):
    text = str(exc).lower()
    return any(
        token in text
        for token in (
            "password authentication failed",
            "too many authentication failures",
            "ecircuitbreaker",
            "authentication failed",
        )
    )


def _pg_config():
    dsn = os.getenv("DATABASE_URL", "").strip()
    if dsn:
        return dsn, {"connect_timeout": 12}
    return "", {
        "host": os.environ["LICITANEXO_PGHOST"],
        "port": int(os.getenv("LICITANEXO_PGPORT", "5432")),
        "dbname": os.getenv("LICITANEXO_PGDATABASE", "postgres"),
        "user": os.environ["LICITANEXO_PGUSER"],
        "password": os.environ["LICITANEXO_PGPASSWORD"],
        "sslmode": os.getenv("LICITANEXO_PGSSLMODE", "require"),
        "connect_timeout": 12,
    }


def _configure_pg_connection(raw):
    schema = postgres_schema()
    with raw.cursor() as cursor:
        cursor.execute(
            'SET search_path TO "' + schema.replace('"', '""') + '", public'
        )
    raw.commit()


def _pg_pool():
    global _PG_POOL, _PG_POOL_KEY, _PG_AUTH_BLOCKED_UNTIL, _PG_AUTH_BLOCKED_REASON
    if time.monotonic() < _PG_AUTH_BLOCKED_UNTIL:
        remaining = max(1, int(_PG_AUTH_BLOCKED_UNTIL - time.monotonic()))
        raise sqlite3.OperationalError(
            f"PostgreSQL bloqueado após falha de autenticação. Aguarde {remaining}s. "
            f"{_PG_AUTH_BLOCKED_REASON}"
        )
    try:
        from psycopg_pool import ConnectionPool
    except ImportError as exc:
        raise RuntimeError(
            "Pool PostgreSQL ausente: pip install psycopg-pool"
        ) from exc

    dsn, kwargs = _pg_config()
    pool_key = (dsn, tuple(sorted(kwargs.items())), postgres_schema())
    if _PG_POOL is not None and _PG_POOL_KEY == pool_key:
        return _PG_POOL

    with _PG_POOL_LOCK:
        if _PG_POOL is not None and _PG_POOL_KEY == pool_key:
            return _PG_POOL
        previous = _PG_POOL
        try:
            min_size = max(1, int(os.getenv("LICITANEXO_PG_POOL_MIN", "1")))
            max_size = max(
                min_size,
                int(os.getenv("LICITANEXO_PG_POOL_MAX", "6")),
            )
            pool = ConnectionPool(
                conninfo=dsn,
                kwargs=kwargs,
                min_size=min_size,
                max_size=max_size,
                timeout=float(os.getenv("LICITANEXO_PG_POOL_TIMEOUT", "12")),
                max_idle=float(os.getenv("LICITANEXO_PG_POOL_MAX_IDLE", "300")),
                max_lifetime=float(
                    os.getenv("LICITANEXO_PG_POOL_MAX_LIFETIME", "1800")
                ),
                configure=_configure_pg_connection,
                open=False,
            )
            pool.open(wait=True, timeout=12)
        except Exception as exc:
            if _looks_like_auth_failure(exc):
                _PG_AUTH_BLOCKED_UNTIL = time.monotonic() + 300
                _PG_AUTH_BLOCKED_REASON = str(exc).splitlines()[0][:240]
            raise
        _PG_POOL = pool
        _PG_POOL_KEY = pool_key
        if previous is not None:
            try:
                previous.close()
            except Exception:
                pass
        return pool


def _pg_connect():
    global _PG_AUTH_BLOCKED_UNTIL, _PG_AUTH_BLOCKED_REASON
    if time.monotonic() < _PG_AUTH_BLOCKED_UNTIL:
        remaining = max(1, int(_PG_AUTH_BLOCKED_UNTIL - time.monotonic()))
        raise sqlite3.OperationalError(
            f"PostgreSQL bloqueado após falha de autenticação. Aguarde {remaining}s. "
            f"{_PG_AUTH_BLOCKED_REASON}"
        )
    try:
        pool = _pg_pool()
        lease = pool.connection(
            timeout=float(os.getenv("LICITANEXO_PG_POOL_TIMEOUT", "12"))
        )
        raw = lease.__enter__()
    except Exception as exc:
        if _looks_like_auth_failure(exc):
            _PG_AUTH_BLOCKED_UNTIL = time.monotonic() + 300
            _PG_AUTH_BLOCKED_REASON = str(exc).splitlines()[0][:240]
        raise
    return PostgresCompatConnection(raw, lease=lease)


class ClosingSQLiteConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect_runtime(sqlite_path, search_fold=None):
    if using_postgres():
        return _pg_connect()
    path = Path(sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        str(path),
        timeout=30,
        factory=ClosingSQLiteConnection,
    )
    connection.row_factory = sqlite3.Row
    if search_fold is not None:
        connection.create_function("search_fold", 1, search_fold)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection
