from datetime import datetime, date, time

import streamlit as st

from .formatters import format_brl
from .sources import pncp_official_url, source_label, opportunity_source_and_portal
from .analysis_engine import analyze_essential_pages, extract_pdf_pages
from .exports import saved_editals_excel, saved_editals_pdf
from .pricing_ui import pricing_workspace
from .company_ui import render_document_readiness


ESSENTIAL_STAGES = ["Salvo", "Analisando", "Vou participar", "Encerrado"]
_STAGE_TO_DB = {
    "Salvo": "Nova oportunidade",
    "Analisando": "Em análise",
    "Vou participar": "Decisão",
    "Encerrado": "Arquivada",
}
_DB_TO_STAGE = {value: key for key, value in _STAGE_TO_DB.items()}
_DB_TO_STAGE.update({"Preparação": "Vou participar", "Proposta pronta": "Vou participar", "Proposta enviada": "Vou participar", "Ganha": "Encerrado", "Perdida": "Encerrado"})


def _format_datetime(value):
    if not value:
        return "Não informada"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y às %H:%M")
    except (TypeError, ValueError):
        return str(value).replace("T", " ")[:16]


def pipeline_page(db, user):
    company_id = user["company_id"]
    selected = st.session_state.get("pipeline_opportunity_id")
    if selected:
        opportunity = db.get_opportunity(company_id, selected)
        if opportunity:
            opportunity_detail(db, company_id, opportunity)
            return
        st.session_state.pop("pipeline_opportunity_id", None)

    st.header("⭐ Meus Editais")
    st.caption("Salve o que interessa e acompanhe em um pipeline simples. O LicitaNexo não quer virar seu ERP.")

    with st.expander("➕ Cadastrar edital manualmente"):
        st.caption("Use quando o edital não tiver sido localizado na busca do LicitaNexo.")
        with st.form("manual_opportunity", clear_on_submit=True):
            agency = st.text_input("Órgão / entidade")
            obj = st.text_area("Objeto")
            c1, c2, c3 = st.columns(3)
            city = c1.text_input("Município")
            state = c2.text_input("UF", max_chars=2)
            modality = c3.text_input("Modalidade")
            d1, d2 = st.columns(2)
            certame_date = d1.date_input("Data do certame", value=None)
            certame_time = d2.time_input("Horário", value=time(9, 0))
            source_url = st.text_input("Link do edital (opcional)")
            if st.form_submit_button("Cadastrar em Meus Editais", type="primary", width="stretch"):
                if not agency.strip() or not obj.strip():
                    st.warning("Informe pelo menos o órgão e o objeto do edital.")
                else:
                    certame_at = datetime.combine(certame_date, certame_time).isoformat(timespec="minutes") if certame_date else None
                    db.add_manual_opportunity(
                        company_id, agency.strip(), obj.strip(), city.strip(), state.strip().upper(),
                        modality.strip(), certame_at=certame_at, source_url=source_url.strip(),
                    )
                    st.success("Edital cadastrado em Meus Editais.")
                    st.rerun()

    all_rows = db.pipeline_summaries(company_id, "")
    export_rows = []
    for export_row in all_rows:
        export_item = dict(export_row)
        export_item["stage_display"] = _DB_TO_STAGE.get(export_item.get("stage"), "Salvo")
        details = db.get_details(company_id, export_item["id"]) or {}
        export_item["notes"] = details.get("notes") or ""
        if not export_item.get("certame_at"):
            export_item["certame_at"] = details.get("certame_at")
        export_rows.append(export_item)

    if export_rows:
        e1, e2 = st.columns(2)
        e1.download_button(
            "📊 Exportar todos para Excel",
            saved_editals_excel(export_rows, user.get("company_name") or ""),
            "meus_editais_licitanexo.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
        e2.download_button(
            "📄 Exportar todos para PDF",
            saved_editals_pdf(export_rows, user.get("company_name") or ""),
            "meus_editais_licitanexo.pdf",
            "application/pdf",
            width="stretch",
        )

    c1, c2 = st.columns([3, 2])
    search = c1.text_input("Buscar nos meus editais", placeholder="Órgão ou objeto")
    status_filter = c2.selectbox("Status", ["Todos", *ESSENTIAL_STAGES])
    rows = db.pipeline_summaries(company_id, search)
    if status_filter != "Todos":
        rows = [row for row in rows if _DB_TO_STAGE.get(row.get("stage"), "Salvo") == status_filter]

    if not rows:
        st.info("Nenhum edital salvo aqui. Use Buscar Editais e salve somente o que merece sua atenção.")
        return

    for row in rows:
        status = _DB_TO_STAGE.get(row.get("stage"), "Salvo")
        with st.container(border=True):
            left, right = st.columns([5, 1.2], vertical_alignment="center")
            left.markdown(f"### {row.get('agency') or 'Órgão não informado'}")
            left.write(row.get("object") or "Objeto não informado")
            certame_text = _format_datetime(row.get("certame_at")) if row.get("certame_at") else "Certame não informado"
            left.caption(
                f"{status} · {certame_text} · {row.get('modality') or 'Modalidade não informada'} · "
                f"{row.get('city') or 'Município não informado'}/{row.get('state') or '--'}"
            )
            if right.button("Abrir", key=f"open_{row['id']}", type="primary", width="stretch"):
                st.session_state.pipeline_opportunity_id = row["id"]
                st.rerun()


def opportunity_detail(db, company_id, opportunity):
    db.ensure_opportunity_workspace(company_id, opportunity["id"])
    details = db.get_details(company_id, opportunity["id"])

    if st.button("← Voltar aos meus editais"):
        st.session_state.pop("pipeline_opportunity_id", None)
        st.rerun()

    title, status_col = st.columns([4, 1.5], vertical_alignment="center")
    title.header(opportunity.get("agency") or "Órgão não informado")
    current_status = _DB_TO_STAGE.get(opportunity.get("stage"), "Salvo")
    status = status_col.selectbox("Status", ESSENTIAL_STAGES, index=ESSENTIAL_STAGES.index(current_status))
    if status != current_status:
        db.update_stage(company_id, opportunity["id"], _STAGE_TO_DB[status])
        st.rerun()

    st.write(opportunity.get("object") or "Objeto não informado")
    source_name, portal_label = opportunity_source_and_portal(
        opportunity.get("source_name"), opportunity.get("source_channel"), opportunity.get("source_url")
    )
    st.caption(f"**Fonte:** {source_name} · **Portal de disputa:** {portal_label}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Valor estimado", format_brl(opportunity.get("estimated_value")))
    c2.metric("Fim das propostas", _format_datetime(opportunity.get("closing_at")))
    c3.metric("Data do certame", _format_datetime(details.get("certame_at")))

    with st.expander("📅 Informar ou alterar data do certame", expanded=not bool(details.get("certame_at"))):
        current_certame = details.get("certame_at")
        try:
            parsed_certame = datetime.fromisoformat(str(current_certame).replace("Z", "+00:00")) if current_certame else None
        except (TypeError, ValueError):
            parsed_certame = None
        with st.form(f"certame_form_{opportunity['id']}"):
            d1, d2 = st.columns(2)
            certame_date = d1.date_input("Data", value=parsed_certame.date() if parsed_certame else date.today())
            certame_time = d2.time_input("Horário", value=parsed_certame.time().replace(second=0, microsecond=0) if parsed_certame else time(9, 0))
            if st.form_submit_button("Salvar data do certame", type="primary", width="stretch"):
                db.update_details(
                    company_id, opportunity["id"],
                    certame_at=datetime.combine(certame_date, certame_time).isoformat(timespec="minutes"),
                )
                st.success("Data do certame salva.")
                st.rerun()

    official = pncp_official_url(opportunity.get("pncp_control_number"))
    source_url = str(opportunity.get("source_url") or "")
    has_portal = source_url.startswith(("http://", "https://"))
    if has_portal and official:
        l1, l2 = st.columns(2)
        l1.link_button("🌐 Ir para o portal de disputa", source_url, type="primary", width="stretch")
        l2.link_button("📄 Ver publicação no PNCP", official, width="stretch")
    elif has_portal:
        st.link_button("🌐 Ir para o portal de disputa", source_url, type="primary", width="stretch")
    elif official:
        st.link_button("📄 Ver publicação no PNCP", official, type="primary", width="stretch")
    else:
        st.warning("Não foi possível montar um link oficial desta oportunidade.")

    summary, pricing, analysis = st.tabs(["Resumo", "💰 Precificação", "Análise do edital"])
    with summary:
        with st.form(f"essential_summary_{opportunity['id']}"):
            notes = st.text_area("Minhas anotações", value=details.get("notes") or "", height=140)
            if st.form_submit_button("Salvar anotação", type="primary"):
                db.update_details(company_id, opportunity["id"], notes=notes)
                st.success("Anotação salva.")
    with pricing:
        pricing_workspace(db, company_id, opportunity)
    with analysis:
        edital_analysis_tab(db, company_id, opportunity)

    with st.expander("Mais ações"):
        confirm = st.checkbox("Confirmar remoção de Meus Editais", key=f"confirm_delete_{opportunity['id']}")
        if st.button("Remover", disabled=not confirm, key=f"delete_{opportunity['id']}"):
            db.delete_opportunity(company_id, opportunity["id"])
            st.session_state.pop("pipeline_opportunity_id", None)
            st.rerun()


def edital_analysis_tab(db, company_id, opportunity):
    st.subheader("Entenda o edital")
    st.caption("Envie o PDF para localizar objeto, itens/quantidades/preços, documentação e pontos de atenção. Sem nota de aderência.")
    uploaded = st.file_uploader("Edital em PDF", type=["pdf"], key=f"edital_pdf_{opportunity['id']}")
    if uploaded and st.button("Analisar edital", type="primary", width="stretch", key=f"analyze_{opportunity['id']}"):
        try:
            with st.spinner("Lendo o edital..."):
                pages = extract_pdf_pages(uploaded.getvalue())
                object_text, required_documents, alerts, findings = analyze_essential_pages(pages)
                findings = [f for f in findings if f.get("category") != "Objeto"]
                findings.insert(0, {
                    "severity": "Verde", "category": "Objeto", "title": "Objeto",
                    "evidence": opportunity.get("object") or object_text or "Objeto não identificado automaticamente.",
                    "page_number": None,
                    "recommended_action": "Confira a descrição completa no edital e anexos.",
                })
                analysis_id = db.save_edital_analysis(company_id, opportunity["id"], uploaded.name, 0, len(pages), findings)
                st.session_state[f"analysis_{opportunity['id']}"] = analysis_id
            st.success("Análise concluída.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"Não foi possível analisar este PDF: {error}")

    analyses = db.list_analyses(company_id, opportunity["id"])
    if not analyses:
        st.info("Nenhuma análise realizada para este edital.")
        return
    selected_id = st.selectbox(
        "Análises salvas", [row["id"] for row in analyses],
        format_func=lambda value: next(f"{row['filename']} · {str(row['created_at'])[:16]}" for row in analyses if row["id"] == value),
        key=f"analysis_history_{opportunity['id']}",
    )
    analysis, findings = db.get_analysis(company_id, selected_id)
    if not analysis:
        return
    object_findings = [f for f in findings if f.get("category") == "Objeto"]
    item_price_findings = [f for f in findings if f.get("category") == "Itens e preços"]
    document_findings = [f for f in findings if f.get("category") == "Documentação"]
    attention_findings = [f for f in findings if f.get("category") == "Ponto de atenção"]

    st.markdown("#### Objeto")
    st.write((object_findings[0].get("evidence") if object_findings else opportunity.get("object")) or "Objeto não identificado.")
    st.markdown("#### Itens, quantidades e preços")
    if item_price_findings:
        for item in item_price_findings:
            page = f" · pág. {item['page_number']}" if item.get("page_number") else ""
            st.markdown(f"**Trecho identificado{page}**")
            st.write(item.get("evidence") or "")
    else:
        st.info("Não consegui identificar com segurança uma tabela de quantidades e preços no texto do PDF. Confira o Termo de Referência/anexos.")

    st.markdown("#### Documentação necessária")
    if document_findings:
        for item in document_findings:
            page = f" · pág. {item['page_number']}" if item.get("page_number") else ""
            st.write(f"• **{item.get('title') or 'Documento'}**{page}")
            if item.get("evidence"):
                st.caption(item["evidence"])
    else:
        st.info("Nenhuma exigência documental das regras atuais foi localizada automaticamente. Confira a habilitação e os anexos.")
    render_document_readiness(db, company_id, opportunity["id"], document_findings)
    if attention_findings:
        with st.expander("Outros pontos de atenção"):
            for item in attention_findings:
                page = f" · pág. {item['page_number']}" if item.get("page_number") else ""
                st.write(f"• **{item.get('title') or 'Atenção'}**{page}")
                if item.get("evidence"):
                    st.write(item["evidence"])
    st.warning("Análise de apoio. Confirme sempre o edital e seus anexos.")

