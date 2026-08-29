import calendar
import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .db_runtime import connect_runtime, using_postgres


# A oferta pública é R$ 29,90/mês. Os ciclos maiores permanecem disponíveis
# sem desconto implícito; isso evita preços históricos de R$ 49,90 no checkout.
CYCLES = {
    "monthly": ("Mensal", 1, 2990),
    "quarterly": ("Trimestral", 3, 8970),
    "semiannual": ("Semestral", 6, 17940),
    "annual": ("Anual", 12, 35880),
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


def _append_query(url, **params):
    if not url:
        return ""
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({k: str(v) for k, v in params.items() if v is not None})
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class MercadoPagoGateway:
    provider_name = "mercadopago"
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
            raise BillingError("Gateway Mercado Pago ainda não configurado no servidor.")
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


class InfinitePayGateway:
    """Checkout Integrado da InfinitePay.

    A API pública usa a InfiniteTag (handle) para criar o link. Não existe segredo
    embutido neste módulo. A confirmação sempre é feita via /payment_check e o
    LicitaNexo valida `paid` e o valor original antes de liberar a conta.
    """

    provider_name = "infinitepay"
    API_BASE = "https://api.checkout.infinitepay.io"

    def __init__(self, handle=None, public_url=None, webhook_url=None, timeout=20):
        self.handle = (
            handle or os.getenv("INFINITEPAY_HANDLE", "b2g-solinteg")
        ).strip().lstrip("$")
        self.public_url = (
            public_url or os.getenv("LICITANEXO_PUBLIC_URL", "http://127.0.0.1:8501")
        ).strip().rstrip("/")
        self.webhook_url = (
            webhook_url or os.getenv("INFINITEPAY_WEBHOOK_URL", "")
        ).strip()
        self.timeout = int(timeout)

    @property
    def configured(self):
        return bool(self.handle)

    @property
    def display_name(self):
        return "InfinitePay"

    def _request(self, path, payload):
        if not self.configured:
            raise BillingError("InfinitePay ainda não configurada no servidor.")
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.API_BASE + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw or "{}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise BillingError(
                f"InfinitePay HTTP {exc.code}: {body[:400]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise BillingError(
                f"Falha de conexão com InfinitePay: {exc.reason}"
            ) from exc
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise BillingError("Resposta inválida da InfinitePay.") from exc

    def create_subscription(
        self,
        payer_email,
        company_id,
        cycle,
        external_reference,
    ):
        if cycle not in CYCLES:
            raise BillingError("Ciclo inválido.")
        label, _, cents = CYCLES[cycle]
        payload = {
            "handle": self.handle,
            "order_nsu": external_reference,
            "items": [
                {
                    "quantity": 1,
                    "price": int(cents),
                    "description": f"LicitaNexo Essential · {label}",
                }
            ],
            "customer": {
                "email": str(payer_email or "").strip().lower(),
            },
        }
        if self.public_url.startswith(("http://", "https://")):
            payload["redirect_url"] = _append_query(
                self.public_url,
                billing_return="infinitepay",
            )
        # Webhook só é enviado quando o deploy informar uma URL pública própria.
        if self.webhook_url.startswith(("http://", "https://")):
            payload["webhook_url"] = self.webhook_url

        response = self._request("/links", payload)
        checkout_url = str(response.get("url") or "").strip()
        if not checkout_url:
            raise BillingError("InfinitePay não retornou o link de checkout.")
        return {
            # No Checkout Integrado, o order_nsu é o identificador estável do pedido.
            "id": external_reference,
            "init_point": checkout_url,
            "status": "pending",
        }

    def check_payment(self, order_nsu, transaction_nsu, slug):
        if not all(str(value or "").strip() for value in (order_nsu, transaction_nsu, slug)):
            raise BillingError(
                "Dados de confirmação da InfinitePay incompletos. "
                "Conclua o pagamento e use o botão Continuar no checkout."
            )
        return self._request(
            "/payment_check",
            {
                "handle": self.handle,
                "order_nsu": str(order_nsu).strip(),
                "transaction_nsu": str(transaction_nsu).strip(),
                "slug": str(slug).strip(),
            },
        )


class BillingService:
    def __init__(self, database_path, gateway=None):
        self.path = str(database_path)
        self.gateway = gateway or self._default_gateway()
        if not using_postgres():
            self.ensure_schema()
        # A redirect_url da InfinitePay volta com order_nsu/transaction_nsu/slug.
        # Capturamos esses dados sem depender de uma rota HTTP adicional do Streamlit.
        self._capture_streamlit_infinitepay_return()

    @staticmethod
    def _default_gateway():
        provider = os.getenv("LICITANEXO_PAYMENT_PROVIDER", "infinitepay").strip().lower()
        if provider in {"mercadopago", "mercado_pago", "mp"}:
            return MercadoPagoGateway()
        return InfinitePayGateway()

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

    @property
    def gateway_name(self):
        return getattr(self.gateway, "display_name", None) or (
            "Mercado Pago" if getattr(self.gateway, "provider_name", "") == "mercadopago" else "Gateway"
        )

    def create_checkout(self, company_id, payer_email, cycle):
        if cycle not in CYCLES:
            raise BillingError("Ciclo inválido.")
        _, _, cents = CYCLES[cycle]
        checkout_id = str(uuid.uuid4())
        external_reference = f"LNX-{str(company_id)[:12]}-{checkout_id[:10]}"
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
        provider_name = str(getattr(self.gateway, "provider_name", "gateway") or "gateway")

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO billing_checkouts(
                    id,company_id,payer_email,billing_cycle,amount_cents,provider,
                    provider_id,provider_status,local_status,init_point,external_reference
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    checkout_id,
                    str(company_id),
                    str(payer_email).strip().lower(),
                    cycle,
                    cents,
                    provider_name,
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
            "provider": provider_name,
            "init_point": init_point,
            "status": provider_status,
            "order_nsu": external_reference,
        }

    def _apply(self, connection, company_id, cycle, provider_status, payment_method=None):
        local_status = MP_TO_LOCAL.get(provider_status, "past_due")
        months = CYCLES.get(cycle, CYCLES["monthly"])[1]
        now = _utcnow()
        period_end = _add_months(now, months)
        now_value = _timestamp_value(now)
        end_value = _timestamp_value(period_end)
        method = str(payment_method or getattr(self.gateway, "provider_name", "gateway") or "gateway")

        if local_status == "active":
            connection.execute(
                """
                INSERT INTO commercial_subscriptions(
                    company_id,plan_code,status,current_period_start,current_period_end,
                    billing_cycle,payment_method,updated_at
                ) VALUES (?,'ESSENTIAL','active',?,?,?,?,?)
                ON CONFLICT(company_id) DO UPDATE SET
                    status='active',
                    current_period_start=excluded.current_period_start,
                    current_period_end=excluded.current_period_end,
                    billing_cycle=excluded.billing_cycle,
                    payment_method=excluded.payment_method,
                    updated_at=excluded.updated_at
                """,
                (
                    str(company_id),
                    now_value,
                    end_value,
                    cycle,
                    method,
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
                ) VALUES (?,'ESSENTIAL',?,?,?,?)
                ON CONFLICT(company_id) DO UPDATE SET
                    status=excluded.status,
                    billing_cycle=excluded.billing_cycle,
                    payment_method=excluded.payment_method,
                    updated_at=excluded.updated_at
                """,
                (str(company_id), local_status, cycle, method, now_value),
            )
            connection.execute(
                "UPDATE companies SET subscription_status=? WHERE id=?",
                (local_status, str(company_id)),
            )
        return local_status

    def capture_infinitepay_return(
        self,
        order_nsu,
        transaction_nsu,
        slug,
        receipt_url="",
        capture_method="",
    ):
        order_nsu = str(order_nsu or "").strip()
        transaction_nsu = str(transaction_nsu or "").strip()
        slug = str(slug or "").strip()
        if not order_nsu or not transaction_nsu or not slug:
            return None
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM billing_checkouts
                WHERE external_reference=? AND provider='infinitepay'
                ORDER BY created_at DESC LIMIT 1
                """,
                (order_nsu,),
            ).fetchone()
            if not row:
                return None
            details = json.dumps(
                {
                    "order_nsu": order_nsu,
                    "transaction_nsu": transaction_nsu,
                    "slug": slug,
                    "receipt_url": str(receipt_url or "")[:1000],
                    "capture_method": str(capture_method or "")[:80],
                },
                ensure_ascii=False,
            )
            connection.execute(
                """
                INSERT INTO billing_events(
                    checkout_id,company_id,event_type,provider_status,details
                ) VALUES (?,?,'infinitepay_return','returned',?)
                """,
                (row["id"], row["company_id"], details),
            )
        return str(row["id"])

    def _latest_infinitepay_return(self, connection, checkout_id):
        event = connection.execute(
            """
            SELECT details FROM billing_events
            WHERE checkout_id=? AND event_type='infinitepay_return'
            ORDER BY created_at DESC, id DESC LIMIT 1
            """,
            (checkout_id,),
        ).fetchone()
        if not event:
            return None
        try:
            return json.loads(event["details"] or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    def _capture_streamlit_infinitepay_return(self):
        if getattr(self.gateway, "provider_name", "") != "infinitepay":
            return
        try:
            import streamlit as st

            params = st.query_params
            order_nsu = str(params.get("order_nsu", "") or "").strip()
            transaction_nsu = str(params.get("transaction_nsu", "") or "").strip()
            slug = str(params.get("slug", "") or "").strip()
            if not (order_nsu and transaction_nsu and slug):
                return
            checkout_id = self.capture_infinitepay_return(
                order_nsu,
                transaction_nsu,
                slug,
                params.get("receipt_url", ""),
                params.get("capture_method", ""),
            )
            if not checkout_id:
                return
            st.session_state.billing_checkout_id = checkout_id
            st.session_state.billing_return_provider = "infinitepay"
            # Confirma automaticamente no servidor; redirect_url isolada nunca libera acesso.
            try:
                result = self._sync_infinitepay_checkout(checkout_id)
                st.session_state.billing_payment_result = result
            except BillingError as exc:
                st.session_state.billing_payment_error = str(exc)
        except Exception:
            # A camada de billing também é usada por testes/CLI sem contexto Streamlit.
            return

    def _sync_infinitepay_checkout(self, checkout_id):
        if not hasattr(self.gateway, "check_payment"):
            raise BillingError("Gateway atual não suporta validação InfinitePay.")
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM billing_checkouts WHERE id=?",
                (checkout_id,),
            ).fetchone()
            if not row:
                raise BillingError("Cobrança não encontrada.")
            if row["local_status"] == "active":
                return {"provider_status": "authorized", "local_status": "active"}
            meta = self._latest_infinitepay_return(connection, checkout_id)
        if not meta:
            raise BillingError(
                "Ainda não recebemos os dados de retorno da InfinitePay. "
                "Finalize o pagamento e clique em Continuar no checkout."
            )

        data = self.gateway.check_payment(
            row["external_reference"],
            meta.get("transaction_nsu"),
            meta.get("slug"),
        )
        paid = bool(data.get("success") and data.get("paid"))
        amount = int(data.get("amount") or 0)
        if paid and amount != int(row["amount_cents"]):
            with self.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO billing_events(
                        checkout_id,company_id,event_type,provider_status,details
                    ) VALUES (?,?,'amount_mismatch','blocked',?)
                    """,
                    (
                        checkout_id,
                        row["company_id"],
                        json.dumps(
                            {"expected": int(row["amount_cents"]), "received": amount},
                            ensure_ascii=False,
                        ),
                    ),
                )
            raise BillingError("Pagamento recebido com valor diferente do pedido. Acesso não liberado.")

        provider_status = "authorized" if paid else "pending"
        local_status = "pending"
        with self.connect() as connection:
            if paid:
                local_status = self._apply(
                    connection,
                    row["company_id"],
                    row["billing_cycle"],
                    "authorized",
                    payment_method=f"infinitepay:{data.get('capture_method') or meta.get('capture_method') or 'online'}",
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
                    json.dumps(
                        {
                            "paid": paid,
                            "amount": amount,
                            "paid_amount": int(data.get("paid_amount") or 0),
                            "installments": int(data.get("installments") or 0),
                            "capture_method": str(data.get("capture_method") or ""),
                            "transaction_nsu": str(meta.get("transaction_nsu") or ""),
                            "slug": str(meta.get("slug") or ""),
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
        return {
            "provider_status": provider_status,
            "local_status": local_status,
            "paid": paid,
            "amount": amount,
        }

    def sync_checkout(self, checkout_id):
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM billing_checkouts WHERE id=?",
                (checkout_id,),
            ).fetchone()
        if not row:
            raise BillingError("Cobrança não encontrada.")

        if str(row["provider"] or "") == "infinitepay":
            return self._sync_infinitepay_checkout(checkout_id)

        data = self.gateway.get_subscription(row["provider_id"])
        provider_status = str(data.get("status") or "pending")
        with self.connect() as connection:
            # Evita estender o mesmo período várias vezes ao sincronizar o mesmo checkout.
            if row["local_status"] == "active" and MP_TO_LOCAL.get(provider_status) == "active":
                local_status = "active"
            else:
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
                "SELECT provider,provider_id FROM billing_checkouts WHERE id=?",
                (checkout_id,),
            ).fetchone()
        if not row:
            raise BillingError("Assinatura não encontrada.")
        if str(row["provider"] or "") == "infinitepay":
            raise BillingError(
                "Este checkout InfinitePay representa um pagamento avulso do período. "
                "Cancelamento/estorno deve ser tratado no painel da InfinitePay."
            )
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
