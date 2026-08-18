from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import database_path
from src.database import Database
from src.formatters import format_brl
from src.mei_catalog import (
    BRAZIL_REGIONS,
    BRAZIL_STATES,
    MeiCatalogService,
    enrich_with_items,
    fetch_price_history_for_item,
)
from src.pncp import MODALITIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo.png"
MEI_VERSION = "1.0 MEI Preview 5"
MEI_PRICE = "R$ 29,90/mês"

db = Database(database_path(PROJECT_ROOT))
catalog = MeiCatalogService(db)

CSS = """
<style>
:root{--ink:#13293D;--ink2:#31516C;--muted:#718397;--brand:#0F8F7B;--brand2:#0A6F61;--brand-soft:#EAF7F4;--navy:#102C46;--gold:#D4A72C;--gold-soft:#FFF8E8;--bg:#F5F7F9;--card:#FFFFFF;--line:#E2E8EE;--soft:#F8FAFC}
html,body,[data-testid="stAppViewContainer"],.stApp{background:var(--bg)!important;color:var(--ink)!important}
header[data-testid="stHeader"]{background:rgba(245,247,249,.97)!important}
.block-container{max-width:1180px!important;padding-top:.55rem!important;padding-bottom:1.5rem!important}
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--line)!important}
[data-testid="stSidebar"]>div:first-child{padding-top:.5rem!important}
[data-testid="stSidebar"] img{max-width:146px!important;display:block;margin:.45rem auto .25rem}
.ln-side-product{font-size:.73rem;color:#6E8293;text-align:center;margin:-.1rem 0 .65rem}
.ln-side-group{font-size:.64rem;font-weight:850;letter-spacing:.10em;color:#98A6B4;text-transform:uppercase;margin:.7rem .15rem .22rem}
[data-testid="stSidebar"] div.stButton>button{justify-content:flex-start!important;text-align:left!important;min-height:2.35rem!important;padding:.45rem .62rem!important;border-radius:10px!important;font-size:.85rem!important;font-weight:730!important;box-shadow:none!important}
[data-testid="stSidebar"] div.stButton>button[kind="secondary"]{background:transparent!important;border:1px solid transparent!important;color:#2C4962!important}
[data-testid="stSidebar"] div.stButton>button[kind="secondary"]:hover{background:#F6F8FA!important;border-color:#ECF0F3!important}
[data-testid="stSidebar"] div.stButton>button[kind="primary"]{background:var(--brand-soft)!important;border:1px solid #CCEAE3!important;border-left:4px solid var(--brand)!important;color:#123F39!important}
.ln-plan{margin-top:.8rem;padding:.7rem .75rem;border-radius:12px;background:#F7F9FB;border:1px solid var(--line);color:#667C90;font-size:.73rem;line-height:1.35}.ln-plan strong{display:block;color:var(--ink);font-size:1.03rem;margin:.08rem 0}.ln-plan b{color:var(--brand2)}
.ln-hero{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1.05rem 1.15rem .95rem;box-shadow:0 6px 20px rgba(31,52,73,.05);margin-bottom:.75rem}.ln-hero-row{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;flex-wrap:wrap}.ln-eyebrow{font-size:.67rem;font-weight:900;letter-spacing:.08em;color:var(--brand2);text-transform:uppercase;margin-bottom:.28rem}.ln-hero h1{font-size:1.65rem;line-height:1.12;color:var(--navy);margin:0 0 .28rem}.ln-hero p{font-size:.9rem;line-height:1.48;color:#63788B;margin:0;max-width:760px}
.ln-value-badges{display:flex;gap:.38rem;flex-wrap:wrap;margin-top:.7rem}.ln-value-badges span{background:#F7F9FB;border:1px solid #E5EAF0;border-radius:999px;padding:.28rem .55rem;color:#466077;font-size:.72rem;font-weight:700}.ln-price-badge{background:var(--gold-soft);border:1px solid #F0DDA1;color:#7A5B04;border-radius:12px;padding:.55rem .75rem;min-width:130px;text-align:center}.ln-price-badge small{display:block;font-size:.61rem;text-transform:uppercase;font-weight:850;letter-spacing:.06em}.ln-price-badge strong{display:block;font-size:1rem;margin-top:.05rem}
.ln-searchbox{background:#fff;border:1px solid var(--line);border-radius:14px;padding:.75rem .85rem .7rem;margin-bottom:.62rem}.ln-search-title{font-size:.92rem;font-weight:850;color:var(--ink);margin:0 0 .25rem}.ln-search-help{font-size:.72rem;color:#7A8D9E;margin:-.05rem 0 .25rem}
[data-testid="stWidgetLabel"] p{font-size:.73rem!important;font-weight:760!important;color:#405A70!important;margin-bottom:.03rem!important}[data-baseweb="input"]>div,[data-baseweb="select"]>div{background:#fff!important;color:var(--ink)!important;border-color:#CAD5DF!important;min-height:2.45rem!important;border-radius:9px!important}input,textarea{color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;background:#fff!important}
div.stButton>button,a[data-testid="stLinkButton"]{border-radius:9px!important;min-height:2.45rem!important;font-weight:800!important}div.stButton>button[kind="primary"]{background:var(--brand)!important;border-color:var(--brand)!important;color:#fff!important}div.stButton>button[kind="primary"]:hover{background:var(--brand2)!important;border-color:var(--brand2)!important}
.ln-resultsbar{display:flex;align-items:end;justify-content:space-between;gap:.8rem;margin:.7rem .05rem .35rem}.ln-resultsbar h2{font-size:1.25rem;color:var(--navy);margin:0}.ln-resultsbar div{font-size:.76rem;color:#75889A}.ln-value-strip{background:#EEF7F5;border:1px solid #D5ECE7;border-radius:11px;padding:.52rem .68rem;color:#3F665F;font-size:.74rem;margin-bottom:.55rem}.ln-value-strip b{color:#155D52}
div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff!important;border:1px solid var(--line)!important;border-radius:15px!important;box-shadow:0 5px 16px rgba(31,52,73,.045)!important;margin-bottom:.55rem!important}div[data-testid="stVerticalBlockBorderWrapper"]>div{padding:.78rem .85rem .7rem!important}
.ln-card-top{display:flex;align-items:center;justify-content:space-between;gap:.5rem;flex-wrap:wrap;margin-bottom:.3rem}.ln-tags{display:flex;gap:.28rem;flex-wrap:wrap;align-items:center}.ln-tag{display:inline-flex;align-items:center;border-radius:999px;padding:.2rem .47rem;font-size:.64rem;font-weight:850}.ln-tag-mode{background:#EAF7F4;color:#0B6F61;border:1px solid #CDEAE3}.ln-tag-cat{background:#EEF3FA;color:#365D88;border:1px solid #DCE6F1}.ln-tag-items{background:#FFF7E6;color:#81610B;border:1px solid #F1DFA7}.ln-portal{display:inline-flex;align-items:center;gap:.28rem;border:1px solid #DEE6ED;background:#F7F9FB;border-radius:999px;padding:.24rem .5rem;font-size:.65rem;color:#496276;font-weight:750}.ln-free{color:#0B7655}.ln-paid{color:#956006}.ln-unknown{color:#728193}.ln-title{font-size:1.03rem;font-weight:850;line-height:1.28;color:#142F46;margin:.1rem 0 .45rem}
.ln-decision-grid{display:grid;grid-template-columns:1.05fr 1.25fr .8fr .9fr;gap:0;border-top:1px solid #EDF1F4;border-bottom:1px solid #EDF1F4;margin:.25rem 0 .52rem}.ln-fact{padding:.46rem .58rem;border-right:1px solid #EDF1F4;min-width:0}.ln-fact:last-child{border-right:0}.ln-fact small{display:block;font-size:.58rem;color:#8A99A7;text-transform:uppercase;letter-spacing:.04em;font-weight:850;margin-bottom:.08rem}.ln-fact strong{display:block;font-size:.78rem;color:#24435D;line-height:1.22;overflow-wrap:anywhere}.ln-fact strong.ln-deadline{color:#9A5B13}
.ln-items-head{display:flex;align-items:center;justify-content:space-between;gap:.5rem;margin:.05rem 0 .2rem}.ln-items-head strong{font-size:.82rem;color:#1E4059}.ln-items-head span{font-size:.65rem;color:#8998A6}.ln-item-row{display:grid;grid-template-columns:minmax(0,1fr) 110px 105px;gap:.45rem;align-items:start;padding:.34rem 0;border-top:1px solid #F0F3F5}.ln-item-name{font-size:.77rem;color:#344E64;line-height:1.27}.ln-item-qty{font-size:.73rem;color:#647789;text-align:right}.ln-item-price{font-size:.74rem;font-weight:850;color:#153F59;text-align:right}.ln-intel{margin-top:.48rem;background:#F7FAFA;border:1px solid #DCEBE8;border-left:4px solid var(--brand);border-radius:9px;padding:.48rem .58rem;font-size:.72rem;color:#55706B}.ln-intel b{color:#195C52}.ln-deadline-pill{display:inline-flex;border-radius:999px;padding:.16rem .42rem;font-size:.61rem;font-weight:850;background:#FFF3DF;color:#8E5C0A;border:1px solid #F0D4A0}
.ln-section-title{font-size:1.25rem;font-weight:880;color:var(--navy);margin:.15rem 0 .08rem}.ln-section-sub{font-size:.82rem;color:#708496;margin:0 0 .55rem}.ln-choice{background:#fff;border:1px solid var(--line);border-radius:12px;padding:.6rem .68rem;margin-bottom:.28rem}.ln-choice strong{display:block;color:#1A3D57;font-size:.88rem}.ln-choice span{display:block;color:#7A8D9D;font-size:.7rem;margin-top:.08rem}.ln-empty{background:#fff;border:1px dashed #C9D5DF;border-radius:13px;padding:1.1rem;text-align:center;color:#718397}.ln-radar{display:flex;gap:.3rem;flex-wrap:wrap;background:#fff;border:1px solid var(--line);border-radius:12px;padding:.58rem .65rem;margin:.4rem 0 .55rem}.ln-chip{background:#F3F6F8;border:1px solid #E3E9EE;border-radius:999px;padding:.26rem .48rem;font-size:.72rem;color:#466077}.ln-chip b{color:#23435C}[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:10px;padding:.45rem .52rem}[data-testid="stMetricLabel"] *,[data-testid="stMetricValue"] *{color:#24435D!important}
@media(max-width:850px){.ln-decision-grid{grid-template-columns:1fr 1fr}.ln-fact{border-bottom:1px solid #EDF1F4}.ln-item-row{grid-template-columns:1fr}.ln-item-qty,.ln-item-price{text-align:left}.block-container{padding-left:.7rem!important;padding-right:.7rem!important}}
</style>
"""


def _dt(value):
    if not value: return "Não informado"
    try: return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError): return str(value).replace("T", " ")[:16]


def _deadline_text(value):
    if not value: return "Prazo não informado"
    try:
        parsed=datetime.fromisoformat(str(value).replace("Z", "+00:00")); now=datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now(); hours=(parsed-now).total_seconds()/3600
        if hours<0: return "Encerrado"
        if hours<2: return "Encerra em menos de 2h"
        if hours<24: return f"Encerra em {max(1,int(hours))}h"
        days=max(1,int(hours//24)); return "Encerra amanhã" if days==1 else f"Encerra em {days} dias"
    except (TypeError, ValueError): return "Prazo informado no edital"


def _money(value):
    try:
        if value is None or float(value)<=0: return "Não informado"
    except (TypeError, ValueError): return "Não informado"
    return format_brl(value)


def _html_money(value): return escape(_money(value)).replace("$", "&#36;")
def _short(value,limit=210):
    clean=" ".join(str(value or "").split()); return clean if len(clean)<=limit else clean[:limit-1].rstrip(" ,.;:-")+"…"

@st.cache_data(ttl=45,show_spinner=False)
def _search(region,states,city,modalities,keyword,limit=160): return catalog.search(region=region,states=states,city=city,modalities=modalities,keyword=keyword,limit=limit)

@st.cache_data(ttl=1800,show_spinner=False)
def _items(controls):
    shells=[{"pncp_control_number":c,"category":"Outros"} for c in controls if c]; enriched=enrich_with_items(shells,max_workers=4,max_items=80)
    return {row.get("pncp_control_number"):{"items":row.get("items") or [],"item_count":int(row.get("item_count") or 0),"items_error":row.get("items_error") or "","category":row.get("category") or "Outros"} for row in enriched}

@st.cache_data(ttl=3600,show_spinner=False)
def _history(item_reference,catalog_code,description,state): return fetch_price_history_for_item({"source_reference":item_reference,"catalog_code":catalog_code,"description":description},state=state,months=18)

@st.cache_data(ttl=120,show_spinner=False)
def _region_counts(): return catalog.counts_by_region()
@st.cache_data(ttl=120,show_spinner=False)
def _state_counts(): return catalog.counts_by_state()


def _init_state():
    defaults={"mei_saved":{},"mei_radars":[],"mei_page":1,"mei_open_opportunity":"","mei_price_item":"","mei_section":"🔎 Descobrir","mei_filters":{"region":"","states":[],"city":"","modalities":[],"keyword":""}}
    for key,value in defaults.items(): st.session_state.setdefault(key,value)


def _go(section): st.session_state.mei_section=section; st.rerun()


def _sidebar():
    with st.sidebar:
        if LOGO_PATH.exists(): st.image(str(LOGO_PATH),width=146)
        st.markdown('<div class="ln-side-product">Oportunidades públicas sem complicação</div>',unsafe_allow_html=True)
        current=st.session_state.mei_section; explore=["🔎 Descobrir","📍 Por localização","📋 Por modalidade","🔥 Em destaque"]; personal=["⭐ Salvos","🔔 Radar"]
        st.markdown('<div class="ln-side-group">Explorar</div>',unsafe_allow_html=True)
        for i,label in enumerate(explore):
            if st.button(label,key=f"nav_e_{i}",type="primary" if current==label else "secondary",width="stretch"): _go(label)
        st.markdown('<div class="ln-side-group">Minha área</div>',unsafe_allow_html=True)
        for i,label in enumerate(personal):
            if st.button(label,key=f"nav_p_{i}",type="primary" if current==label else "secondary",width="stretch"): _go(label)
        st.markdown('<div class="ln-plan">LicitaNexo MEI<strong>R&#36; 29,90/mês</strong><b>Descubra → compare → salve.</b><br>Itens do PNCP e inteligência de preços públicos.</div>',unsafe_allow_html=True)
        st.caption(f"{MEI_VERSION} · B2G SaaS")
    return current


def _hero():
    price=MEI_PRICE.replace("$","&#36;")
    st.markdown(f'''<div class="ln-hero"><div class="ln-hero-row"><div><div class="ln-eyebrow">LicitaNexo MEI</div><h1>Descubra oportunidades antes de escolher um nicho.</h1><p>Veja o que os órgãos públicos estão comprando, quais itens fazem parte do edital e consulte preços homologados de compras anteriores quando houver histórico disponível.</p><div class="ln-value-badges"><span>✓ Sem nicho obrigatório</span><span>📦 Itens do PNCP</span><span>💰 Histórico de preços</span><span>🏷️ Marcas quando publicadas</span></div></div><div class="ln-price-badge"><small>Plano de lançamento</small><strong>{price}</strong></div></div></div>''',unsafe_allow_html=True)


def _filter_panel():
    filters=dict(st.session_state.mei_filters); regions=["Brasil inteiro"]+list(BRAZIL_REGIONS); current_region=filters.get("region") or "Brasil inteiro"
    if current_region not in regions: current_region="Brasil inteiro"
    st.markdown('<div class="ln-searchbox"><div class="ln-search-title">Encontre oportunidades</div><div class="ln-search-help">Você pode deixar tudo em branco e simplesmente explorar.</div>',unsafe_allow_html=True)
    keyword=st.text_input("Produto, serviço ou palavra-chave",value=filters.get("keyword") or "",placeholder="Ex.: papel, café, uniforme, manutenção — ou deixe em branco")
    c1,c2,c3,c4=st.columns([1,1.05,1.25,1.2]); region=c1.selectbox("Região",regions,index=regions.index(current_region)); states=c2.multiselect("Estado",list(BRAZIL_STATES),default=filters.get("states") or [],placeholder="Todos"); city=c3.text_input("Cidade",value=filters.get("city") or "",placeholder="Ex.: Londrina"); modalities=c4.multiselect("Modalidade",list(MODALITIES.keys()),default=filters.get("modalities") or [],placeholder="Todas")
    b1,b2=st.columns([5,1]); search_clicked=b1.button("🔎 Ver oportunidades",type="primary",width="stretch"); clear_clicked=b2.button("Limpar",width="stretch"); st.markdown("</div>",unsafe_allow_html=True)
    if search_clicked: st.session_state.mei_filters={"region":"" if region=="Brasil inteiro" else region,"states":list(states),"city":city.strip(),"modalities":list(modalities),"keyword":keyword.strip()}; st.session_state.mei_page=1; st.rerun()
    if clear_clicked: st.session_state.mei_filters={"region":"","states":[],"city":"","modalities":[],"keyword":""}; st.session_state.mei_page=1; st.rerun()


def _render_price_history(history):
    if not history.get("available"): st.info(history.get("reason") or "Histórico ainda não disponível para este item."); return
    summary=history["summary"]; st.markdown("### 💰 Inteligência de preço público"); st.caption(f"Compras homologadas encontradas no Compras.gov · código de catálogo {history.get('catalog_code')}. Compare especificações antes de tratar produtos como equivalentes.")
    c1,c2,c3,c4,c5=st.columns(5); c1.metric("Último",_money(summary.get("last_price"))); c2.metric("Média",_money(summary.get("average"))); c3.metric("Mediana",_money(summary.get("median"))); c4.metric("Menor",_money(summary.get("minimum"))); c5.metric("Maior",_money(summary.get("maximum"))); st.caption(f"{summary.get('count',0)} compra(s) homologada(s) considerada(s) nos últimos 18 meses.")
    left,right=st.columns(2); brands,suppliers=summary.get("brands") or [],summary.get("suppliers") or []
    with left:
        st.markdown("**🏷️ Marcas encontradas**")
        if brands: st.dataframe(pd.DataFrame([{"Marca":x["name"],"Ocorrências":x["count"]} for x in brands]),hide_index=True,width="stretch")
        else: st.caption("Marca não informada de forma confiável na amostra.")
    with right:
        st.markdown("**🏆 Fornecedores vencedores**")
        if suppliers: st.dataframe(pd.DataFrame([{"Fornecedor":x["name"],"Ocorrências":x["count"]} for x in suppliers]),hide_index=True,width="stretch")
        else: st.caption("Fornecedor não disponível na amostra.")
    rows=summary.get("rows") or []
    if rows:
        frame=pd.DataFrame([{"Data":str(x.get("published_at") or "")[:10],"Órgão":x.get("agency") or "","Cidade/UF":"/".join(p for p in (str(x.get("city") or ""),str(x.get("state") or "")) if p),"Qtd.":x.get("quantity"),"Preço homologado":_money(x.get("homologated_unit_value")),"Marca":x.get("brand_normalized") or x.get("brand") or "Não informada","Fornecedor":x.get("supplier") or ""} for x in rows[:12]]); st.markdown("**Compras recentes**"); st.dataframe(frame,hide_index=True,width="stretch")


def _item_rows_html(items,expanded):
    lines=[]
    for row in (items if expanded else items[:3]):
        desc=escape(_short(row.get("description") or "Item não descrito",260 if expanded else 165))
        try: qty=f"{float(row.get('quantity')):,.2f}".replace(",","X").replace(".",",").replace("X",".")
        except (TypeError,ValueError): qty="—"
        unit=escape(str(row.get("unit_measure") or "")); price="Sigiloso" if row.get("confidential") else _html_money(row.get("unit_price")); lines.append(f'<div class="ln-item-row"><div class="ln-item-name">{desc}</div><div class="ln-item-qty">{qty} {unit}</div><div class="ln-item-price">{price}</div></div>')
    return "".join(lines)


def _render_opportunity(row,pack):
    oid=str(row.get("id") or row.get("pncp_control_number") or ""); modality=escape(str(row.get("modality") or "Modalidade não informada")); category=escape(str(pack.get("category") or row.get("category") or "Outros")); title=escape(_short(row.get("object") or "Objeto não informado",275)); agency=escape(str(row.get("agency") or "Órgão não informado")); city=escape(str(row.get("city") or "Município não informado")); state=escape(str(row.get("state") or "--")); portal=escape(str(row.get("portal") or "Não identificado")); access=escape(str(row.get("portal_access") or "Verificar condições")); tone=str(row.get("portal_access_tone") or "unknown"); tone_class="ln-free" if tone=="free" else "ln-paid" if tone in {"paid","conditional"} else "ln-unknown"; items=pack.get("items") or []; total=int(pack.get("item_count") or len(items)); expanded=st.session_state.mei_open_opportunity==oid
    with st.container(border=True):
        st.markdown(f'''<div class="ln-card-top"><div class="ln-tags"><span class="ln-tag ln-tag-mode">{modality}</span><span class="ln-tag ln-tag-cat">{category}</span><span class="ln-tag ln-tag-items">📦 {total} item(ns)</span><span class="ln-deadline-pill">{escape(_deadline_text(row.get("closing_at")))}</span></div><div class="ln-portal">🌐 {portal} <span class="{tone_class}">● {access}</span></div></div><div class="ln-title">{title}</div><div class="ln-decision-grid"><div class="ln-fact"><small>Onde</small><strong>{city} — {state}</strong></div><div class="ln-fact"><small>Órgão</small><strong>{agency}</strong></div><div class="ln-fact"><small>Valor estimado</small><strong>{_html_money(row.get("estimated_value"))}</strong></div><div class="ln-fact"><small>Prazo</small><strong class="ln-deadline">{escape(_dt(row.get("closing_at")))}</strong></div></div>''',unsafe_allow_html=True)
        if items: st.markdown(f'<div class="ln-items-head"><strong>O que o órgão quer comprar</strong><span>fonte PNCP · {total} item(ns)</span></div>{_item_rows_html(items,expanded)}',unsafe_allow_html=True)
        else: st.caption(pack.get("items_error") or "Itens estruturados não publicados no PNCP.")
        if items:
            a1,a2=st.columns([1.1,2.1])
            if total>3:
                label="Mostrar menos" if expanded else f"Ver todos os {total} itens"
                if a1.button(label,key=f"all_{oid}",width="stretch"): st.session_state.mei_open_opportunity="" if expanded else oid; st.rerun()
            else: a1.caption("Todos os itens estão visíveis.")
            if a2.button("💰 Consultar preços já pagos pelo governo",key=f"prices_{oid}",type="primary",width="stretch"): st.session_state.mei_open_opportunity=oid; st.rerun()
            st.markdown('<div class="ln-intel"><b>Por que isso tem valor:</b> compare o preço estimado deste edital com compras homologadas anteriores e veja marcas e fornecedores quando esses dados existirem.</div>',unsafe_allow_html=True)
        actions=st.columns([1.05,1,1]); saved=oid in st.session_state.mei_saved
        if actions[0].button("✓ Salvo" if saved else "⭐ Salvar",key=f"save_{oid}",disabled=saved,width="stretch"): st.session_state.mei_saved[oid]=dict(row); st.rerun()
        source_url,pncp_url=str(row.get("source_url") or ""),str(row.get("pncp_url") or "")
        if source_url.startswith(("http://","https://")): actions[1].link_button("🌐 Portal da disputa",source_url,width="stretch")
        if pncp_url.startswith(("http://","https://")): actions[2].link_button("📄 Ver no PNCP",pncp_url,width="stretch")
        if expanded and items:
            st.divider(); choices=[x for x in items if str(x.get("description") or "").strip()]
            if choices:
                selected=st.selectbox("Escolha o item para consultar o histórico",range(len(choices)),format_func=lambda i:_short(choices[i].get("description") or "",100),key=f"sel_{oid}"); item=choices[selected]; ref=str(item.get("source_reference") or f"{oid}:{selected}")
                if st.button("Analisar histórico deste item",key=f"hist_{oid}",type="primary"): st.session_state.mei_price_item=ref
                if st.session_state.mei_price_item==ref:
                    with st.spinner("Buscando compras homologadas..."): history=_history(ref,str(item.get("catalog_code") or ""),str(item.get("description") or ""),state)
                    _render_price_history(history)


def _load_rows(filters,limit=160): return _search(filters.get("region") or "",tuple(filters.get("states") or []),filters.get("city") or "",tuple(filters.get("modalities") or []),filters.get("keyword") or "",limit)


def _explore_page():
    _hero(); _filter_panel(); filters=st.session_state.mei_filters
    with st.spinner("Organizando oportunidades..."): rows=_load_rows(filters,160)
    st.markdown(f'<div class="ln-resultsbar"><h2>Oportunidades abertas</h2><div>{len(rows)} encontrada(s) nesta consulta</div></div>',unsafe_allow_html=True); st.markdown('<div class="ln-value-strip"><b>Decida mais rápido:</b> cada oportunidade reúne prazo, valor, portal, itens e acesso ao histórico de preços em um só lugar.</div>',unsafe_allow_html=True)
    if not rows: st.markdown('<div class="ln-empty">Nenhuma oportunidade encontrada. Remova um filtro para ampliar a descoberta.</div>',unsafe_allow_html=True); return
    per_page=8; total_pages=max((len(rows)+per_page-1)//per_page,1); current=min(max(int(st.session_state.mei_page),1),total_pages); visible=rows[(current-1)*per_page:current*per_page]; controls=tuple(str(x.get("pncp_control_number") or "") for x in visible)
    with st.spinner("Carregando itens do PNCP..."): item_map=_items(controls)
    for row in visible:
        control=str(row.get("pncp_control_number") or ""); pack=item_map.get(control,{"items":[],"item_count":0,"items_error":"","category":row.get("category") or "Outros"}); _render_opportunity(row,pack)
    p1,p2,p3=st.columns([1,1,3])
    if p1.button("◀ Anterior",disabled=current<=1,width="stretch"): st.session_state.mei_page=current-1; st.rerun()
    if p2.button("Próxima ▶",disabled=current>=total_pages,width="stretch"): st.session_state.mei_page=current+1; st.rerun()
    p3.caption(f"Página {current} de {total_pages}")


def _apply_discovery(*,region="",states=None,city="",modalities=None,keyword=""): st.session_state.mei_filters={"region":region,"states":list(states or []),"city":city,"modalities":list(modalities or []),"keyword":keyword}; st.session_state.mei_page=1; st.session_state.mei_section="🔎 Descobrir"; st.rerun()


def _location_page():
    st.markdown('<div class="ln-section-title">📍 Explore por localização</div>',unsafe_allow_html=True); st.markdown('<div class="ln-section-sub">Você escolhe o nível de detalhe: região, estado ou cidade. Não precisa definir produto.</div>',unsafe_allow_html=True); counts=_region_counts(); st.markdown("#### Regiões"); cols=st.columns(5)
    for i,region in enumerate(BRAZIL_REGIONS):
        with cols[i%5]:
            st.markdown(f'<div class="ln-choice"><strong>{escape(region)}</strong><span>{int(counts.get(region,0))} oportunidade(s)</span></div>',unsafe_allow_html=True)
            if st.button("Explorar",key=f"region_{region}",width="stretch"): _apply_discovery(region=region)
    st.divider(); c1,c2=st.columns([1.2,2]); state_counts=_state_counts(); states=sorted(BRAZIL_STATES,key=lambda x:(-int(state_counts.get(x,0)),x)); state=c1.selectbox("Estado",["Selecione"]+states); city=c2.text_input("Ou digite uma cidade",placeholder="Ex.: Londrina, João Pessoa, Sao Jose"); b1,b2=st.columns(2)
    if b1.button("Ver oportunidades do estado",disabled=state=="Selecione",width="stretch"): _apply_discovery(states=[state])
    if b2.button("Buscar cidade",type="primary",width="stretch"):
        if city.strip(): _apply_discovery(city=city.strip())
        else: st.warning("Digite uma cidade para continuar.")


def _modality_page():
    st.markdown('<div class="ln-section-title">📋 Explore por modalidade</div>',unsafe_allow_html=True); st.markdown('<div class="ln-section-sub">Escolha como o órgão está contratando e veja as oportunidades abertas.</div>',unsafe_allow_html=True); options=list(MODALITIES.keys()); cols=st.columns(2)
    for i,modality in enumerate(options):
        with cols[i%2]:
            if st.button(str(modality),key=f"mod_{i}",width="stretch"): _apply_discovery(modalities=[modality])


def _highlight_score(row):
    score=0.0; portal=str(row.get("portal") or "").strip().casefold()
    if portal and portal!="não identificado": score+=3
    if str(row.get("portal_access_tone") or "")=="free": score+=2
    try: value=float(row.get("estimated_value") or 0)
    except (TypeError,ValueError): value=0
    if 0<value<=250000: score+=1.5
    closing=row.get("closing_at")
    if closing:
        try:
            parsed=datetime.fromisoformat(str(closing).replace("Z","+00:00")); now=datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now(); hours=(parsed-now).total_seconds()/3600
            if 24<=hours<=240: score+=2
            elif 8<=hours<24: score+=.5
        except (TypeError,ValueError): pass
    return score


def _highlight_page():
    st.markdown('<div class="ln-section-title">🔥 Oportunidades em destaque</div>',unsafe_allow_html=True); st.markdown('<div class="ln-section-sub">Priorizamos oportunidades com dados mais completos, prazo útil, portal identificado e itens publicados. É um ranking de qualidade da informação, não uma recomendação de participação.</div>',unsafe_allow_html=True); rows=_search("",tuple(),"",tuple(),"",80); pre=sorted(rows,key=_highlight_score,reverse=True)[:24]; controls=tuple(str(x.get("pncp_control_number") or "") for x in pre)
    with st.spinner("Organizando destaques..."): item_map=_items(controls)
    ranked=[]
    for row in pre:
        control=str(row.get("pncp_control_number") or ""); pack=item_map.get(control,{"items":[],"item_count":0,"items_error":"","category":row.get("category") or "Outros"}); score=_highlight_score(row)+(4 if int(pack.get("item_count") or 0)>0 else 0); score+=1 if str(pack.get("category") or "Outros")!="Outros" else 0; ranked.append((score,row,pack))
    for _,row,pack in sorted(ranked,key=lambda x:x[0],reverse=True)[:10]: _render_opportunity(row,pack)


def _saved_page():
    st.markdown('<div class="ln-section-title">⭐ Oportunidades salvas</div>',unsafe_allow_html=True); st.markdown('<div class="ln-section-sub">Guarde o que chamou sua atenção e compare depois.</div>',unsafe_allow_html=True); saved=list(st.session_state.mei_saved.values())
    if not saved: st.markdown('<div class="ln-empty">Você ainda não salvou nenhuma oportunidade.</div>',unsafe_allow_html=True); return
    controls=tuple(str(x.get("pncp_control_number") or "") for x in saved); item_map=_items(controls)
    for row in saved:
        control=str(row.get("pncp_control_number") or ""); _render_opportunity(row,item_map.get(control,{"items":[],"item_count":0,"items_error":"","category":row.get("category") or "Outros"})); oid=str(row.get("id") or row.get("pncp_control_number") or "")
        if st.button("Remover dos salvos",key=f"remove_{oid}"): st.session_state.mei_saved.pop(oid,None); st.rerun()


def _radar_page():
    st.markdown('<div class="ln-section-title">🔔 Radar</div>',unsafe_allow_html=True); st.markdown('<div class="ln-section-sub">Salve uma combinação de busca para voltar a ela rapidamente.</div>',unsafe_allow_html=True); filters=dict(st.session_state.mei_filters); chips=[("Região",filters.get("region") or "Brasil inteiro"),("Estado",", ".join(filters.get("states") or []) or "Todos"),("Cidade",filters.get("city") or "Todas"),("Modalidade",", ".join(filters.get("modalities") or []) or "Todas"),("Palavra",filters.get("keyword") or "Modo descoberta")]; html="".join(f'<span class="ln-chip"><b>{escape(k)}:</b> {escape(str(v))}</span>' for k,v in chips); st.markdown(f'<div class="ln-radar">{html}</div>',unsafe_allow_html=True); c1,c2=st.columns([3,1]); name=c1.text_input("Nome do radar",placeholder="Ex.: oportunidades em Londrina")
    if c2.button("Salvar radar",type="primary",width="stretch"): st.session_state.mei_radars.append({"name":name.strip() or f"Radar {len(st.session_state.mei_radars)+1}","filters":filters}); st.success("Radar salvo nesta sessão.")
    for i,radar in enumerate(st.session_state.mei_radars):
        with st.container(border=True):
            left,right=st.columns([4,1]); left.markdown(f"**{escape(radar['name'])}**")
            if right.button("Usar",key=f"use_radar_{i}",width="stretch"): st.session_state.mei_filters=dict(radar["filters"]); st.session_state.mei_section="🔎 Descobrir"; st.session_state.mei_page=1; st.rerun()
    st.caption("No preview, os radares ficam apenas nesta sessão. Alertas automáticos entram na etapa comercial.")


def main():
    st.markdown(CSS,unsafe_allow_html=True); _init_state(); section=_sidebar()
    if section=="🔎 Descobrir": _explore_page()
    elif section=="📍 Por localização": _location_page()
    elif section=="📋 Por modalidade": _modality_page()
    elif section=="🔥 Em destaque": _highlight_page()
    elif section=="⭐ Salvos": _saved_page()
    else: _radar_page()
