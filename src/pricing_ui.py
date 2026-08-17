from __future__ import annotations

import streamlit as st

from .formatters import format_brl
from .pricing import (
    add_supplier,
    delete_supplier,
    item_financials,
    list_suppliers,
    pricing_summary,
    select_supplier,
)


def pricing_workspace(db, company_id, opportunity):
    opportunity_id = opportunity["id"]
    items = db.list_quote_items(company_id, opportunity_id)
    profile = db.get_company_profile(company_id)
    desired_margin = float(profile.get("desired_margin") or 15)

    st.subheader("Formação de preço")
    st.caption(
        "Cadastre os itens do edital, seu preço de participação e as cotações de fornecedores. "
        "O fornecedor selecionado alimenta automaticamente custo e margem do item."
    )

    summary = pricing_summary(items)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Itens", summary["items"])
    c2.metric("Referência edital", format_brl(summary["edital_total"]))
    c3.metric("Minha proposta", format_brl(summary["revenue"]))
    c4.metric("Custo previsto", format_brl(summary["total_cost"]))
    c5.metric("Margem geral", f'{summary["margin_pct"]:.1f}%')
    if items:
        if summary["profit"] < 0:
            st.error(f'Prejuízo previsto: {format_brl(abs(summary["profit"]))}. Revise preço ou fornecedor.')
        else:
            st.success(f'Lucro bruto previsto: {format_brl(summary["profit"])}.')

    with st.expander("➕ Adicionar produto / item", expanded=not bool(items)):
        with st.form(f"new_quote_item_{opportunity_id}", clear_on_submit=True):
            description = st.text_input("Produto / descrição do item")
            a, b, c, d = st.columns(4)
            lot_number = a.text_input("Item / lote", placeholder="Ex.: 01")
            quantity = b.number_input("Quantidade", min_value=0.01, value=1.0, step=1.0)
            edital_price = c.number_input("Preço unitário do edital (R$)", min_value=0.0, value=0.0, step=0.10)
            sale_price = d.number_input("Meu preço unitário (R$)", min_value=0.0, value=0.0, step=0.10)
            commission = st.number_input(
                "Outros custos unitários fixos já conhecidos (R$)", min_value=0.0, value=0.0, step=0.10,
                help="Opcional. Frete, impostos e demais custos também podem ser registrados por fornecedor abaixo do item.",
            )
            if st.form_submit_button("Adicionar item", type="primary", width="stretch"):
                try:
                    db.add_quote_item(
                        company_id, opportunity_id, description, quantity,
                        0, 0, 0, 0, sale_price, "",
                        lot_number=lot_number, edital_price=edital_price, commission=commission,
                    )
                    st.success("Item adicionado. Agora cadastre um ou mais fornecedores.")
                    st.rerun()
                except ValueError as error:
                    st.warning(str(error))

    if not items:
        st.info("Cadastre o primeiro item para começar a comparar preço do edital, fornecedores e margem.")
        return

    for item in items:
        finances = item_financials(item)
        margin_ok = finances["margin_pct"] >= desired_margin if finances["revenue"] > 0 else False
        header = f'{item.get("lot_number") or "Item"} · {item.get("description") or "Sem descrição"}'
        with st.container(border=True):
            st.markdown(f"### {header}")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Quantidade", f'{finances["quantity"]:g}')
            m2.metric("Preço edital", format_brl(finances["edital_price"]))
            m3.metric("Meu preço", format_brl(finances["sale_price"]))
            m4.metric("Custo unitário", format_brl(finances["cost_unit"]))
            m5.metric("Margem", f'{finances["margin_pct"]:.1f}%')
            if finances["sale_price"] > 0:
                status = "✅" if margin_ok and finances["profit"] >= 0 else "⚠️"
                st.caption(
                    f'{status} Lucro bruto do item: {format_brl(finances["profit"])} · '
                    f'Desconto sobre referência: {finances["discount_pct"]:.1f}% · '
                    f'Margem desejada da empresa: {desired_margin:.1f}%'
                )

            suppliers = list_suppliers(db, company_id, item["id"])
            st.markdown("#### Fornecedores e custos")
            if suppliers:
                for supplier in suppliers:
                    total_supplier_unit = sum(float(supplier.get(field) or 0) for field in (
                        "unit_cost", "freight_unit", "taxes_unit", "other_unit_costs",
                    )) + float(item.get("commission") or 0)
                    cols = st.columns([3.2, 1.3, 1.1, 1.1, 1.1])
                    marker = "✅ selecionado" if supplier.get("is_selected") else "cotação"
                    cols[0].write(f'**{supplier["supplier_name"]}** · {marker}')
                    cols[0].caption(
                        f'Prazo: {supplier.get("lead_time_days") if supplier.get("lead_time_days") is not None else "—"} dia(s)'
                        + (f' · {supplier.get("notes")}' if supplier.get("notes") else "")
                    )
                    cols[1].metric("Custo final/un.", format_brl(total_supplier_unit))
                    if not supplier.get("is_selected"):
                        if cols[2].button("Usar", key=f'use_supplier_{supplier["id"]}', width="stretch"):
                            select_supplier(db, company_id, item["id"], supplier["id"])
                            st.rerun()
                    else:
                        cols[2].success("Em uso")
                    if cols[3].button("Excluir", key=f'delete_supplier_{supplier["id"]}', width="stretch"):
                        delete_supplier(db, company_id, item["id"], supplier["id"])
                        st.rerun()
                    delta = finances["sale_price"] - total_supplier_unit
                    cols[4].metric("Folga/un.", format_brl(delta))
            else:
                if item.get("supplier"):
                    st.info(
                        f'Fornecedor legado: {item.get("supplier")} · custo {format_brl(item.get("unit_cost"))}. '
                        "Cadastre uma cotação abaixo para ativar comparação entre fornecedores."
                    )
                else:
                    st.info("Nenhum fornecedor cadastrado para este item.")

            with st.expander("➕ Cadastrar fornecedor"):
                with st.form(f'add_supplier_{item["id"]}', clear_on_submit=True):
                    supplier_name = st.text_input("Fornecedor")
                    s1, s2, s3, s4 = st.columns(4)
                    unit_cost = s1.number_input("Preço de custo/un. (R$)", min_value=0.0, value=0.0, step=0.10)
                    freight = s2.number_input("Frete/un. (R$)", min_value=0.0, value=0.0, step=0.10)
                    taxes = s3.number_input("Impostos/un. (R$)", min_value=0.0, value=0.0, step=0.10)
                    other = s4.number_input("Outros/un. (R$)", min_value=0.0, value=0.0, step=0.10)
                    x1, x2 = st.columns([1, 3])
                    lead_time = x1.number_input("Prazo (dias)", min_value=0, value=0, step=1)
                    notes = x2.text_input("Observação", placeholder="Marca, validade da cotação, condição de pagamento...")
                    if st.form_submit_button("Salvar fornecedor", type="primary", width="stretch"):
                        try:
                            add_supplier(
                                db, company_id, item["id"], supplier_name, unit_cost,
                                freight, taxes, other, None if lead_time == 0 else lead_time, notes,
                            )
                            st.rerun()
                        except ValueError as error:
                            st.warning(str(error))

            with st.expander("Editar item e preço de participação"):
                with st.form(f'edit_quote_item_{item["id"]}'):
                    description = st.text_input("Descrição", value=item.get("description") or "")
                    e1, e2, e3, e4 = st.columns(4)
                    lot_number = e1.text_input("Item / lote", value=item.get("lot_number") or "")
                    quantity = e2.number_input("Quantidade", min_value=0.01, value=float(item.get("quantity") or 1), step=1.0)
                    edital_price = e3.number_input("Preço edital (R$)", min_value=0.0, value=float(item.get("edital_price") or 0), step=0.10)
                    sale_price = e4.number_input("Meu preço (R$)", min_value=0.0, value=float(item.get("sale_price") or 0), step=0.10)
                    commission = st.number_input(
                        "Outros custos unitários fixos (R$)", min_value=0.0,
                        value=float(item.get("commission") or 0), step=0.10,
                    )
                    if st.form_submit_button("Salvar item", type="primary", width="stretch"):
                        try:
                            db.update_quote_item(
                                company_id, item["id"], description, quantity,
                                float(item.get("unit_cost") or 0), float(item.get("freight") or 0),
                                float(item.get("taxes") or 0), float(item.get("other_costs") or 0),
                                sale_price, item.get("supplier") or "", lot_number=lot_number,
                                edital_price=edital_price, commission=commission,
                            )
                            st.rerun()
                        except ValueError as error:
                            st.warning(str(error))
                if st.button("Excluir este item", key=f'delete_quote_item_{item["id"]}'):
                    db.delete_child("opportunity_quote_items", company_id, item["id"])
                    st.rerun()
