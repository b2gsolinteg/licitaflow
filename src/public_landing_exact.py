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
    """Renderiza a landing pública responsiva e isolada do shell autenticado."""
    _render_base_landing(logo_path)

    logo_uri = _image_data_uri(logo_path)

    css = r"""
<style>
html { scroll-behavior: smooth; }

/* Corrige a composição base para caber no viewport real do navegador. */
.ln-page {
    min-height: 100vh !important;
    overflow: visible !important;
}
.ln-header {
    height: 72px !important;
}
.ln-header-inner,
.ln-main {
    width: min(1680px, calc(100% - 64px)) !important;
    max-width: 1680px !important;
}
.ln-header-inner {
    gap: 24px !important;
}
.ln-main {
    padding-top: 20px !important;
    padding-bottom: 24px !important;
}
.ln-grid {
    grid-template-columns: 520px minmax(0, 1fr) !important;
    gap: 36px !important;
}

/* Usa a marca oficial do projeto, sem recriar o logo em CSS. */
.ln-brand-mark,
.ln-brand-name {
    display: none !important;
}
.ln-brand {
    width: 230px !important;
    flex: 0 0 230px !important;
    height: 52px !important;
    min-height: 52px !important;
    background-image: url('__LOGO__') !important;
    background-repeat: no-repeat !important;
    background-position: left center !important;
    background-size: 205px auto !important;
}
.ln-nav {
    gap: 30px !important;
}
.ln-nav a,
.ln-login {
    font-size: 14px !important;
}
.ln-actions {
    gap: 16px !important;
}
.ln-start {
    padding: 12px 20px !important;
    font-size: 14px !important;
}

/* Hero e benefícios proporcionais à altura útil do monitor. */
.ln-left {
    padding-top: 3px !important;
}
.ln-kicker {
    height: 31px !important;
    padding: 0 13px !important;
    font-size: 10px !important;
}
.ln-title {
    margin: 15px 0 9px !important;
    font-size: 43px !important;
    line-height: 1.035 !important;
    letter-spacing: -1.4px !important;
}
.ln-sub {
    margin-bottom: 12px !important;
    font-size: 16px !important;
    line-height: 1.35 !important;
}
.ln-features {
    width: 100% !important;
    gap: 8px !important;
}
.ln-feature {
    height: 76px !important;
    gap: 14px !important;
    padding: 9px 14px !important;
}
.ln-feature-icon {
    width: 52px !important;
    height: 52px !important;
    flex: 0 0 52px !important;
    font-size: 24px !important;
}
.ln-feature-title {
    font-size: 16px !important;
    margin-bottom: 2px !important;
}
.ln-feature-copy {
    max-width: 380px !important;
    font-size: 12px !important;
    line-height: 1.28 !important;
}
.ln-diff-badge {
    top: 8px !important;
    right: 10px !important;
    padding: 4px 7px !important;
    font-size: 8px !important;
}
.ln-price-card {
    width: 100% !important;
    height: 90px !important;
    margin-top: 12px !important;
    grid-template-columns: 170px 1fr !important;
    padding: 11px 12px 10px 18px !important;
    gap: 12px !important;
}
.ln-plan-caption { font-size: 12px !important; }
.ln-currency { font-size: 17px !important; }
.ln-price { font-size: 40px !important; }
.ln-month { font-size: 16px !important; }
.ln-trial a {
    min-width: 0 !important;
    width: 100% !important;
    height: 42px !important;
    padding: 0 13px !important;
    font-size: 12px !important;
}
.ln-trial-note {
    margin-top: 5px !important;
    font-size: 9px !important;
}
.ln-trust {
    width: 100% !important;
    height: 62px !important;
    margin-top: 10px !important;
    padding: 7px 9px !important;
}
.ln-trust-item {
    gap: 7px !important;
    font-size: 9px !important;
}
.ln-trust-icon {
    width: 31px !important;
    height: 31px !important;
    flex: 0 0 31px !important;
    font-size: 14px !important;
}

/* Preview do sistema: mantém a leitura, mas não ultrapassa a altura da tela. */
.ln-demo {
    height: 650px !important;
}
.ln-demo-inner {
    grid-template-columns: 190px minmax(0, 1fr) !important;
}
.ln-side {
    padding: 14px 11px !important;
}
.ln-mini-brand {
    margin: 0 0 12px 6px !important;
    font-size: 17px !important;
}
.ln-side-item {
    height: 31px !important;
    padding: 0 7px !important;
    font-size: 10px !important;
}
.ln-side-ico {
    width: 17px !important;
    font-size: 13px !important;
}
.ln-side-exit {
    margin: 12px 4px 0 !important;
    height: 32px !important;
    padding: 0 9px !important;
    font-size: 10px !important;
}
.ln-detail {
    padding: 16px 18px 12px !important;
}
.ln-pill {
    height: 24px !important;
    padding: 0 9px !important;
    font-size: 9px !important;
}
.ln-fav,
.ln-items {
    height: 34px !important;
    padding: 0 11px !important;
    font-size: 10px !important;
}
.ln-detail-title {
    margin: 10px 0 4px !important;
    font-size: 18px !important;
}
.ln-agency {
    margin-bottom: 5px !important;
    font-size: 10px !important;
}
.ln-desc {
    margin-bottom: 7px !important;
    font-size: 10px !important;
}
.ln-callout {
    right: 14px !important;
    top: 89px !important;
    width: 137px !important;
    height: 58px !important;
    font-size: 10px !important;
}
.ln-callout strong { font-size: 13px !important; }
.ln-callout:before {
    right: 30px !important;
    top: -34px !important;
    font-size: 31px !important;
}
.ln-meta {
    max-width: calc(100% - 145px) !important;
    margin: 7px 0 !important;
}
.ln-meta-cell { padding: 6px 8px !important; }
.ln-meta-label { font-size: 7px !important; }
.ln-meta-value { font-size: 8.5px !important; }
.ln-chips {
    gap: 5px !important;
    margin-bottom: 7px !important;
}
.ln-chip {
    height: 21px !important;
    padding: 0 8px !important;
    font-size: 7.5px !important;
}
.ln-table-headline {
    height: 31px !important;
    font-size: 9px !important;
}
.ln-table th {
    height: 24px !important;
    padding: 0 5px !important;
    font-size: 6.5px !important;
}
.ln-table td {
    height: 41px !important;
    padding: 3px 5px !important;
    font-size: 7.5px !important;
}
.ln-prod-pic {
    width: 29px !important;
    height: 29px !important;
    flex: 0 0 29px !important;
    font-size: 15px !important;
}
.ln-product { gap: 6px !important; }
.ln-product strong { font-size: 8px !important; }
.ln-product small { font-size: 6.5px !important; }
.ln-total {
    height: 30px !important;
    font-size: 9px !important;
}
.ln-bottom {
    height: 70px !important;
    margin: 12px 0 0 190px !important;
    padding: 0 14px !important;
}
.ln-bolt {
    width: 43px !important;
    height: 43px !important;
    flex: 0 0 43px !important;
    font-size: 23px !important;
}
.ln-bottom strong { font-size: 13px !important; }
.ln-bottom span { font-size: 10px !important; }

/* Seções de navegação que antes não existiam. */
.ln-extra {
    background: #031a34;
    color: #fff;
    padding: 56px 32px;
    border-top: 1px solid rgba(255,255,255,.09);
}
.ln-extra-inner {
    width: min(1180px, 100%);
    margin: 0 auto;
}
.ln-extra h2 {
    margin: 0 0 12px;
    color: #fff;
    font-size: 30px;
}
.ln-extra p {
    margin: 0;
    color: #c9d8e7;
    line-height: 1.6;
}
.ln-extra-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
    margin-top: 24px;
}
.ln-extra-card {
    border: 1px solid #1d4e79;
    border-radius: 12px;
    background: #0a2d51;
    padding: 20px;
}
.ln-extra-card strong {
    display: block;
    color: #ffbd18;
    margin-bottom: 6px;
}
.ln-contact-link {
    display: inline-flex;
    margin-top: 18px;
    padding: 11px 18px;
    border-radius: 9px;
    background: #ffbd18;
    color: #071b31 !important;
    text-decoration: none !important;
    font-weight: 800;
}

@media (max-width: 1450px) {
    .ln-header-inner,
    .ln-main { width: min(1360px, calc(100% - 40px)) !important; }
    .ln-grid { grid-template-columns: 455px minmax(0, 1fr) !important; gap: 25px !important; }
    .ln-brand { width: 205px !important; flex-basis: 205px !important; background-size: 185px auto !important; }
    .ln-title { font-size: 37px !important; }
    .ln-nav { gap: 18px !important; }
    .ln-demo { height: 610px !important; }
    .ln-demo-inner { grid-template-columns: 165px minmax(0,1fr) !important; }
    .ln-bottom { margin-left: 165px !important; }
}

@media (max-width: 1180px) {
    .ln-header { height: 64px !important; }
    .ln-header-inner,
    .ln-main { width: calc(100% - 30px) !important; }
    .ln-nav { display: none !important; }
    .ln-brand { width: 190px !important; flex-basis: 190px !important; background-size: 175px auto !important; }
    .ln-actions { margin-left: auto !important; }
    .ln-grid { grid-template-columns: 1fr !important; }
    .ln-left { max-width: 720px !important; margin: 0 auto !important; }
    .ln-demo { height: auto !important; min-height: 600px !important; }
    .ln-bottom { margin-left: 0 !important; }
    .ln-extra-grid { grid-template-columns: 1fr !important; }
}

@media (max-width: 760px) {
    .ln-brand { width: 165px !important; flex-basis: 165px !important; background-size: 150px auto !important; }
    .ln-login { display: none !important; }
    .ln-start { padding: 10px 12px !important; font-size: 12px !important; }
    .ln-title { font-size: 32px !important; }
    .ln-price-card { grid-template-columns: 1fr !important; height: auto !important; }
    .ln-trust { grid-template-columns: 1fr 1fr !important; height: auto !important; }
    .ln-demo-inner { grid-template-columns: 1fr !important; }
    .ln-side { display: none !important; }
    .ln-meta { max-width: 100% !important; }
    .ln-callout { display: none !important; }
    .ln-table-box { overflow-x: auto !important; }
    .ln-table { min-width: 660px !important; }
}
</style>
"""

    if logo_uri:
        css = css.replace("__LOGO__", logo_uri)
    else:
        css = css.replace("background-image: url('__LOGO__') !important;", "")

    st.html(css)

    st.html(
        r"""
<section class="ln-extra" id="depoimentos">
  <div class="ln-extra-inner">
    <h2>Quem usa o LicitaNexo ganha tempo para decidir melhor.</h2>
    <p>Esta área fica preparada para depoimentos reais de clientes. Até haver conteúdo validado, não exibimos avaliações inventadas.</p>
  </div>
</section>
<section class="ln-extra" id="blog">
  <div class="ln-extra-inner">
    <h2>Conteúdos sobre licitações e vendas para o governo</h2>
    <p>O Blog começa como uma seção pública da landing. Quando os primeiros artigos forem publicados, ele pode evoluir para uma página própria sem alterar a área autenticada.</p>
    <div class="ln-extra-grid">
      <div class="ln-extra-card"><strong>Como encontrar oportunidades</strong><span>Boas práticas para pesquisar editais e filtrar oportunidades com mais aderência.</span></div>
      <div class="ln-extra-card"><strong>Como analisar os itens</strong><span>Como usar quantidades, unidades e valores para avaliar rapidamente uma compra pública.</span></div>
      <div class="ln-extra-card"><strong>Como organizar sua rotina</strong><span>Estruture favoritos, calendário e acompanhamento sem perder prazos importantes.</span></div>
    </div>
  </div>
</section>
<section class="ln-extra" id="contato">
  <div class="ln-extra-inner">
    <h2>Fale com o LicitaNexo</h2>
    <p>Para acesso, demonstração ou suporte comercial, use o fluxo de solicitação existente. Assim o contato entra no mesmo processo já usado pelo sistema.</p>
    <a class="ln-contact-link" href="?auth=request">Solicitar acesso</a>
  </div>
</section>
"""
    )
