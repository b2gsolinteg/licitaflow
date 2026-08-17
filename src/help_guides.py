from __future__ import annotations

from functools import lru_cache
from io import BytesIO
import re
from xml.sax.saxutils import escape

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak


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
        "tips": [
            "Datas do portal oficial e dos anexos devem prevalecer em caso de divergência.",
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
        "tips": [
            "A aderência é uma priorização operacional; não garante habilitação nem vitória.",
            "O portal oficial e os anexos continuam sendo a fonte final da contratação.",
            "A exportação do resultado pode ser usada para triagem e compartilhamento interno.",
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
        "tips": [
            "Itens com origem PNCP vêm da API estruturada oficial; itens manuais ficam identificados como Manual.",
            "Se o orçamento for sigiloso, o LicitaNexo não inventa preço de referência.",
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
        "tips": [
            "PDF digitalizado sem camada de texto pode exigir conferência manual.",
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
        "tips": [
            "Descreva o que a empresa realmente vende ou executa; não dependa somente do CNAE.",
            "Mantenha documentos e fornecedores atualizados para reduzir retrabalho na participação.",
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
        "tips": [
            "Evite enviar senhas, tokens ou dados de cartão em mensagens de suporte.",
            "Capturas de tela sem dados sensíveis ajudam a reproduzir problemas visuais.",
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
        "tips": [
            "O LicitaNexo não armazena dados do cartão usados no checkout do provedor de pagamento.",
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
        fontSize=20, leading=24, textColor=colors.HexColor("#152238"), spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="GuideHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=colors.HexColor("#152238"), spaceBefore=6, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="GuideBody", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.5, leading=13.5, textColor=colors.HexColor("#26384D"), spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="GuideSmall", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8, leading=11, textColor=colors.HexColor("#667085"), spaceAfter=3,
    ))
    return styles


def _slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", str(text or "").strip().lower()).strip("-")
    return value or "guia"


def _append_guide(story, page: str, *, include_brand: bool = True):
    guide = GUIDES[page]
    styles = _styles()
    if include_brand:
        story.append(Paragraph("LicitaNexo", styles["GuideSmall"]))
    story.append(Paragraph(escape(guide["title"]), styles["GuideTitle"]))
    story.append(Paragraph(escape(guide["purpose"]), styles["GuideBody"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Como usar", styles["GuideHeading"]))
    for index, item in enumerate(guide["steps"], 1):
        story.append(Paragraph(f"{index}. {escape(item)}", styles["GuideBody"]))
    story.append(Paragraph("Boas práticas", styles["GuideHeading"]))
    for item in guide["tips"]:
        story.append(Paragraph(f"- {escape(item)}", styles["GuideBody"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Este guia explica o uso operacional do LicitaNexo. Em licitações, confirme sempre o edital, "
        "Termo de Referência, anexos e portal oficial antes de tomar uma decisão ou enviar proposta.",
        styles["GuideSmall"],
    ))


@lru_cache(maxsize=32)
def guide_pdf(page: str) -> bytes:
    if page not in GUIDES:
        raise KeyError(page)
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"LicitaNexo - {GUIDES[page]['title']}",
        author="LicitaNexo",
    )
    story = []
    _append_guide(story, page)
    doc.build(story)
    return output.getvalue()


@lru_cache(maxsize=2)
def full_manual_pdf() -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="LicitaNexo - Manual rápido do usuário",
        author="LicitaNexo",
    )
    story = []
    for index, page in enumerate(NAV_ORDER):
        if index:
            story.append(PageBreak())
        _append_guide(story, page, include_brand=True)
    doc.build(story)
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
        st.download_button(
            "Baixar manual do LicitaNexo",
            data=full_manual_pdf(),
            file_name="licitanexo-manual-rapido.pdf",
            mime="application/pdf",
            width="stretch",
            key="licitanexo_full_manual_pdf",
        )
