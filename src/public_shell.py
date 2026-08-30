from __future__ import annotations

import base64
from collections import deque
from io import BytesIO
from pathlib import Path

from PIL import Image
import streamlit as st

from src.public_auth_final import render_public_auth as _render_public_auth
from src.public_landing_exact import render_public_landing as _render_public_landing


OFFICIAL_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "licitanexo-logo.png"


def _official_logo_data_uri() -> str:
    """Remove somente o fundo branco conectado às bordas do PNG oficial para a landing."""
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

    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _landing_official_brand_css() -> str:
    logo_uri = _official_logo_data_uri()
    if not logo_uri:
        return ""

    return f'''
    <style>
    .lnx-top .lnx-brand img,
    .lnx-top .lnx-brand .lnx-mark,
    .lnx-top .lnx-brand .lnx-name {{display:none!important}}
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
    @media(max-width:680px) {{
        .lnx-top .lnx-brand {{
            width:188px!important;
            height:48px!important;
            min-height:48px!important;
            flex-basis:188px!important;
            background-size:180px auto!important;
        }}
    }}
    </style>
    '''


def render_public_landing(logo_path=None) -> None:
    _render_public_landing(logo_path or OFFICIAL_LOGO_PATH)
    css = _landing_official_brand_css()
    if css:
        st.html(css)


def render_public_auth(**kwargs) -> None:
    # O login é autocontido em src/public_auth.py; sem os overrides visuais antigos.
    _render_public_auth(**kwargs)

    # LNX_LAPTOP_VISUAL_FIX_V1
    st.html("""
    <style>

    /* Fundo da ?rea de demonstra??o */
    .lnx-auth-art{
        display:flex!important;
        align-items:center!important;
        justify-content:center!important;
        padding:38px 42px 78px!important;
        background:
            radial-gradient(circle at 82% 12%,rgba(31,104,220,.18),transparent 28%),
            linear-gradient(145deg,#03162f 0%,#061d3e 54%,#031226 100%)!important;
    }

    /* A pr?pria demo vira a tela f?sica do notebook */
    .lnx-auth-art .lnx-art-shell{
        position:relative!important;
        z-index:5!important;

        width:min(1050px,96%)!important;
        max-width:1050px!important;

        height:min(750px,calc(100vh - 145px))!important;
        min-height:570px!important;

        flex:none!important;
        margin:auto!important;

        padding:12px!important;

        border:11px solid #111827!important;
        border-bottom-width:20px!important;
        border-radius:23px 23px 14px 14px!important;

        background:#061a34!important;

        box-shadow:
            0 30px 55px rgba(0,0,0,.42),
            0 0 0 1px #3b4657,
            inset 0 0 0 1px rgba(255,255,255,.08)!important;

        overflow:hidden!important;
        box-sizing:border-box!important;
    }

    /* Pequena c?mera no topo */
    .lnx-auth-art .lnx-art-shell::before{
        content:""!important;
        display:block!important;

        position:absolute!important;
        z-index:50!important;

        top:-7px!important;
        left:50%!important;

        width:6px!important;
        height:6px!important;

        transform:translateX(-50%)!important;

        border-radius:50%!important;
        background:#59677a!important;

        box-shadow:
            0 0 0 2px #080c13,
            0 0 5px rgba(91,151,255,.35)!important;
    }

    /* Base met?lica do notebook */
    .lnx-auth-art::after{
        content:""!important;

        position:absolute!important;
        z-index:4!important;

        left:10%!important;
        right:10%!important;
        bottom:37px!important;

        height:34px!important;

        background:
            linear-gradient(
                180deg,
                #e7ebef 0%,
                #c3cad2 25%,
                #929ca8 63%,
                #626d79 100%
            )!important;

        clip-path:polygon(
            4% 0,
            96% 0,
            100% 68%,
            96% 100%,
            4% 100%,
            0 68%
        )!important;

        border-radius:0 0 16px 16px!important;

        box-shadow:
            0 14px 20px rgba(0,0,0,.38),
            inset 0 1px rgba(255,255,255,.7)!important;
    }

    /* Mant?m todo o conte?do original dentro da tela */
    .lnx-auth-art .lnx-audience-banner{
        flex:0 0 auto!important;
    }

    .lnx-auth-art .lnx-demo{
        min-height:0!important;
    }

    .lnx-auth-art .lnx-benefits{
        flex:0 0 auto!important;
    }

    .lnx-auth-art .lnx-closing{
        flex:0 0 auto!important;
    }

    /* Notebook um pouco menor em telas comuns */
    @media(max-width:1450px){
        .lnx-auth-art{
            padding:25px 25px 66px!important;
        }

        .lnx-auth-art .lnx-art-shell{
            width:97%!important;
            height:calc(100vh - 110px)!important;
            min-height:535px!important;

            border-width:9px!important;
            border-bottom-width:17px!important;

            padding:9px!important;
        }

        .lnx-auth-art::after{
            left:8%!important;
            right:8%!important;
            bottom:29px!important;
            height:29px!important;
        }
    }

    @media(max-height:800px) and (min-width:901px){
        .lnx-auth-art{
            padding-top:14px!important;
            padding-bottom:55px!important;
        }

        .lnx-auth-art .lnx-art-shell{
            height:calc(100vh - 78px)!important;
            min-height:510px!important;
        }

        .lnx-auth-art::after{
            bottom:22px!important;
        }
    }

    /* No celular continua somente o formul?rio */
    @media(max-width:900px){
        .lnx-auth-art{
            display:none!important;
        }

        .lnx-auth-art::after{
            display:none!important;
        }
    }

    </style>
    """)

    st.html("<style>.lnx-login-price-info>div>div{display:block!important;grid-template-columns:none!important}</style>")
