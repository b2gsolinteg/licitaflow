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
    html = f"""
    <style>
    :root{{--lnx-bg:#031326;--lnx-panel:#071b35;--lnx-panel-2:#0a2346;--lnx-border:#163a68;--lnx-blue:#2b74ff;--lnx-blue-2:#4a93ff;--lnx-yellow:#f7bd21;--lnx-text:#f7f9fc;--lnx-muted:#b9c7da;--lnx-green:#43d48b}}
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{margin:0!important;padding:0!important;min-height:100vh!important;background:var(--lnx-bg)!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important}}
    header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,[data-testid="stSidebar"],[data-testid="collapsedControl"]{{display:none!important}}
    [data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{{width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important}}
    [data-testid="stVerticalBlock"],[data-testid="stElementContainer"],[data-testid="stHtml"]{{gap:0!important;margin:0!important;padding:0!important}}
    .lnx-page,.lnx-page *{{box-sizing:border-box}}
    .lnx-page{{min-height:100vh;color:var(--lnx-text);background:radial-gradient(circle at 78% 15%,rgba(24,90,186,.18),transparent 32%),linear-gradient(180deg,#04162d 0,#031326 100%)}}
    .lnx-top{{height:84px;border-bottom:1px solid rgba(44,93,151,.34);display:flex;align-items:center;background:rgba(2,14,29,.86);backdrop-filter:blur(12px)}}
    .lnx-top-inner{{width:min(1580px,calc(100% - 72px));margin:auto;display:flex;align-items:center;justify-content:space-between}}
    .lnx-brand{{display:flex;align-items:center;height:60px;text-decoration:none}}
    .lnx-brand img{{display:block;max-width:250px;max-height:58px;object-fit:contain}}
    .lnx-brand span{{font-size:28px;font-weight:900;color:#fff}}
    .lnx-actions{{display:flex;align-items:center;gap:12px}}
    .lnx-actions a{{height:42px;padding:0 20px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;text-decoration:none!important;font-size:14px;font-weight:850}}
    .lnx-login{{border:1px solid #315a8f;color:#fff!important;background:#08203e}}
    .lnx-trial{{background:var(--lnx-yellow);color:#06172e!important;border:1px solid var(--lnx-yellow)}}
    .lnx-shell{{width:min(1580px,calc(100% - 72px));margin:0 auto;padding:28px 0 30px;display:grid;grid-template-columns:430px minmax(0,1fr);gap:30px}}
    .lnx-left{{padding:8px 0 0}}
    .lnx-kicker{{display:inline-flex;align-items:center;gap:8px;border:1px solid #8b6b08;color:var(--lnx-yellow);background:rgba(247,189,33,.07);border-radius:999px;padding:8px 13px;font-size:11px;font-weight:900;letter-spacing:.015em}}
    .lnx-title{{font-size:clamp(40px,3.05vw,61px);line-height:1.04;letter-spacing:-2px;font-weight:800;margin:22px 0 0;max-width:520px}}
    .lnx-title strong{{color:var(--lnx-yellow)}}
    .lnx-sub{{margin:18px 0 0;color:#d8e3f1;font-size:17px;line-height:1.52;max-width:500px}}
    .lnx-buttons{{display:grid;grid-template-columns:1fr;margin-top:24px;max-width:320px;gap:10px}}
    .lnx-buttons a{{height:54px;border-radius:8px;display:flex;align-items:center;justify-content:center;text-decoration:none!important;font-size:16px;font-weight:900}}
    .lnx-primary{{background:linear-gradient(180deg,#337dff,#1b5bd4);color:#fff!important;border:1px solid #3f84ff;box-shadow:0 12px 28px rgba(24,95,218,.22)}}
    .lnx-secondary{{color:#74b3ff!important;background:transparent;border:0;height:auto!important;padding:7px 0;font-size:14px!important}}
    .lnx-price{{margin-top:24px;border:1px solid #8f6b09;background:linear-gradient(155deg,rgba(12,39,75,.95),rgba(5,24,48,.98));border-radius:14px;padding:20px 20px 16px;box-shadow:0 18px 45px rgba(0,0,0,.23)}}
    .lnx-price-label{{font-size:11px;font-weight:900;color:#e6edf6;letter-spacing:.02em}}
    .lnx-price-value{{display:flex;align-items:flex-end;gap:7px;margin-top:12px}}
    .lnx-price-value span{{font-size:23px;font-weight:800;margin-bottom:6px}}
    .lnx-price-value strong{{font-size:49px;line-height:.92;letter-spacing:-2px}}
    .lnx-price-value small{{font-size:16px;margin-bottom:5px}}
    .lnx-price-benefits{{display:grid;gap:10px;margin-top:16px}}
    .lnx-price-benefits div{{display:flex;gap:9px;color:#f1f5fb;font-size:13px;line-height:1.35}}
    .lnx-price-benefits i{{font-style:normal;color:var(--lnx-yellow);font-weight:900}}
    .lnx-audience{{margin-top:15px;border:1px solid #1a477e;background:#0a2446;border-radius:10px;padding:13px 14px;display:grid;grid-template-columns:38px 1fr;gap:11px;align-items:center}}
    .lnx-audience-icon{{width:38px;height:38px;border-radius:8px;display:grid;place-items:center;background:#123c73;color:#72aaff;font-size:20px}}
    .lnx-audience b{{display:block;font-size:12px;margin-bottom:3px}}
    .lnx-audience span{{display:block;font-size:11px;color:#c6d5e8;line-height:1.38}}
    .lnx-right{{min-width:0}}
    .lnx-audience-banner{{height:90px;border:1px solid #173d70;background:linear-gradient(135deg,#092143,#061a34);border-radius:14px;padding:17px 22px;display:flex;align-items:center;gap:16px}}
    .lnx-banner-icon{{width:50px;height:50px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(180deg,#316ee7,#1643a7);font-size:24px}}
    .lnx-audience-banner b{{display:block;font-size:18px;margin-bottom:4px}}.lnx-audience-banner span{{font-size:13px;color:#d7e3f2}}
    .lnx-demo{{margin-top:18px;border:1px solid #1d477a;background:rgba(5,24,48,.88);border-radius:15px;padding:18px 18px 16px;box-shadow:0 22px 60px rgba(0,0,0,.2)}}
    .lnx-demo-head{{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}}
    .lnx-demo-head h2{{margin:0;font-size:24px;letter-spacing:-.5px}}.lnx-demo-head p{{margin:5px 0 0;color:#c7d5e8;font-size:13px}}
    .lnx-example-badge{{white-space:nowrap;border:1px solid #355d89;border-radius:999px;padding:7px 10px;color:#9fc5f5;font-size:10px;font-weight:850;background:#08213f}}
    .lnx-tender{{margin-top:16px;border:1px solid #234e82;border-radius:12px;background:linear-gradient(180deg,#0a2548,#081e3c);padding:14px;display:grid;grid-template-columns:minmax(260px,1.5fr) .8fr .9fr;gap:12px;align-items:center}}
    .lnx-org{{display:grid;grid-template-columns:52px 1fr;gap:12px;align-items:center}}
    .lnx-org-icon{{width:52px;height:52px;border-radius:10px;background:#edf4ff;color:#174b8f;display:grid;place-items:center;font-size:28px}}
    .lnx-org b{{display:block;font-size:13px;text-transform:uppercase}}.lnx-org span{{display:block;color:#d6e1ef;font-size:11px;line-height:1.4;margin-top:3px}}
    .lnx-meta-block{{border-left:1px solid #1f4777;padding-left:14px}}.lnx-meta-block small{{display:block;color:#9db0c8;font-size:10px;margin-bottom:4px}}.lnx-meta-block strong{{font-size:12px}}
    .lnx-table{{margin-top:12px;border:1px solid #234e82;border-radius:12px;overflow:hidden}}
    .lnx-table-title{{padding:12px 14px;font-size:15px;font-weight:900;border-bottom:1px solid #234e82;background:#092142}}
    .lnx-th,.lnx-tr{{display:grid;grid-template-columns:42px 1fr 88px 100px 105px;align-items:center}}
    .lnx-th{{height:32px;background:#0b284f;color:#afc2d9;font-size:9px;font-weight:800}}
    .lnx-tr{{min-height:55px;border-top:1px solid #183d6c;font-size:11px;color:#eef4fb}}
    .lnx-th>div,.lnx-tr>div{{padding:0 10px}}
    .lnx-item{{display:flex;align-items:center;gap:10px}}.lnx-item-ico{{width:36px;height:36px;border-radius:7px;background:#e9eef5;color:#263c5f;display:grid;place-items:center;font-size:20px;flex:0 0 auto}}
    .lnx-item b{{display:block;font-size:11px;margin-bottom:2px}}.lnx-item small{{display:block;color:#aebed2;font-size:9px}}
    .lnx-table-foot{{height:34px;display:flex;align-items:center;justify-content:center;border-top:1px solid #183d6c;color:#66acff;font-size:11px;font-weight:800;background:#071d39}}
    .lnx-benefits{{margin-top:18px;border:1px solid #173d70;background:#061a34;border-radius:14px;display:grid;grid-template-columns:repeat(4,1fr);overflow:hidden}}
    .lnx-benefit{{padding:16px 14px;display:grid;grid-template-columns:36px 1fr;gap:10px;border-right:1px solid #173d70;min-height:90px}}
    .lnx-benefit:last-child{{border-right:0}}
    .lnx-benefit-icon{{width:36px;height:36px;border-radius:9px;background:#123d75;color:#6da7ff;display:grid;place-items:center;font-size:20px}}
    .lnx-benefit b{{font-size:11px;display:block;margin-bottom:4px}}.lnx-benefit span{{display:block;color:#c6d5e8;font-size:9.5px;line-height:1.4}}
    .lnx-closing{{margin-top:18px;border:1px solid #1d477a;border-radius:12px;background:#08213f;padding:13px 18px;text-align:center;font-size:16px;font-weight:800}}
    .lnx-closing strong{{color:var(--lnx-yellow)}}
    @media(max-width:1220px){{
      .lnx-shell{{grid-template-columns:1fr;padding-top:24px}}
      .lnx-left{{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}}
      .lnx-copy-block{{grid-column:1}}.lnx-price{{grid-column:2;grid-row:1 / span 2;margin-top:0}}
      .lnx-buttons{{max-width:360px}}
    }}
    @media(max-width:820px){{
      .lnx-top{{height:72px}}.lnx-top-inner,.lnx-shell{{width:calc(100% - 28px)}}.lnx-brand img{{max-width:180px;max-height:48px}}.lnx-actions{{gap:7px}}.lnx-actions a{{height:38px;padding:0 12px;font-size:12px}}
      .lnx-shell{{padding-top:18px;gap:18px}}.lnx-left{{display:block}}.lnx-title{{font-size:40px}}.lnx-sub{{font-size:15px}}.lnx-price{{margin-top:22px}}
      .lnx-audience-banner{{height:auto;padding:14px}}.lnx-audience-banner b{{font-size:15px}}
      .lnx-demo{{padding:14px}}.lnx-demo-head{{display:block}}.lnx-example-badge{{display:inline-flex;margin-top:10px}}
      .lnx-tender{{grid-template-columns:1fr}}.lnx-meta-block{{border-left:0;border-top:1px solid #1f4777;padding:10px 0 0}}
      .lnx-th,.lnx-tr{{grid-template-columns:32px 1fr 64px 80px}}.lnx-th>div:last-child,.lnx-tr>div:last-child{{display:none}}
      .lnx-benefits{{grid-template-columns:1fr 1fr}}.lnx-benefit{{border-bottom:1px solid #173d70}}.lnx-benefit:nth-child(2){{border-right:0}}.lnx-benefit:nth-child(3),.lnx-benefit:nth-child(4){{border-bottom:0}}
    }}
    @media(max-width:520px){{
      .lnx-top-inner{{width:calc(100% - 18px)}}.lnx-brand img{{max-width:150px}}.lnx-actions .lnx-login{{display:none}}.lnx-actions a{{padding:0 10px;font-size:11px}}
      .lnx-title{{font-size:34px;letter-spacing:-1.1px}}.lnx-buttons{{max-width:none}}.lnx-audience-banner{{align-items:flex-start}}
      .lnx-demo-head h2{{font-size:21px}}.lnx-org{{grid-template-columns:44px 1fr}}.lnx-org-icon{{width:44px;height:44px}}
      .lnx-th,.lnx-tr{{grid-template-columns:28px 1fr 56px}}.lnx-th>div:nth-child(4),.lnx-tr>div:nth-child(4),.lnx-th>div:nth-child(5),.lnx-tr>div:nth-child(5){{display:none}}
      .lnx-benefits{{grid-template-columns:1fr}}.lnx-benefit{{border-right:0;border-bottom:1px solid #173d70!important}}.lnx-benefit:last-child{{border-bottom:0!important}}
    }}
    </style>
    <div class="lnx-page">
      <header class="lnx-top">
        <div class="lnx-top-inner">
          <a class="lnx-brand" href="?">{logo_html}</a>
          <div class="lnx-actions"><a class="lnx-login" href="?auth=login">Login</a><a class="lnx-trial" href="?auth=request">Teste grátis</a></div>
        </div>
      </header>
      <main class="lnx-shell">
        <section class="lnx-left">
          <div class="lnx-copy-block">
            <div class="lnx-kicker">◎ FEITO PARA MEI, MICROEMPRESAS E EPP</div>
            <h1 class="lnx-title">Encontre licitações mais rápido e <strong>veja os itens</strong> sem abrir edital por edital.</h1>
            <p class="lnx-sub">O LicitaNexo mostra o que realmente importa: itens, quantidades e valores em uma só tela para você decidir onde vale competir.</p>
            <div class="lnx-buttons"><a class="lnx-primary" href="?auth=request">Teste grátis por 7 dias</a><a class="lnx-secondary" href="?auth=login">Acessar a plataforma →</a></div>
          </div>
          <div class="lnx-price">
            <div class="lnx-price-label">PLANO ACESSÍVEL PARA QUEM ESTÁ COMEÇANDO</div>
            <div class="lnx-price-value"><span>R$</span><strong>29,90</strong><small>/mês</small></div>
            <div class="lnx-price-benefits">
              <div><i>✓</i><span>7 dias grátis para conhecer a plataforma.</span></div>
              <div><i>✓</i><span>Preço justo para quem quer começar a vender para o governo.</span></div>
              <div><i>✓</i><span>Cancele quando quiser. Sem burocracia.</span></div>
            </div>
            <div class="lnx-audience"><div class="lnx-audience-icon">▣</div><div><b>Ideal para MEI, microempresas e EPP</b><span>Uma forma simples de dar os primeiros passos nas licitações sem começar com uma ferramenta cara ou complicada.</span></div></div>
          </div>
        </section>
        <section class="lnx-right">
          <div class="lnx-audience-banner"><div class="lnx-banner-icon">♟</div><div><b>Uma plataforma pensada para pequenos negócios venderem ao governo</b><span>Mais clareza para encontrar oportunidades, entender a compra e decidir onde participar.</span></div></div>
          <div class="lnx-demo">
            <div class="lnx-demo-head"><div><h2>Veja o que está sendo comprado.</h2><p>Itens, quantidades e valores organizados para você avaliar a oportunidade com mais rapidez.</p></div><div class="lnx-example-badge">EXEMPLO DEMONSTRATIVO</div></div>
            <div class="lnx-tender">
              <div class="lnx-org"><div class="lnx-org-icon">▦</div><div><b>Prefeitura Municipal de Uberlândia · MG</b><span>Exemplo de compra pública para demonstrar como o LicitaNexo organiza as informações.</span></div></div>
              <div class="lnx-meta-block"><small>Modalidade</small><strong>Pregão eletrônico</strong></div>
              <div class="lnx-meta-block"><small>Visualização</small><strong>Itens organizados na tela</strong></div>
            </div>
            <div class="lnx-table">
              <div class="lnx-table-title">Itens da compra</div>
              <div class="lnx-th"><div>Item</div><div>Descrição</div><div>Qtd.</div><div>Vl. unit.</div><div>Vl. total</div></div>
              <div class="lnx-tr"><div>01</div><div class="lnx-item"><span class="lnx-item-ico">♿</span><span><b>Cadeira de rodas adulto</b><small>Dobrável, aço carbono</small></span></div><div>5 un</div><div>R$ 950</div><div>R$ 4.750</div></div>
              <div class="lnx-tr"><div>02</div><div class="lnx-item"><span class="lnx-item-ico">▱</span><span><b>Cama hospitalar manual</b><small>Com grades laterais</small></span></div><div>3 un</div><div>R$ 1.890</div><div>R$ 5.670</div></div>
              <div class="lnx-tr"><div>03</div><div class="lnx-item"><span class="lnx-item-ico">∥</span><span><b>Muleta axilar</b><small>Alumínio regulável</small></span></div><div>10 un</div><div>R$ 120</div><div>R$ 1.200</div></div>
              <div class="lnx-tr"><div>04</div><div class="lnx-item"><span class="lnx-item-ico">Π</span><span><b>Andador articulado</b><small>Dobrável em alumínio</small></span></div><div>5 un</div><div>R$ 230</div><div>R$ 1.150</div></div>
              <div class="lnx-table-foot">Veja os itens antes de decidir se vale abrir o edital →</div>
            </div>
          </div>
          <div class="lnx-benefits">
            <div class="lnx-benefit"><div class="lnx-benefit-icon">⚡</div><div><b>Comece com pouco</b><span>Uma ferramenta acessível para quem está entrando no mercado público.</span></div></div>
            <div class="lnx-benefit"><div class="lnx-benefit-icon">◎</div><div><b>Foco no que importa</b><span>Encontre oportunidades que combinam melhor com o que sua empresa vende.</span></div></div>
            <div class="lnx-benefit"><div class="lnx-benefit-icon">♧</div><div><b>Alertas personalizados</b><span>Acompanhe novas oportunidades de acordo com seus interesses.</span></div></div>
            <div class="lnx-benefit"><div class="lnx-benefit-icon">◇</div><div><b>Decida com mais clareza</b><span>Veja as informações principais antes de investir tempo na análise completa.</span></div></div>
          </div>
          <div class="lnx-closing">O LicitaNexo foi criado para <strong>empresas como a sua.</strong> &nbsp; Simples de usar. Preço acessível. Informação para decidir melhor.</div>
        </section>
      </main>
    </div>
    """
    st.html(html)
