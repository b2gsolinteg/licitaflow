from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re
from xml.sax.saxutils import escape

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = PROJECT_ROOT / "assets" / "licitanexo-logo.png"
NAVY = colors.HexColor("#152238")
GOLD = colors.HexColor("#D6A84B")
TEXT = colors.HexColor("#26384D")
MUTED = colors.HexColor("#667085")
SOFT = colors.HexColor("#F5F7FA")
B2G_SIGNATURE = "Desenvolvido por B2G SaaS | Business to Growth"


GUIDES = {
    "📅 Calendário": {
        "title": "Calendário de licitações",
        "purpose": "Organizar prazos e datas importantes dos editais salvos para reduzir esquecimentos e atrasos.",
        "steps": [
            "Confira os certames e prazos exibidos para sua empresa.",
            "Abra o edital correspondente quando precisar revisar detalhes, Jornada ou precificação.",
            "Mantenha a data do certame atualizada em Meus Editais quando o órgão alterar a sessão.",
            "Use a Jornada do edital para acompanhar o que ainda falta antes da participação.",
        ],
        "why_fill": [
            "Data do certame: alimenta a organização do calendário e reduz o risco de perder a sessão.",
            "Status do edital: ajuda a separar oportunidades em análise das que realmente exigem ação imediata.",
            "Jornada atualizada: permite enxergar pendências antes do prazo final, em vez de descobri-las no dia da disputa.",
        ],
        "tips": [
            "Datas do portal oficial e dos anexos devem prevalecer em caso de divergência.",
            "Atualize o certame sempre que houver retificação ou adiamento.",
            "Use o calendário como painel operacional, não como substituto do edital.",
        ],
    },
    "🔎 Buscar Editais": {
        "title": "Buscar Editais - Radar LicitaNexo",
        "purpose": "Localizar oportunidades do catálogo PNCP e priorizar as que combinam com o perfil da empresa.",
        "steps": [
            "Digite o produto, serviço ou termo que procura e ajuste UF, modalidade, valores e tipo.",
            "Ative o perfil empresarial quando quiser priorizar resultados por aderência.",
            "Revise objeto, órgão, prazo, valor e fonte antes de salvar.",
            "Clique em Salvar em Meus Editais para levar a oportunidade ao fluxo de análise, Jornada e preço.",
        ],
        "why_fill": [
            "Produtos, serviços e palavras-chave: ajudam o Radar a aproximar a linguagem do edital daquilo que sua empresa realmente vende.",
            "UF e região de atendimento: reduzem resultados inviáveis por logística ou área de atuação.",
            "Faixa de valor e modalidade: diminuem ruído e deixam a triagem mais próxima da capacidade da empresa.",
            "Perfil empresarial completo: melhora a priorização por aderência; perfil incompleto produz uma comparação menos útil.",
        ],
        "tips": [
            "A aderência é uma priorização operacional; não garante habilitação nem vitória.",
            "Use sinônimos e termos comerciais que seus clientes usam, não apenas o nome técnico do CNAE.",
            "O portal oficial e os anexos continuam sendo a fonte final da contratação.",
        ],
    },
    "⭐ Meus Editais": {
        "title": "Meus Editais - preparação da participação",
        "purpose": "Centralizar cada oportunidade salva e transformar o edital em um plano operacional até a sessão.",
        "steps": [
            "Visão geral: confira órgão, objeto, datas, valor e mantenha suas anotações.",
            "Jornada: acompanhe análise, documentação, cotações, preço, proposta, envio e sessão.",
            "Precificação: importe itens oficiais do PNCP quando disponíveis, escolha fornecedores e defina seu preço.",
            "Documentos e análise: envie Edital, Termo de Referência e anexos para identificar exigências e pontos de atenção.",
            "Dossiê de participação: gere PDF ou Excel com dados, itens, custos, margens, fornecedores, Jornada e análise.",
        ],
        "why_fill": [
            "Datas e status: alimentam calendário, prioridade e Jornada do edital.",
            "Quantidade, preço do edital e seu preço: permitem calcular receita, desconto e margem da proposta.",
            "Custos e fornecedor: mostram se ganhar o item será financeiramente saudável e registram a base da decisão.",
            "Frete, impostos e outros custos: evitam uma margem aparentemente boa que desaparece depois da vitória.",
            "Anotações, checklist e Jornada: preservam contexto e reduzem esquecimentos quando há vários editais ao mesmo tempo.",
            "Dados completos tornam o Dossiê de Participação mais confiável para revisão e impressão antes da sessão.",
        ],
        "tips": [
            "Itens com origem PNCP vêm da API estruturada oficial; itens manuais ficam identificados como Manual.",
            "Se o orçamento for sigiloso, o LicitaNexo não inventa preço de referência.",
            "Cadastre todos os custos relevantes antes de avaliar a margem.",
            "Sempre confira quantidades, especificações e condições no edital, TR e anexos antes de enviar proposta.",
        ],
    },
    "📄 Analisar Edital": {
        "title": "Analisar Edital",
        "purpose": "Apoiar a leitura do edital e destacar requisitos, documentos e alertas relevantes para a decisão.",
        "steps": [
            "Envie o PDF disponível para análise.",
            "Revise os achados e trate cada alerta como apoio, não como parecer jurídico.",
            "Quando o edital estiver salvo em Meus Editais, prefira analisar também o Termo de Referência e anexos relacionados.",
            "Cruze as exigências encontradas com os documentos cadastrados em Minha Empresa.",
        ],
        "why_fill": [
            "Enviar o edital completo aumenta a chance de localizar requisitos espalhados em diferentes páginas.",
            "Adicionar Termo de Referência e anexos traz contexto de especificação, entrega, amostra, qualificação e obrigações que podem não estar no corpo principal.",
            "Vincular a análise a um edital salvo permite transformar achados em Jornada, checklist e decisão operacional.",
            "Documentos da empresa atualizados tornam o cruzamento de habilitação mais útil e reduzem falsas pendências.",
        ],
        "tips": [
            "PDF digitalizado sem camada de texto pode exigir conferência manual.",
            "Leia os trechos apontados pelo sistema no documento original antes de decidir.",
            "A fonte final é sempre o edital e seus anexos oficiais.",
        ],
    },
    "🏢 Minha Empresa": {
        "title": "Minha Empresa",
        "purpose": "Cadastrar o contexto da empresa uma vez para melhorar busca, documentação, fornecedores e tomada de decisão.",
        "steps": [
            "Perfil e Cartão CNPJ: revise dados, CNAEs, produtos, serviços, palavras-chave, UFs e margem desejada.",
            "Documentos: mantenha situação e validade das certidões e documentos relevantes.",
            "Fornecedores: cadastre fornecedores permanentes para reutilizá-los em qualquer edital.",
            "Use o perfil no Radar quando quiser priorizar oportunidades compatíveis com sua operação.",
        ],
        "why_fill": [
            "CNPJ e CNAEs ajudam a contextualizar a atividade formal da empresa, mas não substituem a descrição real do que ela vende.",
            "Produtos, serviços, marcas e palavras-chave dão ao Radar vocabulário suficiente para reconhecer oportunidades escritas de formas diferentes.",
            "UFs atendidas e faixa de contrato evitam priorizar oportunidades pouco viáveis para sua operação.",
            "Margem desejada vira referência para a formação de preço e ajuda a detectar propostas abaixo da meta da empresa.",
            "Documentos com validade atualizada permitem identificar pendências de habilitação com antecedência.",
            "Fornecedores permanentes reduzem retrabalho e criam histórico para comparar cotações ao longo do tempo.",
        ],
        "tips": [
            "Descreva o que a empresa realmente vende ou executa; não dependa somente do CNAE.",
            "Prefira dados específicos e atuais a textos genéricos.",
            "Revise documentos, fornecedores e regiões atendidas sempre que a operação da empresa mudar.",
        ],
    },
    "💬 Suporte": {
        "title": "Suporte",
        "purpose": "Registrar dúvidas, dificuldades e solicitações com contexto suficiente para atendimento rápido.",
        "steps": [
            "Descreva o problema e informe em qual tela ele aconteceu.",
            "Explique o que esperava que ocorresse e o que realmente ocorreu.",
            "Quando possível, informe o edital, órgão ou número PNCP relacionado.",
            "Acompanhe o histórico e a situação do atendimento nesta área.",
        ],
        "why_fill": [
            "Tela e ação realizadas ajudam a equipe a reproduzir o problema mais rapidamente.",
            "Resultado esperado versus resultado observado reduz idas e voltas no atendimento.",
            "Número PNCP, órgão ou edital identifica o contexto exato quando a falha depende de uma contratação específica.",
            "Uma descrição completa normalmente diminui o tempo necessário para chegar à correção.",
        ],
        "tips": [
            "Evite enviar senhas, tokens ou dados de cartão em mensagens de suporte.",
            "Capturas de tela sem dados sensíveis ajudam a reproduzir problemas visuais.",
            "Se houver mensagem de erro, copie o texto ou envie o trecho relevante do log.",
        ],
    },
    "👤 Minha Conta": {
        "title": "Minha Conta",
        "purpose": "Consultar plano, acesso, assinatura e preferências pessoais de busca.",
        "steps": [
            "Confira situação do plano e período de teste/assinatura.",
            "Use o checkout oficial quando precisar contratar ou renovar.",
            "Salve preferências de busca para iniciar o Radar com filtros adequados à sua empresa.",
            "Revise seus dados e mantenha o e-mail de acesso sob controle da empresa.",
        ],
        "why_fill": [
            "E-mail correto é essencial para acesso, recuperação de senha e comunicação relacionada à conta.",
            "Preferências de busca poupam tempo e deixam o Radar mais próximo da rotina do usuário.",
            "Acompanhar plano e situação da assinatura evita surpresa com limites ou interrupção do acesso.",
        ],
        "tips": [
            "O LicitaNexo não armazena dados do cartão usados no checkout do provedor de pagamento.",
            "Mantenha o e-mail de acesso em uma conta controlada pela empresa.",
            "Preferências podem ser alteradas antes de qualquer nova busca.",
        ],
    },
}


NAV_ORDER = [
    "📅 Calendário", "🔎 Buscar Editais", "⭐ Meus Editais", "📄 Analisar Edital",
    "🏢 Minha Empresa", "💬 Suporte", "👤 Minha Conta",
]


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="GuideTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=20, leading=24, textColor=NAVY, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="GuideSubtitle", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=8.5, leading=11, textColor=NAVY, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="GuideHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=NAVY, spaceBefore=7, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="GuideBody", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.4, leading=13.4, textColor=TEXT, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="GuideSmall", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.8, leading=10.5, textColor=MUTED, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="GuideCover", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=24, leading=29, textColor=NAVY, alignment=1, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="GuideCoverBody", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=10.5, leading=15, textColor=TEXT, alignment=1, spaceAfter=5,
    ))
    return styles


def _slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", str(text or "").strip().lower()).strip("-")
    return value or "guia"


def _logo(width=52 * mm):
    if not LOGO_PATH.exists():
        return None
    return Image(str(LOGO_PATH), width=width, height=width / 3.54)


def _gold_rule(width=178 * mm):
    rule = Table([[""]], colWidths=[width], rowHeights=[1.4 * mm])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GOLD)]))
    return rule


def _callout(text: str, styles):
    box = Table([[Paragraph(escape(text), styles["GuideBody"])]], colWidths=[174 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDE3EA")),
        ("LINEBEFORE", (0, 0), (0, -1), 3, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return box


def _brand_header(story, styles):
    logo = _logo()
    if logo:
        story.append(logo)
    else:
        story.append(Paragraph("LicitaNexo", styles["GuideTitle"]))
    story.append(Spacer(1, 1.5 * mm))
    story.append(Paragraph(B2G_SIGNATURE, styles["GuideSubtitle"]))
    story.append(Spacer(1, 2 * mm))
    story.append(_gold_rule())
    story.append(Spacer(1, 4 * mm))


def _page_footer(canvas, doc):
    canvas.saveState()
    page_width, _ = A4
    y = 9 * mm
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.7)
    canvas.line(doc.leftMargin, y + 4 * mm, page_width - doc.rightMargin, y + 4 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.2)
    canvas.drawString(doc.leftMargin, y, "LicitaNexo | Desenvolvido por B2G SaaS")
    canvas.drawRightString(page_width - doc.rightMargin, y, f"Página {canvas.getPageNumber()}")
    canvas.restoreState()


def _append_numbered(story, items, styles):
    for index, item in enumerate(items, 1):
        story.append(Paragraph(f"<b>{index}.</b> {escape(item)}", styles["GuideBody"]))


def _append_bullets(story, items, styles):
    for item in items:
        story.append(Paragraph(f"- {escape(item)}", styles["GuideBody"]))


def _append_guide(story, page: str, *, include_brand: bool = True):
    guide = GUIDES[page]
    styles = _styles()
    if include_brand:
        _brand_header(story, styles)
    story.append(Paragraph(escape(guide["title"]), styles["GuideTitle"]))
    story.append(_callout(guide["purpose"], styles))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Como usar", styles["GuideHeading"]))
    _append_numbered(story, guide["steps"], styles)

    story.append(Paragraph("Por que preencher estas informações", styles["GuideHeading"]))
    story.append(Paragraph(
        "Os campos do LicitaNexo não existem apenas para cadastro. Quando estão completos e atualizados, "
        "eles alimentam busca, aderência, organização, análise, precificação e documentos de participação.",
        styles["GuideSmall"],
    ))
    _append_bullets(story, guide["why_fill"], styles)

    story.append(Paragraph("Boas práticas", styles["GuideHeading"]))
    _append_bullets(story, guide["tips"], styles)

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Antes de concluir: dados incompletos podem reduzir a utilidade das recomendações e dos cálculos. "
        "Preencha apenas informações reais, revise quando houver mudança e confirme sempre edital, Termo de Referência, "
        "anexos e portal oficial antes de tomar uma decisão ou enviar proposta.",
        styles["GuideSmall"],
    ))


@lru_cache(maxsize=32)
def guide_pdf(page: str) -> bytes:
    if page not in GUIDES:
        raise KeyError(page)
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=20 * mm,
        title=f"LicitaNexo - {GUIDES[page]['title']}",
        author="B2G SaaS - LicitaNexo",
        subject="Guia operacional do LicitaNexo",
    )
    story = []
    _append_guide(story, page)
    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return output.getvalue()


@lru_cache(maxsize=2)
def full_manual_pdf() -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=20 * mm,
        title="LicitaNexo - Manual do usuário",
        author="B2G SaaS - LicitaNexo",
        subject="Manual operacional do LicitaNexo",
    )
    styles = _styles()
    story = []
    story.append(Spacer(1, 18 * mm))
    logo = _logo(68 * mm)
    if logo:
        logo.hAlign = "CENTER"
        story.append(logo)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(B2G_SIGNATURE, ParagraphStyle(
        "ManualBrand", parent=styles["GuideSubtitle"], alignment=1, fontSize=9,
    )))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Manual do Usuário", styles["GuideCover"]))
    story.append(Paragraph(
        "Como usar o LicitaNexo e por que cada informação preenchida melhora sua preparação para vender ao governo.",
        styles["GuideCoverBody"],
    ))
    story.append(Spacer(1, 7 * mm))
    cover_box = Table([[Paragraph(
        "Preencher bem o LicitaNexo não é burocracia: é o que permite transformar dados dispersos em oportunidades priorizadas, "
        "checklists, cálculos de margem, histórico de fornecedores e um dossiê de participação mais confiável.",
        styles["GuideBody"],
    )]], colWidths=[145 * mm])
    cover_box.hAlign = "CENTER"
    cover_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DDE3EA")),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(cover_box)
    story.append(PageBreak())

    for index, page in enumerate(NAV_ORDER):
        if index:
            story.append(PageBreak())
        _append_guide(story, page, include_brand=False)
    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return output.getvalue()


def render_sidebar_guides(page: str) -> None:
    if page not in GUIDES:
        return
    guide = GUIDES[page]
    st.caption("Ajuda da tela")
    st.download_button(
        "📘 Guia desta tela (PDF)",
        data=guide_pdf(page),
        file_name=f"licitanexo-guia-{_slug(guide['title'])}.pdf",
        mime="application/pdf",
        width="stretch",
        key=f"guide_pdf_{_slug(page)}",
    )
    with st.expander("📚 Manual completo"):
        st.caption("Inclui o motivo de preencher os principais campos e como cada dado ajuda no fluxo de participação.")
        st.download_button(
            "Baixar manual do LicitaNexo",
            data=full_manual_pdf(),
            file_name="licitanexo-manual-do-usuario.pdf",
            mime="application/pdf",
            width="stretch",
            key="licitanexo_full_manual_pdf",
        )
