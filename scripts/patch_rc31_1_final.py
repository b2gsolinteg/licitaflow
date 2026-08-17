from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path, old, new, label):
    file = ROOT / path
    text = file.read_text(encoding="utf-8-sig")
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: esperado 1, encontrado {count}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


# SQL portável: PostgreSQL não possui COLLATE NOCASE do SQLite.
patch(
    "src/supplier_directory.py",
    'ORDER BY name COLLATE NOCASE',
    'ORDER BY LOWER(name), name',
    "ordenação portável de fornecedores",
)

# A análise passa a permitir importar imediatamente os itens oficiais para a Precificação.
patch(
    "src/pipeline_ui.py",
    'from .pncp_items import PncpItemsError, fetch_contract_documents',
    'from .pncp_items import PncpItemsError, fetch_contract_documents, fetch_contract_items, import_contract_items',
    "imports PNCP na análise",
)
patch(
    "src/pipeline_ui.py",
    '''    control_number = str(opportunity.get("pncp_control_number") or "").strip()\n    documents_key = f"pncp_documents_{opportunity['id']}"''',
    '''    control_number = str(opportunity.get("pncp_control_number") or "").strip()\n    if control_number:\n        with st.container(border=True):\n            p1, p2 = st.columns([5, 2], vertical_alignment="center")\n            p1.markdown("**⚡ Levar itens oficiais para a Precificação**")\n            p1.caption(\n                "Quando o PNCP disponibiliza itens estruturados, o LicitaNexo usa descrição, quantidade, "\n                "unidade e preço de referência sem depender da leitura da tabela do PDF."\n            )\n            if p2.button(\n                "Importar itens",\n                key=f"analysis_import_pncp_items_{opportunity['id']}",\n                type="primary",\n                width="stretch",\n            ):\n                try:\n                    with st.spinner("Importando itens oficiais do PNCP..."):\n                        official_items = fetch_contract_items(control_number)\n                        result = import_contract_items(\n                            db, company_id, opportunity["id"], control_number, official_items\n                        )\n                    st.session_state[f"opportunity_workspace_{opportunity['id']}"] = "💰 Precificação"\n                    if result["imported"]:\n                        st.success(f'{result["imported"]} item(ns) levado(s) para a Precificação.')\n                    else:\n                        st.info("Os itens oficiais já estavam na Precificação ou não foram disponibilizados pelo PNCP.")\n                    st.rerun()\n                except (PncpItemsError, ValueError) as error:\n                    st.warning(str(error))\n\n    documents_key = f"pncp_documents_{opportunity['id']}"''',
    "atalho análise para precificação",
)

# Evita depender de suporte a key no link_button na versão fixada do Streamlit.
patch(
    "src/pipeline_ui.py",
    '''                        right.link_button("Abrir documento", url, key=f"official_doc_{opportunity['id']}_{index}", width="stretch")''',
    '''                        right.link_button(f"Abrir documento {index + 1}", url, width="stretch")''',
    "link de documento compatível",
)

# Consistência: formulários operacionais não são enviados ao pressionar Enter.
patch(
    "src/pipeline_ui.py",
    'with st.form("manual_opportunity", clear_on_submit=True):',
    'with st.form("manual_opportunity", clear_on_submit=False, enter_to_submit=False):',
    "formulário manual",
)
patch(
    "src/pipeline_ui.py",
    'with st.form(f"certame_form_{opportunity[\'id\']}"):',
    'with st.form(f"certame_form_{opportunity[\'id\']}", enter_to_submit=False):',
    "formulário certame",
)

print("Acabamento RC31.1 aplicado")
