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


def _auth_value_panel_html() -> str:
    """Painel comercial do login sem métricas promocionais ou dados apresentados como ao vivo."""
    return '''
    <style>
    .lnx-auth-art{display:none!important}
    .lnx-auth-value-panel,.lnx-auth-value-panel *{box-sizing:border-box}
    .lnx-auth-value-panel{
        position:fixed;inset:0 0 0 40%;z-index:2;overflow:auto;
        background:
          radial-gradient(circle at 76% 12%,rgba(32,110,238,.22),transparent 28%),
          linear-gradient(145deg,#061a40 0%,#071f4b 48%,#04152f 100%);
        color:#fff;font-family:Inter,"Segoe UI",Arial,sans-serif;
        padding:clamp(26px,3.2vw,52px);
    }
    .lnx-value-shell{width:min(900px,100%);min-height:100%;margin:auto;display:flex;flex-direction:column;justify-content:center;gap:18px}
    .lnx-value-audience{display:flex;align-items:center;gap:12px;padding:13px 16px;border:1px solid rgba(247,183,20,.42);border-radius:14px;background:rgba(4,21,51,.54);box-shadow:0 14px 40px rgba(0,0,0,.13)}
    .lnx-value-audience-icon{width:42px;height:42px;flex:0 0 42px;border-radius:12px;background:linear-gradient(145deg,#1d67d7,#0d43a2);display:grid;place-items:center;font-size:21px}
    .lnx-value-audience b{display:block;font-size:14px;line-height:1.25}.lnx-value-audience span{display:block;color:#b9c9df;font-size:11px;margin-top:3px;line-height:1.35}
    .lnx-value-copy{padding:2px 2px 0}.lnx-value-copy h2{margin:0;font-size:clamp(29px,2.45vw,44px);line-height:1.02;letter-spacing:-1.5px;max-width:760px}.lnx-value-copy h2 strong{color:#f7b714}.lnx-value-copy p{margin:10px 0 0;color:#c5d3e7;font-size:14px;line-height:1.5;max-width:720px}
    .lnx-value-demo{border:1px solid rgba(63,128,226,.34);border-radius:18px;background:linear-gradient(150deg,rgba(8,40,91,.94),rgba(5,24,56,.96));box-shadow:0 22px 55px rgba(0,0,0,.22);overflow:hidden}
    .lnx-value-demo-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;padding:18px 20px 15px;border-bottom:1px solid rgba(255,255,255,.09)}
    .lnx-value-demo-head h3{margin:0;font-size:18px}.lnx-value-demo-head p{margin:4px 0 0;color:#acbfd8;font-size:10px}.lnx-demo-badge{white-space:nowrap;border:1px solid rgba(247,183,20,.45);color:#ffd45a;background:rgba(247,183,20,.08);padding:7px 10px;border-radius:999px;font-size:9px;font-weight:900;letter-spacing:.04em}
    .lnx-value-org{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;padding:15px 20px;background:rgba(10,51,109,.28);border-bottom:1px solid rgba(255,255,255,.08)}
    .lnx-value-org b{display:block;font-size:13px}.lnx-value-org span{display:block;color:#aec2dc;font-size:9px;margin-top:4px}.lnx-value-org-tag{color:#70a9ff!important;font-weight:800!important;font-size:9px!important;margin:0!important}
    .lnx-value-table{padding:0 20px 14px}.lnx-value-row{display:grid;grid-template-columns:26px minmax(160px,1fr) 72px 92px;gap:8px;align-items:center;min-height:48px;border-bottom:1px solid rgba(255,255,255,.075);font-size:10px}.lnx-value-row:last-child{border-bottom:0}.lnx-value-row.header{min-height:32px;color:#8fa6c4;font-size:8px;font-weight:850;text-transform:uppercase}.lnx-value-item b{font-size:10px}.lnx-value-item small{display:block;color:#91a8c5;font-size:8px;margin-top:2px}.lnx-value-money{color:#ffd04a;font-weight:900}
    .lnx-value-benefits{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.lnx-value-benefit{min-height:92px;border:1px solid rgba(63,128,226,.26);border-radius:14px;background:rgba(5,27,63,.76);padding:14px}.lnx-value-benefit i{font-style:normal;color:#f7b714;font-size:20px}.lnx-value-benefit b{display:block;font-size:11px;margin:6px 0 3px}.lnx-value-benefit span{display:block;color:#aebfd5;font-size:9px;line-height:1.4}
    .lnx-value-price{display:flex;align-items:center;justify-content:space-between;gap:18px;border:1px solid rgba(247,183,20,.48);border-radius:14px;padding:13px 16px;background:linear-gradient(100deg,rgba(247,183,20,.10),rgba(7,31,72,.88) 48%)}
    .lnx-value-price-main{white-space:nowrap}.lnx-value-price-main strong{font-size:26px;color:#ffd04a}.lnx-value-price-main span{font-size:12px;color:#fff}.lnx-value-price-copy{font-size:10px;color:#c7d5e8;line-height:1.4;text-align:right}.lnx-value-price-copy b{color:#fff}
    @media(max-width:1150px){
      .lnx-auth-value-panel{left:46%;padding:24px}.lnx-value-shell{gap:13px}.lnx-value-copy h2{font-size:30px}.lnx-value-copy p{font-size:12px}.lnx-value-audience{padding:11px 13px}.lnx-value-demo-head{padding:14px 15px 12px}.lnx-value-org{padding:12px 15px}.lnx-value-table{padding:0 15px 11px}.lnx-value-row{grid-template-columns:22px minmax(120px,1fr) 56px 72px;font-size:9px;min-height:42px}.lnx-value-item b{font-size:9px}.lnx-value-money{font-size:9px}.lnx-value-benefit{padding:11px;min-height:80px}.lnx-value-price{padding:11px 13px}.lnx-value-price-main strong{font-size:22px}
    }
    @media(max-width:900px){.lnx-auth-value-panel{display:none!important}}
    </style>
    <section class="lnx-auth-value-panel" aria-label="Demonstração do LicitaNexo">
      <div class="lnx-value-shell">
        <div class="lnx-value-audience">
          <div class="lnx-value-audience-icon">▣</div>
          <div><b>Feito para MEI, microempresas e EPP</b><span>Uma forma simples e acessível de começar a encontrar oportunidades públicas.</span></div>
        </div>
        <div class="lnx-value-copy">
          <h2>Comece pequeno. <strong>Venda para o governo com mais clareza.</strong></h2>
          <p>Veja o que está sendo comprado, entenda os itens da oportunidade e concentre seu tempo no que realmente faz sentido para o seu negócio.</p>
        </div>
        <div class="lnx-value-demo">
          <div class="lnx-value-demo-head">
            <div><h3>Veja a compra por dentro</h3><p>Itens e quantidades organizados antes de você aprofundar a análise do edital.</p></div>
            <span class="lnx-demo-badge">EXEMPLO DEMONSTRATIVO</span>
          </div>
          <div class="lnx-value-org">
            <div><b>Prefeitura Municipal de Uberlândia/MG</b><span>Pregão eletrônico · exemplo visual de oportunidade pública</span></div>
            <span class="lnx-value-org-tag">COMPRA PÚBLICA</span>
          </div>
          <div class="lnx-value-table">
            <div class="lnx-value-row header"><div>#</div><div>Item</div><div>Qtd.</div><div>Valor ilustrativo</div></div>
            <div class="lnx-value-row"><div>01</div><div class="lnx-value-item"><b>Cadeira de rodas adulto</b><small>Equipamento para mobilidade</small></div><div>5 un</div><div class="lnx-value-money">R$ 6.250</div></div>
            <div class="lnx-value-row"><div>02</div><div class="lnx-value-item"><b>Cama hospitalar manual</b><small>Uso hospitalar</small></div><div>3 un</div><div class="lnx-value-money">R$ 8.970</div></div>
            <div class="lnx-value-row"><div>03</div><div class="lnx-value-item"><b>Impressora multifuncional</b><small>Equipamento de escritório</small></div><div>10 un</div><div class="lnx-value-money">R$ 3.980</div></div>
          </div>
        </div>
        <div class="lnx-value-benefits">
          <div class="lnx-value-benefit"><i>⚡</i><b>Comece com pouco</b><span>Ferramenta acessível para quem está dando os primeiros passos nas licitações.</span></div>
          <div class="lnx-value-benefit"><i>▤</i><b>Veja os itens primeiro</b><span>Entenda rapidamente o que o órgão quer comprar antes de investir mais tempo.</span></div>
          <div class="lnx-value-benefit"><i>◎</i><b>Foco no que importa</b><span>Organize sua busca e acompanhe oportunidades alinhadas ao seu negócio.</span></div>
        </div>
        <div class="lnx-value-price">
          <div class="lnx-value-price-main"><span>R$ </span><strong>29,90</strong><span>/mês</span></div>
          <div class="lnx-value-price-copy"><b>7 dias grátis.</b> Preço justo para quem quer começar a vender para o governo.</div>
        </div>
      </div>
    </section>
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
    st.html(_auth_value_panel_html())
