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
    """Remove apenas o fundo branco conectado às bordas do PNG oficial."""
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


def _official_brand_css() -> str:
    logo_uri = _official_logo_data_uri()
    if not logo_uri:
        return ""
    return f'''
    <style>
    .lnx-top .lnx-brand img,
    .lnx-top .lnx-brand .lnx-mark,
    .lnx-top .lnx-brand .lnx-name {{display:none!important}}
    .lnx-top .lnx-brand {{
        width:255px!important;height:62px!important;min-height:62px!important;flex:0 0 255px!important;
        background-image:url("{logo_uri}")!important;background-repeat:no-repeat!important;
        background-position:left center!important;background-size:245px auto!important;
    }}
    .lnx-auth-head .lnx-auth-logo img,
    .lnx-auth-head .lnx-brand-mark,
    .lnx-auth-head .lnx-brand-name {{display:none!important}}
    .lnx-auth-head .lnx-auth-logo {{
        display:block!important;width:270px!important;height:68px!important;
        background-image:url("{logo_uri}")!important;background-repeat:no-repeat!important;
        background-position:left center!important;background-size:260px auto!important;
    }}
    @media(max-width:680px) {{
        .lnx-top .lnx-brand {{width:188px!important;height:48px!important;min-height:48px!important;flex-basis:188px!important;background-size:180px auto!important}}
        .lnx-auth-head .lnx-auth-logo {{width:220px!important;height:56px!important;background-size:210px auto!important}}
    }}
    </style>
    '''


def _auth_layout_fix_css() -> str:
    return '''
    <style>
    .lnx-auth-head{
        position:relative!important;left:auto!important;top:auto!important;
        width:calc(100% - 76px)!important;margin:0 0 0 clamp(38px,4.2vw,72px)!important;
        padding-top:clamp(28px,3.4vh,42px)!important;z-index:6!important;
    }
    .lnx-auth-kicker{margin-top:16px!important}.lnx-auth-title{margin-top:14px!important}.lnx-auth-caption{margin-top:10px!important}
    .st-key-lnx_auth_form{margin-top:26px!important;margin-bottom:34px!important}
    @media(max-width:1150px){
        .lnx-auth-head{width:calc(100% - 70px)!important}.st-key-lnx_auth_form{margin-top:24px!important}
    }
    @media(max-width:900px){
        .lnx-auth-head{position:relative!important;left:auto!important;right:auto!important;top:auto!important;width:100%!important;max-width:540px!important;margin:0 auto!important;padding-top:30px!important}
        .st-key-lnx_auth_form{width:100%!important;max-width:540px!important;margin:24px auto 34px!important}
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
    .lnx-auth-title{{font-size:0!important}}.lnx-auth-title strong{{display:none!important}}
    .lnx-auth-title::after{{content:"{title_css}";display:block;max-width:480px;font-size:clamp(27px,2vw,38px)!important;line-height:1.08;letter-spacing:-1px;font-weight:800;color:#071a3d}}
    .lnx-auth-caption{{font-size:0!important}}
    .lnx-auth-caption::after{{content:"{caption_css}";display:block;color:#5e6b80;font-size:14px!important;line-height:1.48;max-width:470px}}
    .lnx-login-price-info>div:nth-child(2)>b,.lnx-login-price-info>div:nth-child(2)>span{{font-size:0!important}}
    .lnx-login-price-info>div:nth-child(2)>b::after{{content:"Preço justo para quem quer começar a vender para o governo";font-size:11px!important;color:#fff;line-height:1.25}}
    .lnx-login-price-info>div:nth-child(2)>span::after{{content:"Comece simples, encontre oportunidades e evolua com o seu negócio.";font-size:9px!important;color:#d7e4f5;line-height:1.3}}
    </style>
    '''


def _native_auth_art_css() -> str:
    """Reutiliza a arte nativa do login, garantindo renderização dentro do viewport desktop."""
    return '''
    <style>
    /* Desativa a camada experimental anterior e usa somente o painel que o public_auth já renderiza. */
    .lnx-auth-value-panel{display:none!important}
    .lnx-auth-art{
        display:block!important;position:fixed!important;inset:0 0 0 40%!important;z-index:1!important;
        overflow:hidden!important;background:
          radial-gradient(circle at 78% 12%,rgba(36,105,225,.23),transparent 30%),
          linear-gradient(145deg,#061a40 0%,#082450 48%,#04152f 100%)!important;
    }
    .lnx-auth-art .grid{display:block!important;opacity:.16!important;background-size:64px 64px!important}
    .lnx-auth-art .orbit,.lnx-auth-hub{display:none!important}
    .lnx-auth-art::before{
        content:"Comece pequeno. Venda para o governo com mais clareza.";
        position:absolute;left:6%;right:6%;top:4.5%;z-index:10;color:#fff;
        font-size:clamp(27px,2.25vw,43px);line-height:1.02;letter-spacing:-1.4px;font-weight:850;
    }
    .lnx-auth-art::after{
        content:"Feito para MEI, microempresas e EPP — encontre oportunidades, veja os itens e decida onde vale competir.";
        position:absolute;left:6%;right:8%;top:14%;z-index:10;color:#b8cbe3;
        font-size:clamp(11px,.9vw,15px);line-height:1.45;
    }
    .lnx-auth-node,.lnx-product-card,.lnx-opportunities{
        position:absolute!important;z-index:6!important;border:1px solid rgba(69,129,215,.36)!important;
        border-radius:14px!important;background:linear-gradient(145deg,rgba(8,39,86,.96),rgba(5,25,58,.98))!important;
        box-shadow:0 15px 36px rgba(0,0,0,.22)!important;color:#fff!important;
    }
    .lnx-auth-node strong{display:none!important}

    /* Público-alvo */
    .lnx-auth-node.a1{left:6%!important;right:6%!important;top:20%!important;width:auto!important;min-height:72px!important;padding:14px 16px!important;border-color:rgba(247,183,20,.48)!important}
    .lnx-auth-node.a1 b,.lnx-auth-node.a1 span{font-size:0!important}
    .lnx-auth-node.a1 b::after{content:"Ideal para MEI, microempresas e EPP";font-size:15px!important;font-weight:900;color:#fff}
    .lnx-auth-node.a1 span::after{content:"Uma forma simples e acessível de começar a vender para o governo.";font-size:10px!important;color:#c1d1e6;line-height:1.4}

    /* Cabeçalho da demonstração */
    .lnx-auth-node.a2{left:6%!important;right:6%!important;top:30%!important;width:auto!important;min-height:68px!important;padding:13px 16px!important}
    .lnx-auth-node.a2 b,.lnx-auth-node.a2 span{font-size:0!important}
    .lnx-auth-node.a2 b::after{content:"Veja a compra por dentro";font-size:16px!important;font-weight:900;color:#fff}
    .lnx-auth-node.a2 span::after{content:"Prefeitura Municipal de Uberlândia/MG · exemplo demonstrativo de compra pública";font-size:10px!important;color:#9fc0eb;line-height:1.4}

    /* Linhas de itens: reutilizam os cards que já renderizam de forma confiável. */
    .lnx-product-card{left:6%!important;right:6%!important;width:auto!important;height:78px!important;padding:12px 15px!important;display:grid!important;grid-template-columns:minmax(170px,1fr) 112px 108px!important;grid-template-rows:auto auto!important;column-gap:14px!important;align-items:center!important}
    .lnx-product-card.p1{top:40%!important;bottom:auto!important}.lnx-product-card.p2{top:50.5%!important;bottom:auto!important}.lnx-product-card.p3{top:61%!important;bottom:auto!important}
    .lnx-product-card .p-title{grid-column:1;grid-row:1;font-size:12px!important;font-weight:900!important;margin:0!important}
    .lnx-product-card .p-org{grid-column:1;grid-row:2;font-size:0!important;min-height:0!important;color:#9fb4cf!important}
    .lnx-product-card .p-org::after{content:"Prefeitura Municipal de Uberlândia/MG · exemplo";font-size:8px!important;color:#9fb4cf!important}
    .lnx-product-card .p-row{grid-column:2;grid-row:1 / span 2;margin:0!important;display:block!important;font-size:0!important;color:#dbe7f6!important}
    .lnx-product-card .p-row span,.lnx-product-card .p-row b{display:block!important}
    .lnx-product-card .p-row span::after{content:"Quantidade";font-size:8px!important;color:#9db2cd!important}
    .lnx-product-card .p-row b{font-size:10px!important;margin-top:4px!important}
    .lnx-product-card .p-price{grid-column:3;grid-row:1;font-size:17px!important;color:#f7bd21!important;font-weight:900!important;margin:0!important;text-align:right!important}
    .lnx-product-card .p-status{grid-column:3;grid-row:2;font-size:0!important;color:#76d9a4!important;text-align:right!important;margin:0!important}
    .lnx-product-card .p-status::after{content:"Exemplo demonstrativo";font-size:8px!important;color:#76d9a4!important;font-weight:800}

    /* Benefícios */
    .lnx-auth-node.a3,.lnx-auth-node.a4{top:72.5%!important;width:42%!important;min-height:82px!important;padding:13px 15px!important}
    .lnx-auth-node.a3{left:6%!important}.lnx-auth-node.a4{right:6%!important;left:auto!important}
    .lnx-auth-node.a3 b,.lnx-auth-node.a3 span,.lnx-auth-node.a4 b,.lnx-auth-node.a4 span{font-size:0!important}
    .lnx-auth-node.a3 b::after{content:"Veja os itens primeiro";font-size:12px!important;color:#fff;font-weight:900}
    .lnx-auth-node.a3 span::after{content:"Entenda rapidamente o que está sendo comprado antes de investir mais tempo.";font-size:9px!important;color:#b6c8df;line-height:1.4}
    .lnx-auth-node.a4 b::after{content:"Foco no que faz sentido";font-size:12px!important;color:#fff;font-weight:900}
    .lnx-auth-node.a4 span::after{content:"Organize sua busca e concentre esforço nas oportunidades mais alinhadas ao seu negócio.";font-size:9px!important;color:#b6c8df;line-height:1.4}

    /* Preço: substitui a antiga caixa de categorias/números fictícios. */
    .lnx-opportunities{left:6%!important;right:6%!important;bottom:4.5%!important;width:auto!important;min-height:72px!important;padding:13px 16px!important;border-color:rgba(247,183,20,.50)!important;display:flex!important;align-items:center!important;justify-content:space-between!important;gap:18px!important;background:linear-gradient(100deg,rgba(247,183,20,.10),rgba(7,31,72,.94) 48%)!important}
    .lnx-opportunities>div{display:none!important}.lnx-opportunities b{font-size:0!important;margin:0!important}
    .lnx-opportunities b::after{content:"R$ 29,90/mês";font-size:24px!important;color:#ffd04a;font-weight:950}
    .lnx-opportunities::after{content:"7 dias grátis · Preço justo para quem quer começar a vender para o governo.";max-width:360px;text-align:right;font-size:10px;color:#c8d6e8;line-height:1.4}

    /* 1366x768 / notebooks: compacta sem cortar a arte. */
    @media(max-width:1500px), (max-height:820px){
      .lnx-auth-art::before{top:3.5%;font-size:30px}.lnx-auth-art::after{top:12.5%;font-size:11px}
      .lnx-auth-node.a1{top:18%!important;min-height:62px!important;padding:10px 13px!important}
      .lnx-auth-node.a2{top:27%!important;min-height:58px!important;padding:10px 13px!important}
      .lnx-product-card{height:65px!important;padding:9px 12px!important;grid-template-columns:minmax(145px,1fr) 94px 95px!important}
      .lnx-product-card.p1{top:36%!important}.lnx-product-card.p2{top:45.5%!important}.lnx-product-card.p3{top:55%!important}
      .lnx-auth-node.a3,.lnx-auth-node.a4{top:65%!important;min-height:70px!important;padding:10px 12px!important}
      .lnx-opportunities{bottom:4%!important;min-height:62px!important;padding:10px 13px!important}
      .lnx-opportunities b::after{font-size:21px!important}
    }
    @media(max-width:1150px){
      .lnx-auth-art{left:46%!important}.lnx-auth-art::before{font-size:26px}.lnx-auth-art::after{font-size:10px}
      .lnx-product-card{grid-template-columns:minmax(120px,1fr) 78px 80px!important}.lnx-product-card .p-price{font-size:14px!important}
      .lnx-auth-node.a3,.lnx-auth-node.a4{width:42%!important}.lnx-opportunities::after{max-width:230px;font-size:9px}
    }
    @media(max-width:900px){.lnx-auth-art{display:none!important}}
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
    st.html(_native_auth_art_css())
