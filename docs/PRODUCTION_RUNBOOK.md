# LicitaNexo · Runbook de Produção

Este documento define a ordem segura de publicação do LicitaNexo quando houver alterações de código e schema PostgreSQL.

## Quality gate obrigatório

Antes de qualquer publicação, o workflow **Quality Gate** deve concluir com sucesso nos dois jobs:

- `SQLite · full suite`
- `PostgreSQL 16 · migrations + integration`

O primeiro preserva a compatibilidade local. O segundo cria um PostgreSQL real, aplica as migrations versionadas e valida sessão, rate limit, consumo mensal, billing e tipos nativos.

## Ordem de deploy

1. Merge da alteração somente com o Quality Gate verde.
2. Execute manualmente o workflow **PostgreSQL Migrations** na `main`.
3. Confirme `POSTGRES_MIGRATIONS=PASS` e `POSTGRES_SCHEMA_CHECK=PASS`.
4. Só então publique/reinicie o aplicativo Streamlit.
5. Confirme que o workflow **PNCP Worker** continua saudável.

Nunca publique uma versão do aplicativo que dependa de uma migration ainda não aplicada.

## Migrations

As migrations ficam em `migrations/postgres/` e são imutáveis depois de aplicadas.

O executor registra em `schema_migrations`:

- nome da migration;
- SHA-256 do conteúdo;
- data/hora da aplicação.

Se uma migration aplicada for editada posteriormente, o executor interrompe a operação por divergência de checksum. Correções devem ser feitas em uma nova migration.

## Banco e timestamps

PostgreSQL é o backend canônico de produção. Datas operacionais críticas devem usar `TIMESTAMPTZ` e UTC no armazenamento. Conversão para `America/Sao_Paulo` é responsabilidade de apresentação.

O tradutor SQLite → PostgreSQL em `src/db_runtime.py` existe apenas para compatibilidade do código legado. Código novo deve utilizar SQL comum aos dois bancos ou SQL PostgreSQL nativo nas camadas específicas de produção.

## Rollback

Migrations destrutivas não devem ser automatizadas sem estratégia explícita de rollback. Para alterações de tipo ou dados:

1. valide backup/snapshot no provedor PostgreSQL;
2. aplique migration compatível com versões anterior e nova quando possível;
3. publique o código;
4. só remova estruturas antigas em uma migration posterior.

Em incidente após uma migration, priorize restaurar a versão anterior do aplicativo quando o schema continuar retrocompatível. Caso contrário, restaure o snapshot do banco de acordo com o procedimento do provedor.

## Segurança

- Secrets nunca entram no repositório.
- Produção usa SSL PostgreSQL (`LICITANEXO_PGSSLMODE=require`).
- Tokens de sessão são armazenados no banco somente como hash.
- Senhas usam PBKDF2-HMAC-SHA256 com salt aleatório.
- Logs passam por redaction básica de tokens e secrets.
- Eventos de autenticação usam hash do IP em vez de IP bruto na trilha de segurança.

## PNCP

A atualização do PNCP é independente da sessão Streamlit. O worker usa:

- advisory lock para impedir concorrência;
- checkpoints persistentes;
- retries e backoff;
- retomada automática;
- atualização incremental recorrente;
- reconciliação completa semanal.

Um estado `partial` é retomável. Erro 429 deve continuar provocando desaceleração, não repetição agressiva.

## Critérios mínimos após publicação

Confirme:

- login e logout;
- ativação de convite;
- recuperação de senha;
- busca de editais;
- abertura de Meus Editais;
- análise de edital e consumo mensal;
- criação de atendimento de suporte;
- área administrativa;
- status do PNCP;
- criação/sincronização de checkout quando Mercado Pago estiver configurado.

Falhas de banco, billing ou PNCP devem aparecer em stdout/logs do ambiente de execução.
