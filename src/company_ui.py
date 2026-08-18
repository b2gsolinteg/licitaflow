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
        "Cadastre apenas o básico para organizar sua operação. Você não precisa conhecer CNAE nem decidir agora tudo o que vai vender ao governo."
    )

    section = st.radio(
        "Área da empresa",
        ["Perfil da empresa", "Documentos", "Fornecedores"],
        horizontal=True,
        label_visibility="collapsed",
        key="company_workspace_section",
    )

    if section == "Perfil da empresa":
        st.markdown("### Dados básicos")
        st.caption(
            "Preencha o que você já sabe. O campo mais importante é descrever, com suas palavras, o que sua empresa consegue fornecer."
        )
        profile = get_extended_profile(db, company_id)
        with st.form("company_essential_profile", clear_on_submit=False, enter_to_submit=False):
            c1, c2 = st.columns(2)
            legal_name = c1.text_input("Razão social", value=profile.get("legal_name") or user.get("company_name") or "")
            trade_name = c2.text_input("Nome fantasia", value=profile.get("trade_name") or "")
            c3, c4 = st.columns(2)
            cnpj = c3.text_input("CNPJ", value=profile.get("cnpj") or "", placeholder="00.000.000/0000-00")
            activity_type = c4.selectbox(
                "O que faz principalmente?", ["Produtos", "Serviços", "Produtos e serviços"],
                index=["Produtos", "Serviços", "Produtos e serviços"].index(
                    profile.get("activity_type") if profile.get("activity_type") in {"Produtos", "Serviços", "Produtos e serviços"} else "Produtos"
                ),
            )
            offerings = st.text_area(
                "O que sua empresa consegue fornecer?",
                value=profile.get("offerings") or "",
                height=150,
                placeholder="Ex.: papel A4, produtos de limpeza, informática, ferramentas, pneus...",
                help="Não precisa escrever termos técnicos. Use os nomes que você usa no dia a dia.",
            )
            s1, s2 = st.columns(2)
            service_states = s1.text_input(
                "UFs onde consegue atender (opcional)",
                value=profile.get("service_states") or "",
                placeholder="SP, PR, SC — deixe vazio para Brasil inteiro",
            )
            desired_margin = s2.number_input(
                "Margem desejada (%)", min_value=0.0, max_value=100.0,
                value=float(profile.get("desired_margin") or 15), step=1.0,
                help="Será usada mais tarde na precificação. Não interfere na busca de licitações.",
            )
            if st.form_submit_button("Salvar dados da empresa", type="primary", width="stretch"):
                try:
                    save_extended_profile(
                        db, company_id,
                        legal_name=legal_name.strip(), trade_name=trade_name.strip(), cnpj=cnpj.strip(),
                        activity_type=activity_type, offerings=offerings.strip(),
                        cnaes=profile.get("cnaes") or "",
                        procurement_interests=profile.get("procurement_interests") or "",
                        interest_keywords=profile.get("interest_keywords") or "",
                        brands=profile.get("brands") or "",
                        service_states=", ".join(_csv_states(service_states)),
                        desired_margin=desired_margin,
                        excluded_keywords=profile.get("excluded_keywords") or "",
                        profile_search_enabled=False,
                    )
                    st.success("Dados salvos. Você já pode continuar pesquisando normalmente.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

        st.info(
            "Para encontrar oportunidades, o LicitaNexo não exige CNAE, score de aderência nem um perfil completo. "
            "Use a busca por produto, estado, cidade ou modalidade e descubra aos poucos o que faz sentido vender ao governo."
        )

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
