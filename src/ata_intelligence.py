import io
import re
import unicodedata
from urllib.parse import urlparse

import requests
from pypdf import PdfReader


PNCP_DATA_BASE = "https://pncp.gov.br/api/pncp/v1"
ATA_CONTROL_RE = re.compile(r"(?P<cnpj>\d{14})-\d-(?P<compra>\d+)/(?P<ano>\d{4})-(?P<ata>\d+)")
MONEY_RE = re.compile(r"R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2,4})|[0-9]+,[0-9]{2,4})")
CNPJ_RE = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")


class AtaExtractionError(RuntimeError):
    pass


def _plain(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in value if not unicodedata.combining(char)).casefold()


def parse_brl(value):
    try:
        return float(str(value).replace(".", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def parse_ata_identifier(value):
    match = ATA_CONTROL_RE.search(str(value or ""))
    if not match:
        return None
    return {
        "cnpj": match.group("cnpj"), "year": int(match.group("ano")),
        "purchase_sequence": int(match.group("compra")),
        "ata_sequence": int(match.group("ata")), "control": match.group(0),
    }


class PncpAtaClient:
    def __init__(self, timeout=60):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "LicitaNexo/0.7.1 (+b2gsolucoesintegradas@gmail.com)",
            "Accept": "application/json, application/pdf, */*",
        })

    def list_documents(self, identifier):
        parsed = parse_ata_identifier(identifier)
        if not parsed:
            raise AtaExtractionError(
                "Informe o identificador completo da ata, por exemplo: "
                "13927801000300-1-000055/2026-000005."
            )
        url = (
            f"{PNCP_DATA_BASE}/orgaos/{parsed['cnpj']}/compras/{parsed['year']}/"
            f"{parsed['purchase_sequence']}/atas/{parsed['ata_sequence']}/arquivos"
        )
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise AtaExtractionError(f"Não foi possível listar os documentos da ata: {error}") from error
        documents = payload if isinstance(payload, list) else payload.get("data", [])
        return parsed, [dict(document) for document in documents]

    def download(self, document):
        url = document.get("url")
        if not url:
            raise AtaExtractionError("O PNCP não informou o endereço do documento.")
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as error:
            raise AtaExtractionError(f"Não foi possível baixar o documento: {error}") from error
        if len(response.content) > 30 * 1024 * 1024:
            raise AtaExtractionError("O documento ultrapassa o limite de 30 MB desta versão.")
        return response.content, response.headers.get("Content-Type", ""), url


def extract_pdf_pages(pdf_bytes):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return [(index, page.extract_text() or "") for index, page in enumerate(reader.pages, start=1)]
    except Exception as error:
        raise AtaExtractionError(f"O PDF não pôde ser lido: {error}") from error


def extract_price_candidates(pdf_bytes, query, source_url="", published_at=None):
    words = [word for word in _plain(query).split() if len(word) >= 2]
    candidates, seen = [], set()
    pages = extract_pdf_pages(pdf_bytes)
    text_pages = 0
    for page_number, text in pages:
        if text.strip():
            text_pages += 1
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            line_plain = _plain(line)
            if words and not all(word in line_plain for word in words):
                continue
            context_lines = lines[max(0, index - 2):min(len(lines), index + 4)]
            context = " | ".join(context_lines)
            prices = MONEY_RE.findall(context)
            for raw_price in prices:
                price = parse_brl(raw_price)
                key = (page_number, line_plain, price)
                if price is None or price <= 0 or key in seen:
                    continue
                seen.add(key)
                cnpj_match = CNPJ_RE.search(context)
                candidates.append({
                    "confirm": False, "description": line[:500],
                    "homologated_unit_value": price, "unit": "",
                    "supplier": "", "supplier_tax_id": cnpj_match.group(0) if cnpj_match else "",
                    "brand": "", "page_number": page_number,
                    "evidence": context[:1200], "confidence": "Média",
                    "source_url": source_url, "published_at": published_at,
                    "source_type": "Ata/SRP - extraído de documento",
                })
    return candidates, {
        "pages": len(pages), "text_pages": text_pages,
        "needs_ocr": bool(pages) and text_pages == 0,
    }

