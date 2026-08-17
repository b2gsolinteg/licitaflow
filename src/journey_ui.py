from __future__ import annotations

import streamlit as st

from .journey import (
    add_custom_step,
    delete_custom_step,
    journey_progress,
    list_journey_steps,
    set_step_done,
    sync_automatic_completion,
)


def _refresh_fragment():
    try:
        st.rerun(scope="fragment")
    except Exception:
        st.rerun()


@st.fragment
def journey_workspace(db, company_id: str, opportunity):
    opportunity_id = opportunity["id"]
    auto = sync_automatic_completion(db, company_id, opportunity_id)
    steps = list_journey_steps(db, company_id, opportunity_id)
    progress = journey_progress(steps)

    st.subheader("Jornada da licitação")
    st.caption(
        "Use esta jornada como roteiro operacional. Algumas etapas são concluídas automaticamente "
        "quando o LicitaNexo detecta análise, cotação ou precificação prontas."
    )

    c1, c2, c3 = st.columns([1, 1, 2])
    c1.metric("Concluídas", f'{progress["done"]}/{progress["total"]}')
    c2.metric("Progresso", f'{progress["percent"]}%')
    status_bits = []
    if auto.get("analysis"):
        status_bits.append("análise realizada")
    if auto.get("suppliers"):
        status_bits.append("itens cotados")
    if auto.get("pricing"):
        status_bits.append("preços definidos")
    if auto.get("margin_positive"):
        status_bits.append("margem não negativa")
    c3.info("Automação: " + (" · ".join(status_bits) if status_bits else "aguardando dados"))
    st.progress(progress["ratio"])

    for step in steps:
        key = f'journey_step_{step["id"]}'
        current = bool(int(step.get("is_done") or 0))
        cols = st.columns([8, 1])
        checked = cols[0].checkbox(
            step.get("title") or "Etapa",
            value=current,
            key=key,
        )
        if checked != current:
            set_step_done(db, company_id, opportunity_id, step["id"], checked)
            _refresh_fragment()
        if str(step.get("step_key") or "").startswith("custom:"):
            if cols[1].button("🗑️", key=f'delete_journey_{step["id"]}', help="Excluir tarefa"):
                delete_custom_step(db, company_id, opportunity_id, step["id"])
                _refresh_fragment()

    try:
        legacy = db.list_checklist(company_id, opportunity_id)
    except Exception:
        legacy = []
    if legacy:
        with st.expander("Pendências detectadas pela análise do edital"):
            for item in legacy:
                title = str(item.get("title") or "Pendência").strip()
                done = bool(int(item.get("is_done") or item.get("done") or 0))
                st.write(f'{"✅" if done else "⚠️"} {title}')

    with st.expander("➕ Adicionar tarefa personalizada"):
        with st.form(
            f"journey_custom_{opportunity_id}",
            clear_on_submit=False,
            enter_to_submit=False,
        ):
            title = st.text_input(
                "Tarefa",
                placeholder="Ex.: solicitar nova cotação ao fornecedor; separar amostra...",
            )
            submitted = st.form_submit_button("Adicionar tarefa", type="primary", width="stretch")
            if submitted:
                try:
                    add_custom_step(db, company_id, opportunity_id, title)
                    st.success("Tarefa adicionada.")
                    _refresh_fragment()
                except ValueError as error:
                    st.warning(str(error))
