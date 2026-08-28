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
        width:310px!important;
        height:78px!important;
        background-image:url("{logo_uri}")!important;
        background-repeat:no-repeat!important;
        background-position:left center!important;
        background-size:300px auto!important;
    }}

    @media(max-width:680px) {{
        .lnx-top .lnx-brand {{
            width:188px!important;height:48px!important;min-height:48px!important;
            flex-basis:188px!important;background-size:180px auto!important;
        }}
        .lnx-auth-head .lnx-auth-logo {{
            width:235px!important;height:60px!important;background-size:225px auto!important;
        }}
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
