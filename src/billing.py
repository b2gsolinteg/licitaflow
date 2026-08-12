import json
import os
import sqlite3
from .db_runtime import connect_runtime, using_postgres
import urllib.error
import urllib.request
import uuid

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

class MercadoPagoGateway:
    API_BASE = "https://api.mercadopago.com"
    def __init__(self, access_token=None, public_url=None, timeout=20):
        self.access_token=(access_token or os.getenv("MERCADOPAGO_ACCESS_TOKEN","")).strip()
        self.public_url=(public_url or os.getenv("LICITANEXO_PUBLIC_URL","")).strip().rstrip("/")
        self.timeout=int(timeout)
    @property
    def configured(self):
        return bool(self.access_token and self.public_url.startswith(("https://","http://")))
    def _request(self, method, path, payload=None, idempotency_key=None):
        if not self.configured:
            raise BillingError("Gateway ainda não configurado no servidor.")
        headers={"Authorization":f"Bearer {self.access_token}","Content-Type":"application/json"}
        if idempotency_key: headers["X-Idempotency-Key"]=idempotency_key
        data=json.dumps(payload).encode("utf-8") if payload is not None else None
        req=urllib.request.Request(self.API_BASE+path,data=data,headers=headers,method=method)
        try:
            with urllib.request.urlopen(req,timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body=exc.read().decode("utf-8",errors="replace")
            raise BillingError(f"Mercado Pago HTTP {exc.code}: {body[:400]}") from exc
        except urllib.error.URLError as exc:
            raise BillingError(f"Falha de conexão com Mercado Pago: {exc.reason}") from exc
    def create_subscription(self, payer_email, company_id, cycle, external_reference):
        if cycle not in CYCLES: raise BillingError("Ciclo inválido.")
        label, months, cents=CYCLES[cycle]
        payload={
            "reason":f"LicitaNexo Essential · {label}",
            "external_reference":external_reference,
            "payer_email":str(payer_email).strip().lower(),
            "auto_recurring":{
                "frequency":months,"frequency_type":"months",
                "transaction_amount":cents/100,"currency_id":"BRL"
            },
            "back_url":self.public_url,
            "status":"pending",
        }
        return self._request("POST","/preapproval",payload,external_reference)
    def get_subscription(self, provider_id):
        return self._request("GET",f"/preapproval/{provider_id}")
    def cancel_subscription(self, provider_id):
        return self._request("PUT",f"/preapproval/{provider_id}",{"status":"canceled"})

class BillingService:
    def __init__(self,database_path,gateway=None):
        self.path=str(database_path); self.gateway=gateway or MercadoPagoGateway(); 
        if not using_postgres():
            self.ensure_schema()
    def connect(self):
        return connect_runtime(self.path)
    def ensure_schema(self):
        with self.connect() as c:
            c.executescript("""
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
            """)
    @staticmethod
    def cycles():
        return [{"code":k,"label":v[0],"months":v[1],"amount_cents":v[2],
                 "amount":v[2]/100,"monthly_equivalent":v[2]/100/v[1]} for k,v in CYCLES.items()]
    @property
    def gateway_configured(self): return self.gateway.configured
    def create_checkout(self,company_id,payer_email,cycle):
        if cycle not in CYCLES: raise BillingError("Ciclo inválido.")
        _,_,cents=CYCLES[cycle]; cid=str(uuid.uuid4()); ref=f"LN-{company_id}-{cid[:10]}"
        data=self.gateway.create_subscription(payer_email,company_id,cycle,ref)
        pid=str(data.get("id") or ""); url=str(data.get("init_point") or ""); ps=str(data.get("status") or "pending")
        if not pid or not url: raise BillingError("Gateway não retornou link de checkout.")
        with self.connect() as c:
            c.execute("""INSERT INTO billing_checkouts
              (id,company_id,payer_email,billing_cycle,amount_cents,provider_id,provider_status,local_status,init_point,external_reference)
              VALUES (?,?,?,?,?,?,?,?,?,?)""",(cid,str(company_id),str(payer_email).strip().lower(),cycle,cents,pid,ps,"pending",url,ref))
            c.execute("""INSERT INTO billing_events(checkout_id,company_id,event_type,provider_status,details)
              VALUES (?,?,'checkout_created',?,?)""",(cid,str(company_id),ps,ref))
        return {"id":cid,"provider_id":pid,"init_point":url,"status":ps}
    def _apply(self,c,company_id,cycle,provider_status):
        local=MP_TO_LOCAL.get(provider_status,"past_due"); months=CYCLES.get(cycle,CYCLES["monthly"])[1]
        if local=="active":
            c.execute("""INSERT INTO commercial_subscriptions(company_id,plan_code,status,current_period_start,current_period_end,billing_cycle,payment_method,updated_at)
              VALUES (?,'ESSENTIAL','active',CURRENT_TIMESTAMP,datetime('now',?),?,'mercadopago',CURRENT_TIMESTAMP)
              ON CONFLICT(company_id) DO UPDATE SET status='active',current_period_start=CURRENT_TIMESTAMP,
              current_period_end=datetime('now',?),billing_cycle=excluded.billing_cycle,payment_method='mercadopago',updated_at=CURRENT_TIMESTAMP""",
              (str(company_id),f"+{months} months",cycle,f"+{months} months"))
            try:
                c.execute("UPDATE companies SET plan='Essential',subscription_status='active',subscription_ends_at=datetime('now',?) WHERE id=?",(f"+{months} months",str(company_id)))
            except sqlite3.Error: pass
        elif local in {"past_due","canceled"}:
            c.execute("""INSERT INTO commercial_subscriptions(company_id,plan_code,status,billing_cycle,payment_method)
              VALUES (?,'ESSENTIAL',?,?,'mercadopago')
              ON CONFLICT(company_id) DO UPDATE SET status=excluded.status,updated_at=CURRENT_TIMESTAMP""",(str(company_id),local,cycle))
            try: c.execute("UPDATE companies SET subscription_status=? WHERE id=?",(local,str(company_id)))
            except sqlite3.Error: pass
        return local
    def sync_checkout(self,checkout_id):
        with self.connect() as c: row=c.execute("SELECT * FROM billing_checkouts WHERE id=?",(checkout_id,)).fetchone()
        if not row: raise BillingError("Cobrança não encontrada.")
        data=self.gateway.get_subscription(row["provider_id"]); ps=str(data.get("status") or "pending")
        with self.connect() as c:
            local=self._apply(c,row["company_id"],row["billing_cycle"],ps)
            c.execute("UPDATE billing_checkouts SET provider_status=?,local_status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(ps,local,checkout_id))
            c.execute("""INSERT INTO billing_events(checkout_id,company_id,event_type,provider_status,details)
              VALUES (?,?,'checkout_synced',?,?)""",(checkout_id,row["company_id"],ps,str(data.get("next_payment_date") or "")))
        return {"provider_status":ps,"local_status":local}
    def cancel(self,checkout_id):
        with self.connect() as c: row=c.execute("SELECT provider_id FROM billing_checkouts WHERE id=?",(checkout_id,)).fetchone()
        if not row: raise BillingError("Assinatura não encontrada.")
        self.gateway.cancel_subscription(row["provider_id"]); return self.sync_checkout(checkout_id)
    def list_company(self,company_id,limit=20):
        with self.connect() as c: return [dict(r) for r in c.execute("SELECT * FROM billing_checkouts WHERE company_id=? ORDER BY created_at DESC LIMIT ?",(str(company_id),int(limit))).fetchall()]
    def list_all(self,limit=300):
        with self.connect() as c: return [dict(r) for r in c.execute("SELECT * FROM billing_checkouts ORDER BY created_at DESC LIMIT ?",(int(limit),)).fetchall()]
    def metrics(self):
        with self.connect() as c:
            return {k:int(c.execute("SELECT COUNT(*) FROM billing_checkouts WHERE local_status=?",(k,)).fetchone()[0]) for k in ("active","pending","canceled","past_due")}
