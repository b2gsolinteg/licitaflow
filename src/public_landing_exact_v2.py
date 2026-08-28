from __future__ import annotations

import streamlit as st

from src.brand_assets import APPROVED_LOGO_DARK_DATA_URI


def render_public_landing(logo_path=None) -> None:
    _ = logo_path
    html = f'''
    <style>
    html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{
      margin:0!important;padding:0!important;min-height:100vh!important;background:#F3EEE3!important;
      font-family:Inter,"Segoe UI",Arial,sans-serif!important;overflow-x:hidden!important;
    }}
    header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,
    [data-testid="stSidebar"],[data-testid="collapsedControl"]{{display:none!important}}
    [data-testid="stMain"]>div,[data-testid="stMainBlockContainer"],.block-container{{
      width:100vw!important;max-width:100vw!important;margin:0!important;padding:0!important;
    }}
    [data-testid="stVerticalBlock"],[data-testid="stElementContainer"],[data-testid="stHtml"]{{gap:0!important;margin:0!important;padding:0!important}}
    .lnx-page,.lnx-page *{{box-sizing:border-box}}
    .lnx-page{{min-height:100vh;background:#F3EEE3;color:#0B1735}}
    .lnx-top{{height:86px;background:#07152F;display:flex;align-items:center}}
    .lnx-top-inner{{width:min(1500px,calc(100% - 96px));margin:0 auto;display:flex;align-items:center;justify-content:space-between}}
    .lnx-brand{{display:inline-flex;align-items:center;text-decoration:none}}
    .lnx-brand img{{display:block;width:220px;height:auto;max-height:58px;object-fit:contain;object-position:left center}}
    .lnx-actions{{display:flex;align-items:center;gap:20px}}
    .lnx-actions a{{height:42px;padding:0 20px;display:inline-flex;align-items:center;justify-content:center;border-radius:5px;text-decoration:none!important;font-size:15px;font-weight:700}}
    .lnx-login{{background:#F3EEE3;color:#081533!important}}
    .lnx-trial{{background:#A7E7EF;color:#081533!important}}
    .lnx-hero{{min-height:calc(100vh - 86px);display:grid;grid-template-columns:46.5% 53.5%;overflow:hidden}}
    .lnx-copy{{padding:clamp(70px,9vh,104px) 5vw 62px;display:flex;flex-direction:column;justify-content:center;background:#F3EEE3}}
    .lnx-title{{margin:0;max-width:640px;font-size:clamp(45px,3.2vw,63px);line-height:1.055;letter-spacing:-2px;font-weight:420;color:#0B1735}}
    .lnx-sub{{max-width:650px;margin:27px 0 0;color:#63708A;font-size:clamp(17px,1.02vw,20px);line-height:1.52}}
    .lnx-buttons{{display:flex;gap:24px;margin-top:42px;flex-wrap:wrap}}
    .lnx-buttons a{{height:56px;padding:0 31px;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;background:#14246A;color:#fff!important;text-decoration:none!important;font-size:17px;font-weight:750}}
    .lnx-visual{{position:relative;min-height:calc(100vh - 86px);background:#152468;overflow:hidden;display:flex;align-items:center;justify-content:center;padding:58px 5.5vw 54px 3vw}}
    .lnx-visual:before{{content:"";position:absolute;width:480px;height:480px;border:78px solid #A7E7EF;border-radius:54px;right:-230px;top:-265px;transform:rotate(45deg)}}
    .lnx-visual:after{{content:"";position:absolute;width:660px;height:150px;background:#A7E7EF;border-radius:85px;right:-180px;bottom:45px;transform:rotate(-24deg)}}
    .lnx-curve{{position:absolute;z-index:1;width:560px;height:560px;border:82px solid #A7E7EF;border-radius:50%;right:-390px;top:210px}}
    .lnx-product{{position:relative;z-index:3;width:min(760px,94%);height:min(575px,68vh);min-height:470px;background:#fff;border-radius:64px;overflow:hidden;box-shadow:0 28px 70px rgba(0,0,0,.25);display:grid;grid-template-columns:170px 1fr}}
    .lnx-side{{background:#0B2347;color:#fff;padding:24px 14px}}
    .lnx-side-logo{{font-size:17px;font-weight:850;margin:0 0 24px 8px;color:#fff}}.lnx-side-logo span{{color:#F4B814}}
    .lnx-side-row{{height:35px;padding:0 10px;border-radius:7px;display:flex;align-items:center;gap:9px;font-size:11px;color:#DCE7F5;margin-bottom:3px}}
    .lnx-side-row.active{{background:#15487A;color:#F4B814;font-weight:800}}
    .lnx-side-ico{{width:18px;text-align:center;color:#9EC7E9}}
    .lnx-app{{padding:28px 28px 22px;background:#fff;color:#14243E;overflow:hidden}}
    .lnx-app-top{{display:flex;align-items:center;justify-content:space-between;gap:16px}}
    .lnx-pill{{display:inline-flex;height:26px;padding:0 10px;align-items:center;border-radius:7px;background:#EAF2FF;color:#205E9A;font-size:10px;font-weight:900}}
    .lnx-open{{height:34px;padding:0 12px;border-radius:7px;background:#F4B814;color:#10213D;display:inline-flex;align-items:center;font-size:10px;font-weight:900}}
    .lnx-app h2{{font-size:20px;line-height:1.18;margin:15px 0 6px;color:#14243E}}
    .lnx-agency{{font-size:10px;color:#286092;font-weight:800;margin-bottom:8px}}
    .lnx-desc{{font-size:10px;line-height:1.4;color:#607086;margin-bottom:12px}}
    .lnx-meta{{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid #E2E8EF;border-radius:8px;overflow:hidden;margin-bottom:12px}}
    .lnx-meta div{{padding:8px 9px;border-right:1px solid #E2E8EF}}.lnx-meta div:last-child{{border-right:0}}
    .lnx-meta small{{display:block;color:#8B98AA;font-size:7px;margin-bottom:4px}}.lnx-meta strong{{font-size:8.5px;color:#36506F}}
    .lnx-table{{border:1px solid #DDE5EC;border-radius:8px;overflow:hidden}}
    .lnx-th,.lnx-tr{{display:grid;grid-template-columns:34px 1fr 70px 76px;align-items:center}}
    .lnx-th{{height:30px;background:#FAFBFC;color:#65758A;font-size:7px;font-weight:900;border-bottom:1px solid #E5EAF0}}
    .lnx-tr{{min-height:52px;border-bottom:1px solid #E8EDF2;color:#29415F;font-size:8px}}.lnx-tr:last-child{{border-bottom:0}}
    .lnx-th>div,.lnx-tr>div{{padding:0 8px}}
    .lnx-item{{display:flex;align-items:center;gap:8px}}.lnx-item-ico{{width:28px;height:28px;border-radius:5px;background:#E8EDF1;display:grid;place-items:center;color:#5C6C7C;font-size:14px}}
    .lnx-item strong{{display:block;font-size:8px;color:#1B3553;margin-bottom:2px}}.lnx-item small{{font-size:6.5px;color:#7D8A9C}}
    .lnx-total{{height:34px;display:flex;align-items:center;justify-content:flex-end;padding:0 12px;background:#FBFCFD;color:#315278;font-size:9px;font-weight:900}}
    @media(max-width:1180px){{
      .lnx-top-inner{{width:calc(100% - 46px)}}.lnx-brand img{{width:190px}}.lnx-hero{{grid-template-columns:1fr}}
      .lnx-copy{{min-height:600px;padding:70px 7vw}}.lnx-visual{{min-height:660px;padding:52px 5vw}}.lnx-product{{height:560px;min-height:0}}
    }}
    @media(max-width:700px){{
      .lnx-top{{height:72px}}.lnx-top-inner{{width:calc(100% - 26px)}}.lnx-brand img{{width:154px;max-height:44px}}.lnx-actions{{gap:8px}}.lnx-actions a{{height:38px;padding:0 12px;font-size:12px}}
      .lnx-copy{{min-height:auto;padding:54px 24px 60px}}.lnx-title{{font-size:40px;letter-spacing:-1.3px}}.lnx-sub{{font-size:17px}}.lnx-buttons{{gap:12px;margin-top:30px}}.lnx-buttons a{{width:100%;height:50px}}
      .lnx-visual{{min-height:500px;padding:36px 18px}}.lnx-product{{width:100%;height:430px;grid-template-columns:1fr;border-radius:38px}}.lnx-side{{display:none}}.lnx-app{{padding:20px 16px}}.lnx-app h2{{font-size:16px}}.lnx-meta{{grid-template-columns:1fr 1fr}}.lnx-meta div:nth-child(2){{border-right:0}}.lnx-th,.lnx-tr{{grid-template-columns:28px 1fr 54px}}.lnx-th>div:nth-child(4),.lnx-tr>div:nth-child(4){{display:none}}
    }}
    </style>
    <div class="lnx-page">
      <header class="lnx-top">
        <div class="lnx-top-inner">
          <a class="lnx-brand" href="#"><img src="{APPROVED_LOGO_DARK_DATA_URI}" alt="LicitaNexo"></a>
          <div class="lnx-actions"><a class="lnx-login" href="?auth=login">Login</a><a class="lnx-trial" href="?auth=request">Teste grátis</a></div>
        </div>
      </header>
      <main class="lnx-hero">
        <section class="lnx-copy">
          <h1 class="lnx-title">LicitaNexo, a plataforma completa para encontrar licitações com mais clareza e vender ao governo.</h1>
          <p class="lnx-sub">Encontre oportunidades, veja os itens da compra e organize sua participação em um só lugar, sem perder tempo abrindo edital por edital.</p>
          <div class="lnx-buttons"><a href="?auth=request">Teste grátis</a><a href="?auth=login">Acessar a plataforma</a></div>
        </section>
        <section class="lnx-visual">
          <div class="lnx-curve"></div>
          <div class="lnx-product">
            <aside class="lnx-side">
              <div class="lnx-side-logo">Licita<span>Nexo</span></div>
              <div class="lnx-side-row active"><span class="lnx-side-ico">⌕</span>Buscar licitações</div>
              <div class="lnx-side-row"><span class="lnx-side-ico">◇</span>Por Estado</div>
              <div class="lnx-side-row"><span class="lnx-side-ico">⌖</span>Por Cidade</div>
              <div class="lnx-side-row"><span class="lnx-side-ico">▣</span>Por Modalidade</div>
              <div class="lnx-side-row"><span class="lnx-side-ico">◎</span>Por site de disputa</div>
              <div class="lnx-side-row"><span class="lnx-side-ico">▽</span>Filtro avançado</div>
              <div class="lnx-side-row"><span class="lnx-side-ico">☆</span>Minha lista</div>
              <div class="lnx-side-row"><span class="lnx-side-ico">□</span>Calendário</div>
            </aside>
            <div class="lnx-app">
              <div class="lnx-app-top"><span class="lnx-pill">DISPENSA DE LICITAÇÃO</span><span class="lnx-open">Ver itens da compra</span></div>
              <h2>Aquisição de equipamentos e materiais para reabilitação e atendimento hospitalar</h2>
              <div class="lnx-agency">MUNICÍPIO DE GUARDA-MOR · MG</div>
              <div class="lnx-desc">Itens, quantidades e valores reunidos em uma única tela para apoiar sua decisão.</div>
              <div class="lnx-meta"><div><small>Modalidade</small><strong>Dispensa</strong></div><div><small>Processo</small><strong>DL 034/2024</strong></div><div><small>Publicado</small><strong>27/08/2024</strong></div><div><small>Itens</small><strong>6 itens</strong></div></div>
              <div class="lnx-table">
                <div class="lnx-th"><div>#</div><div>DESCRIÇÃO DO ITEM</div><div>QTD.</div><div>VALOR</div></div>
                <div class="lnx-tr"><div>1</div><div class="lnx-item"><span class="lnx-item-ico">◫</span><span><strong>Cadeira de rodas adulto</strong><small>Dobrável, em aço carbono</small></span></div><div>5</div><div>R$ 6.250</div></div>
                <div class="lnx-tr"><div>2</div><div class="lnx-item"><span class="lnx-item-ico">▱</span><span><strong>Cama hospitalar manual</strong><small>Com grades laterais</small></span></div><div>3</div><div>R$ 8.970</div></div>
                <div class="lnx-tr"><div>3</div><div class="lnx-item"><span class="lnx-item-ico">∥</span><span><strong>Muleta axilar</strong><small>Em alumínio regulável</small></span></div><div>10</div><div>R$ 1.800</div></div>
                <div class="lnx-tr"><div>4</div><div class="lnx-item"><span class="lnx-item-ico">Π</span><span><strong>Andador articulado</strong><small>Dobrável em alumínio</small></span></div><div>5</div><div>R$ 1.600</div></div>
                <div class="lnx-total">VALOR TOTAL ESTIMADO&nbsp;&nbsp; R$ 54.850,80</div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
    '''
    st.html(html)
