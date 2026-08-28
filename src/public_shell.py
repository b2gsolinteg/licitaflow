from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.public_auth import render_public_auth as _render_public_auth
from src.public_landing_exact import render_public_landing as _render_public_landing


OFFICIAL_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "licitanexo-logo.png"


def _official_logo_data_uri() -> str:
    if not OFFICIAL_LOGO_PATH.exists():
        return ""
    encoded = base64.b64encode(OFFICIAL_LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _official_brand_css() -> str:
    logo_uri = _official_logo_data_uri()
    if not logo_uri:
        return ""

    return f'''
    <style>
    /* A marca pública usa exclusivamente o arquivo oficial assets/licitanexo-logo.png. */
    .lnx-top {{
        background:#FFFFFF!important;
        border-bottom:1px solid #E7ECF2!important;
        box-shadow:0 1px 8px rgba(8,29,61,.05)!important;
    }}

    .lnx-top .lnx-brand img,
    .lnx-top .lnx-brand .lnx-mark,
    .lnx-top .lnx-brand .lnx-name {{
        display:none!important;
    }}

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
    .lnx-auth-head .lnx-brand-name {{
        display:none!important;
    }}

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
            width:188px!important;
            height:48px!important;
            min-height:48px!important;
            flex-basis:188px!important;
            background-size:180px auto!important;
        }}
        .lnx-auth-head .lnx-auth-logo {{
            width:235px!important;
            height:60px!important;
            background-size:225px auto!important;
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
