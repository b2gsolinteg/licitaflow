import re
import time
import unicodedata
from datetime import date, datetime
from urllib.parse import urlencode

import requests


BASE_URL = "https://dadosabertos.compras.gov.br"
CATMAT_SEARCH_URL = "https://catmat.com.br/api/v1/search"
CATMAT_ITEM_URL = "https://catmat.com.br/api/v1/item"
MATERIAL_CATALOG_URL = f"{BASE_URL}/modulo-material/4_consultarItemMaterial"
SERVICE_CATALOG_URL = f"{BASE_URL}/modulo-servico/6_consultarItemServico"
MATERIAL_PRICES_URL = f"{BASE_URL}/modulo-pesquisa-preco/1_consultarMaterial"
SERVICE_PRICES_URL = f"{BASE_URL}/modulo-pesquisa-preco/3_consultarServico"


class PublicPriceError(RuntimeError):
    pass


def normalize_brand(value):
    original = str(value or "").strip()
    if not original:
        return "Não informada"
    normalized = unicodedata.normalize("NFKD", original)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"\bMARCA\b", " ", normalized.upper())
    normalized = re.sub(r"[^A-Z0-9]+", " ", normalized).strip()
    if normalized in {"", "NAO INFORMADA", "NAO INFORMADO", "SEM", "SEM MARCA", "S M"}:
        return "Não informada"
    # Une siglas grafadas com espaços, como 3 M e H P.
    tokens = normalized.split()
    if len(tokens) <= 4 and all(len(token) == 1 for token in tokens):
        normalized = "".join(tokens)
    return normalized.title() if not normalized.isupper() or len(normalized) > 4 else normalized


class ComprasGovPriceClient:
    def __init__(self, timeout=45):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "LicitaNexo/0.6.8 (+b2gsolucoesintegradas@gmail.com)",
            "Accept": "application/json",
        })

    def _get(self, url, params, attempts=3, not_found_is_empty=False):
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 404 and not_found_is_empty:
                    return {"resultado": [], "totalPaginas": 0}, getattr(
                        response, "url", f"{url}?{urlencode(params)}"
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    raise requests.HTTPError(
                        f"HTTP {response.status_code}", response=response
                    )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("resposta JSON inesperada")
                return payload, getattr(response, "url", f"{url}?{urlencode(params)}")
            except (requests.RequestException, ValueError) as error:
                last_error = error
                if attempt < attempts:
                    retry_after = getattr(getattr(error, "response", None), "headers", {}).get("Retry-After")
                    try:
                        wait = min(float(retry_after), 8)
                    except (TypeError, ValueError):
                        wait = min(2 ** (attempt - 1), 8)
                    time.sleep(wait)
        raise PublicPriceError(
            f"A fonte oficial de preços não respondeu após {attempts} tentativas: {last_error}"
        ) from last_error

    @staticmethod
    def _plain(value):
        value = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in value if not unicodedata.combining(char)).casefold()

    @classmethod
    def _query_variants(cls, query):
        """Variações pequenas ajudam a API quando ela diferencia acentuação."""
        variants = [query]
        accent_aliases = {
            "agua": "água", "alcool": "álcool", "lampada": "lâmpada",
            "oculos": "óculos", "protecao": "proteção", "eletrico": "elétrico",
        }
        plain = cls._plain(query)
        if plain in accent_aliases:
            variants.append(accent_aliases[plain])
        return list(dict.fromkeys(value.strip() for value in variants if value.strip()))

    @staticmethod
    def _date_value(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except (TypeError, ValueError):
            try:
                return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
            except (TypeError, ValueError):
                return None

    def search_catalog(self, query, kind="Material", limit=60):
        query = str(query or "").strip()
        if len(query) < 2:
            return []
        if kind == "Serviço":
            if not query.isdigit():
                raise PublicPriceError(
                    "Nesta etapa, serviços devem ser pesquisados pelo código CATSER. "
                    "A busca textual de materiais já está disponível."
                )
            payload, _ = self._get(SERVICE_CATALOG_URL, {
                "pagina": 1, "tamanhoPagina": limit, "codigoServico": int(query),
                "statusServico": True,
            })
            return [{
                "code": item.get("codigoServico"),
                "description": item.get("nomeServico") or "Serviço sem descrição",
                "group": item.get("nomeClasse") or item.get("nomeGrupo") or "Serviços",
                "kind": "Serviço",
                "catalog_source": "Compras.gov",
            } for item in payload.get("resultado", []) if item.get("codigoServico") is not None]
        if query.isdigit():
            try:
                payload, _ = self._get(f"{CATMAT_ITEM_URL}/{int(query)}", {})
                code = payload.get("codigo_item") or payload.get("codigoItem")
                description = payload.get("descricao_item") or payload.get("descricaoItem")
                if code is not None and description:
                    return [{
                        "code": code,
                        "description": str(description).strip(),
                        "group": payload.get("grupo") or payload.get("nomeGrupo") or "Materiais",
                        "class": payload.get("classe") or payload.get("nomeClasse") or "",
                        "kind": "Material",
                        "catalog_source": "Portal CATMAT",
                    }]
            except PublicPriceError:
                # O código ainda será procurado na API oficial pela contingência abaixo.
                pass
        # O índice público do Portal CATMAT foi criado especificamente para busca
        # textual/fuzzy. Ele apenas descobre o código; preços e fornecedores continuam
        # vindo da API oficial do Compras.gov.
        try:
            payload, _ = self._get(CATMAT_SEARCH_URL, {
                "q": query, "size": min(max(int(limit), 1), 100),
            })
            hits = payload.get("hits") or []
            if isinstance(hits, list):
                candidates = []
                seen = set()
                query_plain = self._plain(query)
                query_words = [word for word in query_plain.split() if len(word) > 1]
                for item in hits:
                    code = item.get("codigo_item") or item.get("codigoItem")
                    description = str(
                        item.get("descricao_item") or item.get("descricaoItem") or ""
                    ).strip()
                    if code is None or not description or str(code) in seen:
                        continue
                    description_plain = self._plain(description)
                    # A busca fuzzy do catálogo pode interpretar termos com OR. O
                    # LicitaNexo exige todos os termos para evitar que "água mineral"
                    # devolva sal mineral, suplemento mineral etc.
                    if query_words and not all(word in description_plain for word in query_words):
                        continue
                    seen.add(str(code))
                    phrase_position = description_plain.find(query_plain)
                    relevance = 1000 if phrase_position >= 0 else 0
                    relevance += 300 if description_plain.startswith(query_plain) else 0
                    relevance += max(0, 100 - (phrase_position if phrase_position >= 0 else 100))
                    relevance += float(item.get("score") or 0)
                    candidates.append({
                        "code": code,
                        "description": description,
                        "group": item.get("grupo") or item.get("nomeGrupo") or "Materiais",
                        "class": item.get("classe") or item.get("nomeClasse") or "",
                        "kind": "Material",
                        "catalog_source": "Portal CATMAT",
                        "_relevance": relevance,
                    })
                if candidates:
                    candidates.sort(key=lambda candidate: (
                        -candidate.pop("_relevance"), candidate["description"]
                    ))
                    return candidates[:limit]
        except PublicPriceError:
            # Contingência abaixo: consulta diretamente o catálogo oficial.
            pass
        words = [word for word in self._plain(query).split() if word]
        by_code = {}
        for variant in self._query_variants(query):
            for page in range(1, 4):
                params = {"pagina": page, "tamanhoPagina": 500, "statusItem": "true"}
                if query.isdigit():
                    params["codigoItem"] = int(query)
                else:
                    params["descricaoItem"] = variant
                payload, _ = self._get(MATERIAL_CATALOG_URL, params)
                result = payload.get("resultado") or payload.get("resultados") or []
                if not isinstance(result, list):
                    raise PublicPriceError("O catálogo oficial devolveu um formato não reconhecido.")
                for item in result:
                    description = str(item.get("descricaoItem") or "").strip()
                    plain_description = self._plain(description)
                    if words and not all(word in plain_description for word in words):
                        continue
                    code = item.get("codigoItem")
                    if code is None:
                        continue
                    # Quanto mais cedo a expressão aparece, mais relevante é a sugestão.
                    position = plain_description.find(self._plain(query))
                    score = 1000 if plain_description == self._plain(query) else 0
                    score += 300 if plain_description.startswith(self._plain(query)) else 0
                    score += max(0, 100 - (position if position >= 0 else 100))
                    score -= len(description) / 1000
                    by_code[str(code)] = {
                        "code": code, "description": description,
                        "group": item.get("nomePdm") or item.get("nomeClasse") or "Materiais",
                        "class": item.get("nomeClasse") or "",
                        "kind": "Material", "score": score,
                        "catalog_source": "Compras.gov",
                    }
                total_pages = int(payload.get("totalPaginas") or 0)
                if (not result or (total_pages and page >= total_pages)
                        or (not total_pages and len(result) < 500)):
                    break
        candidates = sorted(
            by_code.values(), key=lambda item: (-item["score"], item["description"])
        )
        for candidate in candidates:
            candidate.pop("score", None)
        return candidates[:limit]

    def fetch_prices(self, catalog_code, state="", kind="Material", start_date=None,
                     max_pages=30):
        url = SERVICE_PRICES_URL if kind == "Serviço" else MATERIAL_PRICES_URL
        rows = []
        cutoff = self._date_value(start_date)
        self.last_fetch_stats = {"processed": 0, "old": 0, "without_result": 0}
        for page in range(1, max_pages + 1):
            params = {
                "pagina": page, "tamanhoPagina": 100,
                "codigoItemCatalogo": int(catalog_code), "dataResultado": "true",
            }
            if state:
                params["estado"] = state.upper()
            payload, evidence_url = self._get(url, params, not_found_is_empty=True)
            result = payload.get("resultado", [])
            for item in result:
                self.last_fetch_stats["processed"] += 1
                result_date = self._date_value(item.get("dataResultado") or item.get("dataCompra"))
                if cutoff and (not result_date or result_date < cutoff):
                    self.last_fetch_stats["old"] += 1
                    continue
                price = item.get("precoUnitario")
                supplier = str(item.get("nomeFornecedor") or "").strip()
                if price is None or not supplier:
                    self.last_fetch_stats["without_result"] += 1
                    continue
                procurement_form = str(item.get("forma") or "").upper()
                price_nature = "Ata/SRP" if "SISRP" in procurement_form else "Homologado"
                rows.append({
                    "opportunity_id": None,
                    "query": "",
                    "catalog_code": str(item.get("codigoItemCatalogo") or catalog_code),
                    "purchase_id": str(item.get("idCompra") or ""),
                    "item_number": str(item.get("numeroItemCompra") or ""),
                    "source_type": price_nature,
                    "description": item.get("descricaoItem") or "",
                    "agency": item.get("nomeOrgao") or item.get("nomeUasg") or "",
                    "city": item.get("municipio") or "",
                    "state": item.get("estado") or "",
                    "quantity": item.get("quantidade"),
                    "unit": item.get("nomeUnidadeFornecimento") or item.get("nomeUnidadeMedida")
                            or item.get("siglaUnidadeMedida") or "",
                    "estimated_unit_value": None,
                    "homologated_unit_value": price,
                    "supplier": supplier,
                    "supplier_tax_id": item.get("niFornecedor") or "",
                    "procurement_form": item.get("forma") or "",
                    "brand": item.get("marca") or "",
                    "brand_normalized": normalize_brand(item.get("marca")),
                    "source_url": evidence_url,
                    "published_at": item.get("dataResultado") or item.get("dataCompra"),
                })
            total_pages = int(payload.get("totalPaginas") or 0)
            if not result or (total_pages and page >= total_pages):
                break
        return rows
