from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.public_landing import render_public_landing as _render_base_landing


def _image_data_uri(path_like: Path | str | None) -> str:
    if not path_like:
        return ""
    path = Path(path_like)
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime = "image/png"
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    elif suffix == ".svg":
        mime = "image/svg+xml"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_public_landing(logo_path: Path | str | None = None) -> None:
    """Renderiza a home aprovada sem herdar o shell visual da área autenticada."""
    _render_base_landing(logo_path)

    logo_uri = _image_data_uri(logo_path)
    if not logo_uri:
        return

    css = """
<style>
.ln-brand-mark,
.ln-brand-name {
    display: none !important;
}
.ln-brand {
    width: 320px !important;
    flex: 0 0 320px !important;
    height: 68px !important;
    min-height: 68px !important;
    background-image: url('__LOGO__') !important;
    background-repeat: no-repeat !important;
    background-position: left center !important;
    background-size: 255px auto !important;
}
@media (max-width: 1450px) {
    .ln-brand {
        width: 270px !important;
        flex-basis: 270px !important;
        height: 60px !important;
        min-height: 60px !important;
        background-size: 225px auto !important;
    }
}
@media (max-width: 1180px) {
    .ln-brand {
        width: 220px !important;
        flex-basis: 220px !important;
        height: 54px !important;
        min-height: 54px !important;
        background-size: 195px auto !important;
    }
}
@media (max-width: 760px) {
    .ln-brand {
        width: 178px !important;
        flex-basis: 178px !important;
        height: 46px !important;
        min-height: 46px !important;
        background-size: 165px auto !important;
    }
}
</style>
"""
    st.html(css.replace("__LOGO__", logo_uri))
