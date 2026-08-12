import random
import time

import requests

from .pncp import PncpTemporaryError
from .sources import COMPRASGOV_MODALITY_BY_PNCP


BASE_URL = (
    "https://dadosabertos.compras.gov.br/modulo-contratacoes/"
    "1_consultarContratacoes_PNCP_14133"
)

# O Compras.gov não usa a mesma tabela de códigos de modalidade do PNCP.
# A interface trabalha com os códigos PNCP e este conector faz a tradução.

class ComprasGovClient:
    """Conector da API oficial de Dados Abertos do Compras.gov.br."""

    def __init__(self, timeout=45, page_delay=1.5, max_attempts=4):
        self.timeout = timeout
        self.page_delay = page_delay
        self.max_attempts = max_attempts
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "LicitaNexo/0.6.4", "Accept": "application/json"})

    def sync(self, start_date, end_date, modality_code, state, checkpoint_getter,
             page_saver, checkpoint_saver, progress=None, max_pages_per_run=None):
        stats = {"pages": 0, "received": 0, "saved": 0, "days_completed": 0,
                 "partial": False, "errors": [], "current_page": 0, "total_pages": 0}
        checkpoint = checkpoint_getter(start_date.isoformat())
        if checkpoint and checkpoint["completed"]:
            stats["days_completed"] = 1
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
                items, total_pages = self.fetch_page(start_date, end_date, modality_code, state, page)
            except PncpTemporaryError as error:
                message = f"página {page}: {error}"
                checkpoint_saver(start_date.isoformat(), page, False, accumulated, message)
                stats["partial"] = True
                stats["errors"].append(message)
                return stats
            saved = page_saver(items)
            stats["pages"] += 1
            stats["received"] += len(items)
            stats["saved"] += saved
            stats["total_pages"] = total_pages or stats["total_pages"]
            accumulated += saved
            completed = page >= total_pages if total_pages else not items
            checkpoint_saver(start_date.isoformat(), page + 1, completed, accumulated, "")
            if progress:
                progress(end_date, page, stats)
            if completed:
                stats["days_completed"] = 1
                return stats
            page += 1
            time.sleep(self.page_delay + random.uniform(0.1, 0.4))

    def fetch_page(self, start_date, end_date, modality_code, state, page):
        comprasgov_modality = COMPRASGOV_MODALITY_BY_PNCP.get(modality_code)
        if comprasgov_modality is None:
            raise PncpTemporaryError(
                f"A modalidade PNCP {modality_code} ainda não possui correspondência no Compras.gov"
            )
        params = {
            "pagina": page,
            "tamanhoPagina": 100,
            "dataPublicacaoPncpInicial": start_date.isoformat(),
            "dataPublicacaoPncpFinal": end_date.isoformat(),
            "codigoModalidade": comprasgov_modality,
        }
        if state:
            params["unidadeOrgaoUfSigla"] = state
        response = self._get(params)
        try:
            response.raise_for_status()
            payload = response.json()
            items = [self._normalize(item) for item in payload.get("resultado", [])]
            return items, int(payload.get("totalPaginas") or 0)
        except (requests.RequestException, ValueError, AttributeError) as error:
            raise PncpTemporaryError(f"Resposta inválida do Compras.gov: {error}") from error

    def _get(self, params):
        last_error = "Falha temporária no Compras.gov"
        for attempt in range(self.max_attempts):
            try:
                response = self.session.get(BASE_URL, params=params, timeout=self.timeout)
                if response.status_code not in (429, 500, 502, 503, 504):
                    return response
                last_error = f"Compras.gov respondeu com erro temporário {response.status_code}"
                retry_after = response.headers.get("Retry-After")
                try:
                    wait = float(retry_after)
                except (TypeError, ValueError):
                    wait = min(3 * (2 ** attempt), 45)
            except (requests.Timeout, requests.ConnectionError) as error:
                wait = min(2 * (2 ** attempt), 30)
                last_error = f"Compras.gov demorou para responder: {error.__class__.__name__}"
            if attempt < self.max_attempts - 1:
                time.sleep(wait + random.uniform(0.2, 0.8))
        raise PncpTemporaryError(f"{last_error}. O progresso foi salvo; tente continuar mais tarde.")

    @staticmethod
    def _normalize(item):
        return {
            "numeroControlePNCP": (
                item.get("numeroControlePNCP") or item.get("numeroControlePncp")
                or item.get("idContratacaoPNCP") or item.get("idContratacaoPncp") or ""
            ),
            "orgao": item.get("orgaoEntidadeRazaoSocial") or item.get("unidadeOrgaoNomeUnidade") or "",
            "municipio": item.get("unidadeOrgaoMunicipioNome") or "",
            "uf": item.get("unidadeOrgaoUfSigla") or "",
            "modalidade": item.get("modalidadeNome") or "",
            "publicacao": item.get("dataPublicacaoPncp") or item.get("dataInclusaoPncp"),
            "abertura": item.get("dataAberturaPropostaPncp") or item.get("dataAberturaProposta"),
            "encerramento": item.get("dataEncerramentoPropostaPncp") or item.get("dataEncerramentoProposta"),
            "srp": bool(item.get("srp")),
            "objeto": item.get("objetoCompra") or "",
            "valor": item.get("valorTotalEstimado"),
            "link": item.get("linkSistemaOrigem") or "",
            "source_name": "Compras.gov",
            "source_channel": "Compras.gov API",
        }
