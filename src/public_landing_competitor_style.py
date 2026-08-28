from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


def _data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime = "image/png"
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def render_public_landing(logo_path: Path | str | None = None) -> None:
    root = Path(logo_path).parent if logo_path else Path(__file__).resolve().parents[1] / "assets"
    hero_uri = _data_uri(root / "login-hero-final.png")

    hero_media = (
        f'<img src="{hero_uri}" alt="Demonstração visual do LicitaNexo">'
        if hero_uri
        else '<div class="lnx-hero-fallback"><span>Licita</span><strong>Nexo</strong></div>'
    )

    html = f'''
    <style>
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{margin:0!important;padding:0!important;min-height:100vh!important;background:#F4EFE4!important;font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important}}
    header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,[data-testid="stSidebar"],[data-testid="collapsedControl"]{{display:none!important}}
    [data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{{width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important}}
    [data-testid="stVerticalBlock"]{{gap:0!important}}
    .lnx-home,.lnx-home *{{box-sizing:border-box}}
    .lnx-home{{min-height:100vh;background:#F4EFE4;color:#0E1B3D}}
    .lnx-top{{height:88px;background:#07152F;display:flex;align-items:center}}
    .lnx-top-inner{{width:min(1780px,calc(100% - 96px));margin:auto;display:flex;align-items:center;justify-content:space-between}}
    .lnx-brand{{display:flex;align-items:center;gap:12px;text-decoration:none}}
    .lnx-mark{{width:45px;height:45px;display:block}}.lnx-mark svg{{width:100%;height:100%}}
    .lnx-name{{font-size:31px;line-height:1;font-weight:820;color:#fff;letter-spacing:-1px}}.lnx-name span{{color:#F5B914}}
    .lnx-actions{{display:flex;align-items:center;gap:22px}}
    .lnx-login{{height:44px;padding:0 22px;display:inline-flex;align-items:center;justify-content:center;border-radius:5px;background:#F4EFE4;color:#0C1938!important;text-decoration:none!important;font-size:15px;font-weight:700}}
    .lnx-trial{{height:44px;padding:0 24px;display:inline-flex;align-items:center;justify-content:center;border-radius:5px;background:#9EE7EF;color:#0C1938!important;text-decoration:none!important;font-size:15px;font-weight:750}}
    .lnx-hero{{min-height:calc(100vh - 88px);display:grid;grid-template-columns:46% 54%;background:#F4EFE4;overflow:hidden}}
    .lnx-copy{{padding:clamp(72px,10vh,120px) clamp(48px,5vw,96px) 70px;display:flex;flex-direction:column;justify-content:center}}
    .lnx-title{{margin:0;max-width:660px;font-size:clamp(42px,3.35vw,68px);line-height:1.02;letter-spacing:-2.3px;font-weight:500;color:#0C1938}}
    .lnx-sub{{max-width:640px;margin:28px 0 0;font-size:clamp(17px,1.08vw,22px);line-height:1.42;color:#64708A}}
    .lnx-buttons{{display:flex;gap:28px;margin-top:44px;flex-wrap:wrap}}
    .lnx-buttons a{{min-height:58px;padding:0 34px;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;text-decoration:none!important;font-size:17px;font-weight:750}}
    .lnx-primary,.lnx-secondary{{background:#152568;color:#fff!important}}
    .lnx-secondary{{background:#26377B}}
    .lnx-visual{{position:relative;min-height:calc(100vh - 88px);background:#142568;display:flex;align-items:center;justify-content:center;overflow:hidden}}
    .lnx-visual:before{{content:"";position:absolute;width:430px;height:430px;border:78px solid #9EE7EF;border-radius:44px;right:-220px;top:-150px;transform:rotate(45deg)}}
    .lnx-visual:after{{content:"";position:absolute;width:520px;height:160px;background:#9EE7EF;border-radius:90px;right:-130px;bottom:40px;transform:rotate(-23deg)}}
    .lnx-photo{{position:relative;z-index:2;width:88%;height:72%;min-height:520px;border-radius:72px 72px 72px 72px;overflow:hidden;box-shadow:0 30px 80px rgba(4,15,48,.24);background:#E6EDF4}}
    .lnx-photo img{{width:100%;height:100%;object-fit:cover;display:block}}
    .lnx-hero-fallback{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#fff,#eef3f8);font-size:66px;color:#173C75;gap:10px}}.lnx-hero-fallback strong{{color:#F5B914}}
    @media(max-width:1180px){{.lnx-top-inner{{width:calc(100% - 48px)}}.lnx-hero{{grid-template-columns:1fr}}.lnx-copy{{min-height:620px;padding:70px 7vw}}.lnx-visual{{min-height:650px}}.lnx-photo{{min-height:500px;width:86%;height:78%}}}}
    @media(max-width:680px){{.lnx-top{{height:72px}}.lnx-top-inner{{width:calc(100% - 28px)}}.lnx-name{{font-size:24px}}.lnx-mark{{width:38px;height:38px}}.lnx-actions{{gap:8px}}.lnx-login,.lnx-trial{{height:40px;padding:0 13px;font-size:13px}}.lnx-hero{{min-height:auto}}.lnx-copy{{min-height:auto;padding:54px 24px 62px}}.lnx-title{{font-size:42px;letter-spacing:-1.4px}}.lnx-sub{{font-size:17px}}.lnx-buttons{{gap:12px;margin-top:32px}}.lnx-buttons a{{width:100%;min-height:52px}}.lnx-visual{{min-height:480px}}.lnx-photo{{width:90%;height:390px;min-height:0;border-radius:40px}}}}
    </style>
    <div class="lnx-home">
      <header class="lnx-top">
        <div class="lnx-top-inner">
          <a class="lnx-brand" href="#">
            <span class="lnx-mark">
              <svg viewBox="0 0 64 64" aria-hidden="true"><g fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="7"><path d="M18 35l-4 4a13 13 0 0018 18l8-8a13 13 0 000-18" stroke="#F5B914"/><path d="M46 29l4-4A13 13 0 0032 7l-8 8a13 13 0 000 18" stroke="#2A74C9"/><path d="M25 39l14-14" stroke="#CFE3FF"/></g></svg>
            </span>
            <span class="lnx-name">Licita<span>Nexo</span></span>
          </a>
          <div class="lnx-actions"><a class="lnx-login" href="?auth=login">Login</a><a class="lnx-trial" href="?auth=request">Teste grátis</a></div>
        </div>
      </header>
      <main class="lnx-hero">
        <section class="lnx-copy">
          <h1 class="lnx-title">LicitaNexo, a plataforma para encontrar licitações e vender ao governo com mais clareza</h1>
          <p class="lnx-sub">Encontre oportunidades, veja os itens da compra e organize sua participação em um só lugar, sem perder tempo abrindo edital por edital.</p>
          <div class="lnx-buttons"><a class="lnx-primary" href="?auth=request">Teste grátis</a><a class="lnx-secondary" href="?auth=login">Acessar a plataforma</a></div>
        </section>
        <section class="lnx-visual"><div class="lnx-photo">{hero_media}</div></section>
      </main>
    </div>
    '''
    st.html(html)
