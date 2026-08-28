from __future__ import annotations

import base64
import random
from pathlib import Path

import streamlit as st


OFFICIAL_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "licitanexo-logo.png"


def _logo_data_uri() -> str:
    if not OFFICIAL_LOGO_PATH.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(OFFICIAL_LOGO_PATH.read_bytes()).decode('ascii')}"


def _brand_html() -> str:
    logo_uri = _logo_data_uri()
    if logo_uri:
        return f'<div class="lnx-auth-logo"><img src="{logo_uri}" alt="LicitaNexo"></div>'
    return '<div class="lnx-auth-logo"><strong>LicitaNexo</strong></div>'


def _auth_css() -> str:
    return """
    <style>
    :root{--lnx-navy:#061a40;--lnx-navy2:#082960;--lnx-blue:#0e5fd7;--lnx-yellow:#f7b714;--lnx-ink:#071a3d;--lnx-muted:#5e6b80}
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{margin:0!important;padding:0!important;background:#fff!important;min-height:100vh!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important}
    header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
    [data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important}
    [data-testid="stVerticalBlock"]{gap:0!important}
    .block-container>[data-testid="stVerticalBlock"]{width:40%!important;min-height:100vh!important;padding:0!important;margin:0!important;position:relative!important;z-index:3!important;background:#fff!important;overflow-y:auto!important}

    .lnx-auth-art{position:fixed;inset:0 0 0 40%;z-index:0;overflow:hidden;background:radial-gradient(circle at 47% 42%,#0b3b84 0,#082a63 25%,#061e4a 52%,#041632 100%)}
    .lnx-auth-art .grid{position:absolute;inset:0;opacity:.28;background-image:linear-gradient(rgba(55,128,244,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(55,128,244,.10) 1px,transparent 1px);background-size:58px 58px}
    .lnx-auth-art .orbit{position:absolute;left:48%;top:42%;transform:translate(-50%,-50%);border:1px solid rgba(67,139,255,.35);border-radius:50%}
    .lnx-auth-art .o1{width:430px;height:430px}.lnx-auth-art .o2{width:640px;height:640px;opacity:.55}.lnx-auth-art .o3{width:850px;height:850px;opacity:.28}
    .lnx-auth-hub{position:absolute;left:48%;top:42%;transform:translate(-50%,-50%);width:132px;height:132px;border-radius:50%;background:#fff;display:grid;place-items:center;z-index:5;box-shadow:0 0 0 11px rgba(31,119,242,.17),0 0 42px rgba(247,183,20,.25);border:2px solid var(--lnx-yellow)}
    .lnx-auth-hub img{width:96px;max-height:82px;object-fit:contain}
    .lnx-auth-node,.lnx-product-card,.lnx-opportunities{position:absolute;z-index:4;color:#fff;background:linear-gradient(145deg,rgba(8,40,88,.96),rgba(5,25,58,.98));border:1px solid rgba(247,183,20,.58);border-radius:16px;box-shadow:0 14px 36px rgba(0,0,0,.25)}
    .lnx-auth-node{padding:15px 17px}.lnx-auth-node b{display:block;font-size:13px;margin-bottom:3px}.lnx-auth-node strong{font-size:30px;letter-spacing:-1px}.lnx-auth-node span{display:block;color:#dbe7f6;font-size:10px;line-height:1.35;margin-top:4px}
    .lnx-auth-node.a1{left:9%;top:7%;width:200px}.lnx-auth-node.a2{right:9%;top:10%;width:210px}.lnx-auth-node.a3{left:6%;top:28%;width:210px}.lnx-auth-node.a4{right:7%;top:29%;width:215px}
    .lnx-product-card{padding:13px 14px;width:245px}.lnx-product-card.p1{left:8%;bottom:19%}.lnx-product-card.p2{right:9%;bottom:18%}.lnx-product-card.p3{left:39%;bottom:4%}
    .lnx-product-card .p-title{font-size:12px;font-weight:850;margin-bottom:5px}.lnx-product-card .p-org{font-size:8px;line-height:1.35;color:#c9d9ed;min-height:22px}.lnx-product-card .p-row{display:flex;justify-content:space-between;gap:8px;margin-top:10px;font-size:9px;color:#dce8f8}.lnx-product-card .p-price{font-size:18px;color:var(--lnx-yellow);font-weight:900;margin-top:5px}.lnx-product-card .p-status{display:inline-block;margin-top:8px;color:#79e7a3;font-size:8px;font-weight:800}
    .lnx-opportunities{right:5%;bottom:3%;width:205px;padding:14px 16px}.lnx-opportunities b{display:block;font-size:12px;margin-bottom:8px}.lnx-opportunities div{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.10);font-size:9px;color:#dbe6f4}.lnx-opportunities div:last-child{border-bottom:0;color:var(--lnx-yellow);font-weight:800}

    .lnx-auth-head{position:absolute;left:clamp(38px,4.2vw,72px);top:clamp(30px,4vh,48px);z-index:6;width:calc(40vw - 90px)}
    .lnx-auth-logo img{display:block;width:275px;max-width:100%;height:auto}.lnx-auth-logo strong{font-size:32px;color:var(--lnx-ink)}
    .lnx-auth-kicker{display:inline-flex;margin-top:22px;background:#edf4ff;color:#1558bd;border-radius:999px;padding:7px 12px;font-size:11px;font-weight:900;letter-spacing:.02em}
    .lnx-auth-title{margin-top:17px;max-width:480px;font-size:clamp(27px,2vw,38px);line-height:1.08;letter-spacing:-1px;font-weight:800;color:var(--lnx-ink)}.lnx-auth-title strong{color:#0d5fcc}
    .lnx-auth-caption{margin-top:12px;color:var(--lnx-muted);font-size:14px;line-height:1.48;max-width:470px}

    .st-key-lnx_auth_form{width:calc(40vw - 92px)!important;max-width:500px!important;margin-left:clamp(38px,4.2vw,72px)!important;margin-top:clamp(260px,34vh,325px)!important;margin-bottom:32px!important;position:relative!important;z-index:5!important;background:transparent!important}
    .st-key-lnx_auth_form [data-testid="stForm"]{border:0!important;background:transparent!important;padding:0!important}
    .st-key-lnx_auth_form label p{font-size:13px!important;color:#172543!important;font-weight:700!important}
    .st-key-lnx_auth_form [data-baseweb="input"],.st-key-lnx_auth_form [data-baseweb="base-input"]{background:#fff!important;border:1px solid #cbd4e1!important;border-radius:6px!important;box-shadow:none!important}
    .st-key-lnx_auth_form input{height:46px!important;background:#fff!important;color:#172543!important;-webkit-text-fill-color:#172543!important;font-size:14px!important}
    .st-key-lnx_auth_form input::placeholder{color:#9aa6b8!important;-webkit-text-fill-color:#9aa6b8!important}
    .st-key-lnx_auth_form .stFormSubmitButton button{width:100%!important;min-height:48px!important;background:var(--lnx-navy)!important;color:#fff!important;border:1px solid var(--lnx-navy)!important;border-radius:6px!important;font-weight:800!important;font-size:16px!important;box-shadow:none!important;margin-top:12px!important}
    .st-key-lnx_auth_form .stFormSubmitButton button:hover{background:#082b61!important;border-color:#082b61!important}
    .lnx-forgot{text-align:right;margin:-2px 0 7px}.lnx-forgot a{color:#0d5fcc!important;text-decoration:none!important;font-size:13px;font-weight:700}
    .lnx-auth-bottom{margin-top:18px;text-align:center;color:#66738a;font-size:13px;line-height:1.45}.lnx-auth-bottom a{color:#0d5fcc!important;text-decoration:none!important;font-weight:850}.lnx-auth-back{display:block;margin-top:8px;color:#6c778a!important;font-size:12px!important;font-weight:600!important}
    .lnx-login-price{margin-top:20px;min-height:112px;border-radius:13px;background:linear-gradient(135deg,#062656,#061a40);color:#fff;display:grid;grid-template-columns:1.04fr 1fr;overflow:hidden;box-shadow:0 10px 25px rgba(6,31,70,.14);text-align:left}
    .lnx-login-price-main{display:flex;align-items:center;padding:18px 20px;border-right:1px solid rgba(255,255,255,.18)}.lnx-login-price-value{white-space:nowrap}.lnx-login-price-value span{font-size:20px;font-weight:850}.lnx-login-price-value strong{font-size:42px;letter-spacing:-1.5px}.lnx-login-price-value small{font-size:13px}
    .lnx-login-price-info{padding:16px 17px;display:grid;align-content:center;gap:10px}.lnx-login-price-info b{font-size:11px;color:#fff;display:block}.lnx-login-price-info span{font-size:9px;color:#d7e4f5;display:block;margin-top:2px;line-height:1.3}.lnx-login-price-info i{font-style:normal;color:var(--lnx-yellow);margin-right:5px}

    @media(max-width:1150px){
      .block-container>[data-testid="stVerticalBlock"]{width:46%!important}.lnx-auth-art{left:46%}.lnx-auth-head{width:calc(46vw - 86px)}.st-key-lnx_auth_form{width:calc(46vw - 90px)!important}.lnx-auth-node.a3,.lnx-auth-node.a4{display:none}.lnx-product-card{width:210px}.lnx-product-card.p3{display:none}
    }
    @media(max-width:900px){
      .lnx-auth-art{display:none}.block-container>[data-testid="stVerticalBlock"]{width:100%!important;min-height:100vh!important;padding:0 22px!important;box-sizing:border-box!important}.lnx-auth-head{position:absolute;left:22px;right:22px;top:32px;width:auto}.lnx-auth-logo img{width:225px}.lnx-auth-title{font-size:31px}.st-key-lnx_auth_form{width:100%!important;max-width:540px!important;margin:245px auto 34px!important}.lnx-login-price{grid-template-columns:1fr}.lnx-login-price-main{border-right:0;border-bottom:1px solid rgba(255,255,255,.18);justify-content:center}.lnx-login-price-info{text-align:center}
    }
    </style>
    """


def _art_html() -> str:
    logo_uri = _logo_data_uri()
    hub = f'<img src="{logo_uri}" alt="LicitaNexo">' if logo_uri else '<strong>LN</strong>'
    return f'''
    <div class="lnx-auth-art" aria-hidden="true">
      <div class="grid"></div><div class="orbit o1"></div><div class="orbit o2"></div><div class="orbit o3"></div>
      <div class="lnx-auth-hub">{hub}</div>
      <div class="lnx-auth-node a1"><b>Alertas ativos</b><strong>38</strong><span>Editais relevantes para você hoje</span></div>
      <div class="lnx-auth-node a2"><b>Economia de tempo</b><strong>80%</strong><span>Menos tempo buscando, mais tempo vendendo.</span></div>
      <div class="lnx-auth-node a3"><b>Cobertura nacional</b><strong>5.570+</strong><span>Municípios monitorados</span></div>
      <div class="lnx-auth-node a4"><b>Inteligência de preços</b><span>Compare valores históricos e tome decisões com mais precisão.</span></div>
      <div class="lnx-product-card p1"><div class="p-title">Cadeira de rodas adulto</div><div class="p-org">PREFEITURA MUNICIPAL DE GUARDA-MOR · MG</div><div class="p-row"><span>Quantidade</span><b>5 unidades</b></div><div class="p-price">R$ 6.250,00</div><span class="p-status">● Aberto</span></div>
      <div class="lnx-product-card p2"><div class="p-title">Cama hospitalar manual</div><div class="p-org">FUNDO MUNICIPAL DE SAÚDE · MG</div><div class="p-row"><span>Quantidade</span><b>3 unidades</b></div><div class="p-price">R$ 8.970,00</div><span class="p-status">● Aberto</span></div>
      <div class="lnx-product-card p3"><div class="p-title">Impressora multifuncional</div><div class="p-org">PREFEITURA MUNICIPAL DE UBERLÂNDIA · MG</div><div class="p-row"><span>Quantidade</span><b>10 unidades</b></div><div class="p-price">R$ 3.980,00</div><span class="p-status">● Aberto</span></div>
      <div class="lnx-opportunities"><b>Oportunidades em destaque</b><div><span>Saúde</span><strong>128</strong></div><div><span>Educação</span><strong>87</strong></div><div><span>Administração</span><strong>64</strong></div><div><span>Ver todas as oportunidades</span><strong>→</strong></div></div>
    </div>
    '''


def _shell(mode: str) -> None:
    st.html(_auth_css())
    st.html(_art_html())
    heading = {
        "login": "Acesse sua conta e transforme oportunidades em resultados.",
        "request": "Comece seu teste grátis e encontre mais oportunidades.",
        "invite": "Ative seu convite e acesse o LicitaNexo.",
        "recovery": "Recupere seu acesso com segurança.",
    }[mode]
    caption = {
        "login": "Encontre licitações, acompanhe editais e faça melhores negócios com agilidade e segurança.",
        "request": "7 dias grátis, sem cartão. Depois, continue por R$ 29,90/mês se fizer sentido para sua empresa.",
        "invite": "Use o código recebido para criar sua senha e ativar o acesso.",
        "recovery": "Solicite um código e defina uma nova senha com segurança.",
    }[mode]
    highlighted = heading.replace("resultados.", "<strong>resultados.</strong>").replace("oportunidades.", "<strong>oportunidades.</strong>")
    st.html(f'<div class="lnx-auth-head">{_brand_html()}<div class="lnx-auth-kicker">INTELIGÊNCIA EM LICITAÇÕES</div><div class="lnx-auth-title">{highlighted}</div><div class="lnx-auth-caption">{caption}</div></div>')


def _login_price_html() -> str:
    return '''
    <div class="lnx-login-price">
      <div class="lnx-login-price-main"><div class="lnx-login-price-value"><span>R$ </span><strong>29,90</strong><small>/mês</small></div></div>
      <div class="lnx-login-price-info"><div><b><i>▣</i>7 dias grátis</b><span>Teste completo, sem compromisso.</span></div><div><b><i>✦</i>Um dos menores preços do mercado</b><span>Mais economia para o seu negócio.</span></div></div>
    </div>
    '''


def render_public_auth(*, db, security, conversion, commercial, client_ip_getter, motivational_phrases) -> None:
    raw_mode = st.query_params.get("auth", "login")
    if isinstance(raw_mode, list):
        raw_mode = raw_mode[0] if raw_mode else "login"
    mode = str(raw_mode or "login").strip().lower()
    if mode not in {"login", "request", "invite", "recovery"}:
        mode = "login"
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
                    except Exception as error:
                        st.warning(str(error))
            st.html('<div class="lnx-auth-bottom">Ainda não tem uma conta? <a href="?auth=request">Teste grátis por 7 dias</a><a class="lnx-auth-back" href="?">Voltar para a página inicial</a></div>')
            st.html(_login_price_html())

        elif mode == "request":
            with st.form("access_request", clear_on_submit=False, enter_to_submit=False):
                company = st.text_input("Empresa / Razão social")
                cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
                name = st.text_input("Seu nome")
                email = st.text_input("E-mail profissional", key="request_email")
                whatsapp = st.text_input("WhatsApp", placeholder="(00) 00000-0000")
                segment = st.text_input("Segmento da empresa", placeholder="Ex.: materiais hospitalares")
                campaign_code = st.text_input("Código de indicação ou cupom (opcional)")
                if st.form_submit_button("Solicitar acesso", width="stretch"):
                    client_ip = client_ip_getter()
                    try:
                        security.precheck("access_request", email, client_ip)
                        decision = commercial.evaluate_trial(cnpj, email, client_ip)
                        if not decision.allowed:
                            commercial.record_trial_request(cnpj, email, client_ip, decision.outcome, decision.risk_score)
                            raise ValueError(decision.message)
                        risk = db.request_access(company, name, email, whatsapp, segment, cnpj=cnpj, client_ip=client_ip, campaign_code=campaign_code)
                        final_outcome = "review" if (decision.outcome == "review" or risk.get("outcome") == "review") else "allowed"
                        commercial.record_trial_request(cnpj, email, client_ip, final_outcome, max(decision.risk_score, int(risk.get("risk_score") or 0)))
                        security.register_attempt("access_request", email, client_ip, success=True)
                        st.success("Solicitação recebida. Seu teste é de 7 dias, sem cartão.")
                    except Exception as error:
                        st.warning(str(error))
            st.html('<div class="lnx-auth-bottom"><a href="?auth=login">Já possui acesso? Entrar</a><a class="lnx-auth-back" href="?">Voltar para a página inicial</a></div>')

        elif mode == "invite":
            with st.form("activate_invitation", clear_on_submit=False, enter_to_submit=False):
                email = st.text_input("E-mail do convite", placeholder="seu@email.com")
                invitation_code = st.text_input("Código de acesso", placeholder="NX-XXXXXXXX")
                password = st.text_input("Crie sua senha", type="password", placeholder="Mínimo de 8 caracteres")
                password_confirmation = st.text_input("Confirme sua senha", type="password")
                if st.form_submit_button("Ativar convite", width="stretch"):
                    normalized_email = str(email or "").strip().lower()
                    client_ip = client_ip_getter()
                    try:
                        if not normalized_email or not str(invitation_code or "").strip():
                            raise ValueError("Informe o e-mail e o código de acesso do convite.")
                        if len(str(password or "")) < 8:
                            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
                        if password != password_confirmation:
                            raise ValueError("As senhas não coincidem.")
                        security.precheck("invitation_activation", normalized_email, client_ip)
                        user = db.activate_invitation(normalized_email, invitation_code, password)
                        if not user:
                            raise ValueError("Não foi possível ativar o convite.")
                        security.register_attempt("invitation_activation", normalized_email, client_ip, success=True)
                        token = security.create_session(user.get("company_id", ""), user.get("id", ""))
                        st.session_state.user = user
                        st.session_state.security_session_token = token
                        st.session_state.motivational_phrase = random.choice(tuple(motivational_phrases))
                        st.session_state.just_logged_in = True
                        st.rerun()
                    except Exception as error:
                        st.warning(str(error))
            st.html('<div class="lnx-auth-bottom"><a href="?auth=login">Voltar para o login</a></div>')

        else:
            with st.form("password_recovery_request", clear_on_submit=False, enter_to_submit=False):
                recovery_email = st.text_input("E-mail cadastrado", placeholder="seu@email.com", key="password_recovery_request_email")
                if st.form_submit_button("Solicitar código", width="stretch"):
                    normalized_email = str(recovery_email or "").strip().lower()
                    client_ip = client_ip_getter()
                    try:
                        security.precheck("password_recovery_request", normalized_email, client_ip)
                        db.request_password_reset(normalized_email)
                        security.register_attempt("password_recovery_request", normalized_email, client_ip, success=True)
                        st.success("Solicitação registrada. Se o e-mail estiver cadastrado, o código poderá ser gerado pelo suporte.")
                    except Exception as error:
                        st.warning(str(error))
            st.markdown("---")
            with st.form("password_recovery_reset", clear_on_submit=False, enter_to_submit=False):
                reset_email = st.text_input("E-mail", placeholder="seu@email.com", key="password_recovery_reset_email")
                recovery_code = st.text_input("Código de recuperação", placeholder="NX-R-XXXXXXXX")
                new_password = st.text_input("Nova senha", type="password", placeholder="Mínimo de 8 caracteres")
                new_password_confirmation = st.text_input("Confirme a nova senha", type="password")
                if st.form_submit_button("Redefinir senha", width="stretch"):
                    normalized_email = str(reset_email or "").strip().lower()
                    client_ip = client_ip_getter()
                    try:
                        if not normalized_email or not str(recovery_code or "").strip():
                            raise ValueError("Informe o e-mail e o código de recuperação.")
                        if len(str(new_password or "")) < 8:
                            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
                        if new_password != new_password_confirmation:
                            raise ValueError("As senhas não coincidem.")
                        security.precheck("password_recovery_reset", normalized_email, client_ip)
                        db.reset_password(normalized_email, recovery_code, new_password)
                        security.register_attempt("password_recovery_reset", normalized_email, client_ip, success=True)
                        st.success("Senha alterada. Agora você já pode entrar.")
                    except Exception as error:
                        st.warning(str(error))
            st.html('<div class="lnx-auth-bottom"><a href="?auth=login">Voltar para o login</a></div>')
