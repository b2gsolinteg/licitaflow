import json
from datetime import datetime, timezone

from .db_runtime import connect_runtime, using_postgres


class UsageLimitError(RuntimeError):
    pass


def _month_bounds_utc(reference=None):
    now = reference or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    if using_postgres():
        return start, end
    # SQLite legado armazena timestamps como TEXT.
    return (
        start.strftime("%Y-%m-%d %H:%M:%S+00:00"),
        end.strftime("%Y-%m-%d %H:%M:%S+00:00"),
    )


class UsageService:
    DEFAULT_ANALYSIS_LIMIT = 15

    def __init__(self, database_path):
        self.path = str(database_path)
        if not using_postgres():
            self.ensure_schema()

    def connect(self):
        return connect_runtime(self.path)

    def ensure_schema(self):
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS usage_settings(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS usage_company_limits(
                    company_id TEXT PRIMARY KEY,
                    analysis_monthly_limit INTEGER,
                    estimated_analysis_cost_cents REAL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS usage_events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id TEXT NOT NULL,
                    user_id TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL,
                    units INTEGER NOT NULL DEFAULT 1,
                    estimated_cost_cents REAL NOT NULL DEFAULT 0,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_usage_events_company_month
                    ON usage_events(company_id, event_type, created_at DESC);
                CREATE INDEX IF NOT EXISTS ix_usage_events_type
                    ON usage_events(event_type, created_at DESC);
                """
            )
            conn.execute(
                """
                INSERT INTO usage_settings(key,value)
                VALUES ('essential_analysis_monthly_limit', ?)
                ON CONFLICT(key) DO NOTHING
                """,
                (str(self.DEFAULT_ANALYSIS_LIMIT),),
            )
            conn.execute(
                """
                INSERT INTO usage_settings(key,value)
                VALUES ('estimated_analysis_cost_cents', '0')
                ON CONFLICT(key) DO NOTHING
                """
            )

    def _setting(self, key, default):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT value FROM usage_settings WHERE key=?", (key,)
            ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_settings(key,value,updated_at)
                VALUES (?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value, updated_at=CURRENT_TIMESTAMP
                """,
                (str(key), str(value)),
            )

    def default_analysis_limit(self):
        try:
            return max(
                0,
                int(
                    float(
                        self._setting(
                            "essential_analysis_monthly_limit",
                            self.DEFAULT_ANALYSIS_LIMIT,
                        )
                    )
                ),
            )
        except (TypeError, ValueError):
            return self.DEFAULT_ANALYSIS_LIMIT

    def default_estimated_cost_cents(self):
        try:
            return max(
                0.0,
                float(self._setting("estimated_analysis_cost_cents", 0)),
            )
        except (TypeError, ValueError):
            return 0.0

    def company_policy(self, company_id):
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT analysis_monthly_limit, estimated_analysis_cost_cents
                FROM usage_company_limits WHERE company_id=?
                """,
                (str(company_id),),
            ).fetchone()
        return {
            "analysis_monthly_limit": (
                int(row["analysis_monthly_limit"])
                if row and row["analysis_monthly_limit"] is not None
                else self.default_analysis_limit()
            ),
            "estimated_analysis_cost_cents": (
                float(row["estimated_analysis_cost_cents"])
                if row and row["estimated_analysis_cost_cents"] is not None
                else self.default_estimated_cost_cents()
            ),
        }

    def set_company_policy(
        self,
        company_id,
        analysis_limit=None,
        estimated_cost_cents=None,
    ):
        if analysis_limit is not None and int(analysis_limit) < 0:
            raise ValueError("O limite não pode ser negativo.")
        if estimated_cost_cents is not None and float(estimated_cost_cents) < 0:
            raise ValueError("O custo estimado não pode ser negativo.")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_company_limits(
                    company_id,analysis_monthly_limit,estimated_analysis_cost_cents,updated_at
                ) VALUES (?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(company_id) DO UPDATE SET
                    analysis_monthly_limit=excluded.analysis_monthly_limit,
                    estimated_analysis_cost_cents=excluded.estimated_analysis_cost_cents,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    str(company_id),
                    None if analysis_limit is None else int(analysis_limit),
                    None if estimated_cost_cents is None else float(estimated_cost_cents),
                ),
            )

    def month_usage(self, company_id, event_type="analysis"):
        month_start, next_month = _month_bounds_utc()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(units),0) AS units,
                       COALESCE(SUM(estimated_cost_cents),0) AS cost
                FROM usage_events
                WHERE company_id=? AND event_type=?
                  AND created_at >= ?
                  AND created_at < ?
                """,
                (str(company_id), str(event_type), month_start, next_month),
            ).fetchone()
        return {
            "units": int(row["units"] or 0),
            "cost_cents": float(row["cost"] or 0),
        }

    def analysis_status(self, company_id):
        policy = self.company_policy(company_id)
        used = self.month_usage(company_id, "analysis")
        limit = int(policy["analysis_monthly_limit"])
        remaining = max(0, limit - used["units"]) if limit > 0 else None
        return {
            "used": used["units"],
            "limit": limit,
            "remaining": remaining,
            "cost_cents": used["cost_cents"],
            "estimated_unit_cost_cents": policy["estimated_analysis_cost_cents"],
            "allowed": (limit == 0 or used["units"] < limit),
        }

    def assert_analysis_allowed(self, company_id):
        status = self.analysis_status(company_id)
        if not status["allowed"]:
            raise UsageLimitError(
                f'Franquia mensal de {status["limit"]} análises atingida. '
                "Fale com a B2G SaaS para ampliar o limite."
            )
        return status

    def record(
        self,
        company_id,
        user_id,
        event_type,
        units=1,
        metadata=None,
        estimated_cost_cents=None,
    ):
        units = max(1, int(units))
        if estimated_cost_cents is None:
            estimated_cost_cents = (
                self.company_policy(company_id)["estimated_analysis_cost_cents"] * units
                if event_type == "analysis"
                else 0
            )
        payload = json.dumps(
            metadata or {}, ensure_ascii=False, separators=(",", ":")
        )
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_events(
                    company_id,user_id,event_type,units,estimated_cost_cents,metadata
                ) VALUES (?,?,?,?,?,?)
                """,
                (
                    str(company_id),
                    str(user_id or ""),
                    str(event_type),
                    units,
                    max(0.0, float(estimated_cost_cents)),
                    payload[:4000],
                ),
            )

    def record_analysis(self, company_id, user_id, filename="", pages=0):
        self.record(
            company_id,
            user_id,
            "analysis",
            1,
            {"filename": str(filename)[:180], "pages": int(pages or 0)},
        )

    def record_search(self, company_id, user_id, keyword=""):
        self.record(
            company_id,
            user_id,
            "search",
            1,
            {"keyword": str(keyword or "")[:180]},
            estimated_cost_cents=0,
        )

    def company_summary(self, company_id):
        analysis = self.analysis_status(company_id)
        searches = self.month_usage(company_id, "search")
        return {
            **analysis,
            "searches": searches["units"],
        }

    def admin_summary(self):
        month_start, next_month = _month_bounds_utc()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT u.company_id,
                       COALESCE(c.name,'') AS company_name,
                       SUM(CASE WHEN u.event_type='analysis' THEN u.units ELSE 0 END) AS analyses,
                       SUM(CASE WHEN u.event_type='search' THEN u.units ELSE 0 END) AS searches,
                       SUM(u.estimated_cost_cents) AS estimated_cost_cents,
                       MAX(u.created_at) AS last_activity
                FROM usage_events u
                LEFT JOIN companies c ON c.id=u.company_id
                WHERE u.created_at >= ?
                  AND u.created_at < ?
                GROUP BY u.company_id, c.name
                ORDER BY estimated_cost_cents DESC, analyses DESC, searches DESC
                """,
                (month_start, next_month),
            ).fetchall()
        result = []
        for row in rows:
            policy = self.company_policy(row["company_id"])
            result.append(
                {
                    "company_id": row["company_id"],
                    "company_name": row["company_name"],
                    "analyses": int(row["analyses"] or 0),
                    "searches": int(row["searches"] or 0),
                    "estimated_cost_cents": float(
                        row["estimated_cost_cents"] or 0
                    ),
                    "analysis_limit": int(policy["analysis_monthly_limit"]),
                    "last_activity": row["last_activity"],
                }
            )
        return result

    def events(self, limit=300):
        with self.connect() as conn:
            return [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT u.*, COALESCE(c.name,'') AS company_name
                    FROM usage_events u
                    LEFT JOIN companies c ON c.id=u.company_id
                    ORDER BY u.created_at DESC, u.id DESC LIMIT ?
                    """,
                    (int(limit),),
                ).fetchall()
            ]
