from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st
from .suppliers_ui import supplier_directory_page

from .company_intelligence import (
    document_readiness,
    get_company_document_upload,
    get_extended_profile,
    profile_search_ready,
    save_company_document_upload,
    save_extended_profile,
)


def _date_or_none(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return None


def _csv_states(value):
    return [
        item.strip().upper()
        for item in str(value or "").replace(";", ",").split(",")
        if len(item.strip()) == 2
    ]


def company_page(db, user):
    company_id = user["company_id"]
    profile = get_extended_profile(db, company_id)

    st.header("🏢 Minha Empresa")
    st.caption(
        "Ensine o LicitaNexo sobre sua empresa uma vez. Esse perfil pode priorizar editais, "
        "apoiar a análise documental e reduzir pesquisas manuais."
    )

    section = st.radio(
        "Área da empresa",
        ["Perfil e Cartão CNPJ", "Documentos", "Fornecedores", "Como o Radar usa meu perfil"],
        horizontal=True,
        label_visibility="collapsed",
        key="company_workspace_section",
    )

    if section == "Perfil e Cartão CNPJ":
        st.markdown("### Cartão CNPJ")
        st.caption(
            "Envie o Cartão CNPJ em PDF ou imagem. Em PDF com texto, o LicitaNexo tenta preencher "
            "CNPJ, razão social, nome fantasia e CNAEs automaticamente. Você sempre pode revisar os dados."
        )
        uploaded = st.file_uploader(
            "Cartão CNPJ",
            type=["pdf", "png", "jpg", "jpeg"],
            key="company_cnpj_card",
            help="Tamanho máximo usado pelo LicitaNexo: 4 MB.",
        )
        if uploaded is not None and st.button(
            "Ler e salvar Cartão CNPJ", type="primary", width="stretch", key="company_cnpj_upload_button"
        ):
            try:
                result = save_company_document_upload(
                    db, company_id, "Cartão CNPJ", uploaded.name,
                    uploaded.type or "application/octet-stream", uploaded.getvalue(),
                )
                detected = {
                    key: value for key, value in {
                        "cnpj": result.get("cnpj"),
                        "legal_name": result.get("legal_name"),
                        "trade_name": result.get("trade_name"),
                        "cnaes": result.get("cnaes"),
                    }.items() if str(value or "").strip()
                }
                if detected:
                    save_extended_profile(
                        db, company_id,
                        excluded_keywords=profile.get("excluded_keywords") or "",
                        profile_search_enabled=bool(profile.get("profile_search_enabled", 1)),
                        **detected,
                    )
                    st.success("Cartão CNPJ salvo e dados identificados aplicados ao perfil. Revise abaixo.")
                elif result.get("automatic_extraction"):
                    st.success("Cartão CNPJ salvo. Revise e complete os dados abaixo.")
                else:
                    st.info(
                        "Imagem salva. A leitura automática depende de texto extraível; complete os dados manualmente abaixo."
                    )
                st.rerun()
            except Exception as error:
                st.error(f"Não foi possível processar o Cartão CNPJ: {error}")

        stored_card = get_company_document_upload(db, company_id, "Cartão CNPJ")
        if stored_card:
            c1, c2 = st.columns([3, 1])
            c1.success(f'Cartão CNPJ salvo: {stored_card.get("file_name") or "arquivo"}')
            c2.download_button(
                "Baixar arquivo",
                stored_card["content"],
                file_name=stored_card.get("file_name") or "cartao-cnpj",
                mime=stored_card.get("mime_type") or "application/octet-stream",
                width="stretch",
            )

        st.divider()
        st.markdown("### O que sua empresa vende e executa")
        st.caption(
            "Não dependa apenas do CNAE. Descreva com linguagem comercial o que vocês realmente fornecem; "
            "isso melhora a aderência dos editais."
        )
        profile = get_extended_profile(db, company_id)
        with st.form("company_intelligence_profile"):
            c1, c2 = st.columns(2)
            legal_name = c1.text_input("Razão social", value=profile.get("legal_name") or user.get("company_name") or "")
            trade_name = c2.text_input("Nome fantasia", value=profile.get("trade_name") or "")
            c3, c4 = st.columns(2)
            cnpj = c3.text_input("CNPJ", value=profile.get("cnpj") or "", placeholder="00.000.000/0000-00")
            activity_type = c4.selectbox(
                "Atuação principal", ["Produtos", "Serviços", "Produtos e serviços"],
                index=["Produtos", "Serviços", "Produtos e serviços"].index(
                    profile.get("activity_type") if profile.get("activity_type") in {"Produtos", "Serviços", "Produtos e serviços"} else "Produtos"
                ),
            )
            cnaes = st.text_area(
                "CNAEs / atividades formais",
                value=profile.get("cnaes") or "",
                height=120,
                placeholder="Um CNAE/atividade por linha, ou cole o conteúdo do Cartão CNPJ.",
            )
            offerings = st.text_area(
                "Produtos e serviços que sua empresa realmente fornece",
                value=profile.get("offerings") or "",
                height=150,
                placeholder="Ex.: papel A4, material de limpeza hospitalar, EPIs, manutenção de ar-condicionado...",
            )
            procurement_interests = st.text_area(
                "Oportunidades que mais interessam",
                value=profile.get("procurement_interests") or "",
                height=100,
                placeholder="Ex.: fornecimento recorrente de papelaria; contratos de manutenção preventiva...",
            )
            k1, k2 = st.columns(2)
            interest_keywords = k1.text_area(
                "Palavras-chave prioritárias",
                value=profile.get("interest_keywords") or "",
                height=100,
                placeholder="Separe por vírgula: luvas nitrílicas, álcool 70, papel A4",
            )
            excluded_keywords = k2.text_area(
                "Palavras que não interessam",
                value=profile.get("excluded_keywords") or "",
                height=100,
                placeholder="Separe por vírgula: obra pesada, combustível...",
            )
            brands = st.text_input(
                "Marcas / linhas que trabalha (opcional)",
                value=profile.get("brands") or "",
                placeholder="Ex.: 3M, Dell, Tramontina",
            )
            s1, s2, s3 = st.columns(3)
            service_states = s1.text_input(
                "UFs onde atende",
                value=profile.get("service_states") or "",
                placeholder="SP, PR, SC",
                help="Deixe vazio se atende o Brasil inteiro.",
            )
            max_contract_value = s2.number_input(
                "Maior contrato desejado (R$)", min_value=0.0,
                value=float(profile.get("max_contract_value") or 0), step=1000.0,
                help="0 = sem limite para o ranqueamento.",
            )
            desired_margin = s3.number_input(
                "Margem desejada (%)", min_value=0.0, max_value=100.0,
                value=float(profile.get("desired_margin") or 15), step=1.0,
            )
            use_profile = st.checkbox(
                "Usar este perfil para priorizar editais na busca",
                value=bool(int(profile.get("profile_search_enabled") if profile.get("profile_search_enabled") is not None else 1)),
            )
            if st.form_submit_button("Salvar perfil da empresa", type="primary", width="stretch"):
                try:
                    save_extended_profile(
                        db, company_id,
                        legal_name=legal_name.strip(), trade_name=trade_name.strip(), cnpj=cnpj.strip(),
                        activity_type=activity_type, cnaes=cnaes.strip(), offerings=offerings.strip(),
                        procurement_interests=procurement_interests.strip(),
                        interest_keywords=interest_keywords.strip(), brands=brands.strip(),
                        service_states=", ".join(_csv_states(service_states)),
                        max_contract_value=None if max_contract_value <= 0 else max_contract_value,
                        desired_margin=desired_margin,
                        excluded_keywords=excluded_keywords.strip(), profile_search_enabled=use_profile,
                    )
                    st.session_state.pop("radar_search_criteria", None)
                    st.success("Perfil empresarial salvo. O Radar já pode usar essas informações.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

        refreshed = get_extended_profile(db, company_id)
        if profile_search_ready(refreshed):
            st.success("Perfil pronto para o Radar de aderência.")
        else:
            st.warning("Preencha ao menos produtos/serviços, interesses, palavras-chave ou CNAEs para ativar a aderência.")

    elif section == "Documentos":
        st.markdown("### Cofre documental da empresa")
        st.caption(
            "Mantenha situação e validade dos documentos essenciais. Na análise de um edital, o LicitaNexo cruza "
            "as exigências reconhecidas com este cadastro."
        )
        documents = db.list_company_documents(company_id)
        frame = pd.DataFrame([{
            "Documento": row.get("document_type"),
            "Aplicável": row.get("applicable") or "Não informado",
            "Situação": row.get("status") or "Não informado",
            "Validade": _date_or_none(row.get("expiry_date")),
            "Emissor": row.get("issuer") or "",
            "Observações": row.get("notes") or "",
        } for row in documents])
        edited = st.data_editor(
            frame,
            hide_index=True,
            width="stretch",
            disabled=["Documento"],
            column_config={
                "Aplicável": st.column_config.SelectboxColumn(
                    options=["Sim", "Não", "Não informado"], required=True,
                ),
                "Situação": st.column_config.SelectboxColumn(
                    options=["Válido", "Vencido", "Em renovação", "Não possui", "Não se aplica", "Não informado"],
                    required=True,
                ),
                "Validade": st.column_config.DateColumn(format="DD/MM/YYYY"),
            },
            key="company_documents_editor",
        )
        if st.button("Salvar documentos", type="primary", width="stretch", key="save_company_documents"):
            payload = []
            for _, row in edited.iterrows():
                expiry = row.get("Validade")
                payload.append({
                    "document_type": row.get("Documento"),
                    "applicable": row.get("Aplicável"),
                    "status": row.get("Situação"),
                    "expiry_date": expiry.isoformat() if hasattr(expiry, "isoformat") else (str(expiry)[:10] if expiry else None),
                    "issuer": row.get("Emissor") or "",
                    "notes": row.get("Observações") or "",
                })
            db.save_company_documents(company_id, payload)
            st.success("Documentos atualizados.")
            st.rerun()

        with st.expander("Adicionar outro documento"):
            with st.form("add_company_document_form", clear_on_submit=True):
                document_name = st.text_input("Nome do documento")
                if st.form_submit_button("Adicionar"):
                    try:
                        db.add_company_document(company_id, document_name)
                        st.rerun()
                    except ValueError as error:
                        st.warning(str(error))

    elif section == "Fornecedores":
        supplier_directory_page(db, company_id)

    else:
        st.markdown("### O perfil não esconde oportunidades")
        st.write(
            "Quando a opção de aderência está ligada, o LicitaNexo mantém os filtros escolhidos pelo usuário e "
            "ordena os resultados por compatibilidade com produtos, serviços, CNAEs, interesses, palavras-chave, "
            "UFs atendidas e limite de contrato. Editais com termos excluídos recebem aderência zero."
        )
        st.info(
            "A nota é uma priorização operacional, não uma decisão jurídica ou garantia de habilitação. "
            "O edital e seus anexos continuam sendo a fonte final."
        )


def render_document_readiness(db, company_id, opportunity_id, findings):
    readiness = document_readiness(db.list_company_documents(company_id), findings or [])
    if not readiness:
        return
    st.markdown("#### Seu checklist documental")
    icons = {
        "ready": "✅", "expiring": "⚠️", "expired": "🔴", "missing": "🔴", "review": "⚠️",
    }
    for item in readiness:
        st.write(f'{icons.get(item["state"], "⚠️")} **{item["document_type"]}** — {item["label"]}')
    pending = [item for item in readiness if item["state"] in {"missing", "expired", "expiring", "review"}]
    if pending and st.button(
        "Adicionar pendências documentais ao checklist",
        key=f"document_readiness_checklist_{opportunity_id}", width="stretch",
    ):
        current = {row.get("title") for row in db.list_checklist(company_id, opportunity_id)}
        added = 0
        for item in pending:
            title = f'Resolver documento: {item["document_type"]} ({item["label"]})'
            if title not in current:
                db.add_checklist_item(company_id, opportunity_id, title)
                added += 1
        st.success(f"{added} pendência(s) adicionada(s) ao checklist.")
        st.rerun()
