# InfinitePay no LicitaNexo

Integração do Checkout Integrado da InfinitePay para o fluxo comercial do LicitaNexo.

## Configuração

A InfiniteTag oficial usada no checkout é `b2g-solinteg` (sem `$`). Ela não é uma credencial secreta.

Variáveis opcionais/recomendadas:

```env
LICITANEXO_PAYMENT_PROVIDER=infinitepay
INFINITEPAY_HANDLE=b2g-solinteg
LICITANEXO_PUBLIC_URL=http://127.0.0.1:8501
```

Em produção, `LICITANEXO_PUBLIC_URL` deve apontar para a URL HTTPS pública do LicitaNexo.

Quando houver um endpoint HTTP público próprio para webhook, também pode ser definido:

```env
INFINITEPAY_WEBHOOK_URL=https://seu-dominio.com/webhook-infinitepay
```

O webhook não é necessário para o primeiro fluxo. A confirmação principal usa o retorno do checkout + `POST /payment_check`.

## Fluxo

1. O LicitaNexo cria um `order_nsu` único.
2. Envia o pedido para `POST https://api.checkout.infinitepay.io/links`.
3. O checkout recebe o valor em centavos. O mensal oficial é `2990` (R$ 29,90).
4. Após o pagamento, a InfinitePay retorna `order_nsu`, `transaction_nsu` e `slug` pela `redirect_url`.
5. O LicitaNexo grava o retorno e consulta `POST https://api.checkout.infinitepay.io/payment_check` no servidor.
6. A conta só é liberada se `success=true`, `paid=true` e `amount` for exatamente igual ao valor do pedido armazenado.
7. Retorno forjado, pagamento pendente ou divergência de valor não libera acesso.

## Recorrência

O Checkout Integrado documentado pela InfinitePay funciona como cobrança por checkout. Este código trata cada pagamento como compra de um período do LicitaNexo. A automação de débito recorrente mensal deve ser habilitada somente quando houver confirmação/documentação específica da API de Planos e Recorrências da InfinitePay.

## Webhook

A InfinitePay exige URL publicamente acessível para webhook; `127.0.0.1` não atende essa condição. Enquanto o desenvolvimento estiver local, o retorno do navegador + `payment_check` é suficiente para validar o fluxo sem confiar apenas na URL de redirecionamento.
