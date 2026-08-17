from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path, old, new, label):
    file = ROOT / path
    text = file.read_text(encoding="utf-8-sig")
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: esperado 1 trecho, encontrado {count}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "src/config.py",
    'APP_VERSION = "1.0 Essential RC31.1"',
    'APP_VERSION = "1.0 Essential RC31.2"',
    "versao",
)

replace_once(
    "src/pipeline_ui.py",
    'from .exports import saved_editals_excel, saved_editals_pdf\nfrom .pricing_ui import pricing_workspace',
    'from .exports import saved_editals_excel, saved_editals_pdf\nfrom .dossier_export import build_opportunity_dossier, opportunity_dossier_excel, opportunity_dossier_pdf\nfrom .pricing_ui import pricing_workspace',
    "import dossie",
)

old = '''    else:\n        st.warning("Não foi possível montar um link oficial desta oportunidade.")\n\n    section = st.radio(\n'''
new = '''    else:\n        st.warning("Não foi possível montar um link oficial desta oportunidade.")\n\n    dossier_key = f"opportunity_dossier_{opportunity['id']}"\n    with st.expander("📦 Dossiê de participação · PDF e Excel"):\n        st.caption(\n            "Gere um pacote completo para revisar, imprimir ou levar para a sessão: resumo do edital, Jornada, "\n            "itens, preços, custos, fornecedores, margem, documentos, checklist e análise. O Excel separa as informações em abas."\n        )\n        if st.button(\n            "Preparar / atualizar dossiê",\n            key=f"prepare_dossier_{opportunity['id']}",\n            type="primary",\n            width="stretch",\n        ):\n            try:\n                with st.spinner("Montando dossiê com todas as áreas deste edital..."):\n                    bundle = build_opportunity_dossier(db, company_id, opportunity)\n                    st.session_state[dossier_key] = {\n                        "pdf": opportunity_dossier_pdf(bundle),\n                        "xlsx": opportunity_dossier_excel(bundle),\n                        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),\n                    }\n            except Exception as error:\n                st.error(f"Não foi possível gerar o dossiê: {error}")\n\n        prepared = st.session_state.get(dossier_key)\n        if prepared:\n            st.caption(f'Dossiê preparado em {prepared["generated_at"]}. Gere novamente após alterar preços, fornecedores ou Jornada.')\n            d1, d2 = st.columns(2)\n            d1.download_button(\n                "📄 Baixar dossiê PDF",\n                prepared["pdf"],\n                "dossie_participacao_licitanexo.pdf",\n                "application/pdf",\n                key=f"download_dossier_pdf_{opportunity['id']}",\n                width="stretch",\n            )\n            d2.download_button(\n                "📊 Baixar dossiê Excel",\n                prepared["xlsx"],\n                "dossie_participacao_licitanexo.xlsx",\n                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",\n                key=f"download_dossier_xlsx_{opportunity['id']}",\n                width="stretch",\n            )\n\n    section = st.radio(\n'''
replace_once("src/pipeline_ui.py", old, new, "dossie no edital")
