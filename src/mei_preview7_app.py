from __future__ import annotations

from html import escape

import streamlit as st

from src import mei_preview6_app as base


MEI_VERSION = "1.0 MEI Preview 7"
FLAG_BASE_URL = "https://raw.githubusercontent.com/akagabi/bandeira-dos-estados-do-brasil/master"


CSS7 = """
<style>
/* Preview 7: sidebar realmente alinhada à esquerda e mais compacta */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  gap: .18rem !important;
}
[data-testid="stSidebar"] img {
  margin-left: 0 !important;
  margin-right: auto !important;
}
[data-testid="stSidebar"] .ln-version,
[data-testid="stSidebar"] .ln-side-copy,
[data-testid="stSidebar"] .ln-side-group,
[data-testid="stSidebar"] .ln-plan {
  text-align: left !important;
  margin-left: 0 !important;
}
[data-testid="stSidebar"] div.stButton {
  margin: 0 !important;
  width: 100% !important;
}
[data-testid="stSidebar"] div.stButton > button {
  width: 100% !important;
  justify-content: flex-start !important;
  text-align: left !important;
  padding: .43rem .62rem !important;
  min-height: 2.35rem !important;
  font-size: 1.02rem !important;
  line-height: 1.15 !important;
}
[data-testid="stSidebar"] div.stButton > button > div,
[data-testid="stSidebar"] div.stButton > button div[data-testid="stMarkdownContainer"] {
  width: 100% !important;
  display: flex !important;
  justify-content: flex-start !important;
  align-items: center !important;
  text-align: left !important;
}
[data-testid="stSidebar"] div.stButton > button p {
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  text-align: left !important;
  font-size: 1.02rem !important;
  line-height: 1.15 !important;
}
[data-testid="stSidebar"] .ln-side-group {
  margin-top: .55rem !important;
  margin-bottom: .08rem !important;
}

/* Estado: bandeira pequena, nome alinhado e card mais comercial */
.ln-state-card {
  min-height: 110px !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: space-between !important;
  padding: .72rem .78rem .62rem !important;
  border-radius: 12px !important;
  background: #FFFFFF !important;
  border: 1px solid #DFE6EC !important;
  box-shadow: 0 3px 10px rgba(27,49,69,.025) !important;
}
.ln-state-title {
  display: flex;
  align-items: center;
  gap: .5rem;
  min-width: 0;
}
.ln-state-flag {
  width: 32px;
  height: 22px;
  object-fit: cover;
  border-radius: 3px;
  border: 1px solid #D9E1E7;
  box-shadow: 0 1px 2px rgba(20,45,67,.08);
  flex: 0 0 auto;
}
.ln-state-name {
  font-size: .94rem;
  font-weight: 850;
  line-height: 1.15;
  color: #173B55;
}
.ln-state-name .uf {
  color: #7A8997;
  font-weight: 750;
}
.ln-state-count {
  font-size: 1.5rem;
  line-height: 1;
  font-weight: 900;
  color: #11314D;
  margin-top: .48rem;
}
.ln-state-label {
  font-size: .7rem;
  color: #738493;
  margin-top: .12rem;
}

/* Corrige contraste dos botões secundários da área principal */
[data-testid="stAppViewContainer"] div.stButton > button[kind="secondary"] {
  background: #FFFFFF !important;
  color: #21465F !important;
  border: 1px solid #D7E1E8 !important;
  box-shadow: none !important;
}
[data-testid="stAppViewContainer"] div.stButton > button[kind="secondary"]:hover {
  background: #F7FAFB !important;
  color: #0B6F61 !important;
  border-color: #BFDAD4 !important;
}
/* Reaplica visual próprio da sidebar depois da regra geral acima */
[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
  background: transparent !important;
  border: 1px solid transparent !important;
  color: #27465D !important;
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
  background: #EAF7F4 !important;
  border: 1px solid #CDE9E3 !important;
  border-left: 4px solid #0F8F7B !important;
  color: #123F39 !important;
}
</style>
"""


def _sidebar():
    with st.sidebar:
        if base.LOGO_PATH.exists():
            st.image(str(base.LOGO_PATH), width=154)
        st.markdown(f'<div class="ln-version">● {MEI_VERSION}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="ln-side-copy">Descubra o que o governo compra e encontre oportunidades sem precisar escolher um nicho antes.</div>',
            unsafe_allow_html=True,
        )

        current = st.session_state.mei_section
        explore = [
            "🏠  Início",
            "🔎  Buscar editais",
            "📍  Por localização",
            "📋  Por modalidade",
            "🔥  Em destaque",
        ]
        personal = ["⭐  Salvos", "🔔  Radar"]
        canonical = {
            "🏠  Início": "🏠 Início",
            "🔎  Buscar editais": "🔎 Buscar editais",
            "📍  Por localização": "📍 Por localização",
            "📋  Por modalidade": "📋 Por modalidade",
            "🔥  Em destaque": "🔥 Em destaque",
            "⭐  Salvos": "⭐ Salvos",
            "🔔  Radar": "🔔 Radar",
        }

        st.markdown('<div class="ln-side-group">Explorar</div>', unsafe_allow_html=True)
        for index, label in enumerate(explore):
            target = canonical[label]
            if st.button(
                label,
                key=f"p7_nav_explore_{index}",
                type="primary" if current == target else "secondary",
                width="stretch",
            ):
                base._go(target)

        st.markdown('<div class="ln-side-group">Minha área</div>', unsafe_allow_html=True)
        for index, label in enumerate(personal):
            target = canonical[label]
            if st.button(
                label,
                key=f"p7_nav_personal_{index}",
                type="primary" if current == target else "secondary",
                width="stretch",
            ):
                base._go(target)

        st.markdown(
            '<div class="ln-plan">LicitaNexo MEI<strong>R&#36; 29,90/mês</strong>'
            '<b>Descubra → avalie → salve.</b><br>'
            'Itens oficiais do PNCP e inteligência de preço quando você decidir avançar.</div>',
            unsafe_allow_html=True,
        )
    return current


def _home_page():
    counts = base._state_counts()
    total = sum(int(counts.get(uf, 0)) for uf in base.BRAZIL_STATES)
    active_states = sum(1 for uf in base.BRAZIL_STATES if int(counts.get(uf, 0)) > 0)
    top_uf = max(base.BRAZIL_STATES, key=lambda uf: int(counts.get(uf, 0))) if base.BRAZIL_STATES else "--"

    st.markdown(
        f'<div class="ln-page-head"><div><h1>Licitações abertas no Brasil</h1>'
        f'<p>Comece explorando por Estado. Você não precisa saber o que quer vender para encontrar oportunidades.</p>'
        f'</div><div class="ln-page-chip">Plano MEI · R&#36; 29,90/mês</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            f'<div class="ln-kpis">'
            f'<div class="ln-kpi"><small>Oportunidades abertas</small><strong>{total:,}</strong><span>na base atual</span></div>'
            f'<div class="ln-kpi"><small>Estados com oportunidades</small><strong>{active_states}</strong><span>UFs com editais abertos</span></div>'
            f'<div class="ln-kpi"><small>Maior volume agora</small><strong>{top_uf}</strong><span>{int(counts.get(top_uf, 0))} oportunidade(s)</span></div>'
            f'</div>'
        ).replace(",", "."),
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ln-section-title">Explore por Estado</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ln-section-sub">Clique em um Estado para ver as oportunidades abertas e os itens publicados no PNCP.</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for index, uf in enumerate(base.BRAZIL_STATES):
        with cols[index % 3]:
            count = int(counts.get(uf, 0))
            name = base.UF_NAMES.get(uf, uf)
            flag_url = f"{FLAG_BASE_URL}/{uf.lower()}.svg"
            st.markdown(
                f'<div class="ln-state-card">'
                f'<div class="ln-state-title">'
                f'<img class="ln-state-flag" src="{flag_url}" alt="Bandeira de {escape(name)}" loading="lazy">'
                f'<div class="ln-state-name">{escape(name)} <span class="uf">({uf})</span></div>'
                f'</div>'
                f'<div><div class="ln-state-count">{count}</div>'
                f'<div class="ln-state-label">licitação(ões) aberta(s)</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "Ver oportunidades",
                key=f"p7_home_state_{uf}",
                width="stretch",
            ):
                base._set_state_and_search(uf)


def main():
    st.markdown(base.CSS, unsafe_allow_html=True)
    st.markdown(CSS7, unsafe_allow_html=True)
    base._init_state()
    section = _sidebar()

    if section == "🏠 Início":
        _home_page()
    elif section == "🔎 Buscar editais":
        base._search_page()
    elif section == "📍 Por localização":
        base._location_page()
    elif section == "📋 Por modalidade":
        base._modality_page()
    elif section == "🔥 Em destaque":
        base._highlight_page()
    elif section == "⭐ Salvos":
        base._saved_page()
    else:
        base._radar_page()
