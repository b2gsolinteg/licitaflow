from __future__ import annotations

import base64
import random
from collections import deque
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image



OFFICIAL_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "licitanexo-logo.png"


def _logo_data_uri() -> str:
    """Prepara o logo oficial para uso sobre fundo escuro."""
    if not OFFICIAL_LOGO_PATH.exists():
        return ""

    with Image.open(OFFICIAL_LOGO_PATH) as source:
        image = source.convert("RGBA")

    width, height = image.size
    pixels = image.load()

    # Remove somente o branco conectado ?s bordas.
    queue = deque()
    visited = set()

    def is_background(x, y):
        r, g, b, a = pixels[x, y]
        return a > 0 and r >= 235 and g >= 235 and b >= 235

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))

    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()

        if (x, y) in visited:
            continue

        visited.add((x, y))

        if not is_background(x, y):
            continue

        pixels[x, y] = (255, 255, 255, 0)

        if x > 0:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y > 0:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))

    # Em fundo escuro, transforma apenas pixels realmente escuros
    # da palavra LICITA em branco. Azul vivo e amarelo permanecem.
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            if a == 0:
                continue

            brightness = max(r, g, b)

            # Tons navy/cinza escuro.
            if brightness < 105 and abs(r - g) < 55:
                pixels[x, y] = (255, 255, 255, a)

    bbox = image.getchannel("A").getbbox()
    if bbox:
        image = image.crop(bbox)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)

    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _logo_original_data_uri() -> str:
    """Logo oficial original para uso sobre fundo claro."""
    if not OFFICIAL_LOGO_PATH.exists():
        return ""

    encoded = base64.b64encode(
        OFFICIAL_LOGO_PATH.read_bytes()
    ).decode("ascii")

    return f"data:image/png;base64,{encoded}"


def _screen_html() -> str:
    logo = _logo_data_uri()
    mini_logo_source = _logo_original_data_uri()
    logo_html = (
        f'<img class="lf-logo" src="{logo}" alt="LicitaNexo">'
        if logo
        else '<div class="lf-logo-fallback">Licita<span>Nexo</span></div>'
    )
    mini_logo = (
        f'<img class="lf-mini-logo" src="{mini_logo_source}" alt="LicitaNexo">'
        if logo
        else '<strong>LicitaNexo</strong>'
    )

    return f"""
    <div class="lf-stage" aria-hidden="true">
      <div class="lf-laptop">
        <div class="lf-camera"></div>
        <div class="lf-screen">
          <section class="lf-left">
            {logo_html}
            <div class="lf-hero">
              <h1>Licitações públicas<br>de forma <strong>simples e<br>acessível</strong></h1>
            </div>

            <div class="lf-features">
              <div class="lf-feature">
                <div class="lf-feature-icon">▣</div>
                <div><b>Produtos e serviços direto na tela</b><span>Veja o que o governo está comprando<br>sem abrir edital por edital.</span></div>
              </div>
              <div class="lf-feature">
                <div class="lf-feature-icon">◴</div>
                <div><b>Mais tempo para avaliar</b><span>Compare mais oportunidades antes<br>de decidir onde aprofundar.</span></div>
              </div>
              <div class="lf-feature">
                <div class="lf-feature-icon">☑</div>
                <div><b>Controle fácil das participações</b><span>Salve editais e acompanhe suas<br>participações.</span></div>
              </div>
            </div>

            <div class="lf-price">
              <div class="lf-tag">◆</div>
              <div class="lf-price-main"><small>Plano mensal</small><div><span>R$</span> 29,90<em>/mês</em></div></div>
              <div class="lf-price-copy">Acesso rápido para<br>avaliar oportunidades e<br>controlar suas participações.</div>
              <div class="lf-trial-pill">7 dias grátis</div>
            </div>
          </section>

          <section class="lf-app">
            <div class="lf-app-top">
              <div>{mini_logo}</div>
              <div class="lf-search">⌕ &nbsp; Buscar licitações</div>
            </div>

            <div class="lf-app-body">
              <aside class="lf-app-nav">
                <div class="active">⌕ &nbsp; Buscar licitações</div>
                <div>◫ &nbsp; Por Estado</div>
                <div>⌖ &nbsp; Por Cidade</div>
                <div>⌘ &nbsp; Por Modalidade</div>
                <div>◎ &nbsp; Por site de disputa</div>
                <div>▽ &nbsp; Filtro avançado</div>
                <div>↗ &nbsp; Em destaque</div>
                <div>▱ &nbsp; Minhas participações</div>
                <div>▦ &nbsp; Calendário</div>
                <div>☷ &nbsp; Preferências</div>
                <div>◉ &nbsp; Radar de licitações</div>
                <div>▣ &nbsp; Suporte</div>
                <div>◎ &nbsp; Minha conta</div>
                <div class="exit">↪ &nbsp; Sair</div>
              </aside>

              <main class="lf-results">
                <article class="lf-tender">
                  <b>DISPENSA DE LICITAÇÃO</b>
                  <strong>CÂMARA MUNICIPAL DE TRÊS CORAÇÕES</strong>
                  <p>Contratação de empresa especializada para confecção e fornecimento de materiais institucionais. Exemplo demonstrativo do LicitaNexo.</p>
                  <div class="lf-chips"><span>Local &nbsp; Três Corações - MG</span><span>Site &nbsp; Site não informado</span></div>
                  <div class="lf-chips"><span>Valor &nbsp; R$ 2.033,90</span><span>Itens &nbsp; Itens sob demanda</span></div>
                  <div class="lf-items-title">Itens da licitação - 2 item(ns)</div>
                  <div class="lf-item"><span>1</span>Confecção e fornecimento de placa institucional</div>
                  <div class="lf-item"><span>2</span>Confecção e fornecimento de quadro</div>
                </article>

                <article class="lf-tender lf-second">
                  <b>DISPENSA DE LICITAÇÃO</b>
                  <strong>MUNICÍPIO DE PARAPUÃ</strong>
                  <p>Contratação de empresa especializada para aquisição de peças e condicionamento. Exemplo demonstrativo.</p>
                  <div class="lf-chips"><span>Local &nbsp; Parapuã - SP</span><span>Site &nbsp; Site não informado</span></div>
                  <div class="lf-chips"><span>Valor &nbsp; R$ 32.438,00</span><span>Itens &nbsp; Itens sob demanda</span></div>
                  <div class="lf-items-title">Itens da licitação - 4 item(ns)</div>
                  <div class="lf-item"><span>1</span>Mão de obra</div>
                  <div class="lf-item"><span>2</span>Jogo de bicos</div>
                  <div class="lf-item"><span>3</span>Bomba alta</div>
                  <div class="lf-item"><span>4</span>Filtro de combustível</div>
                </article>
              </main>
            </div>
          </section>
        </div>
        <div class="lf-base"></div>
      </div>
    </div>
    """


def _css(mode: str) -> str:
    request_mode = mode == "request"
    recovery_mode = mode == "recovery"

    card_width = "370px" if request_mode else "330px"
    card_max_height = "74vh" if request_mode else "620px"
    card_top = "50%" if not request_mode else "50%"
    overflow = "auto" if request_mode or recovery_mode else "visible"

    return f"""
    <style>
    :root {{
      --lf-navy:#041a38;
      --lf-navy2:#062854;
      --lf-blue:#0d5fd7;
      --lf-yellow:#ffbf00;
      --lf-white:#ffffff;
      --lf-text:#071a3d;
    }}

    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"] {{
      margin:0!important;
      padding:0!important;
      min-height:100vh!important;
      overflow:hidden!important;
      background:
        radial-gradient(circle at 85% 13%,#08386f 0%,#051d3e 31%,#020f23 73%,#010a18 100%)!important;
      font-family:Inter,"Segoe UI",Arial,sans-serif!important;
    }}

    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    #MainMenu,footer {{
      display:none!important;
    }}

    [data-testid="stMain"]>div,
    [data-testid="stMainBlockContainer"],
    .block-container {{
      width:100vw!important;
      max-width:100vw!important;
      height:100vh!important;
      min-height:100vh!important;
      margin:0!important;
      padding:0!important;
    }}

    .lf-stage {{
      position:fixed;
      inset:0;
      z-index:1;
      display:flex;
      align-items:center;
      justify-content:center;
      padding:2.2vh 2.5vw 6.5vh;
      box-sizing:border-box;
      pointer-events:none;
    }}

    .lf-laptop {{
      position:relative;
      width:min(1510px,94vw);
      height:min(850px,88vh);
      min-height:610px;
      border:4px solid #6c7582;
      border-bottom:16px solid #1b2027;
      border-radius:28px 28px 14px 14px;
      background:#090d13;
      padding:13px;
      box-sizing:border-box;
      box-shadow:
        0 42px 80px rgba(0,0,0,.48),
        inset 0 0 0 2px #111820,
        0 0 0 2px rgba(255,255,255,.08);
    }}

    .lf-camera {{
      position:absolute;
      width:7px;height:7px;
      left:50%;top:8px;
      transform:translateX(-50%);
      background:#1e2937;
      border-radius:50%;
      box-shadow:0 0 0 2px #05080c;
      z-index:7;
    }}

    .lf-screen {{
      width:100%;
      height:100%;
      display:grid;
      grid-template-columns:34% 66%;
      overflow:hidden;
      border-radius:8px;
      background:linear-gradient(135deg,#03172f,#062c61);
    }}

    .lf-base {{
      position:absolute;
      left:-8.5%;
      right:-8.5%;
      height:50px;
      bottom:-58px;
      border-radius:0 0 24px 24px;
      background:linear-gradient(180deg,#d8dde3 0%,#89919b 28%,#505762 62%,#c8cdd2 100%);
      clip-path:polygon(2% 0,98% 0,100% 72%,97% 100%,3% 100%,0 72%);
      box-shadow:0 18px 24px rgba(0,0,0,.40),inset 0 2px rgba(255,255,255,.65);
    }}

    .lf-base::before {{
      content:"";
      position:absolute;
      left:43%;right:43%;top:0;
      height:13px;
      background:linear-gradient(#676f79,#a7adb4);
      border-radius:0 0 9px 9px;
    }}

    .lf-left {{
      position:relative;
      padding:35px 48px 31px;
      color:#fff;
      background:
        radial-gradient(circle at 115% 18%,rgba(18,87,181,.22),transparent 34%),
        linear-gradient(150deg,#02152e 0%,#052143 62%,#02162f 100%);
      box-sizing:border-box;
      overflow:hidden;
    }}

    .lf-logo {{
      width:245px;
      max-height:76px;
      object-fit:contain;
      object-position:left center;
      display:block;
    }}

    .lf-logo-fallback {{
      color:#fff;font-size:30px;font-weight:900;
    }}
    .lf-logo-fallback span {{color:var(--lf-yellow)}}

    .lf-hero {{margin-top:42px}}
    .lf-hero h1 {{
      margin:0;
      color:#fff;
      font-size:clamp(32px,2.6vw,48px);
      line-height:1.07;
      letter-spacing:-1.4px;
      font-weight:850;
    }}
    .lf-hero h1 strong {{color:var(--lf-yellow)}}

    .lf-features {{
      margin-top:34px;
      display:grid;
      gap:22px;
    }}
    .lf-feature {{
      display:grid;
      grid-template-columns:68px 1fr;
      gap:14px;
      align-items:center;
    }}
    .lf-feature-icon {{
      width:62px;height:62px;
      border:1px solid #0c68ca;
      border-radius:11px;
      display:grid;
      place-items:center;
      color:var(--lf-yellow);
      background:linear-gradient(145deg,#07366d,#04224a);
      font-size:30px;
      box-shadow:inset 0 0 18px rgba(11,93,206,.20);
    }}
    .lf-feature b {{
      display:block;
      color:#fff;
      font-size:15px;
      margin-bottom:5px;
    }}
    .lf-feature span {{
      display:block;
      color:#e4edf8;
      font-size:13px;
      line-height:1.43;
    }}

    .lf-price {{
      position:absolute;
      left:48px;right:35px;bottom:38px;
      min-height:88px;
      display:grid;
      grid-template-columns:58px 1.15fr .95fr;
      gap:12px;
      align-items:center;
      border:1px solid #d59700;
      border-radius:12px;
      padding:13px 16px;
      box-sizing:border-box;
      background:linear-gradient(130deg,#05254b,#071d39);
    }}
    .lf-tag {{
      width:49px;height:49px;
      border-radius:10px;
      display:grid;place-items:center;
      color:#061a34;
      background:var(--lf-yellow);
      font-size:26px;
      transform:rotate(-9deg);
    }}
    .lf-price-main small {{
      display:block;
      color:#fff;
      font-size:12px;
      font-weight:800;
      margin-bottom:2px;
    }}
    .lf-price-main div {{
      color:var(--lf-yellow);
      font-size:31px;
      line-height:1;
      font-weight:900;
      white-space:nowrap;
    }}
    .lf-price-main div span {{font-size:20px}}
    .lf-price-main em {{
      font-style:normal;
      font-size:14px;
      margin-left:3px;
    }}
    .lf-price-copy {{
      color:#fff;
      font-size:10px;
      line-height:1.45;
    }}
    .lf-trial-pill {{
      position:absolute;
      right:18px;
      bottom:-25px;
      min-width:126px;
      text-align:center;
      padding:7px 15px;
      border-radius:999px;
      background:var(--lf-yellow);
      color:#091a34;
      font-size:12px;
      font-weight:900;
      box-shadow:0 5px 12px rgba(0,0,0,.22);
    }}

    .lf-app {{
      position:relative;
      overflow:hidden;
      background:#e9eef5;
    }}

    .lf-app-top {{
      height:62px;
      display:flex;
      align-items:center;
      gap:50px;
      padding:0 22px;
      box-sizing:border-box;
      color:#fff;
      background:linear-gradient(90deg,#052550,#0a3470);
      border-bottom:1px solid #15457d;
    }}
    .lf-mini-logo {{
      width:126px;
      max-height:40px;
      object-fit:contain;
      object-position:left center;
    }}
    .lf-search {{
      width:205px;
      padding:10px 14px;
      border-radius:7px;
      background:#123e75;
      color:#dce8f8;
      font-size:10px;
    }}

    .lf-app-body {{
      height:calc(100% - 62px);
      display:grid;
      grid-template-columns:148px 1fr;
    }}
    .lf-app-nav {{
      padding:16px 10px;
      background:linear-gradient(180deg,#052b5b,#06244c);
      color:#fff;
      font-size:10px;
      display:flex;
      flex-direction:column;
      gap:6px;
    }}
    .lf-app-nav div {{
      padding:10px 9px;
      border-radius:6px;
      white-space:nowrap;
    }}
    .lf-app-nav .active {{
      background:#164d88;
      color:var(--lf-yellow);
      font-weight:800;
    }}
    .lf-app-nav .exit {{
      margin-top:auto;
      border:1px solid #d89c00;
      color:var(--lf-yellow);
    }}

    .lf-results {{
      padding:18px 27px;
      background:linear-gradient(135deg,#f8fafc,#e9eef5);
      overflow:hidden;
    }}
    .lf-tender {{
      background:#fff;
      border:1px solid #d8e0e9;
      border-radius:8px;
      padding:17px 18px 13px;
      box-shadow:0 4px 12px rgba(18,41,72,.04);
    }}
    .lf-tender b {{
      display:block;
      color:#061b40;
      font-size:11px;
    }}
    .lf-tender strong {{
      display:block;
      color:#14325d;
      font-size:9px;
      margin-top:2px;
    }}
    .lf-tender p {{
      max-width:520px;
      margin:9px 0;
      color:#2c4567;
      font-size:8px;
      line-height:1.55;
    }}
    .lf-chips {{
      display:flex;
      gap:7px;
      margin:6px 0;
    }}
    .lf-chips span {{
      padding:4px 6px;
      border-radius:999px;
      color:#1e3553;
      background:#f4f6f8;
      border:1px solid #e1e5ea;
      font-size:7px;
    }}
    .lf-chips span::first-letter {{color:#d79500}}
    .lf-items-title {{
      margin-top:9px;
      border-top:1px solid #e4e9ef;
      padding-top:8px;
      color:#162e52;
      font-size:8px;
      font-weight:800;
    }}
    .lf-item {{
      display:grid;
      grid-template-columns:25px 1fr;
      gap:8px;
      padding-top:7px;
      color:#304761;
      font-size:7.5px;
    }}
    .lf-second {{margin-top:14px}}

    .st-key-lnx_auth_form {{
      position:fixed!important;
      z-index:50!important;
      left:calc(50% + min(34vw,520px))!important;
      top:{card_top}!important;
      transform:translate(-50%,-50%)!important;
      width:min({card_width},24vw)!important;
      max-height:{card_max_height}!important;
      overflow-y:{overflow}!important;
      box-sizing:border-box!important;
      padding:28px 29px 25px!important;
      border:1px solid rgba(255,255,255,.82)!important;
      border-radius:25px!important;
      background:rgba(255,255,255,.96)!important;
      backdrop-filter:blur(12px)!important;
      box-shadow:0 22px 48px rgba(13,31,58,.22)!important;
    }}

    .st-key-lnx_auth_form [data-testid="stForm"] {{
      border:0!important;
      padding:0!important;
      background:transparent!important;
    }}

    .lf-form-title {{
      margin:0 0 4px;
      color:#071a3d;
      font-size:27px;
      line-height:1.08;
      letter-spacing:-.7px;
      font-weight:900;
    }}
    .lf-form-sub {{
      margin:0 0 18px;
      color:#233b5f;
      font-size:12px;
      line-height:1.5;
    }}

    .st-key-lnx_auth_form [data-testid="stWidgetLabel"] p,
    .st-key-lnx_auth_form label p {{
      color:#0b2146!important;
      font-size:12px!important;
      font-weight:800!important;
    }}

    .st-key-lnx_auth_form [data-baseweb="input"],
    .st-key-lnx_auth_form [data-baseweb="base-input"] {{
      border:1px solid #b9c9dc!important;
      border-radius:7px!important;
      background:#fff!important;
      box-shadow:none!important;
    }}
    .st-key-lnx_auth_form input {{
      height:42px!important;
      color:#163255!important;
      -webkit-text-fill-color:#163255!important;
      font-size:12px!important;
      background:#fff!important;
    }}

    .st-key-lnx_auth_form .stFormSubmitButton button {{
      width:100%!important;
      min-height:50px!important;
      margin-top:10px!important;
      border:0!important;
      border-radius:7px!important;
      background:linear-gradient(180deg,#ffc400,#ffb600)!important;
      color:#091a34!important;
      font-size:14px!important;
      font-weight:900!important;
      box-shadow:0 8px 15px rgba(207,149,0,.18)!important;
    }}
    .st-key-lnx_auth_form .stFormSubmitButton button:hover {{
      background:linear-gradient(180deg,#ffd12a,#ffc000)!important;
    }}

    .lf-forgot {{
      margin:2px 0 10px;
      text-align:left;
    }}
    .lf-forgot a {{
      color:#0864d8!important;
      font-size:11px!important;
      font-weight:700!important;
      text-decoration:underline!important;
    }}

    .lf-or {{
      display:flex;
      align-items:center;
      gap:10px;
      margin:13px 0;
      color:#59708e;
      font-size:11px;
    }}
    .lf-or::before,.lf-or::after {{
      content:"";
      height:1px;
      flex:1;
      background:#d9e1ea;
    }}

    .lf-trial-link {{
      display:block;
      width:100%;
      box-sizing:border-box;
      padding:13px 12px;
      border:1px solid #3280e5;
      border-radius:7px;
      text-align:center;
      color:#0a55c7!important;
      text-decoration:none!important;
      font-size:13px;
      font-weight:900;
      background:#fff;
    }}

    .lf-back {{
      display:block;
      margin-top:12px;
      text-align:center;
      color:#64748b!important;
      font-size:10px!important;
      text-decoration:none!important;
    }}

    .lf-signup-note {{
      margin:10px 0 0;
      color:#66758a;
      font-size:9.5px;
      line-height:1.45;
      text-align:center;
    }}

    @media(max-width:1450px) {{
      .lf-laptop {{
        width:96vw;
        height:90vh;
        min-height:560px;
      }}
      .lf-left {{padding:25px 34px 24px}}
      .lf-logo {{width:205px}}
      .lf-hero {{margin-top:24px}}
      .lf-hero h1 {{font-size:34px}}
      .lf-features {{margin-top:22px;gap:14px}}
      .lf-feature {{grid-template-columns:53px 1fr}}
      .lf-feature-icon {{width:48px;height:48px;font-size:23px}}
      .lf-feature b {{font-size:12.5px}}
      .lf-feature span {{font-size:10.5px}}
      .lf-price {{left:34px;right:24px;bottom:25px;min-height:75px;padding:10px 12px;grid-template-columns:45px 1.15fr .9fr}}
      .lf-tag {{width:40px;height:40px;font-size:20px}}
      .lf-price-main div {{font-size:25px}}
      .lf-price-copy {{font-size:8.5px}}
      .lf-app-body {{grid-template-columns:124px 1fr}}
      .lf-app-nav {{font-size:8.5px}}
      .lf-results {{padding:13px 18px}}
      .st-key-lnx_auth_form {{
        left:calc(50% + min(33vw,430px))!important;
        width:min({card_width},27vw)!important;
        padding:22px 23px 20px!important;
      }}
      .lf-form-title {{font-size:22px}}
    }}

    @media(max-height:760px) and (min-width:901px) {{
      .lf-stage {{padding-top:1vh;padding-bottom:5.5vh}}
      .lf-laptop {{height:90vh;min-height:520px}}
      .lf-left {{padding-top:20px}}
      .lf-hero {{margin-top:17px}}
      .lf-features {{margin-top:18px;gap:10px}}
      .lf-feature-icon {{width:43px;height:43px}}
      .lf-price {{bottom:18px}}
      .st-key-lnx_auth_form {{
        padding-top:18px!important;
        padding-bottom:17px!important;
      }}
      .st-key-lnx_auth_form input {{height:38px!important}}
    }}

    @media(max-width:900px) {{
      html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"] {{
        overflow:auto!important;
        background:#f4f7fb!important;
      }}
      .lf-stage {{display:none!important}}
      .st-key-lnx_auth_form {{
        position:relative!important;
        left:auto!important;
        top:auto!important;
        transform:none!important;
        width:calc(100% - 32px)!important;
        max-width:520px!important;
        max-height:none!important;
        margin:32px auto!important;
        overflow:visible!important;
        border-radius:18px!important;
      }}
    }}

    /* LNX_NO_NOTEBOOK_FINAL_V1 */
    .lf-stage{{
      inset:0!important;
      padding:0!important;
      display:block!important;
      background:
        radial-gradient(circle at 88% 8%,rgba(13,78,159,.22),transparent 28%),
        linear-gradient(145deg,#03162f 0%,#061f42 52%,#021227 100%)!important;
    }}

    .lf-laptop{{
      position:absolute!important;
      inset:0!important;
      width:100vw!important;
      height:100vh!important;
      min-height:100vh!important;
      max-width:none!important;
      margin:0!important;
      padding:0!important;
      border:0!important;
      border-radius:0!important;
      background:transparent!important;
      box-shadow:none!important;
    }}

    .lf-camera,
    .lf-base{{
      display:none!important;
    }}

    .lf-screen{{
      width:100vw!important;
      height:100vh!important;
      min-height:100vh!important;
      border:0!important;
      border-radius:0!important;
      box-shadow:none!important;
      grid-template-columns:35% 65%!important;
      background:linear-gradient(135deg,#03172f,#062c61)!important;
    }}

    .lf-left{{
      padding:clamp(24px,3.3vh,42px) clamp(30px,3.3vw,58px) 28px!important;
    }}

    .lf-logo{{
      width:245px!important;
      max-height:74px!important;
    }}

    .lf-hero{{
      margin-top:clamp(22px,4vh,44px)!important;
    }}

    .lf-hero h1{{
      font-size:clamp(34px,2.8vw,50px)!important;
    }}

    .lf-features{{
      margin-top:clamp(22px,3.6vh,36px)!important;
      gap:clamp(14px,2.2vh,22px)!important;
    }}

    .lf-price{{
      left:clamp(30px,3.3vw,58px)!important;
      right:clamp(24px,2.6vw,46px)!important;
      bottom:clamp(22px,3.2vh,38px)!important;
    }}

    .lf-app{{
      margin:16px 18px 16px 0!important;
      border:1px solid rgba(66,128,202,.30)!important;
      border-radius:18px!important;
      overflow:hidden!important;
      box-shadow:0 22px 60px rgba(0,0,0,.20)!important;
    }}

    .st-key-lnx_auth_form{{
      left:auto!important;
      right:clamp(34px,4.2vw,76px)!important;
      top:50%!important;
      transform:translateY(-50%)!important;
      width:min(390px,24.5vw)!important;
      max-height:88vh!important;
      overflow-y:auto!important;
      scrollbar-width:thin!important;
      border-radius:24px!important;
      padding:26px 28px 23px!important;
    }}

    .st-key-lnx_auth_form::-webkit-scrollbar{{
      width:6px;
    }}

    .st-key-lnx_auth_form::-webkit-scrollbar-thumb{{
      background:#cbd5e1;
      border-radius:999px;
    }}

    .st-key-lnx_auth_form input{{
      height:40px!important;
    }}

    .st-key-lnx_auth_form .stFormSubmitButton button{{
      min-height:48px!important;
    }}

    @media(max-width:1450px){{
      .lf-screen{{
        grid-template-columns:36% 64%!important;
      }}

      .lf-left{{
        padding:22px 30px 22px!important;
      }}

      .lf-logo{{
        width:205px!important;
      }}

      .lf-hero{{
        margin-top:20px!important;
      }}

      .lf-hero h1{{
        font-size:34px!important;
      }}

      .lf-feature b{{
        font-size:12.5px!important;
      }}

      .lf-feature span{{
        font-size:10.5px!important;
      }}

      .lf-price{{
        left:30px!important;
        right:24px!important;
        bottom:22px!important;
      }}

      .lf-app{{
        margin:12px 14px 12px 0!important;
      }}

      .st-key-lnx_auth_form{{
        right:24px!important;
        width:min(365px,27vw)!important;
        max-height:91vh!important;
        padding:20px 22px 18px!important;
      }}
    }}

    @media(max-height:780px) and (min-width:901px){{
      .lf-left{{
        padding-top:18px!important;
      }}

      .lf-logo{{
        width:190px!important;
        max-height:55px!important;
      }}

      .lf-hero{{
        margin-top:13px!important;
      }}

      .lf-hero h1{{
        font-size:31px!important;
      }}

      .lf-features{{
        margin-top:15px!important;
        gap:9px!important;
      }}

      .lf-feature-icon{{
        width:42px!important;
        height:42px!important;
        font-size:20px!important;
      }}

      .lf-feature{{
        grid-template-columns:47px 1fr!important;
      }}

      .lf-price{{
        bottom:16px!important;
        min-height:69px!important;
      }}

      .st-key-lnx_auth_form{{
        max-height:94vh!important;
        padding-top:16px!important;
        padding-bottom:15px!important;
      }}

      .lf-form-title{{
        font-size:20px!important;
      }}

      .lf-form-sub{{
        margin-bottom:10px!important;
      }}

      .st-key-lnx_auth_form input{{
        height:36px!important;
      }}

      .st-key-lnx_auth_form .stFormSubmitButton button{{
        min-height:43px!important;
      }}
    }}

    @media(max-width:900px){{
      .lf-stage{{
        display:none!important;
      }}

      .st-key-lnx_auth_form{{
        position:relative!important;
        right:auto!important;
        top:auto!important;
        transform:none!important;
        width:calc(100% - 28px)!important;
        max-width:540px!important;
        max-height:none!important;
        overflow:visible!important;
        margin:24px auto!important;
      }}
    }}

    </style>
    """


def _final_public_polish_css(mode: str) -> str:
    common = """
    <style>
    /* LNX_PUBLIC_POLISH_V2 */

    .lf-logo{
      width:220px!important;
      max-height:62px!important;
      object-fit:contain!important;
      object-position:left center!important;
      box-sizing:border-box!important;
      padding:0!important;
      border-radius:0!important;
      background:transparent!important;
      box-shadow:none!important;
      filter:none!important;
      display:block!important;
    }

    .lf-left{
      display:flex!important;
      flex-direction:column!important;
      overflow:hidden!important;
    }

    .lf-hero{margin-top:24px!important}

    .lf-features{
      margin-top:24px!important;
      gap:16px!important;
    }

    .lf-price{
      position:relative!important;
      left:auto!important;
      right:auto!important;
      bottom:auto!important;
      top:auto!important;
      width:100%!important;
      margin:24px 0 0!important;
      min-height:82px!important;
      flex:0 0 auto!important;
    }

    .lf-trial-pill{
      right:18px!important;
      bottom:-22px!important;
    }

    .lf-app{
      margin:14px 16px 14px 0!important;
      border-radius:16px!important;
    }

    .lf-app-body{grid-template-columns:132px 1fr!important}

    .lf-account-switch{
      margin:-7px 0 14px!important;
      color:#5c6d84!important;
      font-size:11.5px!important;
      line-height:1.4!important;
    }

    .lf-account-switch a{
      color:#0b63d8!important;
      font-weight:850!important;
      text-decoration:none!important;
    }

    .lf-account-switch a:hover{text-decoration:underline!important}

    .st-key-lnx_auth_form{
      width:min(405px,25vw)!important;
      max-height:94vh!important;
      right:clamp(24px,3vw,52px)!important;
      padding:22px 24px 20px!important;
    }

    .st-key-lnx_auth_form [data-testid="stVerticalBlock"]{gap:.48rem!important}
    .st-key-lnx_auth_form [data-testid="stWidgetLabel"]{margin-bottom:1px!important}

    .st-key-lnx_auth_form input{
      height:36px!important;
      min-height:36px!important;
    }

    .st-key-lnx_auth_form .stFormSubmitButton button{
      min-height:44px!important;
      margin-top:7px!important;
    }

    .lf-form-title{
      font-size:23px!important;
      margin-bottom:3px!important;
    }

    .lf-form-sub{
      margin-bottom:11px!important;
      line-height:1.42!important;
    }

    .lf-signup-note{margin-top:8px!important}

    @media(max-width:1450px){
      .lf-logo{
        width:190px!important;
        max-height:54px!important;
        padding:6px 10px!important;
      }

      .lf-hero{margin-top:17px!important}

      .lf-features{
        margin-top:17px!important;
        gap:10px!important;
      }

      .lf-price{
        margin-top:17px!important;
        min-height:72px!important;
      }

      .st-key-lnx_auth_form{
        width:min(390px,27vw)!important;
        right:20px!important;
        padding:18px 20px 16px!important;
      }
    }

    @media(max-height:800px) and (min-width:901px){
      .lf-logo{
        width:178px!important;
        max-height:48px!important;
      }

      .lf-hero{margin-top:11px!important}
      .lf-hero h1{font-size:30px!important}

      .lf-features{
        margin-top:12px!important;
        gap:8px!important;
      }

      .lf-price{
        margin-top:12px!important;
        min-height:65px!important;
      }

      .st-key-lnx_auth_form{
        max-height:96vh!important;
        padding:14px 18px 13px!important;
      }

      .st-key-lnx_auth_form [data-testid="stVerticalBlock"]{gap:.34rem!important}

      .st-key-lnx_auth_form input{
        height:33px!important;
        min-height:33px!important;
      }

      .lf-form-title{font-size:20px!important}

      .lf-form-sub{
        margin-bottom:7px!important;
        font-size:10.5px!important;
      }

      .lf-account-switch{
        margin:-3px 0 8px!important;
        font-size:10.5px!important;
      }
    }
    </style>
    """

    if mode == "request":
        common += """
        <style>
        .st-key-lnx_auth_form{width:min(420px,26vw)!important}
        .st-key-lnx_auth_form [data-testid="stForm"]{padding:0!important}
        .st-key-lnx_auth_form label p{font-size:11px!important}
        .st-key-lnx_auth_form input{font-size:11.5px!important}
        </style>
        """

    return common

def _commercial_final_css() -> str:
    return """
    <style>
    /* LNX_COMMERCIAL_FINAL_V1 */

    .lf-app-top > div:first-child{
      display:flex!important;
      align-items:center!important;
      justify-content:center!important;
      min-width:150px!important;
      min-height:42px!important;
      padding:4px 10px!important;
      border-radius:9px!important;
      background:rgba(255,255,255,.97)!important;
      box-shadow:0 8px 20px rgba(0,0,0,.12)!important;
    }

    .lf-mini-logo{
      width:128px!important;
      max-height:34px!important;
      object-fit:contain!important;
      object-position:center!important;
      filter:none!important;
      opacity:1!important;
    }

    .lf-app-top{
      gap:24px!important;
    }

    .lf-demo-badge{
      margin-left:auto!important;
      padding:7px 10px!important;
      border:1px solid rgba(255,191,0,.65)!important;
      border-radius:999px!important;
      color:#ffd45a!important;
      background:rgba(3,24,54,.46)!important;
      font-size:8.5px!important;
      font-weight:900!important;
      letter-spacing:.04em!important;
      white-space:nowrap!important;
    }

    .lf-account-switch{
      margin:-2px 0 15px!important;
      color:#42546c!important;
      font-size:15px!important;
      line-height:1.35!important;
      font-weight:650!important;
    }

    .lf-account-switch a{
      color:#075fdb!important;
      font-size:15px!important;
      font-weight:900!important;
      text-decoration:none!important;
    }

    .lf-account-switch a:hover{
      text-decoration:underline!important;
    }

    .lf-price{
      margin-top:40px!important;
      min-height:88px!important;
      padding:14px 16px!important;
    }

    .lf-price-copy{
      font-size:10.5px!important;
      line-height:1.42!important;
      color:#eef5ff!important;
    }

    .lf-left::after{
      content:"Cadastro imediato  ?  7 dias gr?tis  ?  Feito para pequenas empresas"!important;
      display:block!important;
      margin-top:24px!important;
      padding:11px 13px!important;
      border:1px solid rgba(63,126,205,.45)!important;
      border-radius:10px!important;
      color:#cbd9eb!important;
      background:rgba(5,32,67,.42)!important;
      font-size:10.5px!important;
      font-weight:700!important;
      line-height:1.35!important;
      text-align:center!important;
    }

    .st-key-lnx_auth_form{
      width:min(430px,27vw)!important;
      padding:22px 24px 20px!important;
      box-shadow:0 28px 60px rgba(9,31,62,.25)!important;
    }

    .lf-form-title{
      font-size:25px!important;
      letter-spacing:-.55px!important;
    }

    .lf-form-sub{
      color:#42546c!important;
      font-size:11.5px!important;
      margin-bottom:8px!important;
    }

    .lf-signup-note{
      margin-top:10px!important;
      color:#52657e!important;
      font-size:10.5px!important;
      font-weight:650!important;
    }

    .st-key-lnx_auth_form .stFormSubmitButton button{
      min-height:48px!important;
      font-size:14px!important;
      letter-spacing:.01em!important;
    }

    .lf-app-body{
      grid-template-columns:128px 1fr!important;
    }

    .lf-app-nav{
      gap:4px!important;
    }

    .lf-app-nav div{
      padding:9px 8px!important;
    }

    @media(max-width:1450px){
      .lf-account-switch,
      .lf-account-switch a{
        font-size:13.5px!important;
      }

      .lf-price{
        margin-top:28px!important;
        min-height:78px!important;
      }

      .lf-left::after{
        margin-top:18px!important;
        font-size:9.5px!important;
        padding:9px 10px!important;
      }

      .st-key-lnx_auth_form{
        width:min(405px,28vw)!important;
      }

      .lf-demo-badge{
        font-size:7.5px!important;
      }
    }

    @media(max-height:800px) and (min-width:901px){
      .lf-account-switch,
      .lf-account-switch a{
        font-size:12.5px!important;
      }

      .lf-price{
        margin-top:18px!important;
        min-height:70px!important;
      }

      .lf-left::after{
        margin-top:12px!important;
        padding:7px 9px!important;
        font-size:8.8px!important;
      }

      .lf-app-top > div:first-child{
        min-width:132px!important;
        min-height:36px!important;
      }

      .lf-mini-logo{
        width:112px!important;
        max-height:29px!important;
      }

      .lf-demo-badge{
        padding:5px 8px!important;
      }
    }

    @media(max-width:900px){
      .lf-left::after{
        display:none!important;
      }
    }
    </style>
    """

def _login_first_commercial_final_css() -> str:
    return """
    <style>
    /* LNX_LOGIN_FIRST_COMMERCIAL_FINAL_V4 */

    .st-key-lnx_auth_form{
      width:min(390px,24vw)!important;
      max-width:390px!important;
      max-height:90vh!important;
      overflow-y:auto!important;
      padding:26px 28px 24px!important;
      border-radius:26px!important;
      background:rgba(255,255,255,.98)!important;
      box-shadow:0 30px 70px rgba(5,22,48,.26)!important;
    }

    .lf-form-title{
      font-size:31px!important;
      line-height:1.05!important;
      letter-spacing:-.75px!important;
      margin-bottom:5px!important;
      color:#0a2147!important;
    }

    .lf-form-sub{
      font-size:14px!important;
      line-height:1.45!important;
      margin-bottom:17px!important;
      color:#526984!important;
      font-weight:600!important;
    }

    .st-key-lnx_auth_form label p{
      font-size:13px!important;
      font-weight:850!important;
      color:#173458!important;
    }

    .st-key-lnx_auth_form input{
      height:45px!important;
      min-height:45px!important;
      border-radius:10px!important;
      font-size:13px!important;
    }

    .lf-forgot a,
    .lf-inline-forgot a{
      color:#075fd8!important;
      font-size:13px!important;
      font-weight:850!important;
    }

    .st-key-lnx_auth_form .stFormSubmitButton button{
      min-height:54px!important;
      border-radius:11px!important;
      font-size:16px!important;
      font-weight:900!important;
      box-shadow:0 14px 25px rgba(255,183,0,.20)!important;
    }

    .lf-trial-card{
      margin-top:6px!important;
      padding:17px 17px 16px!important;
      border:1px solid #cbdcf3!important;
      border-radius:16px!important;
      background:linear-gradient(180deg,#f9fbff 0%,#f2f7ff 100%)!important;
    }

    .lf-trial-card-title{
      color:#0b234b!important;
      font-size:16px!important;
      font-weight:900!important;
      margin-bottom:5px!important;
    }

    .lf-trial-card-copy{
      color:#60748d!important;
      font-size:12px!important;
      line-height:1.45!important;
      margin-bottom:13px!important;
    }

    .lf-trial-link{
      display:block!important;
      width:100%!important;
      box-sizing:border-box!important;
      padding:13px 14px!important;
      border:1.5px solid #2c79e8!important;
      border-radius:10px!important;
      text-align:center!important;
      color:#0a58ca!important;
      background:#fff!important;
      font-size:14px!important;
      font-weight:900!important;
      text-decoration:none!important;
    }

    .lf-trial-link:hover{
      background:#f4f8ff!important;
      border-color:#0a64e8!important;
    }

    /* remove o CTA duplicado no topo do login */
    .lf-account-switch{
      display:none!important;
    }

    .lf-left::after{
      display:none!important;
      content:none!important;
    }

    .lf-price{
      position:relative!important;
      left:auto!important;
      right:auto!important;
      bottom:auto!important;
      top:auto!important;
      width:100%!important;
      min-height:142px!important;
      margin:34px 0 0!important;
      padding:20px 20px 18px!important;
      display:grid!important;
      grid-template-columns:72px minmax(0,1fr) auto!important;
      grid-template-rows:auto auto!important;
      gap:11px 18px!important;
      align-items:center!important;
      border:1px solid rgba(255,191,0,.90)!important;
      border-radius:20px!important;
      background:
        radial-gradient(circle at 100% 0%,rgba(25,100,194,.20),transparent 38%),
        linear-gradient(145deg,#082b59 0%,#061f43 100%)!important;
      box-shadow:0 22px 42px rgba(0,0,0,.22)!important;
      overflow:hidden!important;
    }

    .lf-tag{
      grid-column:1!important;
      grid-row:1 / span 2!important;
      width:62px!important;
      height:62px!important;
      border-radius:15px!important;
      font-size:29px!important;
      background:linear-gradient(145deg,#ffd45a,#ffb900)!important;
      box-shadow:0 11px 20px rgba(255,185,0,.16)!important;
    }

    .lf-price-main{
      grid-column:2!important;
      grid-row:1!important;
      align-self:end!important;
      min-width:0!important;
    }

    .lf-price-main small{
      display:block!important;
      margin-bottom:4px!important;
      color:#dbe8f8!important;
      font-size:12px!important;
      font-weight:850!important;
      text-transform:uppercase!important;
      letter-spacing:.06em!important;
    }

    .lf-price-main div{
      color:#ffbf00!important;
      font-size:43px!important;
      line-height:.98!important;
      font-weight:950!important;
      white-space:nowrap!important;
      letter-spacing:-.035em!important;
    }

    .lf-price-main div span{font-size:20px!important}

    .lf-price-main em{
      color:#fff!important;
      font-size:15px!important;
      font-style:normal!important;
      margin-left:3px!important;
    }

    .lf-trial-pill{
      position:static!important;
      grid-column:3!important;
      grid-row:1!important;
      min-width:126px!important;
      padding:9px 15px!important;
      border-radius:999px!important;
      background:#ffbf00!important;
      color:#0a2147!important;
      font-size:13px!important;
      font-weight:950!important;
      text-align:center!important;
      box-shadow:none!important;
      justify-self:end!important;
    }

    .lf-price-copy{
      display:block!important;
      grid-column:2 / 4!important;
      grid-row:2!important;
      color:#eef5ff!important;
      font-size:13px!important;
      line-height:1.45!important;
      font-weight:700!important;
      padding-top:6px!important;
      border-top:1px solid rgba(255,255,255,.10)!important;
    }

    @media(max-width:1450px){
      .st-key-lnx_auth_form{
        width:min(370px,25vw)!important;
        padding:22px 23px 20px!important;
      }
      .lf-form-title{font-size:28px!important}
      .lf-price{
        margin-top:25px!important;
        min-height:132px!important;
        grid-template-columns:62px minmax(0,1fr) auto!important;
        padding:17px 17px 16px!important;
      }
      .lf-tag{width:54px!important;height:54px!important}
      .lf-price-main div{font-size:37px!important}
      .lf-trial-pill{min-width:112px!important;font-size:12px!important}
      .lf-price-copy{font-size:11.5px!important}
    }

    @media(max-height:800px) and (min-width:901px){
      .st-key-lnx_auth_form{
        max-height:93vh!important;
        padding-top:18px!important;
        padding-bottom:17px!important;
      }
      .lf-form-title{font-size:25px!important}
      .lf-form-sub{font-size:12px!important;margin-bottom:11px!important}
      .st-key-lnx_auth_form input{
        height:39px!important;
        min-height:39px!important;
      }
      .st-key-lnx_auth_form .stFormSubmitButton button{
        min-height:47px!important;
      }
      .lf-price{
        margin-top:18px!important;
        min-height:120px!important;
      }
    }
    
    /* LNX_APPROVED_LOGIN_BORDER_V2 */
    .st-key-lnx_auth_form{
      border:2px solid #ffbf00!important;
      box-shadow:
        0 28px 65px rgba(5,22,48,.24),
        0 0 0 1px rgba(255,191,0,.10)!important;
    }
    </style>
    """

def _set_session(user, security, conversion, motivational_phrases) -> None:
    token = security.create_session(
        user.get("company_id", ""),
        user.get("id", ""),
    )
    conversion.record_event(
        "login",
        user.get("company_id", ""),
        user.get("id", ""),
        {"email": user.get("email", "")},
    )
    st.session_state.user = user
    st.session_state.security_session_token = token
    st.session_state.motivational_phrase = random.choice(tuple(motivational_phrases))
    st.session_state.just_logged_in = True


def render_public_auth(
    *,
    db,
    security,
    conversion,
    commercial,
    client_ip_getter,
    motivational_phrases,
) -> None:
    del commercial  # Mantido na assinatura por compatibilidade com o app.

    raw_mode = st.query_params.get("auth", "login")
    if isinstance(raw_mode, list):
        raw_mode = raw_mode[0] if raw_mode else "login"
    mode = str(raw_mode or "login").strip().lower()

    # O cadastro é self-service; convite não faz mais parte do fluxo público.
    if mode not in {"login", "request", "recovery"}:
        mode = "login"

    signup_raw = st.query_params.get("signup", "")
    if isinstance(signup_raw, list):
        signup_raw = signup_raw[0] if signup_raw else ""
    signup_requested = str(signup_raw or "").strip().lower() in {"1", "true", "yes"}

    # Mesmo em ?auth=request, mostramos login primeiro.
    # O cadastro aparece somente apos o CTA de teste gratis.
    if mode == "request" and not signup_requested:
        mode = "login"

    st.html(_css(mode))
    st.html(_final_public_polish_css(mode))
    st.html(_commercial_final_css())
    st.html(_screen_html())
    st.html(_login_first_commercial_final_css())

    with st.container(key="lnx_auth_form"):
        if mode == "login":
            st.markdown(
                '<div class="lf-form-title">Bem-vindo de volta</div>'
                '<div class="lf-form-sub">Entre para acessar oportunidades<br>em todo o Brasil.</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="lf-account-switch">Ainda n&atilde;o tem conta? '
                '<a href="?auth=request&signup=1">Come?ar teste gr?tis por 7 dias ?</a></div>',
                unsafe_allow_html=True,
            )
            with st.form("login_final", clear_on_submit=False, enter_to_submit=False):
                email = st.text_input("E-mail", placeholder="seu@email.com")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                st.markdown(
                    '<div class="lf-forgot"><a href="?auth=recovery">Esqueceu a senha?</a></div>',
                    unsafe_allow_html=True,
                )
                if st.form_submit_button("Entrar no LicitaNexo", width="stretch"):
                    client_ip = client_ip_getter()
                    try:
                        security.precheck("login", email, client_ip)
                        user = db.authenticate(email, password)
                        if not user:
                            security.register_attempt("login", email, client_ip, success=False)
                            raise ValueError("E-mail ou senha inválidos.")
                        security.register_attempt("login", email, client_ip, success=True)
                        _set_session(user, security, conversion, motivational_phrases)
                        st.rerun()
                    except Exception as error:
                        st.warning(str(error))

            st.html('<div class="lf-or">ou</div>')
            st.markdown(
                '<a class="lf-trial-link" href="?auth=request&signup=1">7 dias grátis</a>',
                unsafe_allow_html=True,
            )

        elif mode == "request":
            st.markdown(
                '<div class="lf-form-title">Comece grátis</div>'
                '<div class="lf-form-sub">Crie sua conta agora. São 7 dias grátis e depois R$ 29,90/mês.</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="lf-account-switch">J&aacute; possui uma conta? '
                '<a href="?auth=login">Entrar</a></div>',
                unsafe_allow_html=True,
            )
            with st.form("self_service_signup_final", clear_on_submit=False, enter_to_submit=False):
                company = st.text_input("Empresa / Razão social")
                cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
                name = st.text_input("Seu nome")
                email = st.text_input("E-mail profissional")
                whatsapp = st.text_input("WhatsApp", placeholder="(00) 00000-0000")
                segment = st.text_input("Segmento da empresa (opcional)")
                password = st.text_input("Crie sua senha", type="password", placeholder="Mínimo de 8 caracteres")
                password_confirmation = st.text_input("Confirme sua senha", type="password")

                if st.form_submit_button("Criar minha conta grátis", width="stretch"):
                    normalized_email = str(email or "").strip().lower()
                    client_ip = client_ip_getter()
                    try:
                        if len(str(password or "")) < 8:
                            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
                        if password != password_confirmation:
                            raise ValueError("As senhas não coincidem.")
                        if not hasattr(db, "register_trial_self_service"):
                            raise ValueError("Cadastro automático ainda não está disponível nesta instalação.")

                        security.precheck("access_request", normalized_email, client_ip)
                        user = db.register_trial_self_service(
                            company,
                            cnpj,
                            name,
                            normalized_email,
                            whatsapp,
                            password,
                            segment=segment,
                            client_ip=client_ip,
                        )
                        security.register_attempt(
                            "access_request",
                            normalized_email,
                            client_ip,
                            success=True,
                        )
                        conversion.record_event(
                            "trial_started",
                            user.get("company_id", ""),
                            user.get("id", ""),
                            {"email": user.get("email", "")},
                        )
                        _set_session(user, security, conversion, motivational_phrases)
                        st.rerun()
                    except Exception as error:
                        try:
                            security.register_attempt(
                                "access_request",
                                normalized_email,
                                client_ip,
                                success=False,
                            )
                        except Exception:
                            pass
                        st.warning(str(error))

            st.markdown(
                '<div class="lf-signup-note">Ao criar a conta, você inicia imediatamente seu período de teste.</div>'
                '<a class="lf-back" href="?auth=login">Já possui conta? Entrar</a>',
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                '<div class="lf-form-title">Recupere seu acesso</div>'
                '<div class="lf-form-sub">Solicite um código e defina uma nova senha.</div>',
                unsafe_allow_html=True,
            )

            with st.form("password_recovery_request_final", clear_on_submit=False, enter_to_submit=False):
                recovery_email = st.text_input(
                    "E-mail cadastrado",
                    placeholder="seu@email.com",
                    key="final_recovery_email",
                )
                if st.form_submit_button("Solicitar código", width="stretch"):
                    normalized_email = str(recovery_email or "").strip().lower()
                    client_ip = client_ip_getter()
                    try:
                        security.precheck("password_recovery_request", normalized_email, client_ip)
                        db.request_password_reset(normalized_email)
                        security.register_attempt(
                            "password_recovery_request",
                            normalized_email,
                            client_ip,
                            success=True,
                        )
                        st.success("Solicitação registrada. Se o e-mail estiver cadastrado, o suporte poderá gerar o código.")
                    except Exception as error:
                        st.warning(str(error))

            st.markdown('<div class="lf-or">nova senha</div>', unsafe_allow_html=True)

            with st.form("password_recovery_reset_final", clear_on_submit=False, enter_to_submit=False):
                reset_email = st.text_input("E-mail", key="final_reset_email")
                recovery_code = st.text_input("Código de recuperação", placeholder="NX-R-XXXXXXXX")
                new_password = st.text_input("Nova senha", type="password", placeholder="Mínimo de 8 caracteres")
                confirmation = st.text_input("Confirme a nova senha", type="password")

                if st.form_submit_button("Redefinir senha", width="stretch"):
                    normalized_email = str(reset_email or "").strip().lower()
                    client_ip = client_ip_getter()
                    try:
                        if len(str(new_password or "")) < 8:
                            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
                        if new_password != confirmation:
                            raise ValueError("As senhas não coincidem.")
                        security.precheck("password_recovery_reset", normalized_email, client_ip)
                        db.reset_password(normalized_email, recovery_code, new_password)
                        security.register_attempt(
                            "password_recovery_reset",
                            normalized_email,
                            client_ip,
                            success=True,
                        )
                        st.success("Senha alterada. Agora você já pode entrar.")
                    except Exception as error:
                        st.warning(str(error))

            st.markdown(
                '<a class="lf-back" href="?auth=login">Voltar para o login</a>',
                unsafe_allow_html=True,
            )
