from __future__ import annotations

import random

import streamlit as st

from src.brand_assets import APPROVED_LOGO_LIGHT_DATA_URI


def _brand_html() -> str:
    return f'<div class="lnx-auth-logo"><img src="{APPROVED_LOGO_LIGHT_DATA_URI}" alt="LicitaNexo"></div>'


def _auth_css() -> str:
    return """
    <style>
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{margin:0!important;padding:0!important;background:#fff!important;min-height:100vh!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important}
    header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
    [data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important}
    [data-testid="stVerticalBlock"]{gap:0!important}
    .lnx-auth-bg{position:fixed;inset:0 0 0 38%;z-index:0;background:#16246A;overflow:hidden}
    .lnx-auth-bg:before{content:"";position:absolute;width:660px;height:660px;border:92px solid #F3EEE3;border-radius:78px;right:-240px;top:-430px;transform:rotate(45deg)}
    .lnx-auth-bg:after{content:"";position:absolute;width:900px;height:165px;background:#F3EEE3;border-radius:95px;left:95px;top:430px;transform:rotate(14deg)}
    .lnx-auth-bg .ring{position:absolute;width:680px;height:680px;border:92px solid #F3EEE3;border-radius:50%;right:-480px;bottom:-300px}
    .lnx-auth-bg .stem{position:absolute;width:190px;height:760px;background:#F3EEE3;border-radius:100px;left:50%;top:-300px}
    .block-container>[data-testid="stVerticalBlock"]{width:38%!important;min-height:100vh!important;padding:0!important;margin:0!important;position:relative!important;z-index:3!important;background:#fff!important}
    .lnx-auth-head{position:fixed;left:clamp(50px,5.7vw,96px);top:clamp(48px,7vh,78px);z-index:5;width:calc(38vw - 120px)}
    .lnx-auth-logo img{display:block;width:305px;max-width:100%;height:auto}
    .lnx-auth-title{margin-top:52px;font-size:15px;font-weight:600;color:#17213F}.lnx-auth-caption{display:none}
    .st-key-lnx_auth_form{width:calc(38vw - 110px)!important;max-width:500px!important;margin-left:clamp(50px,5.7vw,96px)!important;margin-top:calc(50vh - 92px)!important;position:relative!important;z-index:4!important;background:transparent!important}
    .st-key-lnx_auth_form [data-testid="stForm"]{border:0!important;background:transparent!important;padding:0!important}
    .st-key-lnx_auth_form label p{font-size:15px!important;color:#1A2340!important;font-weight:500!important}
    .st-key-lnx_auth_form [data-baseweb="input"],.st-key-lnx_auth_form [data-baseweb="base-input"]{background:#fff!important;border:1px solid #C9D1E2!important;border-radius:4px!important;box-shadow:none!important}
    .st-key-lnx_auth_form input{height:48px!important;background:#fff!important;color:#1B2644!important;-webkit-text-fill-color:#1B2644!important;font-size:15px!important}
    .st-key-lnx_auth_form input::placeholder{color:#B1B7C8!important;-webkit-text-fill-color:#B1B7C8!important}
    .st-key-lnx_auth_form .stFormSubmitButton button{width:100%!important;min-height:48px!important;background:#16246A!important;color:#fff!important;border:1px solid #16246A!important;border-radius:4px!important;font-weight:700!important;font-size:16px!important;box-shadow:none!important;margin-top:14px!important}
    .st-key-lnx_auth_form .stFormSubmitButton button:hover{background:#101D58!important;border-color:#101D58!important}
    .lnx-forgot{text-align:right;margin:-2px 0 8px}.lnx-forgot a{color:#16246A!important;text-decoration:none!important;font-size:14px;font-weight:600}
    .lnx-auth-bottom{position:fixed;left:clamp(50px,5.7vw,96px);bottom:clamp(52px,6vh,74px);width:calc(38vw - 120px);z-index:5;text-align:center;color:#687188;font-size:14px;line-height:1.45}
    .lnx-auth-bottom a{color:#16246A!important;text-decoration:none!important;font-weight:800}
    .lnx-auth-back{display:block;margin-top:8px;color:#66708A!important;text-decoration:none!important;font-size:13px}
    @media(max-width:900px){.lnx-auth-bg{display:none}.block-container>[data-testid="stVerticalBlock"]{width:100%!important;padding:34px 22px!important;box-sizing:border-box!important}.st-key-lnx_auth_form{width:100%!important;max-width:520px!important;margin:190px auto 0!important}.lnx-auth-head{position:absolute;left:22px;right:22px;top:38px;width:auto}.lnx-auth-logo img{width:245px}.lnx-auth-bottom{position:relative;left:auto;bottom:auto;width:auto;margin:30px auto 12px}}
    </style>
    """


def _shell(mode: str) -> None:
    st.html(_auth_css())
    st.html('<div class="lnx-auth-bg"><div class="ring"></div><div class="stem"></div></div>')
    heading = {"login": "Acesse sua conta", "request": "Comece seu teste grátis", "invite": "Ative seu convite", "recovery": "Recupere seu acesso"}[mode]
    st.html(f'<div class="lnx-auth-head">{_brand_html()}<div class="lnx-auth-title">{heading}</div></div>')


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
            st.html('<div class="lnx-auth-bottom">Ainda não possui acesso?<br><a href="?auth=request">Faça um teste grátis!</a><a class="lnx-auth-back" href="?">Voltar para a página inicial</a></div>')

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
