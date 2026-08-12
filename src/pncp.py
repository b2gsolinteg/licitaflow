from datetime import date
import random
import re
import time
import unicodedata
import requests

from .sources import infer_portal_name, parse_pncp_control_number


BASE_URL = "https://pncp.gov.br/api/consulta/v1"
DATA_URL = "https://pncp.gov.br/api/pncp/v1"
MODALITIES = {
    "Leilão eletrônico": 1,
    "Diálogo competitivo": 2,
    "Concurso": 3,
    "Concorrência eletrônica": 4,
    "Concorrência presencial": 5,
    "Pregão eletrônico": 6,
    "Pregão presencial": 7,
    "Dispensa de licitação": 8,
    "Inexigibilidade": 9,
    "Manifestação de interesse": 10,
    "Pré-qualificação": 11,
    "Credenciamento": 12,
    "Leilão presencial": 13,
}


def _plain_modality(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


_MODALITY_CANONICAL = {
    _plain_modality(name): name for name in MODALITIES
}
# O PNCP costuma devolver nomes com hífen (ex.: “Pregão - Eletrônico”),
# enquanto a interface usa nomes mais limpos. Ambos passam a representar a mesma modalidade.
_MODALITY_CANONICAL.update({
    "pregao eletronico": "Pregão eletrônico",
    "pregao presencial": "Pregão presencial",
    "concorrencia eletronica": "Concorrência eletrônica",
    "concorrencia presencial": "Concorrência presencial",
    "leilao eletronico": "Leilão eletrônico",
    "leilao presencial": "Leilão presencial",
    "dialogo competitivo": "Diálogo competitivo",
    "dispensa de licitacao": "Dispensa de licitação",
    "dispensa": "Dispensa de licitação",
    "manifestacao de interesse": "Manifestação de interesse",
    "pre qualificacao": "Pré-qualificação",
})


def canonical_modality_name(value):
    """Normaliza o nome da modalidade para pesquisa e armazenamento consistentes."""
    text = str(value or "").strip()
    if not text:
        return ""
    return _MODALITY_CANONICAL.get(_plain_modality(text), text)


class PncpTemporaryError(RuntimeError):
    def __init__(self, message, status_code=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

    @property
    def is_rate_limit(self):
        return self.status_code == 429


class PncpClient:
    def __init__(self, mode="publication", timeout=30, page_delay=1.4, max_attempts=4):
        if mode not in {"publication", "open_proposals", "update"}:
            raise ValueError("Modo de consulta PNCP inválido.")
        self.mode = mode
        self.timeout = timeout
        self.page_delay = page_delay
        self.max_attempts = max_attempts
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "LicitaNexo/0.6.4 (+b2gsolucoesintegradas@gmail.com)",
            "Accept": "application/json",
        })

    def fetch_modalities(self):
        """Retorna modalidades ativas do PNCP; usa a lista local como contingência."""
        try:
            response = self._get(f"{DATA_URL}/modalidades", {"statusAtivo": "true"})
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                result = {}
                for item in payload:
                    if not isinstance(item, dict) or not item.get("id") or not item.get("nome"):
                        continue
                    result[str(item["nome"]).strip()] = int(item["id"])
                if result:
                    return result
        except Exception:
            pass
        return dict(MODALITIES)

    @staticmethod
    def checkpoint_mode_from_key(value):
        text = str(value or "").strip()
        if PncpClient.parse_range_checkpoint_key(text) is None:
            return None
        match = re.fullmatch(
            r"(publication|open_proposals|update):range:\d{4}-\d{2}-\d{2}:\d{4}-\d{2}-\d{2}",
            text,
        )
        return match.group(1) if match else None

    @staticmethod
    def parse_range_checkpoint_key(value):
        match = re.fullmatch(
            r"(?:publication|open_proposals|update):range:(\d{4}-\d{2}-\d{2}):(\d{4}-\d{2}-\d{2})",
            str(value or "").strip(),
        )
        if not match:
            return None
        try:
            start_date = date.fromisoformat(match.group(1))
            end_date = date.fromisoformat(match.group(2))
        except ValueError:
            return None
        if start_date > end_date:
            return None
        return start_date, end_date
    def sync(self, start_date, end_date, modality_code, state, checkpoint_getter,
             page_saver, checkpoint_saver, progress=None, max_pages_per_run=None, item_filter=None):
        """Sincroniza o intervalo em uma consulta paginada e retomável.

        Consultar o período inteiro reduz chamadas vazias e limitações 429. Cada página
        é salva antes da próxima requisição, preservando o progresso em caso de falha.
        """
        stats = {
            "pages": 0, "received": 0, "saved": 0,
            "days_completed": 0, "partial": False, "errors": [],
            "current_page": 0, "total_pages": 0,
        }
        # Prefixo próprio impede que checkpoints antigos, gravados por dia,
        # sejam confundidos com a nova sincronização por intervalo.
        mode = getattr(self, "mode", "publication")
        checkpoint_key = f"{mode}:range:{start_date.isoformat()}:{end_date.isoformat()}"
        checkpoint = checkpoint_getter(checkpoint_key)
        if checkpoint and checkpoint["completed"]:
            stats["days_completed"] = (end_date - start_date).days + 1
            return stats
        page = checkpoint["next_page"] if checkpoint else 1
        accumulated = checkpoint["items_saved"] if checkpoint else 0
        while True:
            if max_pages_per_run is not None and stats["pages"] >= max_pages_per_run:
                stats["partial"] = True
                return stats
            stats["current_page"] = page
            if progress:
                progress(end_date, page, stats)
            try:
                items, total_pages = self.fetch_page(
                    start_date, end_date, modality_code, state, page
                )
            except PncpTemporaryError as error:
                message = f"página {page}: {error}"
                checkpoint_saver(checkpoint_key, page, False, accumulated, message)
                stats["partial"] = True
                stats["errors"].append(message)
                return stats
            received_count = len(items)
            if item_filter is not None:
                items = [item for item in items if item_filter(item)]
            saved = page_saver(items) if items else 0
            stats["pages"] += 1
            stats["received"] += received_count
            stats["saved"] += saved
            stats["skipped"] = stats.get("skipped", 0) + max(0, received_count - len(items))
            stats["total_pages"] = total_pages or stats["total_pages"]
            accumulated += saved
            completed = page >= total_pages if total_pages else received_count < 50
            checkpoint_saver(checkpoint_key, page + 1, completed, accumulated, "")
            if progress:
                progress(end_date, page, stats)
            if completed:
                stats["days_completed"] = (end_date - start_date).days + 1
                return stats
            page += 1
            time.sleep(self.page_delay + random.uniform(0.2, 0.8))

    def fetch_page(self, start_date, end_date, modality_code, state, page):
        params = {
            "dataFinal": end_date.strftime("%Y%m%d"),
            "codigoModalidadeContratacao": modality_code,
            "pagina": page,
            # Mantém o tamanho de página conservador já validado em produção.
            # Valores maiores podem ser rejeitados por este endpoint do PNCP.
            "tamanhoPagina": 50,
        }
        endpoint = {"publication": "publicacao", "open_proposals": "proposta", "update": "atualizacao"}[self.mode]
        if self.mode in {"publication", "update"}:
            params["dataInicial"] = start_date.strftime("%Y%m%d")
        if state:
            params["uf"] = state
        response = self._get(f"{BASE_URL}/contratacoes/{endpoint}", params)
        if response.status_code == 204:
            return [], 0
        try:
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("conteúdo JSON inesperado")
            # Em propostas abertas, a publicação pode ser antiga e a disputa ainda
            # estar vigente. Por isso nunca filtramos localmente por data de publicação.
            items = [self._normalize(item) for item in payload.get("data", [])]
            return items, int(payload.get("totalPaginas") or 0)
        except (requests.RequestException, ValueError) as error:
            raise PncpTemporaryError(f"Resposta inválida do PNCP: {error}") from error

    def _get(self, url, params):
        """GET conservador para não martelar o PNCP.

        Em 429 respeita Retry-After quando disponível e aumenta o intervalo entre
        tentativas. Em indisponibilidade temporária usa backoff curto. O objetivo da
        sincronização é completar ao longo do tempo, não ser agressiva.
        """
        last_error = "Falha temporária"
        last_status = None
        last_retry_after = None
        for attempt in range(self.max_attempts):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                retryable_statuses = {429, 500, 502, 503, 504}
                if response.status_code not in retryable_statuses:
                    return response
                last_status = response.status_code
                header = response.headers.get("Retry-After")
                try:
                    header_wait = float(header)
                except (TypeError, ValueError):
                    header_wait = None
                if response.status_code == 429:
                    # 429 pede desaceleração. Esperas moderadas evitam dezenas de
                    # novas chamadas enquanto o limite do PNCP ainda está ativo.
                    wait = header_wait if header_wait is not None else 12 * (attempt + 1)
                    wait = min(max(wait, 8), 45) + random.uniform(0.5, 1.5)
                    last_retry_after = wait
                    last_error = "O PNCP limitou temporariamente as consultas (erro 429)"
                else:
                    wait = header_wait if header_wait is not None else 3 * (2 ** attempt)
                    wait = min(max(wait, 2), 20) + random.uniform(0.2, 1.0)
                    last_retry_after = wait
                    last_error = f"O serviço do PNCP está temporariamente indisponível (erro {response.status_code})"
            except (requests.Timeout, requests.ConnectionError) as error:
                last_status = None
                wait = min(3 * (2 ** attempt), 20) + random.uniform(0.2, 1.0)
                last_retry_after = wait
                last_error = f"O PNCP demorou para responder: {error.__class__.__name__}"
            if attempt < self.max_attempts - 1:
                time.sleep(wait)
        raise PncpTemporaryError(
            f"{last_error} após {self.max_attempts} tentativas. "
            "O progresso foi salvo e a próxima execução continuará do ponto correto.",
            status_code=last_status, retry_after=last_retry_after,
        )

    @staticmethod
    def parse_control_number(control_number):
        return parse_pncp_control_number(control_number)

    def fetch_price_references(self, opportunity, query, max_matches=12):
        parsed = self.parse_control_number(opportunity.get("pncp_control_number"))
        if not parsed:
            return []
        cnpj, year, sequence = parsed
        items_url = f"{DATA_URL}/orgaos/{cnpj}/compras/{year}/{sequence}/itens"
        response = self._get(items_url, None)
        if response.status_code == 204:
            return []
        try:
            response.raise_for_status()
            items = response.json()
            if not isinstance(items, list):
                raise ValueError("lista de itens não encontrada")
        except (requests.RequestException, ValueError) as error:
            raise PncpTemporaryError(f"Itens indisponíveis: {error}") from error
        words = [word.lower() for word in str(query or "").split() if len(word) >= 2]
        matched = []
        for item in items:
            description = str(item.get("descricao") or item.get("descricaoItem") or "")
            if words and not all(word in description.lower() for word in words):
                continue
            number = item.get("numeroItem")
            result = {}
            if number is not None:
                result_url = (
                    f"{DATA_URL}/orgaos/{cnpj}/compras/{year}/{sequence}"
                    f"/itens/{number}/resultados/1"
                )
                try:
                    result_response = self._get(result_url, None)
                    if result_response.status_code == 200:
                        candidate = result_response.json()
                        result = candidate if isinstance(candidate, dict) else {}
                except (PncpTemporaryError, ValueError):
                    result = {}
            matched.append({
                "opportunity_id": opportunity.get("id"), "description": description,
                "agency": opportunity.get("agency") or "", "city": opportunity.get("city") or "",
                "state": opportunity.get("state") or "", "quantity": item.get("quantidade"),
                "unit": item.get("unidadeMedida") or item.get("unidadeFornecimento") or "",
                "estimated_unit_value": item.get("valorUnitarioEstimado"),
                "homologated_unit_value": result.get("valorUnitarioHomologado"),
                "supplier": result.get("nomeRazaoSocialFornecedor") or "",
                "brand": result.get("marca") or result.get("marcaFabricante") or "",
                "source_url": opportunity.get("source_url") or "",
                "published_at": opportunity.get("published_at"),
            })
            if len(matched) >= max_matches:
                break
        return matched

    @staticmethod
    def _normalize(item):
        agency = item.get("orgaoEntidade") or {}
        unit = item.get("unidadeOrgao") or {}
        return {
            "numeroControlePNCP": item.get("numeroControlePNCP") or "",
            "orgao": agency.get("razaoSocial") or "",
            "municipio": unit.get("municipioNome") or "",
            "uf": unit.get("ufSigla") or "",
            "modalidade": canonical_modality_name(item.get("modalidadeNome") or ""),
            "publicacao": item.get("dataPublicacaoPncp"),
            "abertura": item.get("dataAberturaProposta"),
            "encerramento": item.get("dataEncerramentoProposta"),
            "srp": bool(item.get("srp")),
            "objeto": item.get("objetoCompra") or "",
            "valor": item.get("valorTotalEstimado"),
            "link": item.get("linkSistemaOrigem") or "",
            "source_name": "PNCP",
            "source_channel": "PNCP",
        }





