# LicitaNexo MEI

O LicitaNexo MEI é uma experiência separada do LicitaNexo Pro. O objetivo é permitir que MEIs e pequenos negócios descubram oportunidades públicas antes mesmo de definirem um nicho de venda.

## Posicionamento

**Descubra o que o governo está comprando — e quanto ele realmente paga.**

Preço de lançamento pretendido: **R$ 29,90/mês**.

## O que entra no MEI

- exploração sem palavra-chave obrigatória;
- busca por Brasil, região, estado, cidade e modalidade;
- palavra-chave opcional;
- cards claros com órgão, cidade, valor, prazo e modalidade;
- identificação do portal de disputa;
- indicação conservadora das condições de acesso do portal;
- itens estruturados do PNCP diretamente nos resultados;
- quantidade, unidade e valor unitário estimado quando publicados;
- histórico de preços homologados do Compras.gov sob demanda;
- média, mediana, menor, maior e último preço encontrado;
- marcas e fornecedores vencedores quando a fonte pública disponibiliza;
- lista de oportunidades e radares no preview.

## O que não entra

O MEI não expõe Jornada, perfil empresarial, tutoriais de participação ou precificação operacional. Essas capacidades permanecem no LicitaNexo Pro.

## Arquitetura

`mei_app.py` é um entrypoint Streamlit independente e reutiliza o mesmo catálogo global sincronizado, o mesmo PostgreSQL e os clientes oficiais já existentes. O `app.py` do Pro permanece intacto.

A versão inicial mantém lista e radares apenas na sessão do navegador. Autenticação, persistência por conta, alertas externos e billing de R$ 29,90 devem ser conectados somente depois da validação da experiência, para não misturar o plano MEI com a assinatura Pro já existente.

## Fontes de dados

- Catálogo de oportunidades: catálogo global PNCP já sincronizado pelo LicitaNexo.
- Itens do edital: endpoint oficial de itens do PNCP.
- Histórico de preços: API de Dados Abertos / Pesquisa de Preços do Compras.gov.
- Marca e fornecedor: somente quando presentes nas fontes públicas consultadas.

O LicitaNexo não inventa preço, marca, fornecedor ou condição de portal quando a informação não puder ser verificada.
