from __future__ import annotations

from pathlib import Path

import streamlit as st


def render_public_landing(logo_path: Path | str | None = None) -> None:
    """Renderiza a home pública com a composição visual do mockup aprovado.

    O conteúdo usa ``st.html`` de propósito: ``st.markdown`` interpreta blocos HTML
    longos como Markdown e pode transformar trechos em código, quebrando a landing.
    """
    _ = logo_path  # mantido por compatibilidade com a chamada existente em app.py

    html = r'''<style>
:root{
  --ln-bg:#021a35;--ln-bg2:#032442;--ln-panel:#0b3159;--ln-panel2:#0a2b50;
  --ln-blue:#0b5fa6;--ln-blue2:#164d82;--ln-yellow:#ffbd18;--ln-white:#ffffff;
  --ln-line:#1d4e79;--ln-muted:#c9d8e7;--ln-ink:#142a46;
}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
  margin:0!important;padding:0!important;min-height:100vh!important;background:var(--ln-bg)!important;
  font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important;
}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,
[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important;height:0!important}
[data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{
  width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important;
}
[data-testid="stVerticalBlock"]{gap:0!important}
[data-testid="stElementContainer"],[data-testid="stHtml"]{width:100%!important;max-width:none!important;margin:0!important;padding:0!important}
.ln-page,.ln-page *{box-sizing:border-box}
.ln-page{min-height:1080px;color:#fff;background:
 radial-gradient(circle at 68% 25%,rgba(20,101,171,.17),transparent 31%),
 radial-gradient(circle at 15% 73%,rgba(6,74,132,.17),transparent 29%),
 linear-gradient(180deg,#031a34 0%,#032443 100%);overflow:hidden}
.ln-header{height:92px;border-bottom:1px solid rgba(255,255,255,.14);display:flex;align-items:center;background:rgba(2,24,49,.74)}
.ln-header-inner{width:calc(100% - 130px);max-width:1790px;margin:0 auto;display:flex;align-items:center;gap:36px}
.ln-brand{display:flex;align-items:center;gap:13px;width:320px;flex:0 0 320px;color:#fff;text-decoration:none}
.ln-brand-mark{position:relative;width:54px;height:54px;flex:0 0 54px}
.ln-brand-mark:before,.ln-brand-mark:after{content:"";position:absolute;border:6px solid #0b67ae;border-radius:10px;transform:rotate(45deg);width:30px;height:30px}
.ln-brand-mark:before{left:4px;top:4px;border-color:#0b4d89}.ln-brand-mark:after{right:4px;bottom:4px;border-color:#0d71bf}
.ln-brand-link{position:absolute;left:12px;top:21px;width:31px;height:11px;border:5px solid var(--ln-yellow);border-radius:999px;transform:rotate(-31deg);z-index:3;background:#06213f}
.ln-brand-name{font-size:31px;font-weight:900;letter-spacing:-1.2px;line-height:1}.ln-brand-name span{color:var(--ln-yellow)}
.ln-nav{display:flex;align-items:center;justify-content:center;gap:48px;flex:1;white-space:nowrap}
.ln-nav a,.ln-login{color:#fff!important;text-decoration:none!important;font-size:16px;font-weight:650}
.ln-nav a:hover,.ln-login:hover{color:var(--ln-yellow)!important}
.ln-actions{display:flex;align-items:center;gap:25px;white-space:nowrap}.ln-login{display:inline-flex;align-items:center;gap:9px}.ln-login:before{content:"♢";font-size:24px;color:#d9e7f7}
.ln-start{background:var(--ln-yellow);color:#071b31!important;text-decoration:none!important;padding:15px 27px;border-radius:10px;font-size:16px;font-weight:900;box-shadow:0 9px 24px rgba(255,189,24,.18)}
.ln-main{width:calc(100% - 130px);max-width:1790px;margin:0 auto;padding-top:34px}
.ln-grid{display:grid;grid-template-columns:600px minmax(0,1fr);gap:52px;align-items:start}
.ln-left{position:relative;padding-top:7px;overflow:visible}.ln-kicker{display:inline-flex;height:36px;align-items:center;border:1px solid #205884;background:#06294c;border-radius:999px;padding:0 16px;color:var(--ln-yellow);font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}
.ln-title{margin:22px 0 11px;font-size:54px;line-height:1.015;letter-spacing:-2px;font-weight:900;color:#fff}.ln-title .line{display:block}.ln-title .yellow{color:var(--ln-yellow)}
.ln-sub{margin:0 0 18px;color:#dfe9f4;font-size:19px;line-height:1.42}
.ln-features{width:535px;display:grid;gap:10px}.ln-feature{position:relative;height:94px;display:flex;align-items:center;gap:20px;padding:11px 18px;border:1px solid #1c5789;border-radius:12px;background:linear-gradient(180deg,#0b355f,#092c52)}
.ln-feature.diff{border-color:#d99b08;box-shadow:0 0 0 1px rgba(255,189,24,.08)}
.ln-feature-icon{width:66px;height:66px;flex:0 0 66px;border-radius:50%;display:grid;place-items:center;border:1px solid #286ca3;background:#0c3a68;color:#fff;font-size:32px;font-weight:700}.ln-feature.diff .ln-feature-icon{color:var(--ln-yellow);border-color:#dca10c}
.ln-feature-title{font-size:20px;font-weight:850;color:#fff;line-height:1.1;margin-bottom:4px}.ln-feature-copy{font-size:14px;line-height:1.35;color:#d1dfed;max-width:390px}
.ln-diff-badge{position:absolute;right:13px;top:11px;background:var(--ln-yellow);color:#09213d;font-size:10px;font-weight:950;padding:5px 10px;border-radius:4px;letter-spacing:.02em}
.ln-price-card{width:585px;height:116px;margin-top:20px;border:1px solid #1c5685;border-radius:12px;background:#0a2d51;display:grid;grid-template-columns:210px 1fr;align-items:center;padding:15px 16px 13px 25px;gap:18px}
.ln-plan-caption{font-size:14px;font-weight:750;color:#fff;margin-bottom:5px}.ln-price-line{display:flex;align-items:flex-end;gap:5px;line-height:1}.ln-currency{font-size:22px;padding-bottom:5px}.ln-price{font-size:50px;font-weight:950;color:var(--ln-yellow);letter-spacing:-2px}.ln-month{font-size:20px;padding-bottom:6px}
.ln-trial{text-align:right}.ln-trial a{display:inline-flex;align-items:center;justify-content:center;gap:17px;min-width:294px;height:50px;border-radius:9px;background:var(--ln-yellow);color:#071b31!important;text-decoration:none!important;font-size:15px;font-weight:900}.ln-trial-note{margin-top:8px;color:#cad8e6;font-size:11px}
.ln-trust{width:812px;height:81px;margin-top:16px;border:1px solid #174c76;border-radius:12px;background:#082846;display:grid;grid-template-columns:repeat(4,1fr);align-items:center;padding:8px 12px;gap:7px;position:relative;z-index:3}
.ln-trust-item{display:flex;align-items:center;gap:10px;color:#cddae7;font-size:11px;line-height:1.35}.ln-trust-icon{width:39px;height:39px;flex:0 0 39px;border-radius:50%;display:grid;place-items:center;border:1px solid #2b668f;background:#0c355e;color:#fff;font-size:18px}
.ln-right{min-width:0}.ln-demo{height:800px;border:2px solid #316b9b;border-radius:18px;background:#0a2d51;padding:5px;box-shadow:0 19px 54px rgba(0,0,0,.23);overflow:hidden}.ln-demo-inner{height:100%;display:grid;grid-template-columns:225px minmax(0,1fr);border-radius:12px;overflow:hidden}
.ln-side{background:linear-gradient(180deg,#0b3b6d,#082e54);padding:20px 16px;color:#fff}.ln-mini-brand{font-size:22px;font-weight:900;margin:0 0 22px 8px;display:flex;align-items:center;gap:8px}.ln-mini-brand .mini-link{color:var(--ln-yellow);font-size:25px}.ln-mini-brand span:last-child{color:var(--ln-yellow)}
.ln-side-item{height:39px;display:flex;align-items:center;gap:10px;border-radius:7px;padding:0 10px;font-size:13px;font-weight:700;color:#fff;margin-bottom:1px}.ln-side-item.active{background:#174d82;color:var(--ln-yellow)}.ln-side-ico{width:21px;text-align:center;font-size:16px}.ln-side-exit{margin:23px 6px 0;height:40px;border:1px solid #e3a40a;border-radius:7px;color:var(--ln-yellow);display:flex;align-items:center;padding:0 13px;font-size:13px;font-weight:850}
.ln-detail{position:relative;background:#fff;color:var(--ln-ink);padding:25px 30px 18px}.ln-detail-top{display:flex;align-items:flex-start;justify-content:space-between;gap:18px}.ln-pill{display:inline-flex;align-items:center;height:29px;padding:0 13px;background:#e6f0ff;color:#145c9c;border-radius:8px;font-size:12px;font-weight:900}.ln-detail-actions{display:flex;gap:11px}.ln-fav,.ln-items{height:44px;border-radius:8px;display:flex;align-items:center;padding:0 18px;font-size:13px;font-weight:850;white-space:nowrap}.ln-fav{border:1px solid #dbe2eb;color:#263a56;background:#fff}.ln-items{background:var(--ln-yellow);color:#0b223f;border:1px solid #d99c09}
.ln-detail-title{font-size:23px;line-height:1.15;font-weight:900;letter-spacing:-.3px;color:#14233b;margin:17px 0 6px;max-width:665px}.ln-agency{font-size:13px;color:#365f91;font-weight:900;margin-bottom:10px}.ln-desc{font-size:13px;line-height:1.38;color:#536883;max-width:730px;margin-bottom:12px}.ln-callout{position:absolute;right:24px;top:126px;width:176px;height:82px;border-radius:10px;background:#082c50;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:14px;font-weight:800;box-shadow:0 9px 24px rgba(0,0,0,.21)}.ln-callout strong{font-size:17px;color:var(--ln-yellow);margin-top:3px}.ln-callout:before{content:"↗";position:absolute;right:42px;top:-48px;color:var(--ln-yellow);font-size:43px;font-weight:300}
.ln-meta{display:grid;grid-template-columns:1.15fr 1fr 1fr 1.15fr;border:1px solid #e0e6ed;border-radius:8px;overflow:hidden;margin:12px 0 11px;max-width:680px}.ln-meta-cell{padding:9px 13px;border-right:1px solid #e5eaf0}.ln-meta-cell:last-child{border-right:0}.ln-meta-label{font-size:9.5px;color:#75859b;margin-bottom:4px}.ln-meta-value{font-size:11.5px;color:#2a496d;font-weight:780}.ln-chips{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px}.ln-chip{height:26px;display:flex;align-items:center;padding:0 12px;border:1px solid #dce4ec;border-radius:999px;background:#fff;color:#345271;font-size:10px;font-weight:800}
.ln-table-box{border:1px solid #d8e0e8;border-radius:8px;overflow:hidden}.ln-table-headline{height:41px;display:flex;align-items:center;padding:0 13px;font-size:12px;font-weight:900;color:#263c59;border-bottom:1px solid #e4e9ef}.ln-table{width:100%;border-collapse:collapse;table-layout:fixed}.ln-table th{height:32px;text-align:left;color:#52647e;font-size:8.5px;font-weight:900;padding:0 8px;border-bottom:1px solid #e5eaf0}.ln-table td{height:54px;color:#29415e;font-size:10px;padding:5px 8px;border-bottom:1px solid #e7ecf1;vertical-align:middle}.ln-table tr:last-child td{border-bottom:0}.ln-col-num{width:38px}.ln-col-desc{width:42%}.ln-col-qtd{width:12%}.ln-col-un{width:12%}.ln-col-val{width:15%}.ln-product{display:flex;align-items:center;gap:10px}.ln-prod-pic{width:39px;height:39px;flex:0 0 39px;border-radius:5px;background:linear-gradient(145deg,#f0f2f4,#dce1e5);display:grid;place-items:center;color:#68788b;font-size:21px}.ln-product strong{display:block;color:#1d3654;font-size:10.5px;line-height:1.15}.ln-product small{display:block;color:#66768c;font-size:8.5px;line-height:1.2;margin-top:2px}.ln-total{height:39px;border-top:1px solid #e2e8ee;background:#fbfcfd;display:flex;align-items:center;justify-content:flex-end;gap:48px;padding:0 15px;color:#315278;font-size:12px;font-weight:900}
.ln-bottom{height:91px;margin:20px 0 0 225px;border:1px solid #18527e;border-radius:12px;background:#0a3158;display:flex;align-items:center;gap:15px;padding:0 18px}.ln-bolt{width:57px;height:57px;flex:0 0 57px;border-radius:50%;display:grid;place-items:center;border:1px solid #2b6a99;background:#0d3d6a;color:var(--ln-yellow);font-size:32px}.ln-bottom strong{display:block;color:#fff;font-size:17px;margin-bottom:4px}.ln-bottom span{color:#cad9e8;font-size:13px}
@media(max-width:1450px){.ln-header-inner,.ln-main{width:calc(100% - 70px)}.ln-grid{grid-template-columns:540px minmax(0,1fr);gap:35px}.ln-title{font-size:48px}.ln-features{width:515px}.ln-price-card{width:535px}.ln-trust{width:720px}.ln-nav{gap:27px}.ln-brand{width:260px;flex-basis:260px}.ln-demo-inner{grid-template-columns:195px minmax(0,1fr)}.ln-bottom{margin-left:195px}}
@media(max-width:1180px){.ln-page{min-height:100vh}.ln-header-inner,.ln-main{width:calc(100% - 34px)}.ln-brand{width:auto;flex-basis:auto}.ln-brand-name{font-size:25px}.ln-brand-mark{width:44px;height:44px;transform:scale(.82)}.ln-nav{display:none}.ln-actions{margin-left:auto}.ln-grid{grid-template-columns:1fr;gap:26px}.ln-left{max-width:720px}.ln-title{font-size:46px}.ln-features,.ln-price-card{width:100%}.ln-trust{width:100%}.ln-demo{height:auto;min-height:760px}.ln-bottom{margin-left:195px;margin-bottom:25px}}
@media(max-width:720px){.ln-header{height:72px}.ln-start{padding:12px 15px;font-size:13px}.ln-login{font-size:13px}.ln-brand-name{font-size:21px}.ln-brand-mark{display:none}.ln-main{padding-top:20px}.ln-title{font-size:37px}.ln-title .line{display:inline}.ln-sub{font-size:16px}.ln-feature{height:auto;min-height:88px}.ln-feature-icon{width:52px;height:52px;flex-basis:52px;font-size:25px}.ln-feature-title{font-size:17px}.ln-feature-copy{font-size:12px}.ln-price-card{height:auto;grid-template-columns:1fr;padding:17px}.ln-trial{text-align:left}.ln-trial a{min-width:0;width:100%}.ln-trust{height:auto;grid-template-columns:1fr 1fr}.ln-demo-inner{grid-template-columns:1fr}.ln-side{display:none}.ln-detail{padding:16px 12px}.ln-callout{display:none}.ln-detail-top{display:block}.ln-detail-actions{margin-top:10px}.ln-meta{grid-template-columns:1fr 1fr;max-width:none}.ln-table-box{overflow-x:auto}.ln-table{min-width:730px}.ln-bottom{margin-left:0;height:auto;min-height:90px}.ln-actions{gap:8px}.ln-login{display:none}}
</style>
<div class="ln-page">
  <header class="ln-header">
    <div class="ln-header-inner">
      <a class="ln-brand" href="#">
        <span class="ln-brand-mark"><i class="ln-brand-link"></i></span>
        <span class="ln-brand-name">Licita<span>Nexo</span></span>
      </a>
      <nav class="ln-nav">
        <a href="#recursos">Recursos</a><a href="#como-funciona">Como funciona</a><a href="#planos">Planos</a><a href="#depoimentos">Depoimentos</a><a href="#blog">Blog</a><a href="#contato">Contato</a>
      </nav>
      <div class="ln-actions"><a class="ln-login" href="?auth=login">Entrar</a><a class="ln-start" href="?auth=request">Começar agora</a></div>
    </div>
  </header>

  <main class="ln-main">
    <div class="ln-grid">
      <section class="ln-left" id="recursos">
        <div class="ln-kicker">A plataforma inteligente de licitações</div>
        <h1 class="ln-title"><span class="line">Encontre licitações</span><span class="line">mais rápido e veja</span><span class="line yellow">os produtos na tela</span><span class="line">sem abrir edital por edital.</span></h1>
        <p class="ln-sub">Economize tempo. Ganhe vantagem.<br>Decida melhor com as informações que importam.</p>

        <div class="ln-features">
          <div class="ln-feature"><div class="ln-feature-icon">⌕</div><div><div class="ln-feature-title">Busque e filtre com precisão</div><div class="ln-feature-copy">Localize oportunidades por cidade, modalidade, palavra-chave e muito mais.</div></div></div>
          <div class="ln-feature diff"><div class="ln-diff-badge">DIFERENCIAL</div><div class="ln-feature-icon">◉</div><div><div class="ln-feature-title">Veja os produtos na tela</div><div class="ln-feature-copy">Itens da compra já visíveis, com quantidades, unidades e valores — sem abrir o edital.</div></div></div>
          <div class="ln-feature"><div class="ln-feature-icon">◎</div><div><div class="ln-feature-title">Decida com mais confiança</div><div class="ln-feature-copy">Compare oportunidades, avalie demandas e prepare propostas mais competitivas.</div></div></div>
        </div>

        <div class="ln-price-card" id="planos">
          <div><div class="ln-plan-caption">Planos a partir de</div><div class="ln-price-line"><span class="ln-currency">R$</span><span class="ln-price">29,90</span><span class="ln-month">/mês</span></div></div>
          <div class="ln-trial"><a href="?auth=request">Testar agora por 7 dias grátis <b>›</b></a><div class="ln-trial-note">🛡 Sem compromisso. Cancele quando quiser.</div></div>
        </div>

        <div class="ln-trust">
          <div class="ln-trust-item"><span class="ln-trust-icon">♙</span><span>Ambiente seguro<br>e criptografado</span></div>
          <div class="ln-trust-item"><span class="ln-trust-icon">▤</span><span>Dados atualizados<br>diariamente</span></div>
          <div class="ln-trust-item"><span class="ln-trust-icon">◖</span><span>Suporte humano<br>especializado</span></div>
          <div class="ln-trust-item"><span class="ln-trust-icon">✓</span><span>Mais de 8.000 usuários<br>em todo o Brasil</span></div>
        </div>
      </section>

      <section class="ln-right" id="como-funciona">
        <div class="ln-demo"><div class="ln-demo-inner">
          <aside class="ln-side">
            <div class="ln-mini-brand"><span class="mini-link">🔗</span>Licita<span>Nexo</span></div>
            <div class="ln-side-item active"><span class="ln-side-ico">⌕</span>Buscar licitações</div>
            <div class="ln-side-item"><span class="ln-side-ico">♧</span>Por Estado</div>
            <div class="ln-side-item"><span class="ln-side-ico">⌖</span>Por Cidade</div>
            <div class="ln-side-item"><span class="ln-side-ico">♜</span>Por Modalidade</div>
            <div class="ln-side-item"><span class="ln-side-ico">⊙</span>Por site de disputa</div>
            <div class="ln-side-item"><span class="ln-side-ico">▽</span>Filtro avançado</div>
            <div class="ln-side-item"><span class="ln-side-ico">⌁</span>Em destaque</div>
            <div class="ln-side-item"><span class="ln-side-ico">▯</span>Minha lista</div>
            <div class="ln-side-item"><span class="ln-side-ico">□</span>Calendário</div>
            <div class="ln-side-item"><span class="ln-side-ico">☷</span>Preferências</div>
            <div class="ln-side-item"><span class="ln-side-ico">◎</span>Radar de licitações</div>
            <div class="ln-side-item"><span class="ln-side-ico">?</span>Suporte</div>
            <div class="ln-side-item"><span class="ln-side-ico">♙</span>Minha conta</div>
            <div class="ln-side-exit">↪ &nbsp; Sair</div>
          </aside>

          <div class="ln-detail">
            <div class="ln-detail-top"><span class="ln-pill">DISPENSA DE LICITAÇÃO</span><div class="ln-detail-actions"><span class="ln-fav">☆ &nbsp; Favoritar</span><span class="ln-items">◉ &nbsp; Ver itens da compra</span></div></div>
            <div class="ln-detail-title">Aquisição de equipamentos e materiais para reabilitação e atendimento hospitalar</div>
            <div class="ln-agency">MUNICÍPIO DE GUARDA-MOR - MG</div>
            <div class="ln-desc">Aquisição de equipamentos e materiais para reabilitação, mobilidade e atendimento hospitalar, em atendimento às necessidades da Secretaria Municipal de Saúde.</div>
            <div class="ln-callout">Itens da compra<strong>já visíveis!</strong></div>

            <div class="ln-meta">
              <div class="ln-meta-cell"><div class="ln-meta-label">Modalidade</div><div class="ln-meta-value">Dispensa de Licitação</div></div>
              <div class="ln-meta-cell"><div class="ln-meta-label">Processo</div><div class="ln-meta-value">DL 034/2024</div></div>
              <div class="ln-meta-cell"><div class="ln-meta-label">Publicado em</div><div class="ln-meta-value">27/08/2024</div></div>
              <div class="ln-meta-cell"><div class="ln-meta-label">Entrega das propostas</div><div class="ln-meta-value">02/09/2024 09:00</div></div>
            </div>
            <div class="ln-chips"><span class="ln-chip">Local: Guarda-Mor - MG</span><span class="ln-chip">Site: Site não informado</span><span class="ln-chip">Valor total: R$ 54.850,80</span><span class="ln-chip">Itens: 6 itens</span></div>

            <div class="ln-table-box">
              <div class="ln-table-headline">Itens da licitação - 6 item(ns)</div>
              <table class="ln-table"><thead><tr><th class="ln-col-num">#</th><th class="ln-col-desc">DESCRIÇÃO DO ITEM</th><th class="ln-col-qtd">QUANTIDADE</th><th class="ln-col-un">UNIDADE</th><th class="ln-col-val">VALOR UNITÁRIO</th><th>VALOR TOTAL</th></tr></thead><tbody>
                <tr><td>1</td><td><div class="ln-product"><span class="ln-prod-pic">♿</span><span><strong>CADEIRA DE RODAS ADULTO</strong><small>Dobrável, em aço carbono, capacidade mínima 100kg</small></span></div></td><td>5</td><td>UNIDADE</td><td>R$ 1.250,00</td><td>R$ 6.250,00</td></tr>
                <tr><td>2</td><td><div class="ln-product"><span class="ln-prod-pic">▱</span><span><strong>CAMA HOSPITALAR MANUAL</strong><small>Com grades laterais, cabeceira e peseira removíveis</small></span></div></td><td>3</td><td>UNIDADE</td><td>R$ 2.990,00</td><td>R$ 8.970,00</td></tr>
                <tr><td>3</td><td><div class="ln-product"><span class="ln-prod-pic">║</span><span><strong>MULETA AXILAR</strong><small>Em alumínio, regulável, com apoio de borracha</small></span></div></td><td>10</td><td>PAR</td><td>R$ 180,00</td><td>R$ 1.800,00</td></tr>
                <tr><td>4</td><td><div class="ln-product"><span class="ln-prod-pic">Π</span><span><strong>ANDADOR ARTICULADO</strong><small>Em alumínio, dobrável, com ponteiras de borracha</small></span></div></td><td>5</td><td>UNIDADE</td><td>R$ 320,00</td><td>R$ 1.600,00</td></tr>
                <tr><td>5</td><td><div class="ln-product"><span class="ln-prod-pic">▥</span><span><strong>CADEIRA DE BANHO</strong><small>Estrutura em alumínio, com apoio de braços</small></span></div></td><td>3</td><td>UNIDADE</td><td>R$ 460,00</td><td>R$ 1.380,00</td></tr>
                <tr><td>6</td><td><div class="ln-product"><span class="ln-prod-pic">▬</span><span><strong>COLCHÃO HOSPITALAR D33</strong><small>Impermeável, com capa em courvin, 188x88x14cm</small></span></div></td><td>8</td><td>UNIDADE</td><td>R$ 231,35</td><td>R$ 1.850,80</td></tr>
              </tbody></table>
              <div class="ln-total"><span>VALOR TOTAL ESTIMADO</span><span>R$ 54.850,80</span></div>
            </div>
          </div>
        </div></div>
        <div class="ln-bottom"><span class="ln-bolt">⚡</span><div><strong>Mais agilidade. Mais clareza. Mais oportunidades para o seu negócio.</strong><span>LicitaNexo mostra o que importa, para você decidir melhor e vender mais.</span></div></div>
      </section>
    </div>
  </main>
</div>'''

    st.html(html)
