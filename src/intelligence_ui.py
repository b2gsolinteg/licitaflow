from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

from .analysis_engine import analyze_pages, extract_pdf_pages
from .ata_intelligence import PncpAtaClient, AtaExtractionError, extract_price_candidates
from .exports import catalog_excel, catalog_pdf
from .formatters import format_brl
from .pncp import PncpClient, PncpTemporaryError
from .public_prices import ComprasGovPriceClient, PublicPriceError, normalize_brand
from .usage import UsageLimitError


def ata_document_section(db, user, query):
    company_id = user["company_id"]
    with st.expander("Ler preços dentro de uma ata do PNCP", expanded=False):
        st.caption(
            "Cole o identificador da ata encontrado no PNCP ou envie o PDF baixado. "
            "O sistema apresenta candidatos para confirmação; nenhum preço é aceito automaticamente."
        )
        ata_id = st.text_input(
            "Identificador da ata PNCP",
            placeholder="Ex.: 13927801000300-1-000055/2026-000005",
        )
        uploaded = st.file_uploader("Ou envie a ata em PDF", type=["pdf"], key="ata_price_pdf")
        selected_document = None
        documents = st.session_state.get("ata_documents", [])
        if st.button("Localizar documentos da ata", disabled=not ata_id.strip()):
            try:
                with st.spinner("Consultando os arquivos oficiais da ata..."):
                    parsed, documents = PncpAtaClient().list_documents(ata_id)
                st.session_state.ata_documents = documents
                st.session_state.ata_parsed = parsed
            except AtaExtractionError as error:
                st.error(str(error))
        if documents:
            labels = {
                f'{doc.get("titulo") or doc.get("tipoDocumentoNome") or "Documento"} · '
                f'{doc.get("dataPublicacaoPncp") or "sem data"}': doc
                for doc in documents
            }
            selected_label = st.selectbox("Documento para leitura", list(labels))
            selected_document = labels[selected_label]
        can_extract = bool(uploaded or selected_document)
        if st.button("Extrair possíveis preços", type="primary", disabled=not can_extract or len(query.strip()) < 2):
            try:
                if uploaded:
                    pdf_bytes, source_url, published_at = uploaded.getvalue(), "", date.today().isoformat()
                else:
                    pdf_bytes, _, source_url = PncpAtaClient().download(selected_document)
                    published_at = selected_document.get("dataPublicacaoPncp")
                with st.spinner("Lendo o documento e procurando tabelas de preço..."):
                    candidates, stats = extract_price_candidates(
                        pdf_bytes, query, source_url=source_url, published_at=published_at,
                    )
                st.session_state.ata_price_candidates = candidates
                st.session_state.ata_price_stats = stats
            except AtaExtractionError as error:
                st.error(str(error))
        candidates = st.session_state.get("ata_price_candidates", [])
        stats = st.session_state.get("ata_price_stats", {})
        if stats.get("needs_ocr"):
            st.warning(
                "Este PDF parece ser apenas uma imagem. Ele precisará do módulo de OCR, "
                "previsto para a próxima etapa."
            )
        if candidates:
            st.write(
                f'{len(candidates)} candidato(s) encontrado(s) em {stats.get("pages", 0)} página(s).'
            )
            editor_rows = [{
                "Confirmar": row["confirm"], "Descrição": row["description"],
                "Preço unitário": row["homologated_unit_value"], "Unidade": row["unit"],
                "Fornecedor": row["supplier"], "Marca": row["brand"],
                "Página": row["page_number"], "Confiança": row["confidence"],
                "Trecho": row["evidence"],
            } for row in candidates]
            edited = st.data_editor(
                pd.DataFrame(editor_rows), use_container_width=True, hide_index=True,
                column_config={"Confirmar": st.column_config.CheckboxColumn(required=True)},
                disabled=["Página", "Confiança", "Trecho"], key="ata_price_editor",
            )
            if st.button("Salvar preços confirmados"):
                confirmed = []
                for index, edited_row in edited.iterrows():
                    if not bool(edited_row["Confirmar"]):
                        continue
                    original = dict(candidates[index])
                    original.update({
                        "description": edited_row["Descrição"],
                        "homologated_unit_value": edited_row["Preço unitário"],
                        "unit": edited_row["Unidade"], "supplier": edited_row["Fornecedor"],
                        "brand": edited_row["Marca"], "query": query,
                        "estimated_unit_value": None, "opportunity_id": None,
                        "catalog_code": "", "purchase_id": original.get("source_url") or ata_id,
                        "item_number": str(original.get("page_number") or ""),
                    })
                    confirmed.append(original)
                if confirmed:
                    db.save_price_references(company_id, query, confirmed)
                    st.success(f"{len(confirmed)} preço(s) revisado(s) foi(ram) salvo(s).")
                else:
                    st.info("Marque pelo menos um candidato como confirmado.")


def profile_page(db, user):
    company_id = user["company_id"]
    profile = db.get_company_profile(company_id)
    st.header("Passaporte de Prontidão")
    st.caption("A LicitaNexo usa este perfil para explicar quais exigências combinam com sua empresa.")
    with st.form("company_profile"):
        c1, c2 = st.columns(2)
        activity = c1.selectbox(
            "Atuação", ["Produtos", "Serviços", "Produtos e serviços"],
            index=["Produtos", "Serviços", "Produtos e serviços"].index(profile["activity_type"])
            if profile["activity_type"] in ["Produtos", "Serviços", "Produtos e serviços"] else 0,
        )
        states = c2.text_input("UFs atendidas", value=profile["service_states"], placeholder="PR, SC, SP")
        max_value = st.number_input(
            "Valor máximo de contrato que consegue atender", min_value=0.0,
            value=float(profile["max_contract_value"] or 0), step=1000.0,
        )
        st.markdown("#### Estrutura e preferências")
        a, b, c = st.columns(3)
        has_certificate = a.checkbox("Possui atestado técnico", bool(profile["has_technical_certificate"]))
        has_balance = a.checkbox("Possui balanço patrimonial", bool(profile["has_balance_sheet"]))
        has_manager = b.checkbox("Possui responsável técnico", bool(profile["has_technical_manager"]))
        accepts_srp = b.checkbox("Aceita Registro de Preços", bool(profile["accepts_price_registration"]))
        accepts_samples = c.checkbox("Consegue apresentar amostras", bool(profile["accepts_samples"]))
        accepts_visit = c.checkbox("Aceita visita técnica", bool(profile["accepts_site_visit"]))
        notes = st.text_area("Observações sobre capacidade, logística ou limitações", value=profile["notes"])
        if st.form_submit_button("Salvar passaporte", type="primary", use_container_width=True):
            db.save_company_profile(
                company_id, activity_type=activity, service_states=states.upper(),
                max_contract_value=max_value or None, has_technical_certificate=int(has_certificate),
                has_balance_sheet=int(has_balance), has_technical_manager=int(has_manager),
                accepts_price_registration=int(accepts_srp), accepts_samples=int(accepts_samples),
                accepts_site_visit=int(accepts_visit), notes=notes,
            )
            st.success("Passaporte atualizado. As próximas análises considerarão este perfil.")
            st.rerun()
    readiness = sum([
        bool(profile["has_technical_certificate"]), bool(profile["has_balance_sheet"]),
        bool(profile["has_technical_manager"]), bool(profile["accepts_samples"]),
        bool(profile["accepts_site_visit"]), bool(profile["service_states"]),
    ])
    st.progress(readiness / 6)
    st.caption(f"Prontidão cadastral inicial: {int(readiness * 100 / 6)}%. Este indicador não substitui a habilitação de cada edital.")


def _render_analysis(db, company_id, analysis_id):
    analysis, findings = db.get_analysis(company_id, analysis_id)
    if not analysis:
        return
    score = analysis["compatibility_score"]
    label = "Boa compatibilidade" if score >= 80 else "Exige atenção" if score >= 55 else "Possíveis impedimentos"
    st.subheader(f"Diagnóstico · {score}% · {label}")
    counts = {severity: sum(item["severity"] == severity for item in findings)
              for severity in ("Verde", "Amarelo", "Vermelho")}
    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Favoráveis", counts["Verde"])
    c2.metric("🟡 Atenções", counts["Amarelo"])
    c3.metric("🔴 Possíveis impedimentos", counts["Vermelho"])
    if not findings:
        st.info("Nenhum dos critérios monitorados foi localizado automaticamente. A leitura integral continua necessária.")
    for finding in findings:
        icon = {"Verde": "🟢", "Amarelo": "🟡", "Vermelho": "🔴"}[finding["severity"]]
        with st.expander(f'{icon} {finding["title"]} · página {finding["page_number"] or "?"}'):
            st.caption(finding["category"])
            if finding["evidence"]:
                st.info(finding["evidence"])
            st.write(f'**Ação recomendada:** {finding["recommended_action"]}')
    if analysis.get("opportunity_id") and findings:
        if st.button("Enviar ações para o checklist da Jornada", type="primary"):
            added = db.add_analysis_actions_to_checklist(company_id, analysis_id)
            st.success(f"{added} nova(s) ação(ões) adicionada(s) ao checklist.")
    st.warning("Diagnóstico de apoio. Confirme o edital, anexos e orientações profissionais antes de decidir.")


def analysis_page(db, user, usage=None):
    company_id = user["company_id"]
    st.header("Diagnóstico de Viabilidade")
    st.caption("Envie um PDF e receba uma leitura explicável, comparada ao Passaporte de Prontidão.")
    if usage is not None:
        usage_status = usage.analysis_status(company_id)
        if usage_status["limit"] > 0:
            st.caption(
                f'Análises neste mês: {usage_status["used"]}/{usage_status["limit"]} · '
                f'Restam {usage_status["remaining"]}.'
            )
        else:
            st.caption(f'Análises neste mês: {usage_status["used"]} · sem limite configurado.')
    opportunities = db.list_opportunities(company_id)
    labels = {row["id"]: f'{row["agency"] or "Órgão"} · {row["object"][:90]}' for row in opportunities}
    options = [None, *labels]
    selected = st.selectbox(
        "Vincular à oportunidade (recomendado)", options,
        format_func=lambda value: "Análise avulsa" if value is None else labels[value],
    )
    uploaded = st.file_uploader("Edital em PDF", type=["pdf"])
    if uploaded and st.button("Analisar compatibilidade", type="primary", use_container_width=True):
        try:
            if usage is not None:
                usage.assert_analysis_allowed(company_id)
            with st.spinner("Lendo o edital e procurando exigências..."):
                pages = extract_pdf_pages(uploaded.getvalue())
                profile = db.get_company_profile(company_id)
                score, findings = analyze_pages(pages, profile)
                analysis_id = db.save_edital_analysis(
                    company_id, selected, uploaded.name, score, len(pages), findings,
                )
                if usage is not None:
                    usage.record_analysis(
                        company_id, user.get("id", ""), uploaded.name, len(pages)
                    )
                st.session_state.last_analysis_id = analysis_id
            st.success("Análise concluída.")
        except UsageLimitError as error:
            st.warning(str(error))
        except ValueError as error:
            st.error(str(error))
        except Exception as error:
            st.error(f"Não foi possível analisar este PDF: {error}")
    analysis_id = st.session_state.get("last_analysis_id")
    if analysis_id:
        _render_analysis(db, company_id, analysis_id)
    history = db.list_analyses(company_id)
    if history:
        with st.expander("Histórico de análises"):
            chosen = st.selectbox(
                "Análise", [row["id"] for row in history],
                format_func=lambda value: next(
                    f'{row["filename"]} · {row["compatibility_score"]}% · {row["created_at"]}'
                    for row in history if row["id"] == value
                ),
            )
            if st.button("Abrir análise selecionada"):
                st.session_state.last_analysis_id = chosen
                st.rerun()


def agenda_page(db, user):
    company_id = user["company_id"]
    st.header("Agenda de Prazos")
    st.caption("Sessões, tarefas, documentos e compromissos da operação em uma única visão.")
    opportunities = db.list_opportunities(company_id)
    labels = {row["id"]: f'{row["agency"] or "Órgão"} · {row["object"][:60]}' for row in opportunities}
    with st.expander("Adicionar compromisso"):
        with st.form("new_calendar_event", clear_on_submit=True):
            title = st.text_input("Compromisso")
            c1, c2, c3 = st.columns(3)
            event_date = c1.date_input("Data", value=date.today())
            event_time = c2.time_input("Horário", value=time(9, 0))
            event_type = c3.selectbox("Tipo", ["Tarefa", "Sessão", "Documento", "Entrega", "Contrato", "Outro"])
            opportunity_id = st.selectbox(
                "Oportunidade", [None, *labels],
                format_func=lambda value: "Sem vínculo" if value is None else labels[value],
            )
            if st.form_submit_button("Adicionar à agenda", type="primary"):
                db.add_calendar_event(
                    company_id, title, datetime.combine(event_date, event_time).isoformat(),
                    event_type, opportunity_id,
                )
                st.rerun()
    c1, c2 = st.columns(2)
    start = c1.date_input("De", value=date.today(), key="agenda_start")
    end = c2.date_input("Até", value=date.today() + timedelta(days=30), key="agenda_end")
    events = db.list_agenda(company_id, start.isoformat(), end.isoformat())
    overdue = sum(str(event["event_at"])[:10] < date.today().isoformat()
                  and event["status"] != "Concluído" for event in events)
    m1, m2, m3 = st.columns(3)
    m1.metric("Eventos no período", len(events))
    m2.metric("Próximos 7 dias", sum(date.today().isoformat() <= str(e["event_at"])[:10]
                                      <= (date.today()+timedelta(days=7)).isoformat() for e in events))
    m3.metric("Atrasados", overdue)
    if events:
        frame = pd.DataFrame([{
            "Data": str(event["event_at"])[:16].replace("T", " "), "Tipo": event["event_type"],
            "Compromisso": event["title"], "Órgão": event.get("agency") or "",
            "Situação": event["status"], "Origem": event["source"],
        } for event in events])
        st.dataframe(frame, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum compromisso no período.")


def public_prices_page(db, user):
    company_id = user["company_id"]
    st.header("Laboratório de Preços (Beta)")
    st.warning(
        "Recurso experimental. Os resultados dependem das fontes oficiais e precisam ser "
        "conferidos no documento original antes de formar uma proposta."
    )
    st.caption(
        "Localize o código no catálogo, escolha o item correto e consulte preços praticados "
        "na fonte oficial — sem depender do Radar ou da Jornada."
    )
    c1, c2, c3, c4 = st.columns([3, 1.2, 1, 1.2])
    query = c1.text_input(
        "Produto ou código CATMAT/CATSER",
        placeholder="Ex.: água, pneu, uniforme ou 309107",
        help="Se o termo de referência informar o código, digite somente os números.",
    )
    kind = c2.selectbox("Tipo", ["Material", "Serviço"])
    states = ["Brasil inteiro", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
              "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS",
              "RO", "RR", "SC", "SP", "SE", "TO"]
    state = c3.selectbox("Estado", states)
    period_label = c4.selectbox(
        "Histórico", ["Últimos 6 meses", "Últimos 3 meses", "Últimos 12 meses", "Últimos 30 dias"],
    )
    period_days = {
        "Últimos 30 dias": 30, "Últimos 3 meses": 92,
        "Últimos 6 meses": 183, "Últimos 12 meses": 365,
    }
    price_start_date = date.today() - timedelta(days=period_days[period_label])

    client = ComprasGovPriceClient(timeout=45)
    if st.button("1. Localizar itens do catálogo", disabled=len(query.strip()) < 2):
        try:
            with st.spinner("Consultando o catálogo oficial..."):
                st.session_state.price_catalog_candidates = client.search_catalog(query, kind=kind)
                st.session_state.price_catalog_query = query
                st.session_state.price_catalog_kind = kind
        except PublicPriceError as error:
            st.session_state.price_catalog_candidates = []
            st.error(str(error))

    candidates = st.session_state.get("price_catalog_candidates", [])
    candidate_query = st.session_state.get("price_catalog_query", "")
    candidate_kind = st.session_state.get("price_catalog_kind", "")
    selected_labels = []
    label_map = {}
    if candidates and candidate_query == query and candidate_kind == kind:
        st.markdown(f"#### Sugestões encontradas para “{query}”")
        st.caption(
            "Escolha uma ou mais especificações. Exemplo: água em copo e galão de 20 litros "
            "ou pneus de aros diferentes devem ser pesquisados separadamente. "
            "A lista abaixo contém somente descrições com todos os termos pesquisados."
        )
        for candidate in candidates:
            group = candidate.get("group") or candidate.get("class") or "Material"
            catalog_label = "CATSER" if candidate["kind"] == "Serviço" else "CATMAT"
            label = f'{candidate["description"]} · {group} · {catalog_label} {candidate["code"]}'
            label_map[label] = candidate
        selected_labels = st.multiselect(
            "Itens encontrados", list(label_map),
            max_selections=10,
            help="Escolha preferencialmente um item por vez. O limite é de 10 códigos.",
        )
        if st.button("2. Consultar preços dos itens selecionados", type="primary",
                     disabled=not selected_labels):
            found, errors = [], []
            fetch_stats = {"processed": 0, "old": 0, "without_result": 0}
            progress = st.progress(0)
            for index, label in enumerate(selected_labels, start=1):
                candidate = label_map[label]
                try:
                    rows = client.fetch_prices(
                        candidate["code"], "" if state == "Brasil inteiro" else state,
                        kind=candidate["kind"], start_date=price_start_date.isoformat(),
                    )
                    for key in fetch_stats:
                        fetch_stats[key] += client.last_fetch_stats.get(key, 0)
                    for row in rows:
                        row["query"] = query
                    found.extend(rows)
                except PublicPriceError as error:
                    errors.append(str(error))
                progress.progress(index / len(selected_labels))
            progress.empty()
            if found:
                db.save_price_references(company_id, query, found)
                st.success(
                    f"{len(found)} preço(s) homologado(s) encontrado(s) desde "
                    f"{price_start_date.strftime('%d/%m/%Y')}. "
                    f"{fetch_stats['old']} registro(s) antigo(s) e "
                    f"{fetch_stats['without_result']} sem fornecedor/resultado foram descartados."
                )
            elif not errors:
                st.info(
                    "O código existe no catálogo, mas a fonte de preços não retornou compras "
                    "homologadas para ele. Tente Brasil inteiro, outro código equivalente ou "
                    "uma especificação mais utilizada."
                )
            if errors:
                st.warning(" | ".join(errors))
    elif query and candidate_query == query and candidate_kind == kind:
        st.info(
            "Nenhuma sugestão foi localizada no catálogo oficial. Tente somente o nome principal "
            "do produto, sem marca — por exemplo: água, pneu, camisa ou computador."
        )
    st.caption(
        "Descoberta de materiais: Portal CATMAT, com contingência no Compras.gov. "
        "Preços, fornecedores e marcas: API oficial do Compras.gov."
    )
    ata_document_section(db, user, query)

    references = db.list_price_references(
        company_id, query, start_date=price_start_date.isoformat(), actual_only=True,
    )
    if not references:
        st.info("Localize um item do catálogo para formar seu histórico independente de preços.")
        return
    units = sorted({row["unit"] for row in references if row["unit"]})
    selected_unit = None
    comparable = references
    if units:
        selected_unit = st.selectbox(
            "Unidade para comparação", units,
            help="Médias só devem comparar registros com a mesma unidade de fornecimento.",
        )
        comparable = [row for row in references if row["unit"] == selected_unit]
    values = [row["homologated_unit_value"] for row in comparable]
    values = [float(value) for value in values if value is not None]
    if values:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mínimo", format_brl(min(values)))
        c2.metric("Mediana", format_brl(float(pd.Series(values).median())))
        c3.metric("Média", format_brl(sum(values)/len(values)))
        c4.metric("Máximo", format_brl(max(values)))
    if len(units) > 1:
        st.warning(
            "Foram encontradas unidades diferentes: " + ", ".join(units) +
            ". Os indicadores acima consideram somente a unidade selecionada."
        )

    if values:
        st.markdown("#### Vale a pena disputar?")
        v1, v2, v3, v4 = st.columns(4)
        product_cost = v1.number_input("Custo do produto", min_value=0.0, step=0.01)
        freight = v2.number_input("Frete por unidade", min_value=0.0, step=0.01)
        taxes = v3.number_input("Impostos por unidade", min_value=0.0, step=0.01)
        desired_margin = v4.number_input("Margem desejada (%)", min_value=0.0, step=1.0, value=10.0)
        total_cost = product_cost + freight + taxes
        target_price = total_cost * (1 + desired_margin / 100)
        median_price = float(pd.Series(values).median())
        if product_cost > 0:
            if target_price <= median_price * 0.90:
                st.success(
                    f"COMPETITIVO · Seu preço-alvo é {format_brl(target_price)}, abaixo da "
                    f"mediana vencedora de {format_brl(median_price)}."
                )
            elif target_price <= median_price:
                st.warning(
                    f"MARGEM APERTADA · Seu preço-alvo é {format_brl(target_price)} e a "
                    f"mediana vencedora é {format_brl(median_price)}."
                )
            else:
                st.error(
                    f"ALTO RISCO · Seu preço-alvo é {format_brl(target_price)}, acima da "
                    f"mediana vencedora de {format_brl(median_price)}."
                )

    st.markdown("#### Marcas mais utilizadas")
    brand_rows = []
    for row in comparable:
        brand = row.get("brand_normalized") or normalize_brand(row.get("brand"))
        value = row["homologated_unit_value"]
        brand_rows.append({"Marca": brand, "Preço": value, "Fornecedor": row.get("supplier") or ""})
    brand_frame = pd.DataFrame(brand_rows)
    brand_summary = []
    for brand, group in brand_frame.groupby("Marca"):
        prices = pd.to_numeric(group["Preço"], errors="coerce").dropna()
        brand_summary.append({
            "Marca": brand, "Ocorrências": len(group),
            "Participação": f'{len(group) / len(brand_frame):.1%}',
            "Preço mediano": float(prices.median()) if len(prices) else None,
            "Fornecedores": group["Fornecedor"].replace("", pd.NA).nunique(),
        })
    st.dataframe(pd.DataFrame(brand_summary).sort_values("Ocorrências", ascending=False),
                 use_container_width=True, hide_index=True)

    st.markdown("#### Preços por item com comprovação")
    frame = pd.DataFrame([{
        "Item": row.get("item_number") or "", "Código": row.get("catalog_code") or "",
        "Descrição": row["description"], "Órgão": row["agency"], "UF": row["state"],
        "Quantidade": row["quantity"], "Unidade": row["unit"],
        "Preço unitário": row["homologated_unit_value"] if row["homologated_unit_value"] is not None
                         else row["estimated_unit_value"],
        "Fornecedor": row["supplier"], "CNPJ/CPF": row.get("supplier_tax_id") or "",
        "Marca": row.get("brand_normalized") or normalize_brand(row["brand"]),
        "Natureza": row.get("source_type") or "Homologado",
        "Data do resultado": row["published_at"],
        "Evidência oficial": row.get("source_url") or "",
    } for row in comparable])
    st.dataframe(frame, use_container_width=True, hide_index=True, column_config={
        "Evidência oficial": st.column_config.LinkColumn("Evidência oficial", display_text="Abrir fonte"),
    })
    excel = catalog_excel(references, user["company_name"], f"Preço: {query or 'histórico'}")
    st.download_button("Exportar preços para Excel", excel, "precos_publicos.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption("Valores públicos são referências. Confira unidade, especificação, data e fonte antes de precificar.")
