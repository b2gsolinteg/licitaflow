from __future__ import annotations

import streamlit as st

from src.brand_assets import APPROVED_LOGO_DARK_DATA_URI, APPROVED_LOGO_LIGHT_DATA_URI
from src.public_auth import render_public_auth as _render_public_auth
from src.public_landing_exact import render_public_landing as _render_public_landing


def _approved_brand_css() -> str:
    return f'''
    <style>
    .lnx-top .lnx-brand .lnx-mark,
    .lnx-top .lnx-brand .lnx-name,
    .lnx-auth-head .lnx-brand .lnx-brand-mark,
    .lnx-auth-head .lnx-brand .lnx-brand-name {{ display:none!important; }}

    .lnx-top .lnx-brand {{
        width:255px!important;
        height:64px!important;
        background-image:url("{APPROVED_LOGO_DARK_DATA_URI}")!important;
        background-repeat:no-repeat!important;
        background-position:left center!important;
        background-size:253px auto!important;
        flex:0 0 255px!important;
    }}

    .lnx-auth-head .lnx-brand {{
        width:300px!important;
        height:76px!important;
        background-image:url("{APPROVED_LOGO_LIGHT_DATA_URI}")!important;
        background-repeat:no-repeat!important;
        background-position:left center!important;
        background-size:296px auto!important;
    }}

    @media(max-width:680px) {{
        .lnx-top .lnx-brand {{ width:190px!important;height:48px!important;background-size:188px auto!important;flex-basis:190px!important; }}
        .lnx-auth-head .lnx-brand {{ width:230px!important;height:59px!important;background-size:226px auto!important; }}
    }}
    </style>
    '''


def render_public_landing(logo_path=None) -> None:
    _render_public_landing(logo_path)
    st.html(_approved_brand_css())


def render_public_auth(**kwargs) -> None:
    _render_public_auth(**kwargs)
    st.html(_approved_brand_css())
