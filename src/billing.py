import calendar
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

from .db_runtime import connect_runtime, using_postgres


CYCLES = {
    "monthly": ("Mensal", 1, 4990),
    "quarterly": ("Trimestral", 3, 13990),
    "semiannual": ("Semestral", 6, 26990),
    "annual": ("Anual", 12, 49990),
}

MP_TO_LOCAL = {
    "pending": "pending",
    "authorized": "active",
    "paused": "past_due",
    "canceled": "canceled",
    "cancelled": "canceled",
}


class BillingError(RuntimeError):
    pass


def _utcnow():
    return datetime.now(timezone.utc)


def _timestamp_value(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _add_months(value, months):
    month_index = value.month - 1 + int(months)
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class MercadoPagoGateway:
    API_BASE = "https://api.mercadopago.com"

    def __init__(self, access_token=None, public_url=None, timeout=20):
        self.access_token = (
            access_token or os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
        ).strip()
        self.public_url = (
            public_url or os.getenv("LICITANEXO_PUBLIC_URL", "")
        ).strip().rstrip("/")
        self.timeout = int(timeout)

    @property
    def configured(self):
        return bool(
            self.access_token
            and self.public_url.startswith(("https://", "http://"))
        )

    def _request(self, method, path, payload=None, idempotency_key=None):
        if not self.configured:
            raise BillingError("Gateway ainda não configurado no servidor.")
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        data = (
            json.dumps(payload, ensure_ascii=False).encode("utf-8")
            if payload is not None
            else None
        )
        request = urllib.request.Request(
            self.API_BASE + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise BillingError(
                f"Mercado Pago HTTP {exc.code}: {body[:400]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise BillingError(
                f"Falha de conexão com Mercado Pago: {exc.reason}"
            ) from exc

    def create_subscription(
        self,
        payer_email,
        company_id,
        cycle,
        external_reference,
    ):
        if cycle not in CYCLES:
            raise BillingError("Ciclo inválido.")
        label, months, cents = CYCLES[cycle]
        payload = {
            "reason": f"LicitaNexo Essential · {label}",
            "external_reference": external_reference,
            "payer_email": str(payer_email).strip().lower(),
            "auto_recurring": {
                "frequency": months,
                "frequency_type": "months",
                "transaction_amount": cents / 100,
                "currency_id": "BRL",
            },
            "back_url": self.public_url,
            "status": "pending",
        }
        return self._request(
            "POST",
            "/preapproval",
            payload,
            external_reference,
        )

    def get_subscription(self, provider_id):
        return self._request("GET", f"/preapproval/{provider_id}")

    def cancel_subscription(self, provider_id):
        return self._request(
            "PUT",
            f"/preapproval/{provider_id}",
            {"status": "canceled"},
        )


class BillingService:
    def __init__(self, database_path, gateway=None):
        self.path = str(database_path)
        self.gateway = gateway or MercadoPagoGateway()
        if not using_postgres():
            self.ensure_schema()

    def connect(self):
        return connect_runtime(self.path)

    def ensure_schema(self):
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS commercial_subscriptions(
                  company_id TEXT PRIMARY KEY,
                  plan_code TEXT NOT NULL DEFAULT 'ESSENTIAL',
                  status TEXT NOT NULL DEFAULT 'trialing',
                  trial_started_at TEXT,
                  trial_ends_at TEXT,
                  current_period_start TEXT,
                  current_period_end TEXT,
                  billing_cycle TEXT NOT NULL DEFAULT 'monthly',
                  payment_method TEXT NOT NULL DEFAULT '',
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS billing_checkouts(
                  id TEXT PRIMARY KEY, company_id TEXT NOT NULL, payer_email TEXT NOT NULL,
                  plan_code TEXT NOT NULL DEFAULT 'ESSENTIAL', billing_cycle TEXT NOT NULL,
                  amount_cents INTEGER NOT NULL, provider TEXT NOT NULL DEFAULT 'mercadopago',
                  provider_id TEXT NOT NULL DEFAULT '', provider_status TEXT NOT NULL DEFAULT 'created',
                  local_status TEXT NOT NULL DEFAULT 'pending', init_point TEXT NOT NULL DEFAULT '',
                  external_reference TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS ix_billing_company ON billing_checkouts(company_id,created_at DESC);
                CREATE TABLE IF NOT EXISTS billing_events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT, checkout_id TEXT NOT NULL DEFAULT '',
                  company_id TEXT NOT NULL DEFAULT '', event_type TEXT NOT NULL,
                  provider_status TEXT NOT NULL DEFAULT '', details TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                """
            )

    @staticmethod
    def cycles():
        return [
            {
                "code": code,
                "label": values[0],
                "months": values[1],
                "amount_cents": values[2],
                "amount": values[2] / 100,
                "monthly_equivalent": values[2] / 100 / values[1],
            }
            for code, values in CYCLES.items()
        ]

    @property
    def gateway_configured(self):
        return self.gateway.configured

    def create_checkout(self, company_id, payer_email, cycle):
        if cycle not in CYCLES:
            raise BillingError("Ciclo inválido.")
        _, _, cents = CYCLES[cycle]
        checkout_id = str(uuid.uuid4())
        external_reference = f"LN-{company_id}-{checkout_id[:10]}"
        data = self.gateway.create_subscription(
            payer_email,
            company_id,
            cycle,
            external_reference,
        )
        provider_id = str(data.get("id") or "")
        init_point = str(data.get("init_point") or "")
        provider_status = str(data.get("status") or "pending")
        if not provider_id or not init_point:
            raise BillingError("Gateway não retornou link de checkout.")

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO billing_checkouts(
                    id,company_id,payer_email,billing_cycle,amount_cents,
                    provider_id,provider_status,local_status,init_point,external_reference
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    checkout_id,
                    str(company_id),
                    str(payer_email).strip().lower(),
                    cycle,
                    cents,
                    provider_id,
                    provider_status,
                    "pending",
                    init_point,
                    external_reference,
                ),
            )
            connection.execute(
                """
                INSERT INTO billing_events(
                    checkout_id,company_id,event_type,provider_status,details
                ) VALUES (?,?,'checkout_created',?,?)
                """,
                (
                    checkout_id,
                    str(company_id),
                    provider_status,
                    external_reference,
                ),
            )
        return {
            "id": checkout_id,
            "provider_id": provider_id,
            "init_point": init_point,
            "status": provider_status,
        }

    def _apply(self, connection, company_id, cycle, provider_status):
        local_status = MP_TO_LOCAL.get(provider_status, "past_due")
        months = CYCLES.get(cycle, CYCLES["monthly"])[1]
        now = _utcnow()
        period_end = _add_months(now, months)
        now_value = _timestamp_value(now)
        end_value = _timestamp_value(period_end)

        if local_status == "active":
            connection.execute(
                """
                INSERT INTO commercial_subscriptions(
                    company_id,plan_code,status,current_period_start,current_period_end,
                    billing_cycle,payment_method,updated_at
                ) VALUES (?,'ESSENTIAL','active',?,?,?,'mercadopago',?)
                ON CONFLICT(company_id) DO UPDATE SET
                    status='active',
                    current_period_start=excluded.current_period_start,
                    current_period_end=excluded.current_period_end,
                    billing_cycle=excluded.billing_cycle,
                    payment_method='mercadopago',
                    updated_at=excluded.updated_at
                """,
                (
                    str(company_id),
                    now_value,
                    end_value,
                    cycle,
                    now_value,
                ),
            )
            connection.execute(
                """
                UPDATE companies
                SET plan='Essential', subscription_status='active', subscription_ends_at=?
                WHERE id=?
                """,
                (end_value, str(company_id)),
            )
        elif local_status in {"past_due", "canceled"}:
            connection.execute(
                """
                INSERT INTO commercial_subscriptions(
                    company_id,plan_code,status,billing_cycle,payment_method,updated_at
                ) VALUES (?,'ESSENTIAL',?,?,'mercadopago',?)
                ON CONFLICT(company_id) DO UPDATE SET
                    status=excluded.status,
                    billing_cycle=excluded.billing_cycle,
                    payment_method='mercadopago',
                    updated_at=excluded.updated_at
                """,
                (str(company_id), local_status, cycle, now_value),
            )
            connection.execute(
                "UPDATE companies SET subscription_status=? WHERE id=?",
                (local_status, str(company_id)),
            )
        return local_status

    def sync_checkout(self, checkout_id):
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM billing_checkouts WHERE id=?",
                (checkout_id,),
            ).fetchone()
        if not row:
            raise BillingError("Cobrança não encontrada.")

        data = self.gateway.get_subscription(row["provider_id"])
        provider_status = str(data.get("status") or "pending")
        with self.connect() as connection:
            local_status = self._apply(
                connection,
                row["company_id"],
                row["billing_cycle"],
                provider_status,
            )
            connection.execute(
                """
                UPDATE billing_checkouts
                SET provider_status=?, local_status=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (provider_status, local_status, checkout_id),
            )
            connection.execute(
                """
                INSERT INTO billing_events(
                    checkout_id,company_id,event_type,provider_status,details
                ) VALUES (?,?,'checkout_synced',?,?)
                """,
                (
                    checkout_id,
                    row["company_id"],
                    provider_status,
                    str(data.get("next_payment_date") or "")[:1000],
                ),
            )
        return {
            "provider_status": provider_status,
            "local_status": local_status,
        }

    def sync_provider_subscription(self, provider_id):
        provider_id = str(provider_id or "").strip()
        if not provider_id:
            raise BillingError("Identificador do provedor não informado.")
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id FROM billing_checkouts
                WHERE provider_id=?
                ORDER BY created_at DESC LIMIT 1
                """,
                (provider_id,),
            ).fetchone()
        if not row:
            raise BillingError("Cobrança do provedor não encontrada.")
        return self.sync_checkout(row["id"])

    def cancel(self, checkout_id):
        with self.connect() as connection:
            row = connection.execute(
                "SELECT provider_id FROM billing_checkouts WHERE id=?",
                (checkout_id,),
            ).fetchone()
        if not row:
            raise BillingError("Assinatura não encontrada.")
        self.gateway.cancel_subscription(row["provider_id"])
        return self.sync_checkout(checkout_id)

    def list_company(self, company_id, limit=20):
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT * FROM billing_checkouts
                    WHERE company_id=? ORDER BY created_at DESC LIMIT ?
                    """,
                    (str(company_id), int(limit)),
                ).fetchall()
            ]

    def list_all(self, limit=300):
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM billing_checkouts ORDER BY created_at DESC LIMIT ?",
                    (int(limit),),
                ).fetchall()
            ]

    def metrics(self):
        with self.connect() as connection:
            return {
                status: int(
                    connection.execute(
                        "SELECT COUNT(*) FROM billing_checkouts WHERE local_status=?",
                        (status,),
                    ).fetchone()[0]
                )
                for status in ("active", "pending", "canceled", "past_due")
            }
