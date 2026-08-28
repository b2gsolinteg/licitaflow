from __future__ import annotations

import base64
from collections import deque
from io import BytesIO
from pathlib import Path

from PIL import Image
import streamlit as st

from src.public_auth import render_public_auth as _render_public_auth
from src.public_landing_exact import render_public_landing as _render_public_landing


OFFICIAL_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "licitanexo-logo.png"


def _official_logo_data_uri() -> str:
    """Cria transparência apenas no fundo branco conectado às bordas do PNG oficial.

    A arte, as cores e eventuais áreas brancas internas da marca são preservadas.
    """
    if not OFFICIAL_LOGO_PATH.exists():
        return ""

    with Image.open(OFFICIAL_LOGO_PATH) as source:
        image = source.convert("RGBA")

    width, height = image.size
    pixels = image.load()
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    def is_background(x: int, y: int) -> bool:
        red, green, blue, alpha = pixels[x, y]
        return alpha > 0 and red >= 242 and green >= 242 and blue >= 242

    for x in range(width):
        if is_background(x, 0):
            queue.append((x, 0))
        if is_background(x, height - 1):
            queue.append((x, height - 1))
    for y in range(height):
        if is_background(0, y):
            queue.append((0, y))
        if is_background(width - 1, y):
            queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or not is_background(x, y):
            continue
        visited.add((x, y))
        red, green, blue, _ = pixels[x, y]
        pixels[x, y] = (red, green, blue, 0)
        if x > 0:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y > 0:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))

    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        image = image.crop(bbox)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _official_brand_css() -> str:
    logo_uri = _official_logo_data_uri()
    if not logo_uri:
        return ""

    return f'''
    <style>
    /* Marca pública: exclusivamente assets/licitanexo-logo.png, com fundo branco removido. */
    .lnx-top {{
        background:#FFFFFF!important;
        border-bottom:1px solid #E7ECF2!important;
        box-shadow:0 1px 8px rgba(8,29,61,.05)!important;
    }}

    .lnx-top .lnx-brand img,
    .lnx-top .lnx-brand .lnx-mark,
    .lnx-top .lnx-brand .lnx-name {{ display:none!important; }}

    .lnx-top .lnx-brand {{
        width:255px!important;
        height:62px!important;
        min-height:62px!important;
        flex:0 0 255px!important;
        background-image:url("{logo_uri}")!important;
        background-repeat:no-repeat!important;
        background-position:left center!important;
        background-size:245px auto!important;
    }}

    .lnx-auth-head .lnx-auth-logo img,
    .lnx-auth-head .lnx-brand-mark,
    .lnx-auth-head .lnx-brand-name {{ display:none!important; }}

    .lnx-auth-head .lnx-auth-logo {{
        display:block!important;
        width:270px!important;
        height:68px!important;
        background-image:url("{logo_uri}")!important;
        background-repeat:no-repeat!important;
        background-position:left center!important;
        background-size:260px auto!important;
    }}

    @media(max-width:680px) {{
        .lnx-top .lnx-brand {{
            width:188px!important;height:48px!important;min-height:48px!important;
            flex-basis:188px!important;background-size:180px auto!important;
        }}
        .lnx-auth-head .lnx-auth-logo {{
            width:220px!important;height:56px!important;background-size:210px auto!important;
        }}
    }}
    </style>
    '''


def _auth_layout_fix_css() -> str:
    """Mantém cabeçalho e formulário no fluxo vertical para impedir sobreposição."""
    return '''
    <style>
    .lnx-auth-head{
        position:relative!important;
        left:auto!important;
        top:auto!important;
        width:calc(100% - 76px)!important;
        margin:0 0 0 clamp(38px,4.2vw,72px)!important;
        padding-top:clamp(28px,3.4vh,42px)!important;
        z-index:6!important;
    }
    .lnx-auth-kicker{margin-top:16px!important}
    .lnx-auth-title{margin-top:14px!important}
    .lnx-auth-caption{margin-top:10px!important}
    .st-key-lnx_auth_form{
        margin-top:26px!important;
        margin-bottom:34px!important;
    }
    @media(max-width:1150px){
        .lnx-auth-head{width:calc(100% - 70px)!important}
        .st-key-lnx_auth_form{margin-top:24px!important}
    }
    @media(max-width:900px){
        .lnx-auth-head{
            position:relative!important;
            left:auto!important;
            right:auto!important;
            top:auto!important;
            width:100%!important;
            max-width:540px!important;
            margin:0 auto!important;
            padding-top:30px!important;
        }
        .st-key-lnx_auth_form{
            width:100%!important;
            max-width:540px!important;
            margin:24px auto 34px!important;
        }
    }
    </style>
    '''


def _commercial_auth_copy_css() -> str:
    raw_mode = st.query_params.get("auth", "login")
    if isinstance(raw_mode, list):
        raw_mode = raw_mode[0] if raw_mode else "login"
    mode = str(raw_mode or "login").strip().lower()

    if mode == "request":
        title = "Comece grátis e descubra oportunidades que podem virar novos negócios."
        caption = "7 dias grátis. Depois, R$ 29,90/mês. Preço justo para quem quer começar a vender para o governo."
    elif mode == "invite":
        title = "Ative seu convite e comece a explorar oportunidades com mais clareza."
        caption = "Use o código recebido para liberar seu acesso ao LicitaNexo."
    elif mode == "recovery":
        title = "Recupere seu acesso e volte às oportunidades que importam."
        caption = "Solicite um código e defina uma nova senha com segurança."
    else:
        title = "Entre e vá direto às oportunidades que merecem sua atenção."
        caption = "Pesquise licitações, veja os itens da compra e organize sua participação em um só lugar."

    title_css = title.replace('"', '\\"')
    caption_css = caption.replace('"', '\\"')
    return f'''
    <style>
    .lnx-auth-title{{font-size:0!important}}
    .lnx-auth-title strong{{display:none!important}}
    .lnx-auth-title::after{{
        content:"{title_css}";
        display:block;
        max-width:480px;
        font-size:clamp(27px,2vw,38px)!important;
        line-height:1.08;
        letter-spacing:-1px;
        font-weight:800;
        color:#071a3d;
    }}
    .lnx-auth-caption{{font-size:0!important}}
    .lnx-auth-caption::after{{
        content:"{caption_css}";
        display:block;
        color:#5e6b80;
        font-size:14px!important;
        line-height:1.48;
        max-width:470px;
    }}
    .lnx-login-price-info>div:nth-child(2)>b,
    .lnx-login-price-info>div:nth-child(2)>span{{font-size:0!important}}
    .lnx-login-price-info>div:nth-child(2)>b::after{{
        content:"Preço justo para quem quer começar a vender para o governo";
        font-size:11px!important;
        color:#fff;
        line-height:1.25;
    }}
    .lnx-login-price-info>div:nth-child(2)>span::after{{
        content:"Comece simples, encontre oportunidades e evolua com o seu negócio.";
        font-size:9px!important;
        color:#d7e4f5;
        line-height:1.3;
    }}
    </style>
    '''


def render_public_landing(logo_path=None) -> None:
    _render_public_landing(logo_path or OFFICIAL_LOGO_PATH)
    css = _official_brand_css()
    if css:
        st.html(css)


def render_public_auth(**kwargs) -> None:
    _render_public_auth(**kwargs)
    css = _official_brand_css()
    if css:
        st.html(css)
    st.html(_auth_layout_fix_css())
    st.html(_commercial_auth_copy_css())
