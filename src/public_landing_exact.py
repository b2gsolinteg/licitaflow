from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def _data_uri(path: Path | str | None) -> str:
    if not path:
        return ""
    candidate = Path(path)
    if not candidate.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(candidate.read_bytes()).decode('ascii')}"


def render_public_landing(logo_path=None) -> None:
    logo_uri = _data_uri(logo_path)
    logo_html = f'<img src="{logo_uri}" alt="LicitaNexo">' if logo_uri else '<span>LicitaNexo</span>'

    html = f'''
    <style>
    :root{{--lnx-navy:#061a40;--lnx-navy-2:#082960;--lnx-blue:#0d5bd7;--lnx-blue-2:#2580ff;--lnx-yellow:#f7b714;--lnx-ink:#071a3d;--lnx-muted:#5d6b82;--lnx-line:#e5eaf1;}}
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{margin:0!important;padding:0!important;min-height:100vh!important;background:#fff!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important}}
    header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,[data-testid="stSidebar"],[data-testid="collapsedControl"]{{display:none!important}}
    [data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{{width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important}}
    [data-testid="stVerticalBlock"],[data-testid="stElementContainer"],[data-testid="stHtml"]{{gap:0!important;margin:0!important;padding:0!important}}
    .lnx-page,.lnx-page *{{box-sizing:border-box}}
    .lnx-page{{min-height:100vh;background:#fff;color:var(--lnx-ink)}}
    .lnx-top{{height:82px;background:#fff;display:flex;align-items:center;border-bottom:1px solid var(--lnx-line);box-shadow:0 1px 10px rgba(5,25,59,.04)}}
    .lnx-top-inner{{width:min(1540px,calc(100% - 88px));margin:auto;display:flex;align-items:center;justify-content:space-between}}
    .lnx-brand{{display:flex;align-items:center;height:58px;text-decoration:none}}
    .lnx-brand img{{max-width:235px;max-height:56px;display:block;object-fit:contain}}
    .lnx-brand span{{font-size:28px;font-weight:850;color:var(--lnx-ink)}}
    .lnx-actions{{display:flex;align-items:center;gap:20px}}
    .lnx-actions a{{height:44px;padding:0 26px;display:inline-flex;align-items:center;justify-content:center;border-radius:7px;text-decoration:none!important;font-size:15px;font-weight:800;transition:.15s ease}}
    .lnx-login{{background:var(--lnx-navy)!important;color:#fff!important;border:1px solid var(--lnx-navy)!important}}
    .lnx-trial{{background:var(--lnx-yellow)!important;color:#07162f!important;border:1px solid var(--lnx-yellow)!important}}
    .lnx-actions a:hover{{transform:translateY(-1px)}}

    .lnx-hero{{min-height:calc(100vh - 82px);display:grid;grid-template-columns:43.5% 56.5%;overflow:hidden}}
    .lnx-copy{{background:#fff;padding:clamp(38px,5.5vh,68px) clamp(36px,4.3vw,74px) 30px;display:flex;flex-direction:column;justify-content:center}}
    .lnx-kicker{{display:inline-flex;align-self:flex-start;background:#eef4ff;color:#1758bd;border-radius:999px;padding:8px 14px;font-size:12px;font-weight:900;letter-spacing:.02em;margin-bottom:20px}}
    .lnx-title{{margin:0;max-width:680px;font-size:clamp(43px,3.05vw,62px);line-height:1.045;letter-spacing:-2.3px;font-weight:780;color:var(--lnx-ink)}}
    .lnx-title strong{{color:#1760d0;font-weight:820}}
    .lnx-sub{{max-width:650px;margin:22px 0 0;color:var(--lnx-muted);font-size:clamp(16px,1.04vw,19px);line-height:1.55}}
    .lnx-buttons{{display:flex;gap:18px;margin-top:30px;flex-wrap:wrap}}
    .lnx-buttons a{{height:52px;padding:0 28px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;text-decoration:none!important;font-size:16px;font-weight:850}}
    .lnx-primary{{background:var(--lnx-yellow);color:#061732!important;border:1px solid var(--lnx-yellow)}}
    .lnx-secondary{{background:#fff;color:var(--lnx-ink)!important;border:1.5px solid #183a6a}}

    .lnx-price{{max-width:640px;margin-top:28px;display:grid;grid-template-columns:1.14fr 1fr;min-height:138px;border-radius:15px;background:linear-gradient(135deg,#052454,#081a40 78%);box-shadow:0 12px 28px rgba(5,29,70,.18);overflow:hidden;color:#fff}}
    .lnx-price-main{{padding:22px 26px;display:flex;align-items:center;border-right:1px solid rgba(255,255,255,.2)}}
    .lnx-price-value{{display:flex;align-items:flex-end;gap:8px;white-space:nowrap}}
    .lnx-price-value span{{font-size:28px;font-weight:850;margin-bottom:7px}}
    .lnx-price-value strong{{font-size:58px;line-height:.88;letter-spacing:-2px}}
    .lnx-price-value small{{font-size:17px;margin-bottom:6px}}
    .lnx-price-benefits{{padding:20px 22px;display:grid;align-content:center;gap:14px}}
    .lnx-price-benefit{{display:grid;grid-template-columns:28px 1fr;gap:9px;align-items:start}}
    .lnx-price-icon{{color:var(--lnx-yellow);font-size:22px;line-height:1}}
    .lnx-price-benefit b{{font-size:13px;color:#fff;display:block;margin-bottom:2px}}
    .lnx-price-benefit span{{font-size:11px;color:#dbe7f6;line-height:1.35}}

    .lnx-features{{max-width:670px;margin-top:28px;display:grid;grid-template-columns:repeat(4,1fr);gap:0}}
    .lnx-feature{{padding:0 14px;border-right:1px solid #e2e7ee;min-height:64px}}
    .lnx-feature:first-child{{padding-left:0}}.lnx-feature:last-child{{border-right:0}}
    .lnx-feature-icon{{font-size:21px;color:#0f5cca;margin-bottom:6px}}
    .lnx-feature b{{display:block;font-size:11px;color:#102849;margin-bottom:3px}}
    .lnx-feature span{{display:block;font-size:9.5px;line-height:1.35;color:#5c6b80}}

    .lnx-visual{{position:relative;min-height:calc(100vh - 82px);overflow:hidden;background:radial-gradient(circle at 48% 36%,#0c3c86 0,#09285e 25%,#061d48 52%,#041735 100%);isolation:isolate}}
    .lnx-grid{{position:absolute;inset:0;opacity:.34;background-image:linear-gradient(rgba(65,137,255,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(65,137,255,.12) 1px,transparent 1px);background-size:58px 58px;mask-image:linear-gradient(to bottom,transparent 0,#000 20%,#000 86%,transparent 100%)}}
    .lnx-orbit{{position:absolute;border:1px solid rgba(64,135,255,.30);border-radius:50%;left:50%;top:47%;transform:translate(-50%,-50%)}}
    .lnx-orbit.o1{{width:560px;height:560px}}.lnx-orbit.o2{{width:760px;height:760px;opacity:.55}}.lnx-orbit.o3{{width:970px;height:970px;opacity:.32}}
    .lnx-hub{{position:absolute;left:50%;top:32%;transform:translate(-50%,-50%);width:132px;height:132px;border-radius:50%;background:#fff;display:grid;place-items:center;z-index:5;box-shadow:0 0 0 12px rgba(24,111,239,.16),0 0 42px rgba(247,183,20,.28)}}
    .lnx-hub:after{{content:"";position:absolute;inset:-2px;border-radius:50%;border:2px solid var(--lnx-yellow);opacity:.85}}
    .lnx-hub img{{width:96px;max-height:82px;object-fit:contain}}
    .lnx-hub span{{font-size:15px;font-weight:900;color:#0b2b5d}}
    .lnx-node{{position:absolute;z-index:4;border:1px solid rgba(247,183,20,.6);background:linear-gradient(145deg,rgba(8,37,82,.95),rgba(6,25,58,.97));box-shadow:0 12px 34px rgba(0,0,0,.24);border-radius:16px;color:#fff;padding:16px 18px}}
    .lnx-node b{{display:block;font-size:13px;margin-bottom:4px}}.lnx-node strong{{font-size:30px;letter-spacing:-1px}}.lnx-node small{{display:block;margin-top:4px;color:#d4e2f5;font-size:10px;line-height:1.35}}
    .lnx-node.n1{{left:8%;top:7%;width:190px}}.lnx-node.n2{{right:7%;top:7%;width:210px}}.lnx-node.n3{{left:4%;top:27%;width:205px}}.lnx-node.n4{{right:4%;top:27%;width:215px}}
    .lnx-node .ico{{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:#1766d5;font-size:18px;float:left;margin-right:10px}}

    .lnx-demo{{position:absolute;z-index:6;left:50%;bottom:5.5%;transform:translateX(-50%);width:min(640px,70%);height:46%;min-height:355px;background:#fff;border-radius:18px;box-shadow:0 28px 65px rgba(0,0,0,.34);overflow:hidden;display:grid;grid-template-columns:142px 1fr}}
    .lnx-demo-side{{background:linear-gradient(180deg,#082b62,#051d45);padding:21px 13px;color:#fff}}
    .lnx-demo-brand{{font-size:17px;font-weight:900;margin:0 0 22px 7px}}.lnx-demo-brand span{{color:var(--lnx-yellow)}}
    .lnx-demo-row{{height:32px;border-radius:6px;padding:0 8px;display:flex;align-items:center;gap:7px;font-size:9px;color:#d8e6f6;margin-bottom:3px}}
    .lnx-demo-row.active{{background:#0d58aa;color:var(--lnx-yellow);font-weight:850}}
    .lnx-demo-main{{padding:22px 20px;background:#fff;overflow:hidden;color:#173454}}
    .lnx-demo-top{{display:flex;justify-content:space-between;gap:8px;align-items:center}}
    .lnx-chip{{font-size:8px;font-weight:900;color:#125bbd;background:#edf4ff;padding:6px 8px;border-radius:6px}}
    .lnx-items-btn{{font-size:8px;font-weight:900;color:#092044;background:var(--lnx-yellow);padding:7px 10px;border-radius:6px}}
    .lnx-demo h3{{font-size:17px;line-height:1.18;margin:14px 0 4px;color:#132b4b}}
    .lnx-agency{{font-size:8px;color:#1e63a6;font-weight:850;margin-bottom:12px}}
    .lnx-meta{{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid #e2e8ef;border-radius:8px;overflow:hidden;margin-bottom:10px}}
    .lnx-meta div{{padding:7px;border-right:1px solid #e2e8ef}}.lnx-meta div:last-child{{border-right:0}}.lnx-meta small{{display:block;font-size:6px;color:#8b99a9}}.lnx-meta b{{font-size:7px}}
    .lnx-table{{border:1px solid #e2e7ed;border-radius:8px;overflow:hidden}}
    .lnx-th,.lnx-tr{{display:grid;grid-template-columns:26px 1fr 45px 60px;align-items:center}}
    .lnx-th{{height:25px;background:#fafbfc;font-size:6px;color:#728196;font-weight:900;border-bottom:1px solid #e5eaf0}}.lnx-tr{{height:40px;font-size:7px;color:#29425e;border-bottom:1px solid #e7ecf1}}.lnx-tr:last-child{{border-bottom:0}}
    .lnx-th div,.lnx-tr div{{padding:0 6px}}.lnx-item-name b{{display:block;font-size:7.4px;color:#173653;margin-bottom:2px}}.lnx-item-name small{{font-size:5.8px;color:#8794a5}}

    @media(max-width:1220px){{
      .lnx-top-inner{{width:calc(100% - 46px)}}.lnx-hero{{grid-template-columns:1fr}}
      .lnx-copy{{min-height:auto;padding:56px 7vw 52px}}.lnx-title{{max-width:760px}}.lnx-price{{max-width:720px}}.lnx-features{{max-width:760px}}
      .lnx-visual{{min-height:760px}}.lnx-demo{{height:410px;width:min(720px,78%)}}
    }}
    @media(max-width:720px){{
      .lnx-top{{height:70px}}.lnx-top-inner{{width:calc(100% - 24px)}}.lnx-brand{{height:48px}}.lnx-brand img{{max-width:165px;max-height:44px}}
      .lnx-actions{{gap:7px}}.lnx-actions a{{height:38px;padding:0 12px;font-size:12px}}
      .lnx-copy{{padding:44px 22px 42px}}.lnx-title{{font-size:40px;letter-spacing:-1.5px}}.lnx-sub{{font-size:16px}}.lnx-buttons{{gap:10px}}.lnx-buttons a{{width:100%;height:48px}}
      .lnx-price{{grid-template-columns:1fr;margin-top:23px}}.lnx-price-main{{border-right:0;border-bottom:1px solid rgba(255,255,255,.18);justify-content:center}}.lnx-price-value strong{{font-size:51px}}
      .lnx-features{{grid-template-columns:1fr 1fr;gap:18px}}.lnx-feature{{border-right:0;padding:0}}
      .lnx-visual{{min-height:690px}}.lnx-node{{display:none}}.lnx-hub{{top:18%;width:110px;height:110px}}.lnx-hub img{{width:80px}}
      .lnx-demo{{width:92%;height:430px;bottom:6%;grid-template-columns:1fr;border-radius:16px}}.lnx-demo-side{{display:none}}.lnx-demo-main{{padding:18px 14px}}.lnx-demo h3{{font-size:15px}}.lnx-th,.lnx-tr{{grid-template-columns:24px 1fr 48px}}.lnx-th div:last-child,.lnx-tr div:last-child{{display:none}}
    }}
    </style>
    <div class="lnx-page">
      <header class="lnx-top">
        <div class="lnx-top-inner">
          <a class="lnx-brand" href="?">{logo_html}</a>
          <div class="lnx-actions"><a class="lnx-login" href="?auth=login">Login</a><a class="lnx-trial" href="?auth=request">Teste grátis</a></div>
        </div>
      </header>
      <main class="lnx-hero">
        <section class="lnx-copy">
          <div class="lnx-kicker">INTELIGÊNCIA EM LICITAÇÕES</div>
          <h1 class="lnx-title">Encontre licitações mais rápido e veja os itens <strong>sem abrir edital por edital.</strong></h1>
          <p class="lnx-sub">A LicitaNexo organiza oportunidades públicas e mostra detalhes dos itens, quantidades e valores de forma clara para você decidir melhor e ganhar tempo.</p>
          <div class="lnx-buttons"><a class="lnx-primary" href="?auth=request">Teste grátis por 7 dias</a><a class="lnx-secondary" href="?auth=login">Ver como funciona</a></div>
          <div class="lnx-price">
            <div class="lnx-price-main"><div class="lnx-price-value"><span>R$</span><strong>29,90</strong><small>/mês</small></div></div>
            <div class="lnx-price-benefits">
              <div class="lnx-price-benefit"><div class="lnx-price-icon">▣</div><div><b>7 dias grátis</b><span>Teste completo, sem compromisso.</span></div></div>
              <div class="lnx-price-benefit"><div class="lnx-price-icon">✦</div><div><b>Um dos menores preços do mercado</b><span>Mais economia para o seu negócio.</span></div></div>
            </div>
          </div>
          <div class="lnx-features">
            <div class="lnx-feature"><div class="lnx-feature-icon">◎</div><b>Mais oportunidades</b><span>Editais e dispensas de todo o Brasil em um só lugar.</span></div>
            <div class="lnx-feature"><div class="lnx-feature-icon">▤</div><b>Itens com detalhes</b><span>Veja itens, quantidades e valores sem abrir edital por edital.</span></div>
            <div class="lnx-feature"><div class="lnx-feature-icon">♧</div><b>Alertas inteligentes</b><span>Receba avisos personalizados do que realmente importa.</span></div>
            <div class="lnx-feature"><div class="lnx-feature-icon">◇</div><b>Segurança total</b><span>Seus dados protegidos com tecnologia de ponta.</span></div>
          </div>
        </section>
        <section class="lnx-visual" aria-label="Demonstração visual do LicitaNexo">
          <div class="lnx-grid"></div><div class="lnx-orbit o1"></div><div class="lnx-orbit o2"></div><div class="lnx-orbit o3"></div>
          <div class="lnx-hub">{logo_html}</div>
          <div class="lnx-node n1"><span class="ico">♧</span><b>Alertas ativos</b><strong>38</strong><small>Editais relevantes para você hoje</small></div>
          <div class="lnx-node n2"><span class="ico">◷</span><b>Economia de tempo</b><strong>80%</strong><small>Menos tempo buscando, mais tempo vendendo.</small></div>
          <div class="lnx-node n3"><span class="ico">⌖</span><b>Cobertura nacional</b><strong>5.570+</strong><small>Municípios monitorados</small></div>
          <div class="lnx-node n4"><span class="ico">▥</span><b>Inteligência de preços</b><small>Compare valores históricos e tome decisões com mais precisão.</small></div>
          <div class="lnx-demo">
            <aside class="lnx-demo-side">
              <div class="lnx-demo-brand">Licita<span>Nexo</span></div>
              <div class="lnx-demo-row active">⌕ Buscar licitações</div><div class="lnx-demo-row">◇ Por Estado</div><div class="lnx-demo-row">⌖ Por Cidade</div><div class="lnx-demo-row">▣ Por Modalidade</div><div class="lnx-demo-row">◎ Por site de disputa</div><div class="lnx-demo-row">▽ Filtro avançado</div><div class="lnx-demo-row">☆ Minha lista</div><div class="lnx-demo-row">□ Calendário</div>
            </aside>
            <div class="lnx-demo-main">
              <div class="lnx-demo-top"><span class="lnx-chip">DISPENSA DE LICITAÇÃO</span><span class="lnx-items-btn">Ver itens da compra</span></div>
              <h3>Aquisição de equipamentos e materiais para reabilitação e atendimento hospitalar</h3>
              <div class="lnx-agency">MUNICÍPIO DE GUARDA-MOR · MG</div>
              <div class="lnx-meta"><div><small>Modalidade</small><b>Dispensa</b></div><div><small>Processo</small><b>DL 034/2024</b></div><div><small>Publicado</small><b>27/08/2024</b></div><div><small>Itens</small><b>6 itens</b></div></div>
              <div class="lnx-table">
                <div class="lnx-th"><div>#</div><div>DESCRIÇÃO DO ITEM</div><div>QTD.</div><div>VALOR</div></div>
                <div class="lnx-tr"><div>1</div><div class="lnx-item-name"><b>Cadeira de rodas adulto</b><small>Dobrável, em aço carbono</small></div><div>5</div><div>R$ 6.250</div></div>
                <div class="lnx-tr"><div>2</div><div class="lnx-item-name"><b>Cama hospitalar manual</b><small>Com grades laterais</small></div><div>3</div><div>R$ 8.970</div></div>
                <div class="lnx-tr"><div>3</div><div class="lnx-item-name"><b>Muleta axilar</b><small>Em alumínio regulável</small></div><div>10</div><div>R$ 1.800</div></div>
                <div class="lnx-tr"><div>4</div><div class="lnx-item-name"><b>Andador articulado</b><small>Dobrável em alumínio</small></div><div>5</div><div>R$ 1.600</div></div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
    '''
    st.html(html)
