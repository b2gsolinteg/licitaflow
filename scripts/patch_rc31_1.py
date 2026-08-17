from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def write(path: str, content: str) -> None:
    (ROOT / path).write_text(content, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: esperado 1 trecho, encontrado {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise AssertionError(f"{label}: esperado 1 trecho, encontrado {count}")
    return updated


# Versão
config = read("src/config.py")
config = replace_once(
    config,
    'APP_VERSION = "1.0 Essential RC31.0"',
    'APP_VERSION = "1.0 Essential RC31.1"',
    "versão",
)
write("src/config.py", config)

# Sessão: mantém validação em toda execução completa, mas evita UPDATE de heartbeat em cada rerun.
security = read("src/security_rc25.py")
security = replace_once(
    security,
    '''            connection.execute(\n                "UPDATE security_sessions SET last_seen_at=? WHERE token_hash=?",\n                (_timestamp_value(now), token_hash),\n            )''',
    '''            # A sessão continua validada em toda execução completa, porém o heartbeat\n            # só grava no banco quando passou pelo menos 60s. Fragments de UI não precisam\n            # escrever no PostgreSQL a cada interação de preço/fornecedor.\n            if not last_seen or (now - last_seen).total_seconds() >= 60:\n                connection.execute(\n                    "UPDATE security_sessions SET last_seen_at=? WHERE token_hash=?",\n                    (_timestamp_value(now), token_hash),\n                )''',
    "heartbeat de sessão",
)
write("src/security_rc25.py", security)

# Diretório de fornecedores: consulta histórica não depende das novas colunas de origem.
supplier_directory = read("src/supplier_directory.py")
supplier_directory = replace_once(
    supplier_directory,
    'SELECT s.*, q.description, q.lot_number, q.unit_measure, o.agency, o.pncp_control_number',
    'SELECT s.*, q.description, q.lot_number, o.agency, o.pncp_control_number',
    "histórico de fornecedor",
)
write("src/supplier_directory.py", supplier_directory)

# Fornecedores como fragmento independente.
suppliers_ui = read("src/suppliers_ui.py")
suppliers_ui = replace_once(
    suppliers_ui,
    '''def _refresh():\n    st.rerun()\n\n\ndef supplier_directory_page(db, company_id: str):''',
    '''def _refresh():\n    try:\n        st.rerun(scope="fragment")\n    except Exception:\n        st.rerun()\n\n\n@st.fragment\ndef supplier_directory_page(db, company_id: str):''',
    "fragmento de fornecedores",
)
write("src/suppliers_ui.py", suppliers_ui)

# Precificação: garantir colunas SQLite e reduzir tamanho do título do item.
pricing_ui = read("src/pricing_ui.py")
pricing_ui = replace_once(
    pricing_ui,
    'from .pncp_items import PncpItemsError, fetch_contract_items, import_contract_items',
    'from .pncp_items import (PncpItemsError, ensure_sqlite_quote_source_schema, fetch_contract_items, import_contract_items)',
    "import schema de origem",
)
pricing_ui = replace_once(
    pricing_ui,
    '''    ensure_sqlite_pricing_schema(db)\n    items = db.list_quote_items(company_id, opportunity_id)''',
    '''    ensure_sqlite_pricing_schema(db)\n    ensure_sqlite_quote_source_schema(db)\n    items = db.list_quote_items(company_id, opportunity_id)''',
    "schema pricing sqlite",
)
pricing_ui = replace_once(
    pricing_ui,
    '''        header = f'{item.get("lot_number") or "Item"} · {item.get("description") or "Sem descrição"}'\n        with st.container(border=True):\n            st.markdown(f"### {header}")''',
    '''        header = f'{item.get("lot_number") or "Item"} · {item.get("description") or "Sem descrição"}'\n        display_header = header if len(header) <= 220 else header[:217].rstrip() + "..."\n        with st.container(border=True):\n            st.markdown(f"#### {display_header}")\n            if display_header != header:\n                with st.expander("Ver descrição completa do item"):\n                    st.write(header)''',
    "título compacto de item",
)
write("src/pricing_ui.py", pricing_ui)

# Minha Empresa: navegação lazy e fornecedores permanentes.
company = read("src/company_ui.py")
company = replace_once(
    company,
    'import streamlit as st\n\nfrom .formatters import format_brl',
    'import streamlit as st\n\nfrom .formatters import format_brl\nfrom .suppliers_ui import supplier_directory_page',
    "import fornecedores empresa",
)
company = replace_once(
    company,
    '''    profile_tab, documents_tab, explanation_tab = st.tabs([\n        "Perfil e Cartão CNPJ", "Documentos", "Como o Radar usa meu perfil",\n    ])\n\n    with profile_tab:''',
    '''    section = st.radio(\n        "Área da empresa",\n        ["Perfil e Cartão CNPJ", "Documentos", "Fornecedores", "Como o Radar usa meu perfil"],\n        horizontal=True,\n        label_visibility="collapsed",\n        key="company_workspace_section",\n    )\n\n    if section == "Perfil e Cartão CNPJ":''',
    "navegação lazy empresa",
)
company = replace_once(
    company,
    '    with documents_tab:',
    '    elif section == "Documentos":',
    "aba documentos empresa",
)
company = replace_once(
    company,
    '    with explanation_tab:',
    '''    elif section == "Fornecedores":\n        supplier_directory_page(db, company_id)\n\n    else:''',
    "aba fornecedores empresa",
)
write("src/company_ui.py", company)

# Meus Editais: lazy sections, Jornada, exportação sob demanda e análise multi-documento.
pipeline = read("src/pipeline_ui.py")
pipeline = replace_once(
    pipeline,
    '''from .pricing_ui import pricing_workspace\nfrom .company_ui import render_document_readiness''',
    '''from .pricing_ui import pricing_workspace\nfrom .journey_ui import journey_workspace\nfrom .company_ui import render_document_readiness\nfrom .pncp_items import PncpItemsError, fetch_contract_documents''',
    "imports pipeline RC31.1",
)

pipeline = regex_once(
    pipeline,
    r'''    all_rows = db\.pipeline_summaries\(company_id, ""\).*?\n\n    c1, c2 = st\.columns\(\[3, 2\]\)''',
    '''    export_key = f"pipeline_exports_{company_id}"\n    if st.button("📦 Preparar / atualizar arquivos de exportação", key=f"prepare_exports_{company_id}"):\n        with st.spinner("Preparando exportação..."):\n            all_rows = db.pipeline_summaries(company_id, "")\n            export_rows = []\n            for export_row in all_rows:\n                export_item = dict(export_row)\n                export_item["stage_display"] = _DB_TO_STAGE.get(export_item.get("stage"), "Salvo")\n                details = db.get_details(company_id, export_item["id"]) or {}\n                export_item["notes"] = details.get("notes") or ""\n                if not export_item.get("certame_at"):\n                    export_item["certame_at"] = details.get("certame_at")\n                export_rows.append(export_item)\n            st.session_state[export_key] = {\n                "xlsx": saved_editals_excel(export_rows, user.get("company_name") or ""),\n                "pdf": saved_editals_pdf(export_rows, user.get("company_name") or ""),\n                "count": len(export_rows),\n            }\n    prepared_exports = st.session_state.get(export_key)\n    if prepared_exports:\n        st.caption(f'{prepared_exports["count"]} edital(is) no último pacote preparado.')\n        e1, e2 = st.columns(2)\n        e1.download_button(\n            "📊 Baixar Excel", prepared_exports["xlsx"], "meus_editais_licitanexo.xlsx",\n            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch",\n        )\n        e2.download_button(\n            "📄 Baixar PDF", prepared_exports["pdf"], "meus_editais_licitanexo.pdf",\n            "application/pdf", width="stretch",\n        )\n\n    c1, c2 = st.columns([3, 2])''',
    "exportação sob demanda",
)

pipeline = replace_once(
    pipeline,
    '''    summary, pricing, analysis = st.tabs(["Resumo", "💰 Precificação", "Análise do edital"])\n    with summary:\n        with st.form(f"essential_summary_{opportunity['id']}"):\n            notes = st.text_area("Minhas anotações", value=details.get("notes") or "", height=140)\n            if st.form_submit_button("Salvar anotação", type="primary"):\n                db.update_details(company_id, opportunity["id"], notes=notes)\n                st.success("Anotação salva.")\n    with pricing:\n        pricing_workspace(db, company_id, opportunity)\n    with analysis:\n        edital_analysis_tab(db, company_id, opportunity)''',
    '''    section = st.radio(\n        "Área do edital",\n        ["📋 Visão geral", "✅ Jornada", "💰 Precificação", "📄 Documentos e análise"],\n        horizontal=True,\n        label_visibility="collapsed",\n        key=f"opportunity_workspace_{opportunity['id']}",\n    )\n    if section == "📋 Visão geral":\n        with st.form(f"essential_summary_{opportunity['id']}", enter_to_submit=False):\n            notes = st.text_area("Minhas anotações", value=details.get("notes") or "", height=140)\n            if st.form_submit_button("Salvar anotação", type="primary"):\n                db.update_details(company_id, opportunity["id"], notes=notes)\n                st.success("Anotação salva.")\n    elif section == "✅ Jornada":\n        journey_workspace(db, company_id, opportunity)\n    elif section == "💰 Precificação":\n        pricing_workspace(db, company_id, opportunity)\n    else:\n        edital_analysis_tab(db, company_id, opportunity)''',
    "workspace lazy edital",
)

analysis_prefix = '''def edital_analysis_tab(db, company_id, opportunity):\n    st.subheader("Documentos e análise do edital")\n    st.caption(\n        "Analise o edital junto com o Termo de Referência e outros anexos. Para editais PNCP, "\n        "a Precificação pode importar itens e valores oficiais diretamente da API estruturada."\n    )\n\n    control_number = str(opportunity.get("pncp_control_number") or "").strip()\n    documents_key = f"pncp_documents_{opportunity['id']}"\n    if control_number:\n        if st.button(\n            "📎 Consultar documentos oficiais no PNCP",\n            key=f"fetch_pncp_documents_{opportunity['id']}",\n        ):\n            try:\n                with st.spinner("Consultando documentos oficiais..."):\n                    st.session_state[documents_key] = fetch_contract_documents(control_number)\n            except PncpItemsError as error:\n                st.warning(str(error))\n        official_documents = st.session_state.get(documents_key) or []\n        if official_documents:\n            with st.expander(f"Documentos oficiais encontrados ({len(official_documents)})", expanded=True):\n                for index, document in enumerate(official_documents):\n                    left, right = st.columns([5, 2], vertical_alignment="center")\n                    title = document.get("title") or document.get("type") or "Documento"\n                    left.write(f"**{title}**")\n                    details = " · ".join(\n                        value for value in (document.get("type"), document.get("published_at")) if value\n                    )\n                    if details:\n                        left.caption(details)\n                    url = str(document.get("url") or "")\n                    if url.startswith(("http://", "https://")):\n                        right.link_button("Abrir documento", url, key=f"official_doc_{opportunity['id']}_{index}", width="stretch")\n\n    uploaded_files = st.file_uploader(\n        "Edital, Termo de Referência e anexos em PDF",\n        type=["pdf"],\n        accept_multiple_files=True,\n        key=f"edital_pdf_{opportunity['id']}",\n        help="Você pode selecionar vários PDFs de uma vez. A análise considera o conjunto enviado.",\n    )\n    if uploaded_files:\n        st.caption(\n            f"{len(uploaded_files)} arquivo(s) selecionado(s). A numeração de páginas segue a ordem dos arquivos enviados."\n        )\n    if uploaded_files and st.button(\n        "Analisar documentos", type="primary", width="stretch", key=f"analyze_{opportunity['id']}"\n    ):\n        try:\n            with st.spinner("Lendo edital, Termo de Referência e anexos..."):\n                pages = []\n                names = []\n                for uploaded in uploaded_files:\n                    try:\n                        file_pages = extract_pdf_pages(uploaded.getvalue())\n                    except ValueError as error:\n                        raise ValueError(f"{uploaded.name}: {error}") from error\n                    pages.extend(file_pages)\n                    names.append(uploaded.name)\n                object_text, required_documents, alerts, findings = analyze_essential_pages(pages)\n                findings = [f for f in findings if f.get("category") != "Objeto"]\n                findings.insert(0, {\n                    "severity": "Verde", "category": "Objeto", "title": "Objeto",\n                    "evidence": opportunity.get("object") or object_text or "Objeto não identificado automaticamente.",\n                    "page_number": None,\n                    "recommended_action": "Confira a descrição completa no edital e anexos.",\n                })\n                filename = " + ".join(names)[:240] or "documentos.pdf"\n                analysis_id = db.save_edital_analysis(\n                    company_id, opportunity["id"], filename, 0, len(pages), findings\n                )\n                st.session_state[f"analysis_{opportunity['id']}"] = analysis_id\n            st.success("Análise concluída sobre o conjunto de documentos.")\n            st.rerun()\n        except ValueError as error:\n            st.error(str(error))\n        except Exception as error:\n            st.error(f"Não foi possível analisar estes documentos: {error}")\n\n'''
pipeline = regex_once(
    pipeline,
    r'''def edital_analysis_tab\(db, company_id, opportunity\):.*?(?=    analyses = db\.list_analyses\(company_id, opportunity\["id"\]\))''',
    analysis_prefix,
    "análise multi-documento",
)
write("src/pipeline_ui.py", pipeline)

print("RC31.1 patch aplicado com sucesso")
