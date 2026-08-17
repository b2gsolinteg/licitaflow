from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1 match, encontrado {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


app = ROOT / "app.py"
replace_once(
    app,
    "from src.pipeline_ui import pipeline_page\n",
    "from src.pipeline_ui import pipeline_page\nfrom src.company_ui import company_page\nfrom src.company_intelligence import profile_search_ready, rank_opportunities\n",
    "app imports",
)
replace_once(
    app,
    '    st.header("🔎 Buscar Editais")\n    st.caption("Monitoramos as principais fontes de licitações públicas do Brasil. Separe assuntos diferentes por vírgula: medicamentos, uniformes, luvas.")\n\n    criteria = st.session_state.get("radar_search_criteria") or {}\n',
    '    st.header("🔎 Buscar Editais")\n    st.caption("Monitoramos as principais fontes de licitações públicas do Brasil. Separe assuntos diferentes por vírgula: medicamentos, uniformes, luvas.")\n\n    profile_ready = profile_search_ready(profile)\n    profile_enabled_raw = profile.get("profile_search_enabled")\n    profile_enabled_default = bool(int(profile_enabled_raw if profile_enabled_raw is not None else 1))\n    use_profile = st.toggle(\n        "✨ Priorizar oportunidades compatíveis com minha empresa",\n        value=profile_enabled_default,\n        key="radar_profile_match",\n        help="Ordena os resultados por aderência ao perfil da empresa sem esconder oportunidades.",\n    )\n    if use_profile and not profile_ready:\n        st.info("Complete produtos/serviços, CNAEs ou palavras-chave em Minha Empresa para ativar a aderência automática.")\n\n    criteria = st.session_state.get("radar_search_criteria") or {}\n',
    "search profile toggle",
)
replace_once(
    app,
    '            criteria = {\n                "keyword": keyword.strip(), "nature": nature,\n                "states": selected_states, "modalities": selected_modalities,\n                "srp": srp_label, "horizon": horizon_label, "order": order_label,\n                "minimum": minimum, "maximum": maximum,\n            }\n',
    '            criteria = {\n                "keyword": keyword.strip(), "nature": nature,\n                "states": selected_states, "modalities": selected_modalities,\n                "srp": srp_label, "horizon": horizon_label, "order": order_label,\n                "minimum": minimum, "maximum": maximum,\n                "use_profile": bool(use_profile and profile_ready),\n            }\n',
    "search criteria profile",
)
replace_once(
    app,
    '    for item in items:\n        item["nature"] = _opportunity_nature(item)\n\n    catalog_total = db.global_catalog_count()\n',
    '    for item in items:\n        item["nature"] = _opportunity_nature(item)\n    if criteria.get("use_profile") and profile_ready:\n        items = rank_opportunities(items, profile)\n\n    catalog_total = db.global_catalog_count()\n',
    "search ranking",
)
replace_once(
    app,
    '                with st.container(border=True):\n                    st.markdown(f\'#### {item.get("agency") or "Órgão não informado"}\')\n',
    '                with st.container(border=True):\n                    if criteria.get("use_profile") and "_match_score" in item:\n                        score = int(item.get("_match_score") or 0)\n                        st.markdown(f"**✨ Aderência à sua empresa: {score}%**")\n                        reasons = item.get("_match_reasons") or []\n                        if reasons:\n                            st.caption("Encontrado por: " + " · ".join(reasons[:3]))\n                    st.markdown(f\'#### {item.get("agency") or "Órgão não informado"}\')\n',
    "search card score",
)
replace_once(
    app,
    '            pages = [\n                "📅 Calendário", "🔎 Buscar Editais", "⭐ Meus Editais",\n                "📄 Analisar Edital", "💬 Suporte", "👤 Minha Conta",\n            ]\n',
    '            pages = [\n                "📅 Calendário", "🔎 Buscar Editais", "⭐ Meus Editais",\n                "📄 Analisar Edital", "🏢 Minha Empresa", "💬 Suporte", "👤 Minha Conta",\n            ]\n',
    "navigation company page",
)
replace_once(
    app,
    '    elif page == "💬 Suporte":\n        support_page(user)\n    elif page == "👤 Minha Conta":\n        essential_account_page(user)\n',
    '    elif page == "🏢 Minha Empresa":\n        company_page(db, user)\n    elif page == "💬 Suporte":\n        support_page(user)\n    elif page == "👤 Minha Conta":\n        essential_account_page(user)\n',
    "route company page",
)

pipeline = ROOT / "src" / "pipeline_ui.py"
replace_once(
    pipeline,
    "from .exports import saved_editals_excel, saved_editals_pdf\n",
    "from .exports import saved_editals_excel, saved_editals_pdf\nfrom .pricing_ui import pricing_workspace\nfrom .company_ui import render_document_readiness\n",
    "pipeline imports",
)
replace_once(
    pipeline,
    '    summary, analysis = st.tabs(["Resumo", "Análise do edital"])\n    with summary:\n',
    '    summary, pricing, analysis = st.tabs(["Resumo", "💰 Precificação", "Análise do edital"])\n    with summary:\n',
    "pipeline pricing tab declaration",
)
replace_once(
    pipeline,
    '                db.update_details(company_id, opportunity["id"], notes=notes)\n                st.success("Anotação salva.")\n    with analysis:\n        edital_analysis_tab(db, company_id, opportunity)\n',
    '                db.update_details(company_id, opportunity["id"], notes=notes)\n                st.success("Anotação salva.")\n    with pricing:\n        pricing_workspace(db, company_id, opportunity)\n    with analysis:\n        edital_analysis_tab(db, company_id, opportunity)\n',
    "pipeline pricing tab body",
)
replace_once(
    pipeline,
    '    else:\n        st.info("Nenhuma exigência documental das regras atuais foi localizada automaticamente. Confira a habilitação e os anexos.")\n    if attention_findings:\n',
    '    else:\n        st.info("Nenhuma exigência documental das regras atuais foi localizada automaticamente. Confira a habilitação e os anexos.")\n    render_document_readiness(db, company_id, opportunity["id"], document_findings)\n    if attention_findings:\n',
    "analysis document readiness",
)

config = ROOT / "src" / "config.py"
replace_once(
    config,
    'APP_VERSION = "1.0 Essential RC30.0"',
    'APP_VERSION = "1.0 Essential RC31.0"',
    "app version",
)

pg_test = ROOT / "tests" / "test_postgres_integration.py"
replace_once(
    pg_test,
    '            ]\n            for statement in statements:\n                cursor.execute(statement)\n',
    '''            ]\n            statements.extend([\n                """\n                CREATE TABLE opportunities(\n                    id TEXT PRIMARY KEY, company_id TEXT NOT NULL,\n                    pncp_control_number TEXT, agency TEXT NOT NULL DEFAULT '',\n                    city TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT '',\n                    modality TEXT NOT NULL DEFAULT '', published_at TEXT, opening_at TEXT, closing_at TEXT,\n                    object TEXT NOT NULL DEFAULT '', estimated_value DOUBLE PRECISION,\n                    source_url TEXT NOT NULL DEFAULT '', srp INTEGER NOT NULL DEFAULT 0,\n                    source_name TEXT NOT NULL DEFAULT 'PNCP', source_channel TEXT NOT NULL DEFAULT 'PNCP',\n                    stage TEXT NOT NULL DEFAULT 'Oportunidade',\n                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP\n                )\n                """,\n                """\n                CREATE TABLE opportunity_quote_items(\n                    id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, company_id TEXT NOT NULL,\n                    description TEXT NOT NULL, quantity DOUBLE PRECISION NOT NULL DEFAULT 1,\n                    unit_cost DOUBLE PRECISION NOT NULL DEFAULT 0, freight DOUBLE PRECISION NOT NULL DEFAULT 0,\n                    taxes DOUBLE PRECISION NOT NULL DEFAULT 0, other_costs DOUBLE PRECISION NOT NULL DEFAULT 0,\n                    sale_price DOUBLE PRECISION NOT NULL DEFAULT 0, supplier TEXT NOT NULL DEFAULT '',\n                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP\n                )\n                """,\n            ])\n            for statement in statements:\n                cursor.execute(statement)\n''',
    "postgres legacy pricing schema",
)
replace_once(
    pg_test,
    '    def test_migrations_are_idempotent(self):\n',
    '''    def test_company_intelligence_schema_is_available(self):\n        from src.db_runtime import connect_runtime\n\n        with connect_runtime(ROOT / "data" / "ci.db") as connection:\n            rows = connection.execute(\n                """\n                SELECT table_name,column_name,data_type\n                FROM information_schema.columns\n                WHERE table_schema=? AND table_name IN (\n                    'company_profiles','company_document_uploads','opportunity_item_suppliers'\n                )\n                """,\n                (self.schema,),\n            ).fetchall()\n        columns = {(row["table_name"], row["column_name"]): row["data_type"] for row in rows}\n        self.assertIn(("company_profiles", "excluded_keywords"), columns)\n        self.assertIn(("company_profiles", "profile_search_enabled"), columns)\n        self.assertEqual(columns.get(("company_document_uploads", "created_at")), "timestamp with time zone")\n        self.assertEqual(columns.get(("opportunity_item_suppliers", "created_at")), "timestamp with time zone")\n\n    def test_migrations_are_idempotent(self):\n''',
    "postgres intelligence assertions",
)

checker = ROOT / "scripts" / "check_postgres_schema.py"
replace_once(
    checker,
    '    ("billing_checkouts", "updated_at"),\n}',
    '    ("billing_checkouts", "updated_at"),\n    ("company_profiles", "cnpj_card_uploaded_at"),\n    ("company_document_uploads", "created_at"),\n    ("opportunity_item_suppliers", "created_at"),\n    ("opportunity_item_suppliers", "updated_at"),\n}',
    "schema checker RC31 timestamps",
)

print("RC31 patch applied successfully")
