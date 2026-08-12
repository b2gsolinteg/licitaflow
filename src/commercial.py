import hashlib
import re
import sqlite3
from .db_runtime import connect_runtime, using_postgres
from dataclasses import dataclass

VALID_SUBSCRIPTION_STATES={"trialing","active","past_due","canceled","expired","blocked"}
VALID_PLANS={"ESSENTIAL","PRO","BUSINESS"}

def normalize_email(v): return str(v or "").strip().lower()
def normalize_cnpj(v): return re.sub(r"\D","",str(v or ""))
def valid_cnpj(v):
    c=normalize_cnpj(v)
    if len(c)!=14 or c==c[0]*14: return False
    def d(base,w):
        r=sum(int(n)*x for n,x in zip(base,w))%11
        return "0" if r<2 else str(11-r)
    d1=d(c[:12],[5,4,3,2,9,8,7,6,5,4,3,2]); d2=d(c[:12]+d1,[6,5,4,3,2,9,8,7,6,5,4,3,2])
    return c[-2:]==d1+d2
def fingerprint(ip):
    s=str(ip or "").strip(); return hashlib.sha256(s.encode()).hexdigest()[:20] if s else ""
@dataclass(frozen=True)
class TrialDecision:
    allowed: bool; outcome: str; message: str; risk_score: int=0
class CommercialFoundation:
    def __init__(self,database_path,trial_days=7):
        self.path=str(database_path); self.trial_days=max(int(trial_days),1); 
        if not using_postgres():
            self.ensure_schema()
    def connect(self):
        return connect_runtime(self.path)
    def ensure_schema(self):
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS commercial_trial_claims(id INTEGER PRIMARY KEY AUTOINCREMENT,cnpj TEXT NOT NULL,email TEXT NOT NULL,ip_fingerprint TEXT NOT NULL DEFAULT '',outcome TEXT NOT NULL,risk_score INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE INDEX IF NOT EXISTS ix_commercial_trial_cnpj ON commercial_trial_claims(cnpj,created_at DESC);
            CREATE INDEX IF NOT EXISTS ix_commercial_trial_email ON commercial_trial_claims(email,created_at DESC);
            CREATE TABLE IF NOT EXISTS commercial_plans(code TEXT PRIMARY KEY,name TEXT NOT NULL,monthly_price_cents INTEGER NOT NULL,active INTEGER NOT NULL DEFAULT 1,sort_order INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS commercial_subscriptions(company_id TEXT PRIMARY KEY,plan_code TEXT NOT NULL DEFAULT 'ESSENTIAL',status TEXT NOT NULL DEFAULT 'trialing',trial_started_at TEXT,trial_ends_at TEXT,current_period_start TEXT,current_period_end TEXT,billing_cycle TEXT NOT NULL DEFAULT 'monthly',payment_method TEXT NOT NULL DEFAULT '',updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS commercial_events(id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,company_id TEXT NOT NULL DEFAULT '',email TEXT NOT NULL DEFAULT '',cnpj TEXT NOT NULL DEFAULT '',details TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            """)
            for row in [('ESSENTIAL','LicitaNexo Essential',4990,1,10),('PRO','LicitaNexo Pro',9990,0,20),('BUSINESS','LicitaNexo Business',19990,0,30)]:
                c.execute("INSERT OR IGNORE INTO commercial_plans(code,name,monthly_price_cents,active,sort_order) VALUES (?,?,?,?,?)",row)
    def evaluate_trial(self,cnpj,email,ip=''):
        cn=normalize_cnpj(cnpj); em=normalize_email(email)
        if not valid_cnpj(cn): return TrialDecision(False,'blocked','Informe um CNPJ válido.')
        if not em or '@' not in em: return TrialDecision(False,'blocked','Informe um e-mail válido.')
        with self.connect() as c:
            bc=c.execute("SELECT 1 FROM commercial_trial_claims WHERE cnpj=? AND outcome IN ('allowed','review','activated') LIMIT 1",(cn,)).fetchone()
            be=c.execute("SELECT 1 FROM commercial_trial_claims WHERE email=? AND outcome IN ('allowed','review','activated') LIMIT 1",(em,)).fetchone()
            try: ec=c.execute("SELECT 1 FROM access_requests WHERE replace(replace(replace(replace(cnpj,'.',''),'/',''),'-',''),' ','')=? LIMIT 1",(cn,)).fetchone()
            except sqlite3.Error: ec=None
            try: ee=c.execute("SELECT 1 FROM users WHERE lower(email)=? LIMIT 1",(em,)).fetchone()
            except sqlite3.Error: ee=None
            if bc or ec: return TrialDecision(False,'blocked','Este CNPJ já utilizou ou solicitou o período gratuito.')
            if be or ee: return TrialDecision(False,'blocked','Este e-mail já utilizou ou solicitou o período gratuito.')
            fp=fingerprint(ip); recent=c.execute("SELECT COUNT(*) FROM commercial_trial_claims WHERE ip_fingerprint=? AND created_at>=datetime('now','-30 days')",(fp,)).fetchone()[0] if fp else 0
        return TrialDecision(True,'review','Solicitação recebida para validação rápida.',40) if recent>=2 else TrialDecision(True,'allowed','Elegível para o teste gratuito.',0)
    def record_trial_request(self,cnpj,email,ip,outcome,risk_score=0):
        with self.connect() as c:
            cn=normalize_cnpj(cnpj); em=normalize_email(email)
            c.execute("INSERT INTO commercial_trial_claims(cnpj,email,ip_fingerprint,outcome,risk_score) VALUES (?,?,?,?,?)",(cn,em,fingerprint(ip),outcome,int(risk_score)))
            c.execute("INSERT INTO commercial_events(event_type,email,cnpj,details) VALUES ('trial_request',?,?,?)",(em,cn,f'outcome={outcome};risk={int(risk_score)}'))
    def plans(self,include_inactive=False):
        with self.connect() as c:
            q="SELECT * FROM commercial_plans"+("" if include_inactive else " WHERE active=1")+" ORDER BY sort_order,code"
            return [dict(r) for r in c.execute(q).fetchall()]
