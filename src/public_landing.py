from __future__ import annotations

import base64
from html import escape
from pathlib import Path

import streamlit as st


def _logo_data_uri(logo_path: Path | str | None) -> str:
    if not logo_path:
        return ""
    path = Path(logo_path)
    if not path.exists():
        return ""
    mime = "image/png"
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def render_public_landing(logo_path: Path | str | None = None) -> None:
    """Landing pública do LicitaNexo, fiel ao mockup comercial aprovado."""
    logo_uri = _logo_data_uri(logo_path)
    logo_html = (
        f'<img src="{escape(logo_uri)}" alt="LicitaNexo">'
        if logo_uri
        else '<div class="ln-brand-fallback">Licita<span>Nexo</span></div>'
    )

    st.markdown(
        f"""
<style>
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{
    margin:0!important;padding:0!important;min-height:100vh!important;
    background:#031b36!important;color:#fff!important;
    font-family:Inter,"Segoe UI",Arial,sans-serif!important;
}}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,
[data-testid="stSidebar"],[data-testid="collapsedControl"]{{display:none!important}}
.block-container{{
    width:100%!important;max-width:none!important;margin:0!important;padding:0!important;
}}
[data-testid="stMainBlockContainer"]{{max-width:none!important;padding:0!important}}
.ln-public *{{box-sizing:border-box}}
.ln-public{{min-height:100vh;background:
    radial-gradient(circle at 70% 22%,rgba(24,104,177,.16),transparent 31%),
    radial-gradient(circle at 15% 75%,rgba(4,64,116,.18),transparent 28%),
    linear-gradient(180deg,#031a34 0%,#04213f 100%);color:#fff}}
.ln-top{{height:80px;border-bottom:1px solid rgba(255,255,255,.13);display:flex;align-items:center}}
.ln-top-in{{width:min(1540px,calc(100% - 64px));margin:auto;display:flex;align-items:center;justify-content:space-between;gap:28px}}
.ln-logo{{width:215px;display:flex;align-items:center;min-width:190px}}
.ln-logo img{{display:block;max-width:205px;max-height:52px;width:auto;height:auto}}
.ln-brand-fallback{{font-size:29px;font-weight:900;letter-spacing:-.035em;color:white}}
.ln-brand-fallback span{{color:#ffbd18}}
.ln-nav{{display:flex;gap:42px;align-items:center;justify-content:center;flex:1}}
.ln-nav a{{color:#fff;text-decoration:none;font-size:16px;font-weight:650;white-space:nowrap}}
.ln-nav a:hover{{color:#ffc126}}
.ln-actions{{display:flex;gap:18px;align-items:center;white-space:nowrap}}
.ln-login-link{{color:white!important;text-decoration:none!important;font-size:16px;font-weight:700;display:inline-flex;gap:9px;align-items:center;padding:11px 8px}}
.ln-login-link:before{{content:"♢";font-size:23px;color:#dbe8f7}}
.ln-cta{{background:#ffbd18;color:#071c33!important;text-decoration:none!important;border-radius:10px;padding:15px 25px;font-size:16px;font-weight:900;box-shadow:0 8px 24px rgba(255,189,24,.18)}}
.ln-cta:hover{{background:#ffc936}}
.ln-main{{width:min(1540px,calc(100% - 64px));margin:0 auto;padding:30px 0 26px}}
.ln-grid{{display:grid;grid-template-columns:minmax(460px,.82fr) minmax(760px,1.5fr);gap:54px;align-items:start}}
.ln-copy{{padding-top:7px}}
.ln-kicker{{display:inline-flex;align-items:center;border:1px solid #1b5689;background:#06294d;border-radius:999px;padding:8px 15px;color:#ffbd18;font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}}
.ln-h1{{font-size:55px;line-height:1.04;letter-spacing:-.038em;font-weight:900;margin:20px 0 12px;max-width:620px;color:white}}
.ln-h1 .yellow{{color:#ffbd18}}
.ln-sub{{font-size:19px;line-height:1.42;color:#dce7f3;margin:0 0 17px;max-width:580px}}
.ln-features{{display:grid;gap:9px}}
.ln-feature{{position:relative;display:flex;align-items:center;gap:17px;border:1px solid #154d7e;background:#0a2d51;border-radius:12px;padding:12px 16px;min-height:80px}}
.ln-feature.diff{{border-color:#df9f08;box-shadow:0 0 0 1px rgba(255,189,24,.06)}}
.ln-feature-badge{{position:absolute;right:13px;top:10px;background:#ffbd18;color:#08203a;font-size:10px;font-weight:900;border-radius:4px;padding:4px 8px;letter-spacing:.03em}}
.ln-icon{{width:59px;height:59px;border-radius:50%;border:1px solid #2e6ea4;background:#103d6d;display:flex;align-items:center;justify-content:center;flex:0 0 59px;font-size:29px}}
.diff .ln-icon{{border-color:#e4a70d;color:#ffbd18}}
.ln-ft-title{{font-size:18px;font-weight:850;margin-bottom:3px;color:white}}
.ln-ft-copy{{font-size:13.5px;line-height:1.35;color:#c8d8e8;max-width:450px}}
.ln-price-card{{margin-top:14px;border:1px solid #1b527f;background:#0a2c4f;border-radius:12px;padding:14px 17px;display:grid;grid-template-columns:1fr auto;align-items:center;gap:18px}}
.ln-plan-caption{{font-size:13px;font-weight:700;color:white;margin-bottom:2px}}
.ln-price-line{{display:flex;align-items:flex-end;gap:4px;line-height:1}}
.ln-currency{{font-size:20px;padding-bottom:4px}} .ln-price{{font-size:47px;color:#ffbd18;font-weight:950;letter-spacing:-.05em}} .ln-month{{font-size:18px;padding-bottom:5px}}
.ln-trial{{text-align:right}}
.ln-trial a{{display:inline-flex;align-items:center;gap:12px;background:#ffbd18;color:#071c33!important;text-decoration:none!important;border-radius:9px;padding:13px 21px;font-size:14px;font-weight:900}}
.ln-trial-note{{margin-top:7px;font-size:11px;color:#c7d5e3}}
.ln-trust{{margin-top:11px;border:1px solid #15466f;background:#082744;border-radius:12px;padding:11px 13px;display:grid;grid-template-columns:repeat(4,1fr);gap:6px}}
.ln-trust-item{{display:flex;align-items:center;gap:9px;color:#c9d7e5;font-size:10.5px;line-height:1.3}}
.ln-trust-icon{{width:34px;height:34px;border-radius:50%;border:1px solid #2a618e;background:#0d345d;display:flex;align-items:center;justify-content:center;color:white;font-size:16px;flex:0 0 34px}}
.ln-demo-wrap{{padding-top:0}}
.ln-demo{{border:2px solid #2e6393;border-radius:17px;background:#0a2b4d;padding:4px;box-shadow:0 20px 60px rgba(0,0,0,.23);overflow:hidden}}
.ln-demo-inner{{display:grid;grid-template-columns:190px minmax(0,1fr);min-height:645px;border-radius:12px;overflow:hidden}}
.ln-demo-side{{background:linear-gradient(180deg,#0c3a69,#082d52);padding:18px 14px;color:white}}
.ln-mini-logo{{margin:0 0 17px;padding:0 5px;font-size:20px;font-weight:900;color:white;display:flex;align-items:center;gap:7px}} .ln-mini-logo span{{color:#ffbd18}}
.ln-side-item{{display:flex;align-items:center;gap:10px;height:35px;border-radius:7px;padding:0 9px;font-size:12px;font-weight:700;color:#fff;margin-bottom:2px}}
.ln-side-item.active{{background:#164b80;color:#ffbd18}}
.ln-side-icon{{width:19px;text-align:center;font-size:15px}}
.ln-side-exit{{margin-top:18px;border:1px solid #e6a70a;color:#ffbd18;border-radius:7px;height:36px;display:flex;align-items:center;padding:0 12px;font-size:12px;font-weight:800}}
.ln-demo-body{{background:#fff;color:#10233c;padding:20px 22px 16px}}
.ln-demo-topline{{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}}
.ln-pill{{display:inline-flex;background:#e9f3ff;color:#0b5b9e;border-radius:7px;padding:6px 10px;font-size:11px;font-weight:900;letter-spacing:.02em}}
.ln-demo-actions{{display:flex;gap:8px}}
.ln-fav{{border:1px solid #d9e1ea;background:white;border-radius:7px;padding:9px 13px;font-size:11px;font-weight:800;color:#23344d}}
.ln-items-btn{{background:#ffbd18;border:1px solid #e3a50b;border-radius:7px;padding:9px 16px;font-size:11px;font-weight:900;color:#0b223c;white-space:nowrap}}
.ln-demo-title{{font-size:22px;line-height:1.15;font-weight:900;letter-spacing:-.02em;margin:13px 0 5px;max-width:625px;color:#14233a}}
.ln-agency{{font-size:12px;font-weight:850;color:#36577c;margin-bottom:8px}}
.ln-demo-desc{{font-size:12px;line-height:1.35;color:#4f6280;margin-bottom:12px;max-width:650px}}
.ln-callout{{position:absolute;right:20px;top:94px;background:#082c50;color:white;border-radius:9px;padding:12px 15px;font-size:12px;font-weight:800;box-shadow:0 8px 25px rgba(0,0,0,.18)}} .ln-callout strong{{display:block;color:#ffbd18;font-size:15px}}
.ln-demo-body{{position:relative}}
.ln-meta{{display:grid;grid-template-columns:1.2fr 1fr 1fr 1.2fr;border:1px solid #e0e6ed;border-radius:7px;margin:8px 0 9px;overflow:hidden}}
.ln-meta-cell{{padding:8px 10px;border-right:1px solid #e8edf2}} .ln-meta-cell:last-child{{border-right:0}}
.ln-meta-label{{font-size:9px;color:#728098;margin-bottom:3px}} .ln-meta-value{{font-size:11px;color:#24405e;font-weight:750}}
.ln-chips{{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}}
.ln-chip{{border:1px solid #dce4ec;border-radius:999px;padding:5px 10px;font-size:9.5px;font-weight:800;color:#2f4969;background:#fff}}
.ln-table-box{{border:1px solid #d9e1e9;border-radius:8px;overflow:hidden}}
.ln-table-headline{{padding:9px 11px;font-size:11px;font-weight:900;color:#1f344f;border-bottom:1px solid #e4e9ef}}
.ln-table{{width:100%;border-collapse:collapse;font-size:9.5px}}
.ln-table th{{text-align:left;padding:7px 7px;color:#50607a;font-size:8px;border-bottom:1px solid #e4e9ef;font-weight:900}}
.ln-table td{{padding:6px 7px;border-bottom:1px solid #e7ecf1;color:#263c58;vertical-align:middle}}
.ln-table tr:last-child td{{border-bottom:0}}
.ln-prod{{display:flex;align-items:center;gap:8px}}
.ln-prod-icon{{width:31px;height:31px;border-radius:5px;background:#edf2f6;display:flex;align-items:center;justify-content:center;font-size:17px;flex:0 0 31px}}
.ln-prod strong{{display:block;font-size:9.5px;color:#1c334e}} .ln-prod small{{display:block;color:#63738a;font-size:8px;margin-top:1px;line-height:1.15}}
.ln-total{{display:flex;justify-content:flex-end;gap:42px;padding:10px 11px;background:#fbfcfd;border-top:1px solid #e4e9ef;font-size:11px;font-weight:900;color:#315173}}
.ln-bottom{{margin-top:16px;border:1px solid #16507e;background:#0b3158;border-radius:12px;padding:13px 17px;display:flex;align-items:center;gap:14px}}
.ln-bolt{{width:47px;height:47px;border-radius:50%;border:1px solid #276b9e;background:#0f3e6b;display:flex;align-items:center;justify-content:center;color:#ffbd18;font-size:27px}}
.ln-bottom strong{{display:block;color:#fff;font-size:15px;margin-bottom:2px}} .ln-bottom span{{color:#c8d8e8;font-size:12px}}
@media(max-width:1250px){{
    .ln-grid{{grid-template-columns:1fr;gap:28px}}
    .ln-copy{{max-width:760px;margin:auto}}
    .ln-demo-wrap{{max-width:950px;margin:auto;width:100%}}
    .ln-h1{{max-width:730px}}
}}
@media(max-width:900px){{
    .ln-top{{height:auto;padding:14px 0}} .ln-top-in,.ln-main{{width:min(100% - 28px,760px)}}
    .ln-nav{{display:none}} .ln-logo{{min-width:0;width:auto}} .ln-logo img{{max-width:160px}}
    .ln-actions{{gap:7px}} .ln-login-link{{font-size:13px}} .ln-cta{{padding:11px 13px;font-size:13px}}
    .ln-main{{padding-top:18px}} .ln-h1{{font-size:39px}} .ln-sub{{font-size:17px}}
    .ln-demo-inner{{grid-template-columns:1fr}} .ln-demo-side{{display:none}}
    .ln-demo-body{{padding:15px 12px}} .ln-callout{{display:none}}
    .ln-meta{{grid-template-columns:1fr 1fr}} .ln-meta-cell:nth-child(2){{border-right:0}}
    .ln-table-box{{overflow-x:auto}} .ln-table{{min-width:690px}}
    .ln-price-card{{grid-template-columns:1fr}} .ln-trial{{text-align:left}}
    .ln-trust{{grid-template-columns:1fr 1fr}}
}}
@media(max-width:560px){{
    .ln-actions .ln-login-link{{display:none}} .ln-h1{{font-size:34px}}
    .ln-feature{{padding:11px}} .ln-icon{{width:48px;height:48px;flex-basis:48px;font-size:23px}}
    .ln-ft-title{{font-size:16px}} .ln-ft-copy{{font-size:12px}}
    .ln-trust{{grid-template-columns:1fr}} .ln-price{{font-size:42px}}
}}
</style>
<div class="ln-public">
  <header class="ln-top">
    <div class="ln-top-in">
      <div class="ln-logo">{logo_html}</div>
      <nav class="ln-nav">
        <a href="#recursos">Recursos</a><a href="#como-funciona">Como funciona</a><a href="#planos">Planos</a>
        <a href="#depoimentos">Depoimentos</a><a href="#blog">Blog</a><a href="#contato">Contato</a>
      </nav>
      <div class="ln-actions">
        <a class="ln-login-link" href="?auth=login">Entrar</a>
        <a class="ln-cta" href="?auth=request">Começar agora</a>
      </div>
    </div>
  </header>

  <main class="ln-main">
    <div class="ln-grid">
      <section class="ln-copy" id="recursos">
        <div class="ln-kicker">A plataforma inteligente de licitações</div>
        <div class="ln-h1">Encontre licitações mais rápido e veja <span class="yellow">os produtos na tela</span> sem abrir edital por edital.</div>
        <p class="ln-sub">Economize tempo. Ganhe vantagem.<br>Decida melhor com as informações que importam.</p>

        <div class="ln-features">
          <div class="ln-feature"><div class="ln-icon">⌕</div><div><div class="ln-ft-title">Busque e filtre com precisão</div><div class="ln-ft-copy">Localize oportunidades por cidade, modalidade, palavra-chave e muito mais.</div></div></div>
          <div class="ln-feature diff"><div class="ln-feature-badge">DIFERENCIAL</div><div class="ln-icon">◉</div><div><div class="ln-ft-title">Veja os produtos na tela</div><div class="ln-ft-copy">Itens da compra já visíveis, com quantidades, unidades e valores — sem abrir o edital.</div></div></div>
          <div class="ln-feature"><div class="ln-icon">◎</div><div><div class="ln-ft-title">Decida com mais confiança</div><div class="ln-ft-copy">Compare oportunidades, avalie demandas e prepare propostas mais competitivas.</div></div></div>
        </div>

        <div class="ln-price-card" id="planos">
          <div><div class="ln-plan-caption">Planos a partir de</div><div class="ln-price-line"><span class="ln-currency">R$</span><span class="ln-price">29,90</span><span class="ln-month">/mês</span></div></div>
          <div class="ln-trial"><a href="?auth=request">Testar agora por 7 dias grátis <span>›</span></a><div class="ln-trial-note">🛡 Sem compromisso. Cancele quando quiser.</div></div>
        </div>

        <div class="ln-trust">
          <div class="ln-trust-item"><span class="ln-trust-icon">⌾</span><span>Ambiente seguro<br>e criptografado</span></div>
          <div class="ln-trust-item"><span class="ln-trust-icon">▤</span><span>Dados atualizados<br>diariamente</span></div>
          <div class="ln-trust-item"><span class="ln-trust-icon">◖</span><span>Suporte humano<br>especializado</span></div>
          <div class="ln-trust-item"><span class="ln-trust-icon">✓</span><span>Mais de 8.000 usuários<br>em todo o Brasil</span></div>
        </div>
      </section>

      <section class="ln-demo-wrap" id="como-funciona">
        <div class="ln-demo">
          <div class="ln-demo-inner">
            <aside class="ln-demo-side">
              <div class="ln-mini-logo">🔗 Licita<span>Nexo</span></div>
              <div class="ln-side-item active"><span class="ln-side-icon">⌕</span>Buscar licitações</div>
              <div class="ln-side-item"><span class="ln-side-icon">♙</span>Por Estado</div>
              <div class="ln-side-item"><span class="ln-side-icon">⌖</span>Por Cidade</div>
              <div class="ln-side-item"><span class="ln-side-icon">♜</span>Por Modalidade</div>
              <div class="ln-side-item"><span class="ln-side-icon">⊙</span>Por site de disputa</div>
              <div class="ln-side-item"><span class="ln-side-icon">▽</span>Filtro avançado</div>
              <div class="ln-side-item"><span class="ln-side-icon">⌁</span>Em destaque</div>
              <div class="ln-side-item"><span class="ln-side-icon">▯</span>Minha lista</div>
              <div class="ln-side-item"><span class="ln-side-icon">□</span>Calendário</div>
              <div class="ln-side-item"><span class="ln-side-icon">☷</span>Preferências</div>
              <div class="ln-side-item"><span class="ln-side-icon">◎</span>Radar de licitações</div>
              <div class="ln-side-item"><span class="ln-side-icon">?</span>Suporte</div>
              <div class="ln-side-item"><span class="ln-side-icon">♙</span>Minha conta</div>
              <div class="ln-side-exit">↪ &nbsp; Sair</div>
            </aside>

            <div class="ln-demo-body">
              <div class="ln-demo-topline">
                <span class="ln-pill">DISPENSA DE LICITAÇÃO</span>
                <div class="ln-demo-actions"><span class="ln-fav">☆ Favoritar</span><span class="ln-items-btn">◉ &nbsp; Ver itens da compra</span></div>
              </div>
              <div class="ln-demo-title">Aquisição de equipamentos e materiais para reabilitação e atendimento hospitalar</div>
              <div class="ln-agency">MUNICÍPIO DE GUARDA-MOR - MG</div>
              <div class="ln-demo-desc">Aquisição de equipamentos e materiais para reabilitação, mobilidade e atendimento hospitalar, em atendimento às necessidades da Secretaria Municipal de Saúde.</div>
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
                <table class="ln-table">
                  <thead><tr><th>#</th><th>DESCRIÇÃO DO ITEM</th><th>QUANTIDADE</th><th>UNIDADE</th><th>VALOR UNITÁRIO</th><th>VALOR TOTAL</th></tr></thead>
                  <tbody>
                    <tr><td>1</td><td><div class="ln-prod"><span class="ln-prod-icon">♿</span><span><strong>CADEIRA DE RODAS ADULTO</strong><small>Dobrável, em aço carbono, capacidade mínima 100kg</small></span></div></td><td>5</td><td>UNIDADE</td><td>R$ 1.250,00</td><td>R$ 6.250,00</td></tr>
                    <tr><td>2</td><td><div class="ln-prod"><span class="ln-prod-icon">▱</span><span><strong>CAMA HOSPITALAR MANUAL</strong><small>Com grades laterais, cabeceira e peseira removíveis</small></span></div></td><td>3</td><td>UNIDADE</td><td>R$ 2.990,00</td><td>R$ 8.970,00</td></tr>
                    <tr><td>3</td><td><div class="ln-prod"><span class="ln-prod-icon">║</span><span><strong>MULETA AXILAR</strong><small>Em alumínio, regulável, com apoio de borracha</small></span></div></td><td>10</td><td>PAR</td><td>R$ 180,00</td><td>R$ 1.800,00</td></tr>
                    <tr><td>4</td><td><div class="ln-prod"><span class="ln-prod-icon">Π</span><span><strong>ANDADOR ARTICULADO</strong><small>Em alumínio, dobrável, com ponteiras de borracha</small></span></div></td><td>5</td><td>UNIDADE</td><td>R$ 320,00</td><td>R$ 1.600,00</td></tr>
                    <tr><td>5</td><td><div class="ln-prod"><span class="ln-prod-icon">▥</span><span><strong>CADEIRA DE BANHO</strong><small>Estrutura em alumínio, com apoio de braços</small></span></div></td><td>3</td><td>UNIDADE</td><td>R$ 460,00</td><td>R$ 1.380,00</td></tr>
                    <tr><td>6</td><td><div class="ln-prod"><span class="ln-prod-icon">▬</span><span><strong>COLCHÃO HOSPITALAR D33</strong><small>Impermeável, com capa em courvin, 188x88x14cm</small></span></div></td><td>8</td><td>UNIDADE</td><td>R$ 231,35</td><td>R$ 1.850,80</td></tr>
                  </tbody>
                </table>
                <div class="ln-total"><span>VALOR TOTAL ESTIMADO</span><span>R$ 54.850,80</span></div>
              </div>
            </div>
          </div>
        </div>
        <div class="ln-bottom"><span class="ln-bolt">⚡</span><div><strong>Mais agilidade. Mais clareza. Mais oportunidades para o seu negócio.</strong><span>LicitaNexo mostra o que importa, para você decidir melhor e vender mais.</span></div></div>
      </section>
    </div>
  </main>
</div>
""",
        unsafe_allow_html=True,
    )
