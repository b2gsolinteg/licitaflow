from __future__ import annotations

import streamlit as st

from .formatters import format_brl, parse_brl
from .pncp_items import PncpItemsError, fetch_contract_items, import_contract_items
from .pricing import (
    add_supplier,
    delete_supplier,
    ensure_sqlite_pricing_schema,
    item_financials,
    pricing_summary,
    select_supplier,
)
from .sources import parse_pncp_control_number
from .supplier_directory import (
    ensure_company_supplier,
    list_company_suppliers,
    list_opportunity_supplier_quotes,
    recent_supplier_quotes,
)


def _money_input_value(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    if number == 0:
        return ""
    return format_brl(number).replace("R$ ", "")


def _money_from_text(value, label: str) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    parsed = parse_brl(text)
    if parsed is None or parsed < 0:
        raise ValueError(f"{label}: informe um valor válido, como 19,40.")
    return float(parsed)


def _fragment_refresh():
    try:
        st.rerun(scope="fragment")
    except Exception:
        st.rerun()


def _supplier_final_unit(supplier: dict, fixed_cost: float = 0) -> float:
    return fixed_cost + sum(float(supplier.get(field) or 0) for field in (
        "unit_cost", "freight_unit", "taxes_unit", "other_unit_costs",
    ))


@st.fragment
def pricing_workspace(db, company_id, opportunity):
    opportunity_id = opportunity["id"]
    ensure_sqlite_pricing_schema(db)
    items = db.list_quote_items(company_id, opportunity_id)
    profile = db.get_company_profile(company_id)
    desired_margin = float(profile.get("desired_margin") or 15)
    supplier_directory = list_company_suppliers(db, company_id)
    supplier_by_id = {row["id"]: row for row in supplier_directory}
    suppliers_by_item = list_opportunity_supplier_quotes(db, company_id, opportunity_id)

    st.subheader("Formação de preço")
    st.caption(
        "O LicitaNexo traz a referência do órgão quando disponível; você informa seu preço e escolhe o fornecedor. "
        "Pressionar Enter não salva formulários nesta tela — use sempre o botão Salvar."
    )

    control_number = str(opportunity.get("pncp_control_number") or "").strip()
    if parse_pncp_control_number(control_number):
        with st.container(border=True):
            c1, c2 = st.columns([5, 2], vertical_alignment="center")
            c1.markdown("**⚡ Itens oficiais do PNCP**")
            c1.caption(
                "Importa descrição, quantidade, unidade e valor unitário estimado diretamente do PNCP. "
                "Itens já importados não são duplicados."
            )
            if c2.button(
                "Importar / atualizar itens",
                key=f"import_pncp_items_{opportunity_id}",
                type="primary",
                width="stretch",
            ):
                try:
                    with st.spinner("Consultando itens oficiais no PNCP..."):
                        official_items = fetch_contract_items(control_number)
                        result = import_contract_items(
                            db, company_id, opportunity_id, control_number, official_items
                        )
                    if result["imported"]:
                        message = f'{result["imported"]} item(ns) importado(s) do PNCP.'
                        if result["confidential"]:
                            message += f' {result["confidential"]} com orçamento sigiloso ficaram sem preço de referência.'
                        st.success(message)
                    elif result["skipped"]:
                        st.info("Os itens oficiais já estavam importados nesta precificação.")
                    else:
                        st.info("O PNCP não retornou itens para esta contratação.")
                    _fragment_refresh()
                except (PncpItemsError, ValueError) as error:
                    st.warning(str(error))

    summary = pricing_summary(items)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Itens", summary["items"])
    s2.metric("Referência do órgão", format_brl(summary["edital_total"]))
    s3.metric("Minha proposta", format_brl(summary["revenue"]))
    s4.metric("Margem geral", f'{summary["margin_pct"]:.1f}%')
    if items:
        if summary["profit"] < 0:
            st.error(
                f'Custo previsto {format_brl(summary["total_cost"])} · prejuízo previsto '
                f'{format_brl(abs(summary["profit"]))}. Revise preço ou fornecedor.'
            )
        else:
            st.success(
                f'Custo previsto {format_brl(summary["total_cost"])} · lucro bruto previsto '
                f'{format_brl(summary["profit"])}.'
            )

        no_sale_price = [item for item in items if float(item.get("sale_price") or 0) <= 0 and float(item.get("edital_price") or 0) > 0]
        if no_sale_price:
            if st.button(
                "Usar preço de referência como ponto de partida nos itens sem meu preço",
                key=f"copy_reference_{opportunity_id}",
                help="Apenas preenche seu preço inicial com a referência do órgão. Você pode alterar depois.",
            ):
                with db.connect() as conn:
                    conn.execute("""
                        UPDATE opportunity_quote_items
                        SET sale_price=edital_price
                        WHERE company_id=? AND opportunity_id=? AND sale_price<=0 AND edital_price>0
                    """, (company_id, opportunity_id))
                _fragment_refresh()

    with st.expander("➕ Adicionar produto / item manualmente", expanded=not bool(items)):
        with st.form(
            f"new_quote_item_{opportunity_id}",
            clear_on_submit=False,
            enter_to_submit=False,
        ):
            description = st.text_input("Produto / descrição do item")
            a, b = st.columns([2, 1])
            lot_number = a.text_input("Item / lote", placeholder="Ex.: 01")
            quantity = b.number_input("Quantidade", min_value=0.01, value=1.0, step=1.0)
            c, d, e = st.columns(3)
            edital_text = c.text_input("Preço unitário do edital (R$)", placeholder="19,40")
            sale_text = d.text_input("Meu preço unitário (R$)", placeholder="18,90")
            fixed_text = e.text_input("Outros custos fixos/un. (R$)", placeholder="0,00")
            if st.form_submit_button("Adicionar item", type="primary", width="stretch"):
                try:
                    edital_price = _money_from_text(edital_text, "Preço do edital")
                    sale_price = _money_from_text(sale_text, "Meu preço")
                    fixed_cost = _money_from_text(fixed_text, "Outros custos")
                    db.add_quote_item(
                        company_id, opportunity_id, description, quantity,
                        0, 0, 0, 0, sale_price, "",
                        lot_number=lot_number, edital_price=edital_price, commission=fixed_cost,
                    )
                    st.success("Item adicionado.")
                    _fragment_refresh()
                except ValueError as error:
                    st.warning(str(error))

    if not items:
        st.info("Importe os itens do PNCP ou cadastre o primeiro item para começar a formação de preço.")
        return

    for item in items:
        finances = item_financials(item)
        margin_ok = finances["margin_pct"] >= desired_margin if finances["revenue"] > 0 else False
        unit_measure = str(item.get("unit_measure") or "").strip()
        source_kind = str(item.get("source_kind") or "manual").strip().lower()
        header = f'{item.get("lot_number") or "Item"} · {item.get("description") or "Sem descrição"}'
        with st.container(border=True):
            st.markdown(f"### {header}")
            badges = []
            if source_kind == "pncp":
                badges.append("⚡ item oficial PNCP")
            if unit_measure:
                badges.append(f"unidade: {unit_measure}")
            if badges:
                st.caption(" · ".join(badges))

            m1, m2, m3, m4 = st.columns(4)
            quantity_label = f'{finances["quantity"]:g}' + (f" {unit_measure}" if unit_measure else "")
            m1.metric("Quantidade", quantity_label)
            m2.metric("Preço edital", format_brl(finances["edital_price"]))
            m3.metric("Meu preço", format_brl(finances["sale_price"]))
            m4.metric("Margem", f'{finances["margin_pct"]:.1f}%')
            if finances["sale_price"] > 0:
                status = "✅" if margin_ok and finances["profit"] >= 0 else "⚠️"
                st.caption(
                    f'{status} Custo/un. {format_brl(finances["cost_unit"])} · '
                    f'lucro bruto do item {format_brl(finances["profit"])} · '
                    f'desconto sobre referência {finances["discount_pct"]:.1f}% · '
                    f'meta de margem {desired_margin:.1f}%.'
                )

            suppliers = suppliers_by_item.get(str(item["id"]), [])
            st.markdown("#### Fornecedores e custos")
            if suppliers:
                for supplier in suppliers:
                    total_supplier_unit = _supplier_final_unit(
                        supplier, float(item.get("commission") or 0)
                    )
                    delta = finances["sale_price"] - total_supplier_unit
                    row_left, row_values, row_actions = st.columns([4.5, 3.2, 2.3], vertical_alignment="center")
                    marker = "✅ Em uso" if supplier.get("is_selected") else "Cotação"
                    row_left.markdown(f'**{supplier["supplier_name"]}** · {marker}')
                    lead = supplier.get("lead_time_days")
                    details = f'Prazo: {lead if lead is not None else "—"} dia(s)'
                    if supplier.get("notes"):
                        details += f' · {supplier.get("notes")}'
                    row_left.caption(details)
                    row_values.markdown(
                        f'**Custo final/un.: {format_brl(total_supplier_unit)}**  \n'
                        f'Folga/un.: **{format_brl(delta)}**'
                    )
                    with row_actions:
                        a1, a2 = st.columns(2)
                        if supplier.get("is_selected"):
                            a1.success("Em uso")
                        elif a1.button("Usar", key=f'use_supplier_{supplier["id"]}', width="stretch"):
                            select_supplier(db, company_id, item["id"], supplier["id"])
                            _fragment_refresh()
                        if a2.button("Excluir", key=f'delete_supplier_{supplier["id"]}', width="stretch"):
                            delete_supplier(db, company_id, item["id"], supplier["id"])
                            _fragment_refresh()
            elif item.get("supplier"):
                st.info(
                    f'Fornecedor legado: {item.get("supplier")} · custo {format_brl(item.get("unit_cost"))}. '
                    "Cadastre uma nova cotação para ativar a comparação."
                )
            else:
                st.info("Nenhum fornecedor cadastrado para este item.")

            with st.expander("➕ Cadastrar fornecedor / cotação"):
                options = ["__new__", *[row["id"] for row in supplier_directory]]
                selected_directory = st.selectbox(
                    "Fornecedor salvo",
                    options,
                    key=f'directory_supplier_{item["id"]}',
                    format_func=lambda value: "Cadastrar novo fornecedor" if value == "__new__" else supplier_by_id[value]["name"],
                )
                directory_row = supplier_by_id.get(selected_directory)
                if directory_row:
                    history = recent_supplier_quotes(db, company_id, directory_row["name"], limit=3)
                    if history:
                        last = history[0]
                        last_total = _supplier_final_unit(last)
                        st.caption(
                            f'Última cotação registrada: {format_brl(last_total)}/un. · '
                            f'{last.get("description") or "item"} · {last.get("agency") or "órgão não informado"}'
                        )
                with st.form(
                    f'add_supplier_{item["id"]}',
                    clear_on_submit=False,
                    enter_to_submit=False,
                ):
                    if directory_row:
                        st.text_input("Fornecedor", value=directory_row["name"], disabled=True)
                        supplier_name = directory_row["name"]
                    else:
                        supplier_name = st.text_input("Fornecedor")
                    s1, s2, s3, s4 = st.columns(4)
                    unit_text = s1.text_input("Preço de custo/un. (R$)", placeholder="13,20")
                    freight_text = s2.text_input("Frete/un. (R$)", placeholder="0,00")
                    taxes_text = s3.text_input("Impostos/un. (R$)", placeholder="0,00")
                    other_text = s4.text_input("Outros/un. (R$)", placeholder="0,00")
                    x1, x2 = st.columns([1, 3])
                    default_lead = int(directory_row.get("default_lead_time_days") or 0) if directory_row else 0
                    lead_time = x1.number_input("Prazo (dias)", min_value=0, value=default_lead, step=1)
                    notes = x2.text_input("Observação", placeholder="Marca, validade, condição de pagamento...")
                    if st.form_submit_button("Salvar fornecedor", type="primary", width="stretch"):
                        try:
                            unit_cost = _money_from_text(unit_text, "Preço de custo")
                            freight = _money_from_text(freight_text, "Frete")
                            taxes = _money_from_text(taxes_text, "Impostos")
                            other = _money_from_text(other_text, "Outros custos")
                            ensure_company_supplier(
                                db, company_id, supplier_name,
                                default_lead_time_days=None if lead_time == 0 else lead_time,
                            )
                            add_supplier(
                                db, company_id, item["id"], supplier_name, unit_cost,
                                freight, taxes, other, None if lead_time == 0 else lead_time, notes,
                            )
                            st.success("Cotação salva. O fornecedor também ficou salvo na empresa.")
                            _fragment_refresh()
                        except ValueError as error:
                            st.warning(str(error))

            with st.expander("Editar item e preço de participação"):
                with st.form(
                    f'edit_quote_item_{item["id"]}',
                    clear_on_submit=False,
                    enter_to_submit=False,
                ):
                    description = st.text_input("Descrição", value=item.get("description") or "")
                    e1, e2 = st.columns([2, 1])
                    lot_number = e1.text_input("Item / lote", value=item.get("lot_number") or "")
                    quantity = e2.number_input(
                        "Quantidade", min_value=0.01,
                        value=float(item.get("quantity") or 1), step=1.0,
                    )
                    e3, e4, e5 = st.columns(3)
                    edital_text = e3.text_input(
                        "Preço edital (R$)", value=_money_input_value(item.get("edital_price"))
                    )
                    sale_text = e4.text_input(
                        "Meu preço (R$)", value=_money_input_value(item.get("sale_price"))
                    )
                    fixed_text = e5.text_input(
                        "Outros custos fixos/un. (R$)", value=_money_input_value(item.get("commission"))
                    )
                    if st.form_submit_button("Salvar item", type="primary", width="stretch"):
                        try:
                            edital_price = _money_from_text(edital_text, "Preço do edital")
                            sale_price = _money_from_text(sale_text, "Meu preço")
                            fixed_cost = _money_from_text(fixed_text, "Outros custos")
                            db.update_quote_item(
                                company_id, item["id"], description, quantity,
                                float(item.get("unit_cost") or 0), float(item.get("freight") or 0),
                                float(item.get("taxes") or 0), float(item.get("other_costs") or 0),
                                sale_price, item.get("supplier") or "", lot_number=lot_number,
                                edital_price=edital_price, commission=fixed_cost,
                            )
                            st.success("Item atualizado.")
                            _fragment_refresh()
                        except ValueError as error:
                            st.warning(str(error))
                if st.button("Excluir este item", key=f'delete_quote_item_{item["id"]}'):
                    db.delete_child("opportunity_quote_items", company_id, item["id"])
                    _fragment_refresh()
