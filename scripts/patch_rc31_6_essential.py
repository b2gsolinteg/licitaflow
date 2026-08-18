from __future__ import annotations

import re
from pathlib import Path


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Marcador não encontrado: {label}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Database: filtro de cidade e contagens rápidas para as páginas de exploração.
# ---------------------------------------------------------------------------
db_path = Path("src/database.py")
db = db_path.read_text(encoding="utf-8")
db = replace_once(
    db,
    'def list_global_catalog(self, search="", states=None, modalities=None, srp=None, minimum=None,',
    'def list_global_catalog(self, search="", states=None, cities=None, modalities=None, srp=None, minimum=None,',
    "assinatura list_global_catalog",
)
states_block = '''        states = [s for s in (states or []) if s]\n        if states:\n            sql += f" AND state IN ({','.join('?' for _ in states)})"\n            params.extend(states)\n'''
cities_block = states_block + '''        cities = [str(city).strip() for city in (cities or []) if str(city).strip()]\n        if cities:\n            sql += " AND (" + " OR ".join("lower(city)=lower(?)" for _ in cities) + ")"\n            params.extend(cities)\n'''
db = replace_once(db, states_block, cities_block, "filtro por estados")

marker = "    def global_catalog_stats(self):\n"
if marker not in db:
    raise RuntimeError("Marcador global_catalog_stats não encontrado")
extra_methods = '''    def global_catalog_group_counts(self, column, closing_from=None):\n        \"\"\"Contagens leves para Estado/Cidade/Modalidade sem carregar o catálogo inteiro.\"\"\"\n        allowed = {"state", "city", "modality"}\n        if column not in allowed:\n            raise ValueError("Agrupamento de catálogo inválido.")\n        sql = f"SELECT {column} AS label, COUNT(*) AS total FROM global_pncp_catalog WHERE trim({column})<>''"\n        params = []\n        if closing_from:\n            sql += " AND (closing_at IS NULL OR date(closing_at)>=date(?))"\n            params.append(str(closing_from)[:10])\n        sql += f" GROUP BY {column} ORDER BY COUNT(*) DESC, {column} ASC"\n        with self.connect() as conn:\n            return [dict(row) for row in conn.execute(sql, params).fetchall()]\n\n    def global_catalog_quality_stats(self):\n        \"\"\"Diagnóstico simples para a Sala de Controle explicar o número exibido ao cliente.\"\"\"\n        with self.connect() as conn:\n            row = conn.execute(\"\"\"\n                SELECT COUNT(*) AS total,\n                       SUM(CASE WHEN closing_at IS NULL THEN 1 ELSE 0 END) AS without_deadline,\n                       SUM(CASE WHEN closing_at IS NOT NULL AND date(closing_at) >= CURRENT_DATE THEN 1 ELSE 0 END) AS future_deadline,\n                       SUM(CASE WHEN closing_at IS NOT NULL AND date(closing_at) < CURRENT_DATE THEN 1 ELSE 0 END) AS expired_deadline,\n                       SUM(CASE WHEN trim(source_url)='' THEN 1 ELSE 0 END) AS without_portal_url,\n                       SUM(CASE WHEN estimated_value IS NULL OR estimated_value<=0 THEN 1 ELSE 0 END) AS without_value\n                FROM global_pncp_catalog\n            \"\"\").fetchone()\n        return {\n            "total": int(row["total"] or 0),\n            "without_deadline": int(row["without_deadline"] or 0),\n            "future_deadline": int(row["future_deadline"] or 0),\n            "expired_deadline": int(row["expired_deadline"] or 0),\n            "without_portal_url": int(row["without_portal_url"] or 0),\n            "without_value": int(row["without_value"] or 0),\n        }\n\n'''
db = db.replace(marker, extra_methods + marker, 1)
write(str(db_path), db)


# ---------------------------------------------------------------------------
# Company: iniciantes não precisam de CNAE, score ou Cartão CNPJ para pesquisar.
# ---------------------------------------------------------------------------
company_path = Path("src/company_ui.py")
company = company_path.read_text(encoding="utf-8")
company = replace_once(
    company,
    '''    st.caption(\n        "Ensine o LicitaNexo sobre sua empresa uma vez. Esse perfil pode priorizar editais, "\n        "apoiar a análise documental e reduzir pesquisas manuais."\n    )\n''',
    '''    st.caption(\n        "Cadastre apenas o básico para organizar sua operação. Você não precisa conhecer CNAE nem decidir agora tudo o que vai vender ao governo."\n    )\n''',
    "caption Minha Empresa",
)
company = replace_once(
    company,
    '["Perfil e Cartão CNPJ", "Documentos", "Fornecedores", "Como o Radar usa meu perfil"]',
    '["Perfil da empresa", "Documentos", "Fornecedores"]',
    "seções Minha Empresa",
)

pattern = re.compile(
    r'    if section == "Perfil e Cartão CNPJ":\n.*?\n    elif section == "Documentos":',
    re.S,
)
replacement = '''    if section == "Perfil da empresa":\n        st.markdown("### Dados básicos")\n        st.caption(\n            "Preencha o que você já sabe. O campo mais importante é descrever, com suas palavras, o que sua empresa consegue fornecer."\n        )\n        profile = get_extended_profile(db, company_id)\n        with st.form("company_essential_profile", clear_on_submit=False, enter_to_submit=False):\n            c1, c2 = st.columns(2)\n            legal_name = c1.text_input("Razão social", value=profile.get("legal_name") or user.get("company_name") or "")\n            trade_name = c2.text_input("Nome fantasia", value=profile.get("trade_name") or "")\n            c3, c4 = st.columns(2)\n            cnpj = c3.text_input("CNPJ", value=profile.get("cnpj") or "", placeholder="00.000.000/0000-00")\n            activity_type = c4.selectbox(\n                "O que faz principalmente?", ["Produtos", "Serviços", "Produtos e serviços"],\n                index=["Produtos", "Serviços", "Produtos e serviços"].index(\n                    profile.get("activity_type") if profile.get("activity_type") in {"Produtos", "Serviços", "Produtos e serviços"} else "Produtos"\n                ),\n            )\n            offerings = st.text_area(\n                "O que sua empresa consegue fornecer?",\n                value=profile.get("offerings") or "",\n                height=150,\n                placeholder="Ex.: papel A4, produtos de limpeza, informática, ferramentas, pneus...",\n                help="Não precisa escrever termos técnicos. Use os nomes que você usa no dia a dia.",\n            )\n            s1, s2 = st.columns(2)\n            service_states = s1.text_input(\n                "UFs onde consegue atender (opcional)",\n                value=profile.get("service_states") or "",\n                placeholder="SP, PR, SC — deixe vazio para Brasil inteiro",\n            )\n            desired_margin = s2.number_input(\n                "Margem desejada (%)", min_value=0.0, max_value=100.0,\n                value=float(profile.get("desired_margin") or 15), step=1.0,\n                help="Será usada mais tarde na precificação. Não interfere na busca de licitações.",\n            )\n            if st.form_submit_button("Salvar dados da empresa", type="primary", width="stretch"):\n                try:\n                    save_extended_profile(\n                        db, company_id,\n                        legal_name=legal_name.strip(), trade_name=trade_name.strip(), cnpj=cnpj.strip(),\n                        activity_type=activity_type, offerings=offerings.strip(),\n                        cnaes=profile.get("cnaes") or "",\n                        procurement_interests=profile.get("procurement_interests") or "",\n                        interest_keywords=profile.get("interest_keywords") or "",\n                        brands=profile.get("brands") or "",\n                        service_states=", ".join(_csv_states(service_states)),\n                        desired_margin=desired_margin,\n                        excluded_keywords=profile.get("excluded_keywords") or "",\n                        profile_search_enabled=False,\n                    )\n                    st.success("Dados salvos. Você já pode continuar pesquisando normalmente.")\n                    st.rerun()\n                except ValueError as error:\n                    st.error(str(error))\n\n        st.info(\n            "Para encontrar oportunidades, o LicitaNexo não exige CNAE, score de aderência nem um perfil completo. "\n            "Use a busca por produto, estado, cidade ou modalidade e descubra aos poucos o que faz sentido vender ao governo."\n        )\n\n    elif section == "Documentos":'''
company, count = pattern.subn(replacement, company, count=1)
if count != 1:
    raise RuntimeError("Não foi possível substituir o perfil empresarial antigo")
write(str(company_path), company)


# ---------------------------------------------------------------------------
# Pipeline: Minha lista é triagem; Meus Editais começa quando o usuário prepara.
# ---------------------------------------------------------------------------
pipeline_path = Path("src/pipeline_ui.py")
pipeline = pipeline_path.read_text(encoding="utf-8")
pipeline = replace_once(
    pipeline,
    '            all_rows = db.pipeline_summaries(company_id, "")\n',
    '            all_rows = [row for row in db.pipeline_summaries(company_id, "") if row.get("stage") != "Nova oportunidade"]\n',
    "exportação de Meus Editais",
)
pipeline = replace_once(
    pipeline,
    '    rows = db.pipeline_summaries(company_id, search)\n',
    '    rows = [row for row in db.pipeline_summaries(company_id, search) if row.get("stage") != "Nova oportunidade"]\n',
    "lista de Meus Editais",
)
pipeline = replace_once(
    pipeline,
    '        st.info("Nenhum edital salvo aqui. Use Buscar Editais e salve somente o que merece sua atenção.")\n',
    '        st.info("Nenhum edital em preparação. Vá até Minha lista e escolha Começar preparação quando uma oportunidade merecer estudo.")\n',
    "mensagem vazia pipeline",
)
old_manual = '''                    db.add_manual_opportunity(\n                        company_id, agency.strip(), obj.strip(), city.strip(), state.strip().upper(),\n                        modality.strip(), certame_at=certame_at, source_url=source_url.strip(),\n                    )\n                    st.success("Edital cadastrado em Meus Editais.")\n'''
new_manual = '''                    opportunity_id = db.add_manual_opportunity(\n                        company_id, agency.strip(), obj.strip(), city.strip(), state.strip().upper(),\n                        modality.strip(), certame_at=certame_at, source_url=source_url.strip(),\n                    )\n                    if opportunity_id:\n                        db.update_stage(company_id, opportunity_id, "Em análise")\n                    st.success("Edital cadastrado e colocado em preparação.")\n'''
pipeline = replace_once(pipeline, old_manual, new_manual, "cadastro manual pipeline")
write(str(pipeline_path), pipeline)


# ---------------------------------------------------------------------------
# App: nova navegação Essential; telas antigas continuam no código só por compatibilidade.
# ---------------------------------------------------------------------------
app_path = Path("app.py")
app = app_path.read_text(encoding="utf-8")
import_marker = "from src.company_ui import company_page\n"
import_block = '''from src.company_ui import company_page\nfrom src.essential_discovery import (\n    search_page as essential_search_page,\n    state_page as essential_state_page,\n    city_page as essential_city_page,\n    modality_page as essential_modality_page,\n    advanced_search_page as essential_advanced_search_page,\n    top50_page as essential_top50_page,\n    my_list_page as essential_my_list_page,\n    preferences_page as essential_preferences_page,\n    radar_page as essential_radar_page,\n)\n'''
app = replace_once(app, import_marker, import_block, "imports Essential")

# Enriquecer o snapshot administrativo.
app = replace_once(
    app,
    '        "modality_counts": modality_counts,\n',
    '        "modality_counts": modality_counts,\n        "state_counts": db.global_catalog_group_counts("state"),\n        "quality": db.global_catalog_quality_stats(),\n',
    "snapshot administrativo",
)

# CSS final da sidebar: todos os itens alinhados; somente selecionado fica preenchido.
brand_start = app.index("def apply_brand():")
brand_end = app.index("\ndef brand_header", brand_start)
brand = app[brand_start:brand_end]
sidebar_css = '''\n        /* RC31.6 · navegação operacional inspirada em apps de busca, com identidade LicitaNexo. */\n        [data-testid="stSidebar"] .stButton button {\n            width:100% !important; min-height:2.72rem !important; justify-content:flex-start !important;\n            background:#FFFFFF !important; color:#172033 !important; border:1px solid #E2E8F0 !important;\n            border-radius:10px !important; box-shadow:none !important; font-weight:750 !important;\n        }\n        [data-testid="stSidebar"] .stButton button * {color:#172033 !important;}\n        [data-testid="stSidebar"] .stButton button[kind="primary"] {\n            background:#10243F !important; border-color:#10243F !important; color:#FFFFFF !important;\n            box-shadow:inset 4px 0 0 #C99A2E !important;\n        }\n        [data-testid="stSidebar"] .stButton button[kind="primary"] * {color:#FFFFFF !important;}\n        [data-testid="stSidebar"] .st-key-sidebar_logout button {\n            justify-content:center !important; background:#F2F5F8 !important; color:#516176 !important;\n            border-color:#DDE4EC !important; box-shadow:none !important;\n        }\n        [data-testid="stSidebar"] .st-key-sidebar_logout button * {color:#516176 !important;}\n        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {margin-top:.45rem !important;}\n'''
if "</style>" not in brand:
    raise RuntimeError("Fechamento do style do apply_brand não encontrado")
brand = brand.replace("</style>", sidebar_css + "\n</style>", 1)
app = app[:brand_start] + brand + app[brand_end:]

# Sala de Controle: deixa explícito total bruto x oportunidades com prazo futuro.
old_metrics = '''        h1, h2, h3, h4 = st.columns(4)\n        h1.metric("Editais no catálogo", catalog_stats["total"])\n        h2.metric("Novos hoje", catalog_stats["new_today"])\n        h3.metric("Com prazo futuro", catalog_stats["open_now"])\n        h4.metric("Status", f"{health_icon} {health_label}")\n'''
new_metrics = '''        quality = pncp_snapshot.get("quality") or {}\n        state_counts = pncp_snapshot.get("state_counts") or []\n        h1, h2, h3, h4, h5 = st.columns(5)\n        h1.metric("Total bruto no banco", catalog_stats["total"])\n        h2.metric("Com prazo futuro", quality.get("future_deadline", catalog_stats.get("open_now", 0)))\n        h3.metric("Sem prazo informado", quality.get("without_deadline", 0))\n        h4.metric("Novos hoje", catalog_stats["new_today"])\n        h5.metric("Status", f"{health_icon} {health_label}")\n        st.info(\n            "O total bruto não é o mesmo número exibido ao cliente. A área de busca mostra o recorte de oportunidades abertas/viáveis; "\n            "use estes indicadores para distinguir catálogo total, registros sem prazo e oportunidades com prazo futuro."\n        )\n'''
app = replace_once(app, old_metrics, new_metrics, "métricas PNCP admin")
modality_caption = '        st.caption(f"Soma das modalidades: {modality_total} · Total do catálogo: {catalog_stats[\'total\']}")\n'
state_block = modality_caption + '''        if state_counts:\n            st.markdown("#### Cobertura por UF")\n            state_frame = pd.DataFrame([\n                {"UF": row.get("label"), "Quantidade": int(row.get("total") or 0)}\n                for row in state_counts\n            ])\n            st.dataframe(state_frame, hide_index=True, width="stretch", height=min(460, 38 + 31 * len(state_frame)))\n        q1, q2 = st.columns(2)\n        q1.metric("Sem URL do portal", quality.get("without_portal_url", 0))\n        q2.metric("Sem valor estimado", quality.get("without_value", 0))\n'''
app = replace_once(app, modality_caption, state_block, "cobertura por UF")

# Substituir apenas a navegação/routing dentro de main().
nav_pattern = re.compile(
    r'    with st\.sidebar:\n.*?    else:\n        admin_page\(user, admin_section or "Visão geral"\)\n',
    re.S,
)
nav_replacement = '''    admin_section = None\n    with st.sidebar:\n        if LOGO_PATH.exists():\n            st.image(str(LOGO_PATH), width="stretch")\n        else:\n            st.markdown("## 🛡️ LicitaNexo")\n        st.markdown(f'<div style="color:#10243F;font-weight:850">LicitaNexo · {APP_VERSION}</div>', unsafe_allow_html=True)\n        st.markdown('<div style="color:#718096;font-size:.80rem;margin-bottom:.7rem">B2G SaaS · Business to Growth</div>', unsafe_allow_html=True)\n        st.markdown(\n            f'<div style="background:#F7F9FC;border:1px solid #E3E8EF;border-radius:12px;padding:.65rem .72rem;margin-bottom:.75rem">'\n            f'<div style="font-weight:850;color:#172033">{_greeting(user)} 👋</div>'\n            f'<div style="font-size:.76rem;color:#718096">{escape(str(user.get("name") or user.get("email") or "Minha conta"))}</div></div>',\n            unsafe_allow_html=True,\n        )\n\n        if _is_admin_user(user):\n            pending = _cached_pending_access_requests()\n            page = "Administração"\n            st.caption(f"Ambiente: {ENVIRONMENT}")\n            st.markdown("##### SALA DE CONTROLE")\n            admin_section = st.radio(\n                "Funções administrativas",\n                ADMIN_SECTIONS,\n                format_func=lambda value: ADMIN_SECTION_LABELS[value],\n                key="admin_sidebar_section",\n                label_visibility="collapsed",\n            )\n        else:\n            explore_pages = [\n                "🔎 Buscar licitações", "🗺️ Por Estado", "📍 Por Cidade",\n                "☰ Por Modalidade", "⚙️ Filtro avançado", "🏆 Top 50",\n            ]\n            work_pages = [\n                "❤️ Minha lista", "📋 Meus Editais", "📄 Analisar Edital",\n                "🏢 Minha Empresa", "📅 Calendário",\n            ]\n            account_pages = ["🔔 Preferências", "📡 Radar de licitações", "💬 Suporte", "👤 Minha Conta"]\n            pages = [*explore_pages, *work_pages, *account_pages]\n            if not allowed:\n                explore_pages, work_pages = [], []\n                account_pages = ["💬 Suporte", "👤 Minha Conta"]\n                pages = account_pages\n\n            requested_page = st.session_state.pop("_navigation_request", None)\n            if requested_page in pages:\n                st.session_state["main_navigation"] = requested_page\n            if st.session_state.get("main_navigation") not in pages:\n                st.session_state["main_navigation"] = pages[0]\n            page = st.session_state["main_navigation"]\n\n            def _nav_group(title, options, group_key):\n                nonlocal page\n                if not options:\n                    return\n                st.caption(title)\n                for index, option in enumerate(options):\n                    selected = page == option\n                    if st.button(\n                        option, key=f"nav_{group_key}_{index}",\n                        type="primary" if selected else "secondary", width="stretch",\n                    ):\n                        st.session_state["main_navigation"] = option\n                        st.rerun()\n\n            _nav_group("EXPLORAR", explore_pages, "explore")\n            _nav_group("MINHA ÁREA", work_pages, "work")\n            _nav_group("CONTA", account_pages, "account")\n\n            guide_page = {\n                "🔎 Buscar licitações": "🔎 Buscar Editais",\n                "📋 Meus Editais": "⭐ Meus Editais",\n            }.get(page, page)\n            if guide_page in {\n                "📅 Calendário", "🔎 Buscar Editais", "⭐ Meus Editais",\n                "📄 Analisar Edital", "🏢 Minha Empresa", "💬 Suporte", "👤 Minha Conta",\n            }:\n                render_sidebar_guides(guide_page)\n\n        if st.button("↪ Sair", key="sidebar_logout", width="stretch"):\n            security.revoke_session(st.session_state.get("security_session_token"))\n            security.event("logout", user.get("email", ""), _client_ip(), True, f'user_id={user.get("id", "")}')\n            st.session_state.clear()\n            st.rerun()\n\n    if page == "🔎 Buscar licitações":\n        essential_search_page(db, user, usage)\n    elif page == "🗺️ Por Estado":\n        essential_state_page(db, user)\n    elif page == "📍 Por Cidade":\n        essential_city_page(db, user)\n    elif page == "☰ Por Modalidade":\n        essential_modality_page(db, user)\n    elif page == "⚙️ Filtro avançado":\n        essential_advanced_search_page(db, user)\n    elif page == "🏆 Top 50":\n        essential_top50_page(db, user)\n    elif page == "❤️ Minha lista":\n        essential_my_list_page(db, user)\n    elif page == "📋 Meus Editais":\n        pipeline_page(db, user)\n    elif page == "📄 Analisar Edital":\n        analysis_page(db, user, usage)\n    elif page == "🏢 Minha Empresa":\n        company_page(db, user)\n    elif page == "📅 Calendário":\n        calendar_page(user)\n    elif page == "🔔 Preferências":\n        essential_preferences_page(db, user)\n    elif page == "📡 Radar de licitações":\n        essential_radar_page(db, user)\n    elif page == "💬 Suporte":\n        support_page(user)\n    elif page == "👤 Minha Conta":\n        essential_account_page(user)\n    else:\n        admin_page(user, admin_section or "Visão geral")\n'''
app, count = nav_pattern.subn(nav_replacement, app, count=1)
if count != 1:
    raise RuntimeError("Não foi possível substituir a navegação principal")
write(str(app_path), app)


# ---------------------------------------------------------------------------
# Discovery pages in light mode, keeping the rest of the application untouched.
# ---------------------------------------------------------------------------
discovery_path = Path("src/essential_discovery.py")
discovery = discovery_path.read_text(encoding="utf-8")
discovery = replace_once(
    discovery,
    '''        <style>\n        .ln-discovery-title''',
    '''        <style>\n        .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#EEF2F6 !important;}\n        [data-testid="stMain"] .block-container{max-width:1180px !important;padding-top:1.45rem !important;}\n        [data-testid="stMain"] h1,[data-testid="stMain"] h2,[data-testid="stMain"] h3,\n        [data-testid="stMain"] p,[data-testid="stMain"] label p,[data-testid="stMain"] .stCaption p{color:#10243F;}\n        [data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"]{background:#FFFFFF;border-color:#DDE4EC !important;box-shadow:0 8px 22px rgba(16,36,63,.06);}\n        .ln-discovery-title''',
    "tema claro discovery",
)
write(str(discovery_path), discovery)


# ---------------------------------------------------------------------------
# Version bump.
# ---------------------------------------------------------------------------
config_path = Path("src/config.py")
config = config_path.read_text(encoding="utf-8")
config = replace_once(
    config,
    'APP_VERSION = "1.0 Essential RC31.5"',
    'APP_VERSION = "1.0 Essential RC31.6"',
    "versão RC31.6",
)
write(str(config_path), config)

print("RC31.6 patch applied")
