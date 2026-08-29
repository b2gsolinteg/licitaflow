from __future__ import annotations

import base64
import random
from pathlib import Path

import streamlit as st


OFFICIAL_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "licitanexo-logo.png"


def _logo_data_uri() -> str:
    if not OFFICIAL_LOGO_PATH.exists():
        return ""
    encoded = base64.b64encode(OFFICIAL_LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _brand_html() -> str:
    logo_uri = _logo_data_uri()
    if logo_uri:
        return f'<div class="lnx-auth-logo"><img src="{logo_uri}" alt="LicitaNexo"></div>'
    return '<div class="lnx-auth-logo"><strong>LicitaNexo</strong></div>'


def _auth_css() -> str:
    return """
    <style>
    :root{--lnx-navy:#061a40;--lnx-blue:#0d5fd7;--lnx-yellow:#f7b714;--lnx-ink:#071a3d;--lnx-muted:#5f6d82}
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{margin:0!important;padding:0!important;min-height:100vh!important;background:#fff!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important}
    header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
    [data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important}
    [data-testid="stVerticalBlock"]{gap:0!important}
    .block-container>[data-testid="stVerticalBlock"]{width:36%!important;min-height:100vh!important;margin:0!important;padding:0!important;position:relative!important;z-index:4!important;background:#fff!important;overflow-y:auto!important}

    .lnx-auth-head{position:relative;width:calc(100% - 84px);max-width:520px;margin:0 auto;padding-top:clamp(26px,3.2vh,42px);z-index:7}
    .lnx-auth-logo{height:74px;display:flex;align-items:center}
    .lnx-auth-logo img{display:block;width:270px;max-width:100%;max-height:72px;object-fit:contain;object-position:left center}
    .lnx-auth-logo strong{font-size:32px;color:var(--lnx-ink)}
    .lnx-auth-kicker{display:inline-flex;margin-top:13px;background:#eaf2ff;color:#1059bf;border-radius:8px;padding:7px 11px;font-size:11px;font-weight:900;letter-spacing:.015em}
    .lnx-auth-title{margin-top:15px;max-width:500px;color:var(--lnx-ink);font-size:clamp(30px,2vw,40px);line-height:1.04;letter-spacing:-1.35px;font-weight:820}
    .lnx-auth-title strong{color:#0d63dd}
    .lnx-auth-caption{margin-top:11px;max-width:480px;color:var(--lnx-muted);font-size:14px;line-height:1.48}

    .st-key-lnx_auth_form{width:calc(100% - 84px)!important;max-width:520px!important;margin:22px auto 28px!important;position:relative!important;z-index:6!important;background:transparent!important}
    .st-key-lnx_auth_form [data-testid="stForm"]{border:0!important;background:transparent!important;padding:0!important}
    .st-key-lnx_auth_form label p{font-size:12.5px!important;color:#0b1b38!important;font-weight:800!important}
    .st-key-lnx_auth_form [data-baseweb="input"],.st-key-lnx_auth_form [data-baseweb="base-input"]{background:#fff!important;border:1px solid #ccd6e3!important;border-radius:7px!important;box-shadow:none!important}
    .st-key-lnx_auth_form input{height:44px!important;background:#fff!important;color:#132540!important;-webkit-text-fill-color:#132540!important;font-size:13px!important}
    .st-key-lnx_auth_form input::placeholder{color:#95a2b5!important;-webkit-text-fill-color:#95a2b5!important}
    .st-key-lnx_auth_form .stFormSubmitButton button{width:100%!important;min-height:48px!important;margin-top:10px!important;border:1px solid #071f47!important;border-radius:7px!important;background:linear-gradient(90deg,#071c3e,#062a5d)!important;color:#fff!important;font-size:15px!important;font-weight:850!important;box-shadow:none!important}
    .st-key-lnx_auth_form .stFormSubmitButton button:hover{border-color:#0b4fa8!important;background:linear-gradient(90deg,#082654,#0a397d)!important}
    .lnx-forgot{text-align:right;margin:-3px 0 6px}.lnx-forgot a{color:#0d5fd7!important;text-decoration:none!important;font-size:12px;font-weight:800}
    .lnx-auth-divider{display:flex;align-items:center;gap:12px;margin:14px 0 11px;color:#506077;font-size:12px;font-weight:700}.lnx-auth-divider::before,.lnx-auth-divider::after{content:"";height:1px;background:#d6dee8;flex:1}
    .lnx-auth-bottom{text-align:center;color:#526177;font-size:12.5px;line-height:1.45}.lnx-auth-bottom a{color:#0d5fd7!important;text-decoration:none!important;font-weight:850}.lnx-auth-back{display:block;margin-top:7px;color:#637187!important;font-size:11.5px!important;font-weight:650!important}

    .lnx-login-price{margin-top:15px;border-radius:13px;overflow:hidden;color:#fff;background:linear-gradient(135deg,#062655,#061a40 76%);border:1px solid #0e396f;box-shadow:0 10px 28px rgba(6,31,70,.15);display:grid;grid-template-columns:.95fr 1.15fr;min-height:118px;text-align:left}
    .lnx-login-price-main{display:flex;flex-direction:column;justify-content:center;padding:16px 18px;border-right:1px solid rgba(255,255,255,.18)}
    .lnx-price-eyebrow{color:var(--lnx-yellow);font-size:10px;font-weight:900;margin-bottom:5px}
    .lnx-login-price-value{white-space:nowrap;display:flex;align-items:flex-end;gap:5px}.lnx-login-price-value span{font-size:20px;font-weight:850;margin-bottom:5px}.lnx-login-price-value strong{font-size:45px;line-height:.88;letter-spacing:-1.7px}.lnx-login-price-value small{font-size:12px;margin-bottom:4px}
    .lnx-login-price-info{padding:15px 16px;display:grid;align-content:center;gap:11px}.lnx-login-price-info div{display:grid;grid-template-columns:22px 1fr;gap:7px;align-items:start}.lnx-login-price-info i{font-style:normal;color:var(--lnx-yellow);font-size:18px;line-height:1}.lnx-login-price-info b{display:block;font-size:10.5px;color:#fff}.lnx-login-price-info span{display:block;margin-top:2px;color:#d5e1f0;font-size:8.8px;line-height:1.35}
    .lnx-security-note{margin-top:14px;display:flex;align-items:center;gap:9px;color:#43536b;font-size:10px;line-height:1.35}.lnx-security-icon{width:27px;height:27px;border:1px solid #cad6e5;border-radius:8px;display:grid;place-items:center;color:#123b75;font-size:14px;flex:0 0 27px}

    .lnx-auth-art,.lnx-auth-art *{box-sizing:border-box}
    .lnx-auth-art{position:fixed;inset:0 0 0 36%;z-index:1;overflow:hidden;color:#fff;background:radial-gradient(circle at 86% 10%,rgba(28,93,201,.20),transparent 28%),linear-gradient(145deg,#03162f 0%,#061d3e 54%,#031226 100%);padding:clamp(16px,1.55vw,30px)}
    .lnx-auth-art::before{content:"";position:absolute;inset:0;pointer-events:none;opacity:.18;background-image:linear-gradient(rgba(55,124,228,.11) 1px,transparent 1px),linear-gradient(90deg,rgba(55,124,228,.11) 1px,transparent 1px);background-size:64px 64px;mask-image:linear-gradient(135deg,transparent 0,#000 30%,#000 85%,transparent 100%)}
    .lnx-art-shell{position:relative;z-index:2;width:min(1000px,100%);height:100%;margin:auto;display:flex;flex-direction:column;gap:11px}
    .lnx-audience-banner{min-height:66px;border:1px solid #173e70;border-radius:14px;background:linear-gradient(135deg,#092143,#061a34);padding:11px 16px;display:flex;align-items:center;gap:13px}
    .lnx-banner-icon{width:43px;height:43px;flex:0 0 43px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(180deg,#3477f2,#1748b5);font-size:18px;box-shadow:0 8px 24px rgba(23,93,215,.25)}
    .lnx-audience-banner b{display:block;font-size:16px;margin-bottom:3px}.lnx-audience-banner span{display:block;color:#d7e2f1;font-size:11px;line-height:1.35}

    .lnx-demo{flex:1;min-height:0;border:1px solid #1b477a;border-radius:15px;background:rgba(5,24,48,.91);padding:14px 14px 12px;box-shadow:0 20px 50px rgba(0,0,0,.20);display:flex;flex-direction:column}
    .lnx-demo-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.lnx-demo-head h2{margin:0;font-size:22px;letter-spacing:-.45px}.lnx-demo-head p{margin:4px 0 0;color:#c5d4e7;font-size:11px;line-height:1.35}
    .lnx-example-badge{white-space:nowrap;border:1px solid #355e8d;border-radius:999px;padding:6px 9px;color:#a9cdf8;font-size:8.5px;font-weight:850;background:#08213f}
    .lnx-tender{margin-top:10px;border:1px solid #234f84;border-radius:11px;background:linear-gradient(180deg,#0a2548,#081e3c);padding:10px;display:grid;grid-template-columns:minmax(250px,1.55fr) .78fr .88fr .62fr;gap:10px;align-items:center}
    .lnx-org{display:grid;grid-template-columns:48px 1fr;gap:10px;align-items:center}.lnx-org-icon{width:48px;height:48px;border-radius:9px;background:#eff5ff;color:#174b8f;display:grid;place-items:center;font-size:24px}.lnx-org b{display:block;font-size:11px;text-transform:uppercase}.lnx-org span{display:block;color:#d6e1ef;font-size:9.5px;line-height:1.35;margin-top:2px}
    .lnx-meta-block{border-left:1px solid #1f4777;padding-left:11px}.lnx-meta-block small{display:block;color:#9db0c8;font-size:8.5px;margin-bottom:3px}.lnx-meta-block strong{font-size:10.5px}.lnx-demo-action{display:flex;align-items:center;justify-content:center;min-height:38px;border:1px solid #2568c1;border-radius:8px;color:#7bb7ff;font-size:10px;font-weight:850;background:#071f3d}

    .lnx-table{margin-top:10px;border:1px solid #234e82;border-radius:11px;overflow:hidden;flex:1;min-height:0;display:flex;flex-direction:column}.lnx-table-title{padding:9px 12px;font-size:13px;font-weight:900;border-bottom:1px solid #234e82;background:#092142}
    .lnx-th,.lnx-tr{display:grid;grid-template-columns:34px minmax(190px,1fr) 72px 90px 92px;align-items:center}.lnx-th{height:27px;background:#0b284f;color:#afc2d9;font-size:8px;font-weight:800}.lnx-tr{flex:1;min-height:44px;border-top:1px solid #183d6c;font-size:9.5px;color:#eef4fb}.lnx-th>div,.lnx-tr>div{padding:0 8px}
    .lnx-item{display:flex;align-items:center;gap:9px}.lnx-item-ico{width:34px;height:34px;border-radius:7px;background:#e9eef5;color:#263c5f;display:grid;place-items:center;font-size:18px;flex:0 0 34px}.lnx-item b{display:block;font-size:10px;margin-bottom:1px}.lnx-item small{display:block;color:#aebed2;font-size:8px}.lnx-table-foot{min-height:31px;display:flex;align-items:center;justify-content:center;border-top:1px solid #183d6c;color:#66acff;font-size:10px;font-weight:800;background:#071d39}

    .lnx-benefits{min-height:84px;border:1px solid #173d70;background:#061a34;border-radius:13px;display:grid;grid-template-columns:repeat(4,1fr);overflow:hidden}.lnx-benefit{padding:12px 10px;display:grid;grid-template-columns:32px 1fr;gap:8px;border-right:1px solid #173d70;align-items:start}.lnx-benefit:last-child{border-right:0}.lnx-benefit-icon{width:32px;height:32px;border-radius:8px;background:#123d75;color:#74adff;display:grid;place-items:center;font-size:17px}.lnx-benefit b{font-size:10.5px;display:block;margin-bottom:3px}.lnx-benefit span{display:block;color:#c6d5e8;font-size:8.5px;line-height:1.35}
    .lnx-closing{min-height:47px;border:1px solid #1d477a;border-radius:11px;background:#08213f;padding:9px 14px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:13px;font-weight:800}.lnx-closing strong{color:var(--lnx-yellow)}

    @media(max-width:1450px){.block-container>[data-testid="stVerticalBlock"]{width:39%!important}.lnx-auth-art{left:39%}.lnx-auth-head,.st-key-lnx_auth_form{width:calc(100% - 64px)!important}.lnx-auth-title{font-size:31px}.lnx-auth-caption{font-size:12.5px}.lnx-login-price-value strong{font-size:39px}.lnx-auth-art{padding:14px}.lnx-art-shell{gap:8px}.lnx-audience-banner{min-height:58px;padding:9px 12px}.lnx-demo{padding:10px}.lnx-demo-head h2{font-size:18px}.lnx-demo-head p{font-size:9.5px}.lnx-tender{padding:8px;gap:7px;grid-template-columns:minmax(205px,1.4fr) .72fr .78fr .55fr}.lnx-org{grid-template-columns:40px 1fr;gap:8px}.lnx-org-icon{width:40px;height:40px;font-size:20px}.lnx-org b{font-size:9.5px}.lnx-org span{font-size:8px}.lnx-th,.lnx-tr{grid-template-columns:28px minmax(150px,1fr) 58px 70px 75px}.lnx-table-title{padding:7px 10px;font-size:11.5px}.lnx-th{height:24px}.lnx-tr{min-height:39px}.lnx-item-ico{width:28px;height:28px;flex-basis:28px;font-size:15px}.lnx-item b{font-size:8.7px}.lnx-item small{font-size:7px}.lnx-benefits{min-height:74px}.lnx-benefit{padding:9px 8px;grid-template-columns:27px 1fr;gap:6px}.lnx-benefit-icon{width:27px;height:27px;font-size:14px}.lnx-benefit b{font-size:9px}.lnx-benefit span{font-size:7.3px}.lnx-closing{min-height:41px;font-size:11px}}
    @media(max-height:820px) and (min-width:901px){.lnx-auth-head{padding-top:18px}.lnx-auth-logo{height:58px}.lnx-auth-logo img{width:225px;max-height:56px}.lnx-auth-kicker{margin-top:7px;padding:5px 9px;font-size:9.5px}.lnx-auth-title{margin-top:10px;font-size:28px;line-height:1.03}.lnx-auth-caption{margin-top:7px;font-size:11.5px}.st-key-lnx_auth_form{margin-top:13px!important;margin-bottom:16px!important}.st-key-lnx_auth_form input{height:40px!important}.st-key-lnx_auth_form .stFormSubmitButton button{min-height:43px!important}.lnx-auth-divider{margin:9px 0 7px}.lnx-auth-bottom{font-size:11.5px}.lnx-login-price{margin-top:10px;min-height:96px}.lnx-login-price-main{padding:12px 14px}.lnx-login-price-value strong{font-size:36px}.lnx-login-price-info{padding:11px 12px;gap:8px}.lnx-security-note{margin-top:9px;font-size:8.8px}.lnx-auth-art{padding:10px 12px}.lnx-art-shell{gap:7px}.lnx-audience-banner{min-height:52px}.lnx-banner-icon{width:35px;height:35px;flex-basis:35px;font-size:14px}.lnx-audience-banner b{font-size:13px}.lnx-audience-banner span{font-size:9px}.lnx-demo{padding:9px}.lnx-demo-head h2{font-size:17px}.lnx-demo-head p{font-size:8.8px}.lnx-tender{margin-top:7px}.lnx-table{margin-top:7px}.lnx-tr{min-height:35px}.lnx-table-foot{min-height:25px}.lnx-benefits{min-height:67px}.lnx-closing{min-height:36px;padding:6px 10px}}
    @media(max-width:900px){.block-container>[data-testid="stVerticalBlock"]{width:100%!important;min-height:100vh!important}.lnx-auth-art{display:none!important}.lnx-auth-head,.st-key-lnx_auth_form{width:calc(100% - 38px)!important;max-width:540px!important}.lnx-auth-head{padding-top:25px}.lnx-auth-logo img{width:230px}.lnx-auth-title{font-size:31px}.lnx-login-price{grid-template-columns:1fr}.lnx-login-price-main{border-right:0;border-bottom:1px solid rgba(255,255,255,.18);align-items:center}}
    </style>
    """


def _art_html() -> str:
    return """
    <aside class="lnx-auth-art" aria-label="Demonstração do LicitaNexo">
      <div class="lnx-art-shell">
        <div class="lnx-audience-banner"><div class="lnx-banner-icon">●●●</div><div><b>Ideal para MEI, microempresas e pequenas empresas</b><span>Solução simples, acessível e prática para quem quer vender para o governo.</span></div></div>
        <section class="lnx-demo">
          <div class="lnx-demo-head"><div><h2>Veja o que está sendo comprado.</h2><p>Itens, quantidades e valores de forma clara para você decidir com mais segurança.</p></div><span class="lnx-example-badge">EXEMPLO DEMONSTRATIVO</span></div>
          <div class="lnx-tender"><div class="lnx-org"><div class="lnx-org-icon">🏛</div><div><b>Prefeitura Municipal de Uberlândia/MG</b><span>Pregão eletrônico · oportunidade usada apenas como exemplo visual</span></div></div><div class="lnx-meta-block"><small>Modalidade</small><strong>Pregão eletrônico</strong></div><div class="lnx-meta-block"><small>Referência</small><strong>Compra pública</strong></div><div class="lnx-demo-action">Exemplo visual</div></div>
          <div class="lnx-table">
            <div class="lnx-table-title">Itens da compra</div><div class="lnx-th"><div>Item</div><div>Descrição</div><div>Qtd.</div><div>Valor unit.</div><div>Valor total</div></div>
            <div class="lnx-tr"><div>01</div><div class="lnx-item"><div class="lnx-item-ico">♿</div><div><b>Cadeira de rodas adulto</b><small>Dobrável, aço carbono</small></div></div><div>5 un</div><div>R$ 950</div><div>R$ 4.750</div></div>
            <div class="lnx-tr"><div>02</div><div class="lnx-item"><div class="lnx-item-ico">▰</div><div><b>Cama hospitalar manual</b><small>3 manivelas, grade metálica</small></div></div><div>3 un</div><div>R$ 1.890</div><div>R$ 5.670</div></div>
            <div class="lnx-tr"><div>03</div><div class="lnx-item"><div class="lnx-item-ico">╱╲</div><div><b>Muleta axilar</b><small>Alumínio, regulável</small></div></div><div>10 un</div><div>R$ 120</div><div>R$ 1.200</div></div>
            <div class="lnx-tr"><div>04</div><div class="lnx-item"><div class="lnx-item-ico">⌗</div><div><b>Andador articulado</b><small>Alumínio, dobrável</small></div></div><div>5 un</div><div>R$ 230</div><div>R$ 1.150</div></div>
            <div class="lnx-table-foot">Veja os itens da compra antes de aprofundar a análise do edital →</div>
          </div>
        </section>
        <div class="lnx-benefits">
          <div class="lnx-benefit"><div class="lnx-benefit-icon">⚡</div><div><b>Comece com pouco</b><span>Ferramenta acessível para quem está começando.</span></div></div>
          <div class="lnx-benefit"><div class="lnx-benefit-icon">◎</div><div><b>Foco no que importa</b><span>Encontre oportunidades que fazem sentido para o seu negócio.</span></div></div>
          <div class="lnx-benefit"><div class="lnx-benefit-icon">☷</div><div><b>Itens da compra</b><span>Veja itens, quantidades e valores sem abrir edital por edital.</span></div></div>
          <div class="lnx-benefit"><div class="lnx-benefit-icon">◆</div><div><b>Mais clareza</b><span>Informações organizadas para apoiar sua decisão.</span></div></div>
        </div>
        <div class="lnx-closing">★ &nbsp; O LicitaNexo foi criado para <strong>&nbsp;empresas como a sua.&nbsp;</strong> Simples de usar. Preço acessível.</div>
      </div>
    </aside>
    """


def _shell(mode: str) -> None:
    st.html(_auth_css())
    st.html(_art_html())
    heading = {"login":"Acesse sua conta e transforme oportunidades em resultados.","request":"Comece seu teste grátis e encontre oportunidades para sua empresa.","invite":"Ative seu convite e acesse o LicitaNexo.","recovery":"Recupere seu acesso com segurança."}[mode]
    caption = {"login":"Encontre licitações, acompanhe itens da compra e organize sua participação para vender para o governo.","request":"7 dias grátis. Depois, R$ 29,90/mês. Preço justo para quem quer começar a vender para o governo.","invite":"Use o código recebido para criar sua senha e ativar o acesso.","recovery":"Solicite um código e defina uma nova senha com segurança."}[mode]
    if mode == "login": highlighted = heading.replace("resultados.", "<strong>resultados.</strong>")
    elif mode == "request": highlighted = heading.replace("oportunidades", "<strong>oportunidades</strong>")
    else: highlighted = heading
    st.html(f'<div class="lnx-auth-head">{_brand_html()}<div class="lnx-auth-kicker">INTELIGÊNCIA EM LICITAÇÕES</div><div class="lnx-auth-title">{highlighted}</div><div class="lnx-auth-caption">{caption}</div></div>')


def _login_price_html() -> str:
    return '''<div class="lnx-login-price"><div class="lnx-login-price-main"><div class="lnx-price-eyebrow">Apenas</div><div class="lnx-login-price-value"><span>R$</span><strong>29,90</strong><small>/mês</small></div></div><div class="lnx-login-price-info"><div><i>▣</i><div><b>7 dias grátis</b><span>Teste completo, sem compromisso.</span></div></div><div><i>✦</i><div><b>Preço justo para quem quer começar a vender para o governo.</b><span>Comece simples e evolua com o seu negócio.</span></div></div></div></div>'''


def _login_footer_html() -> str:
    return '''<div class="lnx-auth-divider">ou</div><div class="lnx-auth-bottom">Ainda não tem uma conta? <a href="?auth=request">Teste grátis por 7 dias</a><a class="lnx-auth-back" href="?">Voltar para a página inicial</a></div>'''


def _security_note_html() -> str:
    return '''<div class="lnx-security-note"><div class="lnx-security-icon">✓</div><span>Acesso protegido e autenticação segura para sua conta.</span></div>'''


def render_public_auth(*, db, security, conversion, commercial, client_ip_getter, motivational_phrases) -> None:
    raw_mode = st.query_params.get("auth", "login")
    if isinstance(raw_mode, list): raw_mode = raw_mode[0] if raw_mode else "login"
    mode = str(raw_mode or "login").strip().lower()
    if mode not in {"login", "request", "invite", "recovery"}: mode = "login"
    _shell(mode)

    with st.container(key="lnx_auth_form"):
        if mode == "login":
            with st.form("login", clear_on_submit=False, enter_to_submit=False):
                email = st.text_input("E-mail ou usuário", placeholder="seu@email.com ou usuário")
                password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                st.markdown('<div class="lnx-forgot"><a href="?auth=recovery">Esqueceu sua senha?</a></div>', unsafe_allow_html=True)
                if st.form_submit_button("Entrar", width="stretch"):
                    client_ip = client_ip_getter()
                    try:
                        security.precheck("login", email, client_ip)
                        user = db.authenticate(email, password)
                        if user:
                            security.register_attempt("login", email, client_ip, success=True)
                            token = security.create_session(user.get("company_id", ""), user.get("id", ""))
                            conversion.record_event("login", user.get("company_id", ""), user.get("id", ""), {"email": user.get("email", "")})
                            st.session_state.user = user
                            st.session_state.security_session_token = token
                            st.session_state.motivational_phrase = random.choice(tuple(motivational_phrases))
                            st.session_state.just_logged_in = True
                            st.rerun()
                        security.register_attempt("login", email, client_ip, success=False)
                        st.error("E-mail ou senha inválidos.")
                    except Exception as error: st.warning(str(error))
            st.html(_login_footer_html()); st.html(_login_price_html()); st.html(_security_note_html())

        elif mode == "request":
            with st.form("access_request", clear_on_submit=False, enter_to_submit=False):
                company = st.text_input("Empresa / Razão social"); cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00"); name = st.text_input("Seu nome"); email = st.text_input("E-mail profissional", key="request_email"); whatsapp = st.text_input("WhatsApp", placeholder="(00) 00000-0000"); segment = st.text_input("Segmento da empresa", placeholder="Ex.: materiais hospitalares"); campaign_code = st.text_input("Código de indicação ou cupom (opcional)")
                if st.form_submit_button("Solicitar acesso", width="stretch"):
                    client_ip = client_ip_getter()
                    try:
                        security.precheck("access_request", email, client_ip); decision = commercial.evaluate_trial(cnpj, email, client_ip)
                        if not decision.allowed:
                            commercial.record_trial_request(cnpj, email, client_ip, decision.outcome, decision.risk_score); raise ValueError(decision.message)
                        risk = db.request_access(company, name, email, whatsapp, segment, cnpj=cnpj, client_ip=client_ip, campaign_code=campaign_code)
                        final_outcome = "review" if (decision.outcome == "review" or risk.get("outcome") == "review") else "allowed"
                        commercial.record_trial_request(cnpj, email, client_ip, final_outcome, max(decision.risk_score, int(risk.get("risk_score") or 0))); security.register_attempt("access_request", email, client_ip, success=True); st.success("Solicitação recebida. Seu teste é de 7 dias, sem cartão.")
                    except Exception as error: st.warning(str(error))
            st.html('<div class="lnx-auth-bottom"><a href="?auth=login">Já possui acesso? Entrar</a><a class="lnx-auth-back" href="?">Voltar para a página inicial</a></div>')

        elif mode == "invite":
            with st.form("activate_invitation", clear_on_submit=False, enter_to_submit=False):
                email = st.text_input("E-mail do convite", placeholder="seu@email.com"); invitation_code = st.text_input("Código de acesso", placeholder="NX-XXXXXXXX"); password = st.text_input("Crie sua senha", type="password", placeholder="Mínimo de 8 caracteres"); password_confirmation = st.text_input("Confirme sua senha", type="password")
                if st.form_submit_button("Ativar convite", width="stretch"):
                    normalized_email = str(email or "").strip().lower(); client_ip = client_ip_getter()
                    try:
                        if not normalized_email or not str(invitation_code or "").strip(): raise ValueError("Informe o e-mail e o código de acesso do convite.")
                        if len(str(password or "")) < 8: raise ValueError("A senha deve ter pelo menos 8 caracteres.")
                        if password != password_confirmation: raise ValueError("As senhas não coincidem.")
                        security.precheck("invitation_activation", normalized_email, client_ip); user = db.activate_invitation(normalized_email, invitation_code, password)
                        if not user: raise ValueError("Não foi possível ativar o convite.")
                        security.register_attempt("invitation_activation", normalized_email, client_ip, success=True); token = security.create_session(user.get("company_id", ""), user.get("id", "")); st.session_state.user = user; st.session_state.security_session_token = token; st.session_state.motivational_phrase = random.choice(tuple(motivational_phrases)); st.session_state.just_logged_in = True; st.rerun()
                    except Exception as error: st.warning(str(error))
            st.html('<div class="lnx-auth-bottom"><a href="?auth=login">Voltar para o login</a></div>')

        else:
            with st.form("password_recovery_request", clear_on_submit=False, enter_to_submit=False):
                recovery_email = st.text_input("E-mail cadastrado", placeholder="seu@email.com", key="password_recovery_request_email")
                if st.form_submit_button("Solicitar código", width="stretch"):
                    normalized_email = str(recovery_email or "").strip().lower(); client_ip = client_ip_getter()
                    try: security.precheck("password_recovery_request", normalized_email, client_ip); db.request_password_reset(normalized_email); security.register_attempt("password_recovery_request", normalized_email, client_ip, success=True); st.success("Solicitação registrada. Se o e-mail estiver cadastrado, o código poderá ser gerado pelo suporte.")
                    except Exception as error: st.warning(str(error))
            st.markdown("---")
            with st.form("password_recovery_reset", clear_on_submit=False, enter_to_submit=False):
                reset_email = st.text_input("E-mail", placeholder="seu@email.com", key="password_recovery_reset_email"); recovery_code = st.text_input("Código de recuperação", placeholder="NX-R-XXXXXXXX"); new_password = st.text_input("Nova senha", type="password", placeholder="Mínimo de 8 caracteres"); new_password_confirmation = st.text_input("Confirme a nova senha", type="password")
                if st.form_submit_button("Redefinir senha", width="stretch"):
                    normalized_email = str(reset_email or "").strip().lower(); client_ip = client_ip_getter()
                    try:
                        if not normalized_email or not str(recovery_code or "").strip(): raise ValueError("Informe o e-mail e o código de recuperação.")
                        if len(str(new_password or "")) < 8: raise ValueError("A senha deve ter pelo menos 8 caracteres.")
                        if new_password != new_password_confirmation: raise ValueError("As senhas não coincidem.")
                        security.precheck("password_recovery_reset", normalized_email, client_ip); db.reset_password(normalized_email, recovery_code, new_password); security.register_attempt("password_recovery_reset", normalized_email, client_ip, success=True); st.success("Senha alterada. Agora você já pode entrar.")
                    except Exception as error: st.warning(str(error))
            st.html('<div class="lnx-auth-bottom"><a href="?auth=login">Voltar para o login</a></div>')
