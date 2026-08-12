import re
import unicodedata
from io import BytesIO

def _plain(text):
    normalized = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def extract_pdf_pages(pdf_bytes):
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    if sum(len(page) for page in pages) < 100:
        raise ValueError(
            "O PDF não possui texto suficiente. Ele pode estar digitalizado como imagem; "
            "esta versão ainda não executa OCR local."
        )
    return pages


def _evidence(text, terms, radius=180):
    plain = _plain(text)
    positions = [plain.find(_plain(term)) for term in terms]
    positions = [position for position in positions if position >= 0]
    if not positions:
        return ""
    position = min(positions)
    start = max(0, position - radius)
    end = min(len(text), position + radius)
    excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
    return ("…" if start else "") + excerpt + ("…" if end < len(text) else "")


RULES = [
    {
        "category": "Qualificação técnica", "title": "Atestado de capacidade técnica",
        "terms": ["atestado de capacidade técnica", "atestado de capacidade tecnico", "capacidade técnico-operacional"],
        "profile": "has_technical_certificate",
        "action": "Confirmar se a empresa possui atestado compatível com o objeto e quantitativos exigidos.",
    },
    {
        "category": "Qualificação econômico-financeira", "title": "Balanço patrimonial ou índices financeiros",
        "terms": ["balanço patrimonial", "balanco patrimonial", "índice de liquidez", "indice de liquidez"],
        "profile": "has_balance_sheet",
        "action": "Conferir balanço, exercício exigido e índices financeiros antes da habilitação.",
    },
    {
        "category": "Modelo da contratação", "title": "Sistema de Registro de Preços",
        "terms": ["sistema de registro de preços", "sistema de registro de precos", "ata de registro de preços"],
        "profile": "accepts_price_registration",
        "action": "Avaliar se a empresa aceita demanda incerta e fornecimento conforme futuras solicitações.",
    },
    {
        "category": "Escopo", "title": "Prestação de serviços, instalação ou manutenção",
        "terms": ["prestação de serviços", "prestacao de servicos", "serviço de instalação", "servico de instalacao", "manutenção preventiva", "manutencao preventiva", "mão de obra"],
        "profile": "activity_supports_services",
        "action": "Confirmar equipe, custos e capacidade para executar todos os serviços associados.",
    },
    {
        "category": "Qualificação profissional", "title": "Responsável técnico ou registro profissional",
        "terms": ["responsável técnico", "responsavel tecnico", "registro no conselho", "registro profissional"],
        "profile": "has_technical_manager",
        "action": "Verificar profissional habilitado e documentos do conselho competente.",
    },
    {
        "category": "Amostras", "title": "Apresentação de amostra ou prova de conceito",
        "terms": ["apresentação de amostra", "apresentacao de amostra", "prova de conceito"],
        "profile": "accepts_samples",
        "action": "Planejar amostra, prazo, transporte e critérios de aprovação.",
    },
    {
        "category": "Visita", "title": "Visita ou vistoria técnica",
        "terms": ["visita técnica", "visita tecnica", "vistoria técnica", "vistoria tecnica"],
        "profile": "accepts_site_visit",
        "action": "Confirmar obrigatoriedade, agendamento e emissão do comprovante de visita.",
    },
    {
        "category": "Risco contratual", "title": "Garantia contratual ou garantia da proposta",
        "terms": ["garantia contratual", "garantia da proposta", "caução", "caucao"],
        "action": "Calcular impacto financeiro da garantia e conferir as formas aceitas.",
    },
    {
        "category": "Prazo", "title": "Prazo para impugnação ou esclarecimento",
        "terms": ["prazo para impugnação", "prazo para impugnacao", "pedido de esclarecimento", "pedidos de esclarecimentos"],
        "action": "Registrar a data limite na Agenda após conferir o trecho completo.",
    },
    {
        "category": "Prazo", "title": "Prazo de entrega",
        "terms": ["prazo de entrega", "entrega deverá ocorrer", "entrega devera ocorrer"],
        "action": "Confirmar estoque, fornecedor, frete e capacidade de cumprir o prazo de entrega.",
    },
    {
        "category": "Tratamento favorecido", "title": "Participação exclusiva ou benefício para ME/EPP",
        "terms": ["exclusiva para microempresas", "exclusivo para microempresas", "benefício às microempresas", "beneficio as microempresas", "me/epp"],
        "favorable": True,
        "action": "Confirmar o enquadramento e separar a declaração exigida para ME/EPP.",
    },
    {
        "category": "Regularidade fiscal", "title": "Regularidade fiscal e trabalhista",
        "terms": ["regularidade fiscal", "certidão negativa de débitos", "certidao negativa de debitos", "fgts", "cndt", "débitos trabalhistas"],
        "documents": ["Certidão federal", "Certidão estadual", "Certidão municipal", "Regularidade do FGTS", "CNDT"],
        "action": "Conferir todas as certidões exigidas e suas validades na data da habilitação.",
    },
    {
        "category": "Licença sanitária", "title": "Licença ou alvará sanitário",
        "terms": ["licença sanitária", "licenca sanitaria", "alvará sanitário", "alvara sanitario", "vigilância sanitária"],
        "documents": ["Licença sanitária"],
        "action": "Confirmar se a licença sanitária cobre a atividade, o endereço e o prazo do contrato.",
    },
    {
        "category": "Vigilância sanitária", "title": "AFE da Anvisa",
        "terms": ["autorização de funcionamento de empresa", "autorizacao de funcionamento de empresa", "afe anvisa", "autorização de funcionamento - afe"],
        "documents": ["AFE Anvisa"],
        "action": "Conferir a AFE e se as atividades autorizadas correspondem ao objeto licitado.",
    },
    {
        "category": "Produtos controlados", "title": "Autorização Especial da Anvisa",
        "terms": ["autorização especial", "autorizacao especial", "ae anvisa", "portaria 344"],
        "documents": ["AE Anvisa - produtos controlados"],
        "action": "Confirmar a Autorização Especial e o escopo para produtos sujeitos a controle especial.",
    },
    {
        "category": "Segurança do estabelecimento", "title": "Licenciamento do Corpo de Bombeiros",
        "terms": ["avcb", "clcb", "corpo de bombeiros", "licença do corpo de bombeiros"],
        "documents": ["AVCB / CLCB - Corpo de Bombeiros"],
        "action": "Conferir o documento do Corpo de Bombeiros aplicável ao estabelecimento e sua validade.",
    },
    {
        "category": "Meio ambiente", "title": "Licença ambiental ou regularidade no Ibama",
        "terms": ["licença ambiental", "licenca ambiental", "ibama", "cadastro técnico federal", "ctf/app"],
        "documents": ["Licença ambiental", "CTF / Certificado de regularidade IBAMA"],
        "action": "Verificar quais autorizações ambientais se aplicam ao objeto e à atividade executada.",
    },
    {
        "category": "Transporte", "title": "Autorização ou registro de transporte",
        "terms": ["antt", "registro nacional de transportadores", "transporte de produtos perigosos", "autorização de transporte"],
        "documents": ["Registro ANTT / autorização de transporte"],
        "action": "Conferir registros, veículos e autorizações de transporte exigidos para o objeto.",
    },
    {
        "category": "Qualificação profissional", "title": "CAT, ART ou RRT",
        "terms": ["certidão de acervo técnico", "certidao de acervo tecnico", "cat", "anotação de responsabilidade técnica", "art", "rrt"],
        "documents": ["CAT / ART / RRT", "Registro em conselho profissional"],
        "action": "Confirmar o acervo técnico e os registros profissionais compatíveis com os serviços exigidos.",
    },
]


def _document_matches(required_name, document):
    """Permite que nomes simples do analisador reconheçam os nomes reais/customizados do Passaporte."""
    required = _plain(required_name)
    actual = _plain(document.get("document_type") or "")
    if required == actual or required in actual or actual in required:
        return True
    aliases = {
        "certidao federal": ("certidao conjunta federal", "divida ativa da uniao"),
        "regularidade do fgts": ("regularidade do fgts", "certificado de regularidade do fgts"),
        "cndt": ("cndt", "debitos trabalhistas"),
        "registro em conselho profissional": ("registro no conselho", "conselho profissional"),
        "cat / art / rrt": ("cat", "art", "rrt", "acervo tecnico"),
    }
    return any(alias in actual for alias in aliases.get(required, ()))

def _find_document(documents, required_name):
    return next((item for item in documents if _document_matches(required_name, item)), None)


def analyze_pages(pages, profile, documents=None):
    documents = documents or []
    document_index = {str(item.get("document_type") or ""): item for item in documents}
    findings = []
    seen = set()
    for page_number, page in enumerate(pages, start=1):
        plain_page = _plain(page)
        for rule in RULES:
            if rule["title"] in seen:
                continue
            if not any(_plain(term) in plain_page for term in rule["terms"]):
                continue
            profile_key = rule.get("profile")
            required_documents = rule.get("documents") or []
            compatible = True
            document_message = ""
            if profile_key == "activity_supports_services":
                compatible = profile.get("activity_type") in {"Serviços", "Produtos e serviços"}
            elif profile_key:
                compatible = bool(profile.get(profile_key))
            if required_documents:
                matched = [_find_document(documents, name) for name in required_documents]
                matched = [item for item in matched if item]
                owned = [item for item in matched if item.get("applicable") == "Sim"]
                valid = [item for item in owned if item.get("status") == "Válido"]
                expired = [item for item in owned if item.get("status") == "Vencido"]
                if valid:
                    compatible = True
                    document_message = " Documento cadastrado como válido no Passaporte da Empresa."
                elif expired:
                    compatible = False
                    document_message = " O documento consta no Passaporte, mas está vencido."
                else:
                    compatible = False
                    document_message = " A empresa não confirmou que possui documento válido no Passaporte da Empresa."
            if rule.get("favorable"):
                severity = "Verde"
            elif (profile_key or required_documents) and not compatible:
                severity = "Vermelho"
            elif (profile_key or required_documents) and compatible:
                severity = "Verde"
            else:
                severity = "Amarelo"
            findings.append({
                "severity": severity, "category": rule["category"], "title": rule["title"],
                "evidence": _evidence(page, rule["terms"]), "page_number": page_number,
                "recommended_action": rule["action"] + document_message,
            })
            seen.add(rule["title"])

    # Aderência comercial declarada no Passaporte. Não é impedimento jurídico: serve
    # para dizer se o objeto parece estar dentro do que a empresa procura.
    interest_text = str(profile.get("procurement_interests") or profile.get("interest_keywords") or profile.get("offerings") or "").strip()
    if interest_text:
        full_text = _plain(" ".join(pages))
        stopwords = {
            "para", "com", "sem", "uma", "uns", "das", "dos", "que", "nao", "tenho", "interesse",
            "empresa", "empresas", "licitacao", "licitacoes", "quero", "procuro", "fornecer", "vender",
            "prestar", "meu", "minha", "nosso", "nossa", "por", "em", "de", "do", "da",
        }
        terms = []
        for raw in re.split(r"[,;\n]+", interest_text):
            cleaned = _plain(raw).strip()
            if len(cleaned) >= 4:
                terms.append(cleaned)
            for token in re.findall(r"[a-z0-9-]+", cleaned):
                if len(token) >= 4 and token not in stopwords:
                    terms.append(token)
        terms = list(dict.fromkeys(terms))
        hits = [term for term in terms[:60] if term in full_text]
        if hits:
            findings.insert(0, {
                "severity": "Verde", "category": "Aderência comercial",
                "title": "Objeto alinhado ao que a empresa procura",
                "evidence": ", ".join(hits[:6]), "page_number": None,
                "recommended_action": "O edital contém termos informados no Passaporte como interesse comercial da empresa.",
            })
        elif terms:
            findings.insert(0, {
                "severity": "Amarelo", "category": "Aderência comercial",
                "title": "Confirmar aderência do objeto ao interesse da empresa",
                "evidence": "Nenhum termo principal do campo 'O que você quer encontrar em licitações' foi localizado automaticamente.",
                "page_number": None,
                "recommended_action": "Confirme se o objeto realmente faz parte do foco comercial informado no Passaporte.",
            })

    red = sum(finding["severity"] == "Vermelho" for finding in findings)
    yellow = sum(finding["severity"] == "Amarelo" for finding in findings)
    green = sum(finding["severity"] == "Verde" for finding in findings)
    score = max(0, min(100, 100 - red * 22 - yellow * 5 + green * 2))
    return score, findings




def _contains_term(plain_text, term):
    """Evita falsos positivos de siglas curtas como CAT/ART/RRT dentro de outras palavras."""
    normalized = _plain(term).strip()
    if not normalized:
        return False
    if len(normalized) <= 3 and " " not in normalized:
        return re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", plain_text) is not None
    return normalized in plain_text


def _extract_object_text(pages):
    """Extrai o texto do objeto por cabeçalho/linhas antes de recorrer a regex ampla."""
    heading_re = re.compile(r"^(?:\d+(?:\.\d+)*[.)-]?\s*)?(?:do\s+)?objeto(?:\s+da\s+contratacao)?\s*[:\-–—]?\s*(.*)$", re.IGNORECASE)
    next_heading_re = re.compile(r"^\d+(?:\.\d+)+(?:[.)-])?\s+\S+")
    stop_words = ("habilitacao", "justificativa", "requisitos", "valor estimado", "item descricao", "item descrição", "quantidade valor")
    for page in pages[:8]:
        lines = [re.sub(r"\s+", " ", line).strip() for line in str(page or "").splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            match = heading_re.match(_plain(line))
            if not match:
                continue
            collected = []
            # preserva texto que estiver na mesma linha após o cabeçalho
            raw_match = re.match(r"^(?:\d+(?:\.\d+)*[.)-]?\s*)?(?:do\s+)?objeto(?:\s+da\s+contrata[cç][aã]o)?\s*[:\-–—]?\s*(.*)$", line, re.IGNORECASE)
            if raw_match and raw_match.group(1).strip():
                collected.append(raw_match.group(1).strip())
            for nxt in lines[idx+1:idx+10]:
                pn = _plain(nxt)
                if next_heading_re.match(pn) or any(stop in pn for stop in stop_words):
                    break
                if re.search(r"\b(?:item|quantidade|qtd)\b", pn) and ("valor" in pn or "preco" in pn):
                    break
                collected.append(nxt)
                if len(" ".join(collected)) >= 1200:
                    break
            candidate = re.sub(r"\s+", " ", " ".join(collected)).strip(" .:-")
            if len(candidate) >= 20:
                return candidate[:1200]
    return ""


def _extract_item_price_findings(pages, limit=30):
    """Localiza trechos de tabelas/itens com quantidade e valores sem inventar estrutura.

    PDFs públicos variam muito; por isso o Essential prefere devolver o trecho literal
    (com página) a tentar transformar toda tabela em números possivelmente errados.
    """
    money_re = re.compile(r"(?:R\$\s*)?\d{1,3}(?:\.\d{3})*,\d{2}")
    qty_re = re.compile(r"\b(?:qtd\.?|quantidade|quant\.?)\s*[:\-]?\s*\d+(?:[.,]\d+)?", re.IGNORECASE)
    header_terms = (
        "quantidade", "qtd", "valor unitario", "valor unitário", "preco unitario",
        "preço unitário", "valor total", "preco total", "preço total", "unidade", "item"
    )
    findings = []
    seen = set()

    for page_number, page in enumerate(pages, start=1):
        lines = [re.sub(r"\s+", " ", line).strip() for line in str(page or "").splitlines()]
        lines = [line for line in lines if line]
        plain_lines = [_plain(line) for line in lines]
        table_context = any(
            ("quantidade" in pl or "qtd" in pl) and ("valor" in pl or "preco" in pl)
            for pl in plain_lines
        )
        for idx, line in enumerate(lines):
            if not money_re.search(line):
                continue
            start = max(0, idx - 2)
            end = min(len(lines), idx + 3)
            context_lines = lines[start:end]
            context = " | ".join(context_lines)
            plain_context = _plain(context)
            relevant = table_context or qty_re.search(context) or any(term in plain_context for term in header_terms)
            if not relevant:
                continue
            # Evita capturar só percentuais/multas/capital social sem relação clara com item/preço.
            if len(context) < 18:
                continue
            key = _plain(context)[:400]
            if key in seen or any(key in existing or existing in key for existing in seen):
                continue
            seen.add(key)
            findings.append({
                "severity": "Verde",
                "category": "Itens e preços",
                "title": "Quantidade/preço identificado",
                "evidence": context[:900],
                "page_number": page_number,
                "recommended_action": "Confira unidade, quantidade e valor diretamente na tabela/termo de referência.",
            })
            if len(findings) >= limit:
                return findings
    return findings

def analyze_essential_pages(pages):
    """Análise direta do Essential: objeto, documentação exigida e poucos alertas úteis.

    Não calcula aderência/compatibilidade e não compara o edital com documentos cadastrados.
    O objetivo é responder rapidamente: o que está sendo comprado e o que o edital pede.
    """
    full_text = "\n".join(pages)
    plain_full = _plain(full_text)

    # Objeto: prioriza cabeçalho e linhas seguintes para evitar capturar meia página.
    object_text = _extract_object_text(pages)
    if not object_text:
        object_patterns = (
            r"(?:^|\n)\s*(?:\d+(?:\.\d+)*[\s\-–—:]*)?(?:do\s+)?objeto(?:\s+da\s+contratacao)?\s*[:\-–—]?\s*(.{25,1200})",
            r"objeto\s*[:\-–—]\s*(.{25,1200})",
        )
        searchable = "\n".join(pages[:8])
        for pattern in object_patterns:
            match = re.search(pattern, searchable, flags=re.IGNORECASE | re.DOTALL)
            if match:
                candidate = re.sub(r"\s+", " ", match.group(1)).strip()
                candidate = re.split(
                    r"\s+(?:1\.\d+|2\.|3\.|HABILITACAO|HABILITAÇÃO|DA\s+JUSTIFICATIVA|DO\s+VALOR|DOS\s+REQUISITOS|DA\s+HABILITACAO|DA\s+HABILITAÇÃO)\b",
                    candidate, maxsplit=1, flags=re.IGNORECASE,
                )[0].strip(" .:-")
                if len(candidate) >= 20:
                    object_text = candidate[:1200]
                    break

    document_rules = []
    for rule in RULES:
        documents = rule.get("documents") or []
        if documents:
            document_rules.append((rule, documents))
    # Alguns documentos importantes do Essential estavam representados apenas por perfil.
    document_rules.extend([
        (RULES[0], ["Atestado de capacidade técnica"]),
        (RULES[1], ["Balanço patrimonial / índices financeiros"]),
        (RULES[4], ["Registro profissional / responsável técnico"]),
    ])

    required_documents = []
    seen_docs = set()
    findings = []
    seen_titles = set()
    for page_number, page in enumerate(pages, start=1):
        plain_page = _plain(page)
        for rule, docs in document_rules:
            if not any(_contains_term(plain_page, term) for term in rule["terms"]):
                continue
            evidence = _evidence(page, rule["terms"], radius=140)
            for doc in docs:
                key = _plain(doc)
                if key not in seen_docs:
                    seen_docs.add(key)
                    required_documents.append({
                        "name": doc,
                        "page_number": page_number,
                        "evidence": evidence,
                    })
            if rule["title"] not in seen_titles:
                findings.append({
                    "severity": "Amarelo",
                    "category": "Documentação",
                    "title": rule["title"],
                    "evidence": evidence,
                    "page_number": page_number,
                    "recommended_action": "Confirme a exigência e as condições no edital e anexos.",
                })
                seen_titles.add(rule["title"])

    # Quantidades e preços: preservamos o trecho original e a página, sem inventar
    # uma tabela quando o PDF não oferece estrutura textual suficiente.
    item_price_findings = _extract_item_price_findings(pages)
    findings.extend(item_price_findings)

    # Alertas enxutos que não são documentação, somente quando realmente aparecem.
    alert_titles = {
        "Sistema de Registro de Preços",
        "Apresentação de amostra ou prova de conceito",
        "Visita ou vistoria técnica",
        "Garantia contratual ou garantia da proposta",
        "Prazo para impugnação ou esclarecimento",
        "Prazo de entrega",
        "Participação exclusiva ou benefício para ME/EPP",
    }
    alerts = []
    for page_number, page in enumerate(pages, start=1):
        plain_page = _plain(page)
        for rule in RULES:
            if rule["title"] not in alert_titles or rule["title"] in seen_titles:
                continue
            if any(_contains_term(plain_page, term) for term in rule["terms"]):
                alerts.append({
                    "title": rule["title"],
                    "page_number": page_number,
                    "evidence": _evidence(page, rule["terms"], radius=140),
                })
                findings.append({
                    "severity": "Amarelo",
                    "category": "Ponto de atenção",
                    "title": rule["title"],
                    "evidence": alerts[-1]["evidence"],
                    "page_number": page_number,
                    "recommended_action": rule["action"],
                })
                seen_titles.add(rule["title"])

    if object_text:
        findings.insert(0, {
            "severity": "Verde",
            "category": "Objeto",
            "title": "Objeto identificado",
            "evidence": object_text,
            "page_number": None,
            "recommended_action": "Confira o texto integral do objeto e seus anexos antes de decidir.",
        })

    return object_text, required_documents, alerts, findings
