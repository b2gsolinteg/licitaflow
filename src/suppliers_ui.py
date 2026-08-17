from __future__ import annotations

import streamlit as st

from .formatters import format_brl
from .supplier_directory import (
    list_company_suppliers,
    recent_supplier_quotes,
    save_company_supplier,
    set_company_supplier_active,
)


def _refresh():
    st.rerun()


def supplier_directory_page(db, company_id: str):
    st.markdown("### Fornecedores da empresa")
    st.caption(
        "Todo fornecedor usado em uma cotação pode ficar salvo aqui para reutilização em outros editais. "
        "O histórico abaixo ajuda a lembrar custos já praticados."
    )

    with st.expander("➕ Cadastrar fornecedor", expanded=False):
        with st.form("company_supplier_new", clear_on_submit=False, enter_to_submit=False):
            name = st.text_input("Fornecedor")
            a, b = st.columns(2)
            cnpj = a.text_input("CNPJ (opcional)")
            contact = b.text_input("Contato")
            c, d = st.columns(2)
            phone = c.text_input("Telefone / WhatsApp")
            email = d.text_input("E-mail")
            e, f, g = st.columns([2, 1, 2])
            city = e.text_input("Cidade")
            state = f.text_input("UF", max_chars=2)
            lead = g.number_input("Prazo padrão (dias)", min_value=0, value=0, step=1)
            payment = st.text_input("Condição de pagamento", placeholder="Ex.: 28 dias; à vista; boleto 14/28")
            notes = st.text_area("Observações", height=80)
            if st.form_submit_button("Salvar fornecedor", type="primary", width="stretch"):
                try:
                    save_company_supplier(
                        db, company_id, name,
                        cnpj=cnpj, contact_name=contact, phone=phone, email=email,
                        city=city, state=state, payment_terms=payment,
                        default_lead_time_days=None if lead == 0 else lead,
                        notes=notes,
                    )
                    st.success("Fornecedor salvo e disponível para todos os editais desta empresa.")
                    _refresh()
                except ValueError as error:
                    st.warning(str(error))

    suppliers = list_company_suppliers(db, company_id, active_only=False)
    if not suppliers:
        st.info("Nenhum fornecedor salvo ainda. Ao cadastrar um fornecedor na precificação ele também poderá aparecer aqui.")
        return

    active = [row for row in suppliers if bool(int(row.get("active") or 0))]
    inactive = [row for row in suppliers if not bool(int(row.get("active") or 0))]
    st.caption(f"{len(active)} ativo(s) · {len(inactive)} arquivado(s)")

    for supplier in suppliers:
        marker = "" if bool(int(supplier.get("active") or 0)) else " · arquivado"
        with st.expander(f'{supplier.get("name") or "Fornecedor"}{marker}'):
            history = recent_supplier_quotes(db, company_id, supplier.get("name") or "", limit=5)
            if history:
                st.markdown("**Últimas cotações usadas no LicitaNexo**")
                for quote in history:
                    final_unit = sum(float(quote.get(field) or 0) for field in (
                        "unit_cost", "freight_unit", "taxes_unit", "other_unit_costs",
                    ))
                    st.write(
                        f'• {quote.get("description") or "Item"} · **{format_brl(final_unit)} / un.** '
                        f'· {quote.get("agency") or "órgão não informado"}'
                    )

            with st.form(f'edit_company_supplier_{supplier["id"]}', enter_to_submit=False):
                name = st.text_input("Fornecedor", value=supplier.get("name") or "")
                a, b = st.columns(2)
                cnpj = a.text_input("CNPJ", value=supplier.get("cnpj") or "")
                contact = b.text_input("Contato", value=supplier.get("contact_name") or "")
                c, d = st.columns(2)
                phone = c.text_input("Telefone / WhatsApp", value=supplier.get("phone") or "")
                email = d.text_input("E-mail", value=supplier.get("email") or "")
                e, f, g = st.columns([2, 1, 2])
                city = e.text_input("Cidade", value=supplier.get("city") or "")
                state = f.text_input("UF", value=supplier.get("state") or "", max_chars=2)
                lead = g.number_input(
                    "Prazo padrão (dias)", min_value=0,
                    value=int(supplier.get("default_lead_time_days") or 0), step=1,
                )
                payment = st.text_input("Condição de pagamento", value=supplier.get("payment_terms") or "")
                notes = st.text_area("Observações", value=supplier.get("notes") or "", height=80)
                active_value = st.checkbox("Fornecedor ativo", value=bool(int(supplier.get("active") or 0)))
                if st.form_submit_button("Salvar alterações", type="primary", width="stretch"):
                    try:
                        save_company_supplier(
                            db, company_id, name, supplier_id=supplier["id"],
                            cnpj=cnpj, contact_name=contact, phone=phone, email=email,
                            city=city, state=state, payment_terms=payment,
                            default_lead_time_days=None if lead == 0 else lead,
                            notes=notes, active=active_value,
                        )
                        st.success("Fornecedor atualizado.")
                        _refresh()
                    except ValueError as error:
                        st.warning(str(error))

            if bool(int(supplier.get("active") or 0)):
                if st.button("Arquivar fornecedor", key=f'archive_supplier_{supplier["id"]}'):
                    set_company_supplier_active(db, company_id, supplier["id"], False)
                    _refresh()
