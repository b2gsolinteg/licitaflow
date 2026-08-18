from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    if old not in source:
        raise RuntimeError(f"Trecho esperado não encontrado em {path}: {old[:120]!r}")
    if source.count(old) != 1:
        raise RuntimeError(f"Trecho não é único em {path}: {source.count(old)} ocorrências")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


app = ROOT / "app.py"
pncp_items = ROOT / "src" / "pncp_items.py"
config = ROOT / "src" / "config.py"
ux_tests = ROOT / "tests" / "test_rc31_3_ux.py"

# 1) Função leve de preview: uma única página do PNCP, sem baixar o edital inteiro de itens.
pncp_preview = r'''

def fetch_contract_items_preview(
    control_number: str,
    *,
    limit: int = 4,
    timeout: int = 7,
    session=None,
) -> dict:
    """Busca apenas a primeira página de itens para cards de pesquisa rápida.

    Diferente de ``fetch_contract_items``, esta função não percorre todas as páginas.
    O objetivo é manter o Radar responsivo e exibir um resumo oficial do PNCP antes
    de o usuário decidir abrir ou salvar a oportunidade.
    """
    parsed = parse_pncp_control_number(control_number)
    if not parsed:
        raise PncpItemsError("Número de controle PNCP inválido para consultar os itens.")
    cnpj, year, sequence = parsed
    client = session or requests.Session()
    if session is None:
        client.headers.update({
            "User-Agent": "LicitaNexo/1.0 (+b2gsolucoesintegradas@gmail.com)",
            "Accept": "application/json",
        })
    endpoint = f"{PNCP_DATA_URL}/orgaos/{cnpj}/compras/{year}/{sequence}/itens"
    size = max(1, min(int(limit or 4), 20))
    response = None
    last_error = None

    # Preview não pode transformar a busca em uma espera longa. Faz no máximo
    # uma repetição curta para erros transitórios e devolve falha isolada por card.
    for attempt in range(2):
        try:
            response = client.get(
                endpoint,
                params={"pagina": 1, "tamanhoPagina": size},
                timeout=max(2, int(timeout)),
            )
            if response.status_code == 204:
                return {
                    "items": [], "item_count": 0, "count_known": True,
                    "has_more": False, "items_error": "",
                }
            if response.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                last_error = f"PNCP respondeu {response.status_code}"
                time.sleep(0.35)
                continue
            response.raise_for_status()
            break
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            last_error = str(exc)
            if attempt == 0:
                time.sleep(0.25)

    if response is None or response.status_code >= 400:
        raise PncpItemsError(
            f"Itens temporariamente indisponíveis no PNCP. {last_error or ''}".strip()
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise PncpItemsError("O PNCP retornou os itens em formato inesperado.") from exc

    total_value = None
    if isinstance(payload, list):
        raw_items = payload
        total_value = len(raw_items)
    elif isinstance(payload, dict):
        raw_items = payload.get("itens") or payload.get("data") or payload.get("items") or []
        for key in (
            "totalRegistros", "totalElementos", "totalItems", "total",
            "quantidadeRegistros", "totalCount",
        ):
            if payload.get(key) is not None:
                total_value = payload.get(key)
                break
    else:
        raw_items = []

    if not isinstance(raw_items, list):
        raise PncpItemsError("O PNCP não devolveu a lista de itens no formato esperado.")

    normalized = []
    seen = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        item = _normalize_item(raw, control_number)
        if item["source_reference"] in seen:
            continue
        seen.add(item["source_reference"])
        normalized.append(item)
        if len(normalized) >= size:
            break

    count_known = total_value is not None
    try:
        total = max(int(total_value), len(normalized)) if count_known else len(normalized)
    except (TypeError, ValueError):
        total = len(normalized)
        count_known = False
    has_more = total > len(normalized) if count_known else len(raw_items) >= size
    return {
        "items": normalized,
        "item_count": total,
        "count_known": count_known,
        "has_more": has_more,
        "items_error": "",
    }
'''
replace_once(
    pncp_items,
    "\ndef fetch_contract_documents(control_number: str, *, timeout: int = 20, session=None) -> list[dict]:\n",
    pncp_preview + "\n\ndef fetch_contract_documents(control_number: str, *, timeout: int = 20, session=None) -> list[dict]:\n",
)

# 2) Batch concorrente isolado do Streamlit: só a página visível do Radar.
radar_module = r'''from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from .pncp_items import PncpItemsError, fetch_contract_items_preview


def fetch_radar_item_summaries(
    control_numbers,
    *,
    max_workers: int = 6,
    preview_items: int = 4,
    fetcher=fetch_contract_items_preview,
) -> dict[str, dict]:
    """Busca previews dos itens em paralelo sem deixar uma falha quebrar o Radar."""
    controls = list(dict.fromkeys(
        str(value or "").strip() for value in control_numbers if str(value or "").strip()
    ))
    result = {
        control: {
            "items": [], "item_count": 0, "count_known": False,
            "has_more": False, "items_error": "",
        }
        for control in controls
    }
    if not controls:
        return result

    workers = max(1, min(int(max_workers or 1), 8, len(controls)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(fetcher, control, limit=preview_items): control
            for control in controls
        }
        for future in as_completed(futures):
            control = futures[future]
            try:
                pack = future.result() or {}
                result[control] = {
                    "items": list(pack.get("items") or [])[: max(1, int(preview_items))],
                    "item_count": int(pack.get("item_count") or 0),
                    "count_known": bool(pack.get("count_known")),
                    "has_more": bool(pack.get("has_more")),
                    "items_error": str(pack.get("items_error") or ""),
                }
            except (PncpItemsError, RuntimeError, ValueError) as exc:
                result[control]["items_error"] = str(exc)
            except Exception:
                result[control]["items_error"] = "Itens temporariamente indisponíveis."
    return result
'''
(ROOT / "src" / "radar_items.py").write_text(radar_module, encoding="utf-8")

# 3) Imports e caches do Radar.
replace_once(
    app,
    "from src.pncp import MODALITIES, PncpClient\n",
    "from src.pncp import MODALITIES, PncpClient\n"
    "from src.pncp_items import PncpItemsError, fetch_contract_items\n"
    "from src.radar_items import fetch_radar_item_summaries\n",
)

cache_anchor = '''@st.cache_data(ttl=30, show_spinner=False)\ndef _cached_admin_pncp_snapshot():\n'''
cache_insert = '''@st.cache_data(ttl=900, show_spinner=False)\ndef _cached_radar_item_summaries(control_numbers):\n    return fetch_radar_item_summaries(\n        tuple(control_numbers or ()), max_workers=6, preview_items=4\n    )\n\n\n@st.cache_data(ttl=1800, show_spinner=False)\ndef _cached_full_contract_items(control_number):\n    control_number = str(control_number or "").strip()\n    if not control_number:\n        return []\n    return fetch_contract_items(control_number, timeout=12, page_size=200)\n\n\n'''
replace_once(app, cache_anchor, cache_insert + cache_anchor)

# 4) Sidebar: ocupa a largura toda, mantém altura integral e deixa o item ativo evidente.
old_sidebar_css = r'''        [data-testid="stSidebar"] div[role="radiogroup"] {
            gap:.12rem !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label {
            min-height:2.05rem !important;
            padding:.18rem .32rem !important;
            border-radius:7px !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label p {
            font-size:.94rem !important;
            line-height:1.20rem !important;
        }
'''
new_sidebar_css = r'''        /* MENU LATERAL TOTALMENTE PREENCHIDO: cada opção usa 100% da largura útil. */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child {
            min-height:100vh !important;
            height:100vh !important;
        }

        [data-testid="stSidebar"] [data-testid="stRadio"],
        [data-testid="stSidebar"] div[role="radiogroup"] {
            width:100% !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] {
            gap:.18rem !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label {
            width:100% !important;
            box-sizing:border-box !important;
            min-height:2.62rem !important;
            padding:.42rem .58rem !important;
            border-radius:9px !important;
            border:1px solid #E5EAF0 !important;
            background:#F8FAFC !important;
            transition:background .12s ease,border-color .12s ease,box-shadow .12s ease !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background:#F2F5F8 !important;
            border-color:#D5DDE7 !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background:#10243F !important;
            border-color:#C99A2E !important;
            box-shadow:inset 4px 0 0 #C99A2E !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label p {
            font-size:.94rem !important;
            line-height:1.22rem !important;
            width:100% !important;
        }

        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
            color:#FFFFFF !important;
            font-weight:800 !important;
        }
'''
replace_once(app, old_sidebar_css, new_sidebar_css)

# 5) CSS compacto para os itens já abertos nos cards.
radar_css = r'''
        /* Radar rápido: itens oficiais já visíveis no resultado, sem abrir outra tela. */
        .radar-items-box {
            margin:.72rem 0 .62rem;
            padding:.68rem .72rem;
            background:#F8FBFF;
            border:1px solid #DDE7F2;
            border-radius:11px;
        }
        .radar-items-title {
            color:#17324F;
            font-weight:850;
            font-size:.84rem;
            margin-bottom:.28rem;
        }
        .radar-item-row {
            display:grid;
            grid-template-columns:minmax(0,1fr) 88px 108px;
            gap:.45rem;
            align-items:start;
            padding:.34rem 0;
            border-top:1px solid #E7EDF5;
        }
        .radar-item-row:first-of-type {border-top:0;}
        .radar-item-name {
            color:#2B4057;
            font-size:.78rem;
            line-height:1.28;
            overflow-wrap:anywhere;
        }
        .radar-item-qty,.radar-item-price {
            color:#607086;
            font-size:.72rem;
            line-height:1.28;
            text-align:right;
        }
        .radar-item-price {color:#17324F;font-weight:800;}
        .radar-items-more {color:#738196;font-size:.71rem;margin-top:.32rem;}
        @media(max-width:760px) {
            .radar-item-row {grid-template-columns:1fr;gap:.1rem;}
            .radar-item-qty,.radar-item-price {text-align:left;}
        }
'''
replace_once(app, "\n\n</style>\n    \"\"\", unsafe_allow_html=True)\n", radar_css + "\n\n</style>\n    \"\"\", unsafe_allow_html=True)\n")

# 6) Helpers de renderização antes da busca.
search_anchor = "\ndef search_page(user):\n"
search_helpers = r'''

def _radar_quantity_text(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return "—"
    if number.is_integer():
        return f"{int(number):,}".replace(",", ".")
    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _radar_item_price_text(row: dict) -> str:
    if row.get("confidential"):
        return "Preço sigiloso"
    try:
        price = float(row.get("unit_price") or 0)
    except (TypeError, ValueError):
        price = 0
    return format_brl(price) if price > 0 else "Sem preço publicado"


def _render_radar_item_summary(opportunity: dict, pack: dict) -> None:
    """Mostra itens oficiais já abertos para a decisão acontecer no próprio Radar."""
    control = str(opportunity.get("pncp_control_number") or "").strip()
    preview = list(pack.get("items") or [])
    total = int(pack.get("item_count") or len(preview))
    count_known = bool(pack.get("count_known"))
    has_more = bool(pack.get("has_more")) or total > len(preview)
    error = str(pack.get("items_error") or "").strip()

    if count_known:
        count_label = f"{total} item(ns)"
    elif preview:
        count_label = f"{max(total, len(preview))}+ item(ns)"
    else:
        count_label = "itens oficiais"

    lines = [
        f'<div class="radar-items-box"><div class="radar-items-title">📦 Itens da licitação · {escape(count_label)}</div>'
    ]
    if error:
        lines.append('<div class="radar-items-more">Itens temporariamente indisponíveis no PNCP. O restante do resultado continua acessível.</div>')
    elif not preview:
        lines.append('<div class="radar-items-more">O PNCP não publicou itens estruturados para esta contratação.</div>')
    else:
        for row in preview:
            number = escape(str(row.get("number") or ""))
            description = str(row.get("description") or "Item não descrito").strip()
            if len(description) > 150:
                description = description[:147].rstrip() + "..."
            description = escape(description)
            quantity = _radar_quantity_text(row.get("quantity"))
            unit = escape(str(row.get("unit_measure") or "").strip())
            qty_label = f"{quantity} {unit}".strip()
            price_label = escape(_radar_item_price_text(row))
            prefix = f"<b>{number}.</b> " if number else ""
            lines.append(
                f'<div class="radar-item-row"><div class="radar-item-name">{prefix}{description}</div>'
                f'<div class="radar-item-qty">{escape(qty_label)}</div>'
                f'<div class="radar-item-price">{price_label}</div></div>'
            )
        remaining = max(total - len(preview), 0) if count_known else 0
        if remaining:
            lines.append(f'<div class="radar-items-more">+ {remaining} outro(s) item(ns)</div>')
        elif has_more and not count_known:
            lines.append('<div class="radar-items-more">Há outros itens nesta contratação.</div>')
    lines.append("</div>")
    st.markdown("".join(lines), unsafe_allow_html=True)

    if not control or not preview or not has_more:
        return

    state_key = f"radar_all_items_open_{opportunity.get('id') or control}"
    opened = bool(st.session_state.get(state_key))
    label = "Mostrar apenas o resumo" if opened else "Ver todos os itens"
    if st.button(label, key=f"radar_all_items_button_{opportunity.get('id') or control}", width="stretch"):
        st.session_state[state_key] = not opened
        st.rerun()

    if not opened:
        return
    try:
        with st.spinner("Carregando a lista completa de itens do PNCP..."):
            full_items = _cached_full_contract_items(control)
    except PncpItemsError:
        st.caption("Não foi possível abrir a lista completa agora. O resumo acima continua disponível.")
        return
    if not full_items:
        st.caption("Nenhum item estruturado adicional foi publicado pelo PNCP.")
        return

    rows = []
    for row in full_items[:120]:
        rows.append({
            "Item": row.get("number") or "",
            "Descrição": row.get("description") or "",
            "Quantidade": _radar_quantity_text(row.get("quantity")),
            "Unidade": row.get("unit_measure") or "",
            "Preço ref.": _radar_item_price_text(row),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=min(360, 38 + 34 * len(rows)))
    if len(full_items) > 120:
        st.caption(f"Mostrando 120 de {len(full_items)} itens para manter a tela rápida.")
'''
replace_once(app, search_anchor, search_helpers + search_anchor)

# 7) Página com menos cards por lote e previews concorrentes apenas da página visível.
replace_once(app, "    per_page = 20\n", "    per_page = 8\n")
replace_once(
    app,
    "    page_items = items[first:first + per_page]\n\n    for index in range(0, len(page_items), 2):\n",
    "    page_items = items[first:first + per_page]\n"
    "    visible_controls = tuple(str(row.get(\"pncp_control_number\") or \"\").strip() for row in page_items)\n"
    "    item_preview_map = _cached_radar_item_summaries(visible_controls)\n\n"
    "    for index in range(0, len(page_items), 2):\n",
)

card_anchor = '''                    st.caption(f"**Fonte:** {source_name} · **Portal de disputa:** {portal_label}")\n                    if st.button("⭐ Salvar em Meus Editais", key=f'open_catalog_{item["id"]}', type="primary", width="stretch"):\n'''
card_new = '''                    st.caption(f"**Fonte:** {source_name} · **Portal de disputa:** {portal_label}")\n                    control_number = str(item.get("pncp_control_number") or "").strip()\n                    _render_radar_item_summary(\n                        item,\n                        item_preview_map.get(control_number, {\n                            "items": [], "item_count": 0, "count_known": False,\n                            "has_more": False, "items_error": "",\n                        }),\n                    )\n                    if st.button("⭐ Salvar em Meus Editais", key=f'open_catalog_{item["id"]}', type="primary", width="stretch"):\n'''
replace_once(app, card_anchor, card_new)

# 8) Versão.
replace_once(config, 'APP_VERSION = "1.0 Essential RC31.4"', 'APP_VERSION = "1.0 Essential RC31.5"')
replace_once(ux_tests, 'APP_VERSION = "1.0 Essential RC31.4"', 'APP_VERSION = "1.0 Essential RC31.5"')

# 9) Testes específicos do fluxo rápido e da resiliência dos itens.
radar_tests = r'''import unittest
from pathlib import Path

from src.pncp_items import PncpItemsError, fetch_contract_items_preview
from src.radar_items import fetch_radar_item_summaries


ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "data": [
                {
                    "numeroItem": index,
                    "descricao": f"Produto {index}",
                    "quantidade": 10 * index,
                    "unidadeMedida": "UN",
                    "valorUnitarioEstimado": 5.5 * index,
                }
                for index in range(1, 5)
            ],
            "totalElementos": 17,
        }


class FakeSession:
    headers = {}

    def get(self, url, params=None, timeout=None):
        assert params["pagina"] == 1
        assert params["tamanhoPagina"] == 4
        assert timeout <= 10
        return FakeResponse()


class RadarItemPreviewTests(unittest.TestCase):
    def test_preview_uses_only_first_page_and_exposes_total(self):
        pack = fetch_contract_items_preview(
            "12345678000199-1-10/2026", limit=4, timeout=5, session=FakeSession()
        )
        self.assertEqual(4, len(pack["items"]))
        self.assertEqual(17, pack["item_count"])
        self.assertTrue(pack["count_known"])
        self.assertTrue(pack["has_more"])
        self.assertEqual("Produto 1", pack["items"][0]["description"])

    def test_batch_keeps_other_cards_when_one_preview_fails(self):
        def fake_fetch(control, limit=4):
            if control == "B":
                raise PncpItemsError("falha isolada")
            return {
                "items": [{"description": f"Item {control}"}],
                "item_count": 9,
                "count_known": True,
                "has_more": True,
                "items_error": "",
            }

        result = fetch_radar_item_summaries(
            ["A", "B", "C"], max_workers=3, preview_items=4, fetcher=fake_fetch
        )
        self.assertEqual("Item A", result["A"]["items"][0]["description"])
        self.assertEqual("Item C", result["C"]["items"][0]["description"])
        self.assertIn("falha isolada", result["B"]["items_error"])


class Rc315FastUxContracts(unittest.TestCase):
    def test_search_renders_open_item_summary_before_actions(self):
        source = ROOT.joinpath("app.py").read_text(encoding="utf-8")
        self.assertIn("📦 Itens da licitação", source)
        self.assertIn("_cached_radar_item_summaries", source)
        self.assertIn("_render_radar_item_summary", source)
        self.assertIn("per_page = 8", source)
        self.assertIn("Ver todos os itens", source)

    def test_sidebar_navigation_fills_available_width(self):
        source = ROOT.joinpath("app.py").read_text(encoding="utf-8")
        self.assertIn("MENU LATERAL TOTALMENTE PREENCHIDO", source)
        self.assertIn('label:has(input:checked)', source)
        self.assertIn("width:100% !important", source)
        self.assertIn("min-height:100vh !important", source)

    def test_version_is_rc31_5(self):
        source = ROOT.joinpath("src", "config.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.0 Essential RC31.5"', source)


if __name__ == "__main__":
    unittest.main()
'''
(ROOT / "tests" / "test_rc31_5_fast_radar.py").write_text(radar_tests, encoding="utf-8")

print("RC31.5 fast radar/sidebar patch aplicado")
