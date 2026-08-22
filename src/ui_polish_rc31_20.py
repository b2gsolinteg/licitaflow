from __future__ import annotations

import streamlit as st


RC31_20_CSS = r"""
<style>
/* RC31.20 viewport polish */
html body [data-testid="stSidebar"] > div:first-child{
    padding:56px 12px 16px !important;
    scrollbar-gutter:stable !important;
}
html body [data-testid="stSidebar"] .stButton{
    margin:0 0 .14rem !important;
}
html body [data-testid="stSidebar"] .stButton button{
    min-height:2.76rem !important;
    padding:.22rem .46rem !important;
    gap:.64rem !important;
}
html body [data-testid="stSidebar"] .stButton button p{
    font-size:.94rem !important;
    line-height:1.16 !important;
}
html body [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{
    flex:0 0 2.08rem !important;
    width:2.08rem !important;
    height:2.08rem !important;
}
html body [data-testid="stSidebar"] .st-key-sidebar_logout{
    position:relative !important;
    left:auto !important;
    right:auto !important;
    bottom:auto !important;
    width:100% !important;
    z-index:auto !important;
    margin:.72rem 0 .1rem !important;
}
html body [data-testid="stSidebar"] .st-key-sidebar_logout button{
    width:100% !important;
    min-height:2.55rem !important;
    font-size:.82rem !important;
    border-radius:8px !important;
}
html body [data-testid="stMain"] .ln-home-color-logo{
    height:0 !important;
    min-height:0 !important;
    margin:0 !important;
    padding:0 !important;
    overflow:hidden !important;
}
html body [data-testid="stMain"] .stElementContainer:has(.ln-home-color-logo) + .stElementContainer:has([data-testid="stImage"]),
html body [data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.ln-home-color-logo) + div:has([data-testid="stImage"]){
    max-height:62px !important;
    overflow:hidden !important;
    margin-top:0 !important;
    margin-bottom:.28rem !important;
}
html body [data-testid="stMain"] .stElementContainer:has(.ln-home-color-logo) + .stElementContainer [data-testid="stImage"] img,
html body [data-testid="stMain"] [data-testid="stVerticalBlock"] > div:has(.ln-home-color-logo) + div [data-testid="stImage"] img{
    display:block !important;
    width:190px !important;
    max-width:190px !important;
    max-height:62px !important;
    object-fit:contain !important;
    object-position:left center !important;
    margin:0 !important;
}
@media(max-height:820px) and (min-width:901px){
    html body [data-testid="stSidebar"] .stButton button{
        min-height:2.58rem !important;
    }
    html body [data-testid="stSidebar"] .stButton button p{
        font-size:.90rem !important;
    }
    html body [data-testid="stSidebar"] .stButton [data-testid="stIconMaterial"]{
        flex-basis:1.96rem !important;
        width:1.96rem !important;
        height:1.96rem !important;
    }
}
</style>
"""


def install_rc31_20_polish() -> None:
    """Aplica somente overrides visuais; não altera estado, dados ou navegação."""
    st.markdown(RC31_20_CSS, unsafe_allow_html=True)
