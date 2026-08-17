# Segurança do LicitaNexo

## Relato responsável

Falhas de segurança não devem ser abertas em issues públicas. Envie o relato para o canal de suporte configurado pela B2G SaaS, incluindo:

- componente afetado;
- impacto observado;
- passos mínimos para reprodução;
- evidências sem dados pessoais desnecessários;
- versão/commit quando conhecido.

Não inclua senhas, tokens, chaves de API ou dados de clientes no relato.

## Princípios obrigatórios

- Secrets somente em variáveis de ambiente/GitHub Secrets/secret store do provedor.
- Senhas nunca são armazenadas em texto aberto.
- Tokens de sessão são persistidos somente como hash.
- Queries usam parâmetros; dados de usuário não são concatenados em SQL.
- Toda autorização sensível deve ser validada na camada de serviço/banco, não apenas na UI.
- PostgreSQL de produção usa conexão TLS.
- Mudanças de schema passam por migrations versionadas e Quality Gate.
- Logs não devem registrar credenciais, documentos completos ou conteúdo sensível sem necessidade operacional.
- Códigos de convite e recuperação são armazenados apenas como hash e expiram.
- Operações administrativas relevantes devem possuir auditoria.

## Dependências

Dependabot acompanha dependências Python e GitHub Actions semanalmente. Atualizações devem passar pelo Quality Gate antes do merge.

## Resposta a incidente

Em suspeita de comprometimento:

1. revogue/rotacione secrets potencialmente expostos;
2. invalide sessões afetadas;
3. preserve logs e trilhas de auditoria;
4. bloqueie temporariamente o vetor quando necessário;
5. corrija em branch dedicada com teste de regressão;
6. publique seguindo `docs/PRODUCTION_RUNBOOK.md`;
7. revise dados/eventos posteriores ao início estimado do incidente.

## Dados pessoais

A trilha de segurança utiliza hash do IP para correlação operacional. Dados pessoais devem ser coletados somente quando necessários ao serviço e tratados conforme os Termos e a Política de Privacidade vigentes.
