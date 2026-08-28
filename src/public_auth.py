from __future__ import annotations

import random

import streamlit as st


def _brand_html(theme: str = "dark") -> str:
    text = "#10255A" if theme == "light" else "#FFFFFF"
    return f'''
    <div class="lnx-brand lnx-brand-{theme}">
      <span class="lnx-brand-mark" aria-hidden="true">
        <svg viewBox="0 0 64 64" role="img" aria-label="">
          <g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="7">
            <path d="M18 35l-4 4a13 13 0 0018 18l8-8a13 13 0 000-18" stroke="#F5B914"/>
            <path d="M46 29l4-4A13 13 0 0032 7l-8 8a13 13 0 000 18" stroke="#2A74C9"/>
            <path d="M25 39l14-14" stroke="#1A4E8A"/>
          </g>
        </svg>
      </span>
      <span class="lnx-brand-name" style="color:{text}">Licita<span>Nexo</span></span>
    </div>
    '''


def _auth_css() -> str:
    return """
    <style>
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{margin:0!important;padding:0!important;background:#fff!important;min-height:100vh!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important}
    header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
    [data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important}
    [data-testid="stVerticalBlock"]{gap:0!important}
    .lnx-auth-bg{position:fixed;inset:0 0 0 38%;z-index:0;background:#12235F;overflow:hidden}
    .lnx-auth-bg:before,.lnx-auth-bg:after{content:"";position:absolute;border:92px solid #F5F0E6;border-radius:46px;transform:rotate(45deg);opacity:.98}
    .lnx-auth-bg:before{width:620px;height:620px;right:-110px;top:-350px}
    .lnx-auth-bg:after{width:720px;height:720px;left:210px;bottom:-480px}
    .lnx-auth-bg .cut{position:absolute;left:34%;top:32%;width:700px;height:140px;background:#F5F0E6;border-radius:76px;transform:rotate(14deg)}
    .lnx-brand{display:flex;align-items:center;gap:14px}.lnx-brand-mark{width:56px;height:56px;display:block;flex:0 0 56px}.lnx-brand-mark svg{width:100%;height:100%}.lnx-brand-name{font-size:42px;line-height:1;font-weight:800;letter-spacing:-1.6px}.lnx-brand-name span{color:#F5B914}
    .block-container>[data-testid="stVerticalBlock"]{width:38%!important;min-height:100vh!important;padding:0!important;margin:0!important;position:relative!important;z-index:3!important;background:#fff!important}
    .st-key-lnx_auth_form{width:calc(38vw - 92px)!important;max-width:500px!important;margin-left:clamp(46px,5vw,96px)!important;margin-top:calc(50vh - 120px)!important;position:relative!important;z-index:4!important;background:transparent!important}
    .st-key-lnx_auth_form [data-testid="stForm"]{border:0!important;background:transparent!important;padding:0!important}
    .st-key-lnx_auth_form label p{font-size:15px!important;color:#1A2340!important;font-weight:500!important}
    .st-key-lnx_auth_form [data-baseweb="input"],.st-key-lnx_auth_form [data-baseweb="base-input"]{background:#fff!important;border-color:#CCD3E4!important;border-radius:4px!important;box-shadow:none!important}
    .st-key-lnx_auth_form input{height:48px!important;background:#fff!important;color:#1B2644!important;-webkit-text-fill-color:#1B2644!important;font-size:15px!important}
    .st-key-lnx_auth_form input::placeholder{color:#B1B7C8!important;-webkit-text-fill-color:#B1B7C8!important}
    .st-key-lnx_auth_form .stFormSubmitButton button{width:100%!important;min-height:48px!important;background:#12235F!important;color:#fff!important;border:1px solid #12235F!important;border-radius:4px!important;font-weight:700!important;font-size:16px!important;box-shadow:none!important;margin-top:14px!important}
    .st-key-lnx_auth_form .stFormSubmitButton button:hover{background:#0D1B50!important;border-color:#0D1B50!important}
    .lnx-forgot{text-align:right;margin:-2px 0 8px}.lnx-forgot a{color:#12235F!important;text-decoration:none!important;font-size:14px;font-weight:600}
    .lnx-auth-head{position:fixed;left:clamp(46px,5vw,96px);top:clamp(46px,7vh,86px);z-index:5;width:calc(38vw - 110px)}
    .lnx-auth-title{margin-top:46px;font-size:15px;font-weight:600;color:#17213F}.lnx-auth-caption{margin-top:10px;color:#6E778D;font-size:14px;line-height:1.45}
    .lnx-auth-bottom{position:fixed;left:clamp(46px,5vw,96px);bottom:clamp(34px,5vh,60px);width:calc(38vw - 110px);z-index:5;text-align:center;color:#687188;font-size:14px}
    .lnx-auth-bottom a{color:#12235F!important;text-decoration:none!important;font-weight:800}
    @media(max-width:900px){.lnx-auth-bg{display:none}.block-container>[data-testid="stVerticalBlock"]{width:100%!important;padding:34px 22px!important;box-sizing:border-box!important}.st-key-lnx_auth_form{width:100%!important;max-width:520px!important;margin:165px auto 0!important}.lnx-auth-head{position:absolute;left:22px;right:22px;top:36px;width:auto}.lnx-auth-bottom{position:relative;left:auto;bottom:auto;width:auto;margin:28px auto 12px}.lnx-brand-name{font-size:34px}.lnx-brand-mark{width:48px;height:48px;flex-basis:48px}}
    </style>
    """


def _shell(mode: str) -> None:
    st.html(_auth_css())
    st.html('<div class="lnx-auth-bg"><div class="cut"></div></div>')
    heading = {"login": "Acesse sua conta", "request": "Comece seu teste grátis", "invite": "Ative seu convite", "recovery": "Recupere seu acesso"}[mode]
    caption = {"login": "Entre com seu e-mail e senha para acessar o LicitaNexo.", "request": "7 dias grátis, sem cartão. Depois você decide se deseja continuar.", "invite": "Use o código recebido para criar sua senha e ativar o acesso.", "recovery": "Solicite um código e defina uma nova senha com segurança."}[mode]
    st.html(f'<div class="lnx-auth-head">{_brand_html("light")}<div class="lnx-auth-title">{heading}</div><div class="lnx-auth-caption">{caption}</div></div>')


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
                email = st.text_input("Usuário", placeholder="Digite seu e-mail...")
                password = st.text_input("Senha", type="password", placeholder="Digite sua senha...")
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
            st.html('<div class="lnx-auth-bottom">Ainda não possui acesso?<br><a href="?auth=request">Faça um teste grátis!</a></div>')

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
            st.html('<div class="lnx-auth-bottom"><a href="?auth=login">Já possui acesso? Entrar</a></div>')

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
