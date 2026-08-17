from __future__ import annotations

import base64
import hashlib
import io
import re
import unicodedata
import uuid
from datetime import date, datetime

from pypdf import PdfReader

from .db_runtime import using_postgres


MAX_COMPANY_DOCUMENT_BYTES = 4 * 1024 * 1024

_STOPWORDS = {
    "para", "com", "sem", "dos", "das", "uma", "uns", "nas", "nos", "por", "que",
    "de", "do", "da", "em", "no", "na", "ao", "aos", "as", "os", "e", "ou", "a",
    "o", "empresa", "comercio", "servico", "servicos", "produto", "produtos", "atividade",
    "atividades", "fornecimento", "aquisicao", "contratacao", "material", "materiais",
}

_DOCUMENT_RULES = (
    (("fgts", "fundo de garantia"), "Certificado de regularidade do FGTS"),
    (("cndt", "trabalhista", "trabalhistas"), "CNDT - débitos trabalhistas"),
    (("federal", "divida ativa", "receita federal"), "Certidão conjunta federal e dívida ativa da União"),
    (("estadual",), "Certidão estadual"),
    (("municipal",), "Certidão municipal"),
    (("balanco", "economico-financeira", "economico financeira"), "Balanço patrimonial e demonstrações contábeis"),
    (("falencia", "recuperacao judicial"), "Certidão negativa de falência ou recuperação judicial"),
    (("atestado", "capacidade tecnica", "qualificacao tecnica"), "Atestado de capacidade técnica"),
    (("contrato social", "ato constitutivo"), "Contrato social e alterações"),
    (("sicaf",), "Cadastro SICAF"),
    (("cnpj", "cadastro nacional"), "Cartão CNPJ"),
)


def _fold(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", text).strip()


def _phrases(value: object) -> list[str]:
    raw = re.split(r"[,;\n|]+", str(value or ""))
    return [item.strip() for item in raw if len(item.strip()) >= 3]


def _tokens(value: object) -> set[str]:
    words = re.findall(r"[a-z0-9]+", _fold(value))
    return {word for word in words if len(word) >= 4 and word not in _STOPWORDS and not word.isdigit()}


def profile_search_ready(profile: dict | None) -> bool:
    profile = profile or {}
    return any(
        str(profile.get(field) or "").strip()
        for field in ("offerings", "interest_keywords", "procurement_interests", "cnaes", "brands")
    )


def score_opportunity(item: dict, profile: dict | None) -> tuple[int, list[str]]:
    profile = profile or {}
    if not profile_search_ready(profile):
        return 0, []

    opportunity_text = _fold(" ".join(
        str(item.get(field) or "")
        for field in ("object", "agency", "modality", "city", "state")
    ))
    exclusions = [_fold(value) for value in _phrases(profile.get("excluded_keywords"))]
    blocked = [term for term in exclusions if term and term in opportunity_text]
    if blocked:
        return 0, [f"termo excluído: {blocked[0]}"]

    signal_fields = (
        ("interest_keywords", "palavra-chave"),
        ("procurement_interests", "interesse"),
        ("offerings", "produto/serviço"),
        ("cnaes", "atividade"),
        ("brands", "marca"),
    )
    score = 0.0
    reasons: list[str] = []
    exact_hits = 0
    profile_corpus = []
    for field, label in signal_fields:
        value = profile.get(field) or ""
        profile_corpus.append(str(value))
        for phrase in _phrases(value):
            folded_phrase = _fold(phrase)
            if len(folded_phrase) >= 4 and folded_phrase in opportunity_text:
                exact_hits += 1
                score += 20 if field in {"interest_keywords", "procurement_interests"} else 14
                if len(reasons) < 3:
                    reasons.append(f"{label}: {phrase[:70]}")

    profile_tokens = _tokens(" ".join(profile_corpus))
    opportunity_tokens = _tokens(opportunity_text)
    overlap = sorted(profile_tokens & opportunity_tokens)
    if profile_tokens and overlap:
        ratio = len(overlap) / max(min(len(profile_tokens), 14), 1)
        score += min(42.0, 12.0 + ratio * 52.0)
        if len(reasons) < 3:
            reasons.append("termos em comum: " + ", ".join(overlap[:5]))

    service_states = {
        state.strip().upper()
        for state in re.split(r"[,;|\s]+", str(profile.get("service_states") or ""))
        if len(state.strip()) == 2
    }
    opportunity_state = str(item.get("state") or "").strip().upper()
    if service_states and opportunity_state:
        if opportunity_state in service_states:
            score += 8
            if len(reasons) < 3:
                reasons.append(f"atuação em {opportunity_state}")
        else:
            score -= 8

    max_value = profile.get("max_contract_value")
    estimated = item.get("estimated_value")
    try:
        if max_value not in (None, "") and estimated not in (None, "") and float(estimated) > float(max_value):
            score -= 10
    except (TypeError, ValueError):
        pass

    if exact_hits == 0 and not overlap:
        return 0, []
    return max(0, min(100, int(round(score)))), reasons


def rank_opportunities(items: list[dict], profile: dict | None) -> list[dict]:
    ranked = []
    for position, original in enumerate(items):
        item = dict(original)
        score, reasons = score_opportunity(item, profile)
        item["_match_score"] = score
        item["_match_reasons"] = reasons
        item["_original_order"] = position
        ranked.append(item)
    ranked.sort(key=lambda row: (-int(row.get("_match_score") or 0), int(row.get("_original_order") or 0)))
    return ranked


def _ensure_sqlite_extensions(db) -> None:
    if using_postgres():
        return
    with db.connect() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(company_profiles)").fetchall()}
        if "excluded_keywords" not in columns:
            conn.execute("ALTER TABLE company_profiles ADD COLUMN excluded_keywords TEXT NOT NULL DEFAULT ''")
        if "profile_search_enabled" not in columns:
            conn.execute("ALTER TABLE company_profiles ADD COLUMN profile_search_enabled INTEGER NOT NULL DEFAULT 1")
        if "cnpj_card_uploaded_at" not in columns:
            conn.execute("ALTER TABLE company_profiles ADD COLUMN cnpj_card_uploaded_at TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS company_document_uploads (
                id TEXT PRIMARY KEY, company_id TEXT NOT NULL, document_type TEXT NOT NULL,
                file_name TEXT NOT NULL, mime_type TEXT NOT NULL DEFAULT '',
                content_base64 TEXT NOT NULL, size_bytes INTEGER NOT NULL DEFAULT 0,
                sha256 TEXT NOT NULL, extracted_text TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS ix_company_document_uploads_company ON company_document_uploads(company_id, document_type)")


def get_extended_profile(db, company_id: str) -> dict:
    db.get_company_profile(company_id)
    _ensure_sqlite_extensions(db)
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM company_profiles WHERE company_id=?", (company_id,)).fetchone()
    return dict(row) if row else {}


def save_extended_profile(db, company_id: str, *, excluded_keywords: str = "", profile_search_enabled: bool = True, **fields) -> dict:
    cnpj = str(fields.get("cnpj") or "").strip()
    if cnpj and not db.validate_cnpj(cnpj):
        raise ValueError("Informe um CNPJ válido antes de salvar o perfil.")
    db.save_company_profile(company_id, **fields)
    _ensure_sqlite_extensions(db)
    with db.connect() as conn:
        conn.execute(
            "UPDATE company_profiles SET excluded_keywords=?, profile_search_enabled=?, updated_at=CURRENT_TIMESTAMP WHERE company_id=?",
            (str(excluded_keywords or "").strip(), 1 if profile_search_enabled else 0, company_id),
        )
        if cnpj:
            normalized = db.normalize_cnpj(cnpj)
            current = conn.execute("SELECT cnpj FROM companies WHERE id=?", (company_id,)).fetchone()
            current_cnpj = str(current["cnpj"] or "") if current else ""
            if not current_cnpj or current_cnpj == normalized:
                conn.execute("UPDATE companies SET cnpj=? WHERE id=?", (normalized, company_id))
    return get_extended_profile(db, company_id)


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _line_after(lines: list[str], *labels: str) -> str:
    folded = [_fold(line) for line in lines]
    for index, line in enumerate(folded):
        if any(label in line for label in labels):
            for candidate in lines[index + 1:index + 4]:
                value = candidate.strip()
                if value and not any(label in _fold(value) for label in labels):
                    return value
    return ""


def extract_cnpj_card(file_name: str, mime_type: str, data: bytes) -> dict:
    if not data:
        raise ValueError("O arquivo está vazio.")
    if len(data) > MAX_COMPANY_DOCUMENT_BYTES:
        raise ValueError("O Cartão CNPJ deve ter no máximo 4 MB.")
    is_pdf = str(mime_type or "").lower() == "application/pdf" or str(file_name or "").lower().endswith(".pdf")
    text = _pdf_text(data) if is_pdf else ""
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    search_space = text + "\n" + str(file_name or "")
    cnpj_match = re.search(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b", search_space)
    cnpj = re.sub(r"\D", "", cnpj_match.group(0)) if cnpj_match else ""
    legal_name = _line_after(lines, "nome empresarial")
    trade_name = _line_after(lines, "titulo do estabelecimento", "nome de fantasia")

    cnae_rows = []
    for line in lines:
        match = re.search(r"\b(\d{2}\.\d{2}-\d-\d{2})\s*-?\s*(.*)", line)
        if match:
            label = f"{match.group(1)} - {match.group(2).strip()}".strip(" -")
            if label not in cnae_rows:
                cnae_rows.append(label)

    return {
        "cnpj": cnpj,
        "legal_name": legal_name,
        "trade_name": trade_name,
        "cnaes": "\n".join(cnae_rows),
        "extracted_text": text[:30000],
        "automatic_extraction": bool(text.strip()),
    }


def save_company_document_upload(db, company_id: str, document_type: str, file_name: str, mime_type: str, data: bytes) -> dict:
    parsed = extract_cnpj_card(file_name, mime_type, data) if document_type == "Cartão CNPJ" else {"extracted_text": ""}
    _ensure_sqlite_extensions(db)
    upload_id = str(uuid.uuid4())
    digest = hashlib.sha256(data).hexdigest()
    encoded = base64.b64encode(data).decode("ascii")
    with db.connect() as conn:
        conn.execute("DELETE FROM company_document_uploads WHERE company_id=? AND document_type=?", (company_id, document_type))
        conn.execute("""
            INSERT INTO company_document_uploads(
                id, company_id, document_type, file_name, mime_type, content_base64,
                size_bytes, sha256, extracted_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            upload_id, company_id, document_type, str(file_name or "documento"), str(mime_type or ""),
            encoded, len(data), digest, str(parsed.get("extracted_text") or ""),
        ))
        if document_type == "Cartão CNPJ":
            conn.execute(
                "UPDATE company_profiles SET cnpj_card_uploaded_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE company_id=?",
                (company_id,),
            )
    try:
        db.add_company_document(company_id, document_type)
        db.save_company_documents(company_id, [{
            "document_type": document_type,
            "applicable": "Sim",
            "status": "Válido",
            "expiry_date": None,
            "issuer": "Receita Federal" if document_type == "Cartão CNPJ" else "",
            "notes": "Arquivo anexado ao perfil da empresa.",
        }])
    except Exception:
        pass
    return {**parsed, "id": upload_id, "file_name": file_name, "mime_type": mime_type, "size_bytes": len(data), "sha256": digest}


def get_company_document_upload(db, company_id: str, document_type: str) -> dict | None:
    _ensure_sqlite_extensions(db)
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM company_document_uploads WHERE company_id=? AND document_type=? ORDER BY created_at DESC LIMIT 1",
            (company_id, document_type),
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["content"] = base64.b64decode(result.pop("content_base64"))
    return result


def _parse_expiry(value) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None


def document_readiness(company_documents: list[dict], findings: list[dict]) -> list[dict]:
    by_name = {_fold(row.get("document_type")): row for row in company_documents}
    required_names: list[str] = []
    for finding in findings:
        text = _fold(f"{finding.get('title', '')} {finding.get('evidence', '')}")
        for aliases, canonical in _DOCUMENT_RULES:
            if any(alias in text for alias in aliases) and canonical not in required_names:
                required_names.append(canonical)
    output = []
    today = date.today()
    for canonical in required_names:
        row = by_name.get(_fold(canonical))
        if not row:
            output.append({"document_type": canonical, "state": "missing", "label": "Não cadastrado", "row": None})
            continue
        status = str(row.get("status") or "Não informado")
        expiry = _parse_expiry(row.get("expiry_date"))
        if status in {"Vencido", "Não possui"} or (expiry and expiry < today):
            state, label = "expired", "Vencido / indisponível"
        elif status == "Válido":
            if expiry and (expiry - today).days <= 30:
                state, label = "expiring", f"Vence em {(expiry - today).days} dia(s)"
            else:
                state, label = "ready", "Válido"
        elif status == "Não se aplica":
            state, label = "review", "Marcado como não se aplica"
        else:
            state, label = "review", status or "Não informado"
        output.append({"document_type": canonical, "state": state, "label": label, "row": row})
    return output
