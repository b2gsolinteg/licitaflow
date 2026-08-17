from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def write(path, text):
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: esperado 1 trecho, encontrado {count}")
    return text.replace(old, new, 1)


# Versão
config = read("src/config.py")
config = replace_once(
    config,
    'APP_VERSION = "1.0 Essential RC31.2"',
    'APP_VERSION = "1.0 Essential RC31.3"',
    "versão RC31.3",
)
write("src/config.py", config)

# Autenticação: Enter não deve submeter nem limpar formulários por acidente.
app = read("app.py")
app = replace_once(
    app,
    "from src.logging_setup import configure_logging\n",
    "from src.logging_setup import configure_logging\nfrom src.help_guides import render_sidebar_guides\n",
    "import guias",
)
for form_name in (
    "login", "access_request", "activate_invitation",
    "password_recovery_request", "password_recovery_reset",
):
    app = replace_once(
        app,
        f'with st.form("{form_name}"):',
        f'with st.form("{form_name}", clear_on_submit=False, enter_to_submit=False):',
        f"form auth {form_name}",
    )
app = replace_once(
    app,
    'with st.form("essential_search_profile"):',
    'with st.form("essential_search_profile", clear_on_submit=False, enter_to_submit=False):',
    "preferências de busca sem enter",
)
app = replace_once(
    app,
    '        page = st.radio("Navegação", pages, key="main_navigation")\n        if st.button("↪ Sair", width="stretch"):',
    '        page = st.radio("Navegação", pages, key="main_navigation")\n        render_sidebar_guides(page)\n        if st.button("↪ Sair", width="stretch"):',
    "guia PDF por tela",
)
write("app.py", app)

# Formulário manual de edital também não deve apagar conteúdo ao pressionar Enter.
pipeline = read("src/pipeline_ui.py")
pipeline = replace_once(
    pipeline,
    'with st.form("manual_opportunity", clear_on_submit=True):',
    'with st.form("manual_opportunity", clear_on_submit=False, enter_to_submit=False):',
    "edital manual sem enter",
)
write("src/pipeline_ui.py", pipeline)

# Precificação: comparação de fornecedores em tabela de largura total, sem Markdown com R$.
pricing = read("src/pricing_ui.py")
anchor = '            st.markdown("#### Fornecedores e custos")\n'
anchor_pos = pricing.find(anchor)
if anchor_pos < 0:
    raise AssertionError("âncora de fornecedores não encontrada")
start = pricing.find("            if suppliers:\n", anchor_pos)
end = pricing.find('            elif item.get("supplier"):', start)
if start < 0 or end < 0:
    raise AssertionError("bloco de fornecedores não encontrado")
new_block = '''            if suppliers:\n                ranked_suppliers = sorted(\n                    suppliers,\n                    key=lambda supplier: (\n                        _supplier_final_unit(supplier, float(item.get("commission") or 0)),\n                        str(supplier.get("supplier_name") or "").lower(),\n                    ),\n                )\n                best_supplier_id = ranked_suppliers[0]["id"] if ranked_suppliers else None\n                comparison_rows = []\n                final_costs = {}\n                for supplier in ranked_suppliers:\n                    final_unit = _supplier_final_unit(\n                        supplier, float(item.get("commission") or 0)\n                    )\n                    final_costs[supplier["id"]] = final_unit\n                    delta = finances["sale_price"] - final_unit\n                    potential_margin = (\n                        (delta / finances["sale_price"] * 100)\n                        if finances["sale_price"] > 0 else None\n                    )\n                    if supplier.get("is_selected"):\n                        situation = "✅ Em uso"\n                    elif supplier["id"] == best_supplier_id:\n                        situation = "🏆 Melhor custo"\n                    else:\n                        situation = "Cotação"\n                    lead = supplier.get("lead_time_days")\n                    comparison_rows.append({\n                        "Fornecedor": supplier.get("supplier_name") or "Fornecedor",\n                        "Custo base": format_brl(supplier.get("unit_cost")),\n                        "Frete": format_brl(supplier.get("freight_unit")),\n                        "Impostos": format_brl(supplier.get("taxes_unit")),\n                        "Outros": format_brl(supplier.get("other_unit_costs")),\n                        "Custo final": format_brl(final_unit),\n                        "Folga/un.": format_brl(delta),\n                        "Margem possível": f"{potential_margin:.1f}%" if potential_margin is not None else "—",\n                        "Prazo": f"{lead} dia(s)" if lead is not None else "—",\n                        "Situação": situation,\n                    })\n\n                st.caption("Comparação ordenada pelo menor custo final por unidade.")\n                st.dataframe(\n                    comparison_rows,\n                    hide_index=True,\n                    width="stretch",\n                    height=min(max(120, 38 * len(comparison_rows) + 42), 360),\n                    column_config={\n                        "Fornecedor": st.column_config.TextColumn(width="large"),\n                        "Custo base": st.column_config.TextColumn(width="small"),\n                        "Frete": st.column_config.TextColumn(width="small"),\n                        "Impostos": st.column_config.TextColumn(width="small"),\n                        "Outros": st.column_config.TextColumn(width="small"),\n                        "Custo final": st.column_config.TextColumn(width="small"),\n                        "Folga/un.": st.column_config.TextColumn(width="small"),\n                        "Margem possível": st.column_config.TextColumn(width="small"),\n                        "Prazo": st.column_config.TextColumn(width="small"),\n                        "Situação": st.column_config.TextColumn(width="medium"),\n                    },\n                )\n                if ranked_suppliers:\n                    best = ranked_suppliers[0]\n                    st.caption(\n                        f'🏆 Melhor custo atual: {best.get("supplier_name") or "Fornecedor"} - '\n                        f'{format_brl(final_costs[best["id"]])}/un.'\n                    )\n\n                    option_ids = [supplier["id"] for supplier in ranked_suppliers]\n                    selected_quote_id = st.selectbox(\n                        "Cotação para usar ou gerenciar",\n                        option_ids,\n                        key=f'manage_supplier_{item["id"]}',\n                        format_func=lambda supplier_id: next(\n                            f'{supplier.get("supplier_name") or "Fornecedor"} - '\n                            f'{format_brl(final_costs[supplier_id])}'\n                            for supplier in ranked_suppliers if supplier["id"] == supplier_id\n                        ),\n                    )\n                    selected_quote = next(\n                        supplier for supplier in ranked_suppliers\n                        if supplier["id"] == selected_quote_id\n                    )\n                    a1, a2 = st.columns([2, 1])\n                    if a1.button(\n                        "Usar fornecedor selecionado",\n                        key=f'use_supplier_selected_{item["id"]}',\n                        width="stretch",\n                        disabled=bool(selected_quote.get("is_selected")),\n                        type="primary",\n                    ):\n                        select_supplier(db, company_id, item["id"], selected_quote_id)\n                        _fragment_refresh()\n                    if a2.button(\n                        "Excluir cotação",\n                        key=f'delete_supplier_selected_{item["id"]}',\n                        width="stretch",\n                    ):\n                        delete_supplier(db, company_id, item["id"], selected_quote_id)\n                        _fragment_refresh()\n'''
pricing = pricing[:start] + new_block + pricing[end:]
write("src/pricing_ui.py", pricing)

print("RC31.3 patch applied")
