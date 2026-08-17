# Arquitetura do LicitaNexo

## Visão atual

O LicitaNexo é um monólito modular em Python com Streamlit como camada de apresentação, PostgreSQL como backend canônico de produção e workers independentes para tarefas assíncronas como sincronização do PNCP.

A escolha atual é deliberada: manter uma única aplicação reduz custo operacional enquanto o produto cresce. Modularização deve ocorrer por domínio antes de qualquer divisão em microsserviços.

## Camadas

### UI

`app.py` e módulos `*_ui.py` devem conter somente composição de tela, leitura de input, navegação e apresentação de resultados.

A UI não deve:

- decidir autorização sensível;
- escrever SQL;
- implementar regra comercial duplicada;
- conhecer detalhes do provider de pagamento;
- criar/migrar schema PostgreSQL.

### Serviços de domínio

Serviços como `BillingService`, `UsageService`, `SecurityService` e `SupportService` concentram regras de negócio e invariantes.

Regras obrigatórias:

- validar autorização na própria camada de serviço;
- tratar transações como unidade atômica;
- não engolir exceções de persistência;
- expor erros de domínio próprios quando aplicável;
- usar horário UTC internamente.

### Persistência

PostgreSQL é a fonte de verdade em produção. SQLite permanece como ambiente local/teste de compatibilidade.

Código novo deve preferir:

1. SQL compatível com ambos os bancos quando simples; ou
2. implementação PostgreSQL explícita quando houver semântica específica.

Não adicionar novas dependências à tradução regex de SQLite em `translate_sql()`. Essa camada existe apenas para migração progressiva do legado.

Mudanças estruturais são feitas exclusivamente por arquivos imutáveis em `migrations/postgres/`.

### Workers

Processos demorados ou independentes da sessão web devem sair do rerun do Streamlit. O worker PNCP é o padrão de referência:

- execução independente;
- lock distribuído/advisory lock;
- checkpoint persistente;
- idempotência;
- retries/backoff;
- observabilidade.

## Direção de modularização

Ao tocar áreas grandes de `app.py` ou `src/database.py`, a mudança deve preferencialmente extrair responsabilidade para módulos menores em vez de acrescentar novos blocos monolíticos.

Estrutura alvo incremental:

```text
src/
  services/
    auth.py
    billing.py
    opportunities.py
    support.py
    usage.py
  repositories/
    companies.py
    users.py
    opportunities.py
    billing.py
    support.py
  ui/
    auth.py
    account.py
    search.py
    support.py
    admin/
```

Não é necessário mover tudo de uma vez. Cada feature/refactor pode reduzir o monólito mantendo APIs de fachada compatíveis durante a transição.

## Contratos arquiteturais

- `app.py` não importa `psycopg` diretamente.
- nenhum módulo de UI executa DDL.
- migrations nunca são executadas automaticamente no fluxo de uma requisição/tela.
- worker não depende de `st.session_state`.
- provider externo fica atrás de gateway/service.
- domínio não depende de componentes Streamlit.
- timestamps persistidos em produção usam `TIMESTAMPTZ`.
- valores monetários de cobrança usam centavos inteiros; valores licitatórios devem migrar progressivamente para `NUMERIC` quando forem alterados estruturalmente.
- cada correção de bug relevante recebe teste de regressão.

## Qualidade

Todo PR deve passar por:

- compilação dos módulos Python;
- suíte completa SQLite;
- integração PostgreSQL real quando o banco estiver envolvido;
- verificação de migrations e tipos nativos.

O workflow `Quality Gate` é a referência para esses requisitos.

## Evolução futura

FastAPI deve ser introduzido apenas quando houver necessidade concreta de endpoints externos, especialmente webhooks de billing ou integrações. O frontend não precisa ser reescrito apenas para introduzir uma API.

Microsserviços só devem surgir quando isolamento de escala, segurança, ownership ou disponibilidade justificar o custo operacional adicional.
