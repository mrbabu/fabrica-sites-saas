# Fluxo Financeiro — Cobrança Recorrente

**Status: não implementado.** Pesquisa e recomendação para aprovação — nenhum
código foi alterado a partir deste documento. Item já registrado como
pendente na Fase 1 do `ROADMAP.md` ("Cobrança recorrente + régua de
inadimplência + auto-suspensão").

## 1. Objetivo

Fechar o ciclo `cliente fecha → paga → mensalidade recorrente confirmada
automaticamente` sem depender de conferência manual de PIX pra sempre — hoje
o fluxo é 100% manual (`docs/playbook_dfy_v1.md`, seção 8), o que é aceitável
no volume de validação (15-20 vendas) mas não escala.

## 2. Comparação: Asaas vs Mercado Pago

| | **Asaas** | **Mercado Pago** |
|---|---|---|
| Mensalidade | Nenhuma — só paga por transação usada | Nenhuma |
| PIX avulso | R$ 1,99 por transação recebida | Variável por prazo de recebimento: 4,99% (na hora) / 4,49% (14 dias) / 3,99% (30 dias) |
| PIX recorrente (assinatura) | Mesma taxa do PIX avulso (R$ 1,99) | Suporta PIX/boleto em assinaturas (API PreApproval), mas histórico é cartão-first — **taxa exata pra PIX recorrente não confirmada na documentação pública, validar antes de integrar** |
| Cartão de crédito | R$ 0,49 fixo + 2,99% a 4,29% conforme parcelas | Também variável por prazo |
| PIX Automático (BC, jornada 3) | Suportado, com webhooks dedicados (`PIX_AUTOMATIC_RECURRING_AUTHORIZATION_*`) | Também suportado |
| Custo de integração/API | Nenhum custo de setup | Nenhum custo de setup |
| Promoção conta nova | Taxas reduzidas nos primeiros 3 meses | Não identificado |
| Foco de mercado | MEI/pequenas empresas, PIX como meio principal | Mais genérico/e-commerce, marca mais reconhecida pelo consumidor final |

Fontes: [Preços e taxas Asaas](https://www.asaas.com/precos-e-taxas),
[Pix Automático (Asaas docs)](https://docs.asaas.com/docs/pix-automatico),
[Quanto custa receber pagamentos com assinaturas (Mercado Pago)](https://www.mercadopago.com.br/ajuda/quanto-custa-receber-pagamentos-assinaturas_19495),
[Pix Automático (Mercado Pago blog)](https://www.mercadopago.com.br/blog/pix-automatico-gestao-assinaturas-receita-recorrente).

## 3. Recomendação: Asaas

- **Taxa fixa e previsível** (R$ 1,99/PIX) em vez de percentual variável — pra
  uma mensalidade de referência de R$149 (`docs/playbook_dfy_v1.md`, seção 2),
  isso é ~1,3% de custo, bem abaixo dos 3,99-4,99% do Mercado Pago.
- **PIX é o meio de pagamento já em uso** (manual, hoje) — Asaas é
  historicamente mais forte em PIX pra PJ pequena que o Mercado Pago.
- **`backend/agents/financeiro.py` já foi escrito pensando nisso** — o
  formato de webhook que `monitorar_pagamento()` espera
  (`{status, valor, metadata: {referencia_id}}`) já é compatível com o
  padrão do Asaas, sem precisar reescrever a lógica de conciliação, só
  plugar o webhook real.
- Mercado Pago não está descartado — se o Asaas tiver algum problema de
  aprovação de conta/KYC, é o plano B, mas exige validar a taxa real de PIX
  recorrente antes (não confirmada nesta pesquisa).

## 4. Arquitetura proposta

```
Cliente fecha venda (manual, Fase 2)
        |
        v
Criar assinatura no Asaas (1x, manual ou via API)
  — valor: R$149/mês (ou o combinado), ciclo mensal
        |
        v
Cliente autoriza (1ª cobrança, Jornada 3 do Pix Automático)
        |
        v
Asaas cobra automaticamente todo mês
        |
        v
Webhook Asaas → POST /webhook/pagamento (rota nova)
        |
        v
AgenteFinanceiro.monitorar_pagamento() + conciliar()  [já existe, sem mudança]
        |
        v
Status "ativo" → libera/mantém o site no ar
Status "rejeitado" → régua de inadimplência (seção 5)
```

**Só é código novo:**
- Rota `POST /webhook/pagamento` (mesmo padrão de `whatsapp_inbound.py`:
  recebe, valida assinatura do webhook do Asaas, chama o `AgenteFinanceiro`
  já existente).
- Campo `referencia_id` precisa ser gerado no momento da venda manual (hoje
  não existe esse passo — é o gap de contrato já registrado no `ROADMAP.md`
  Fase 3: "nenhum dos dois primeiros produz esse campo").
- Colunas de assinatura na tabela `sites` (plano, status de pagamento,
  próxima cobrança) — já previsto no `ROADMAP.md` Fase 1.

**Não é código novo:** a lógica de conciliação (`AgenteFinanceiro`) já está
pronta e testada.

## 5. Régua de inadimplência e auto-suspensão (a definir)

Ainda em aberto — decisão de negócio, não só técnica:
- Quantos dias de atraso até suspender o site (sugestão inicial: 5-7 dias,
  Asaas já reenvia cobrança automaticamente em caso de falha)?
- Aviso ao cliente antes de suspender (WhatsApp manual, mesmo canal da
  venda) ou só depois?
- Suspender = tirar do ar, ou só remover branding/funcionalidade?

## 6. Guardrails

- Nenhuma automação de cobrança substitui o processo de venda manual — isso
  é sobre *receber* de quem já fechou, não sobre vender sozinho. Não
  conflita com o guardrail #2 do `ROADMAP.md`.
- Dados financeiros de cliente seguem a mesma regra do `CLAUDE.md`: nunca
  logar em texto plano.

## 7. Plano de implementação quando ativar (esqueleto, não construir ainda)

Divisão em fases pra quando o critério da seção 8 for atingido — só pra
deixar o desenvolvimento previsível, nenhuma tabela ou rota deve ser criada
a partir desta seção isoladamente.

**Fase 1 — Cadastro do cliente:** tabela `customers` (id, nome, telefone,
email, empresa, site_id).

**Fase 2 — Assinatura:** tabela `subscriptions` (id, customer_id, provider,
external_id, status, valor, data_inicio, proximo_pagamento).

**Fase 3 — Webhook:** eventos mínimos a tratar — `PAYMENT_CREATED`,
`PAYMENT_CONFIRMED`, `PAYMENT_OVERDUE`, `PAYMENT_DELETED` (nomes exatos a
confirmar contra a documentação real do Asaas no momento da implementação,
não fixar agora).

**Fase 4 — Controle do site:** campo `sites.status` — `ACTIVE`, `TRIAL`,
`SUSPENDED`, `CANCELLED`.

## 8. Critério para implementar

Pode começar antes do gate de 15-20 vendas (diferente do item de imagens/
nichos) — resolve dor ativa (conferência manual de PIX já está acontecendo
agora) e não amplia escopo de vendas automatizadas. Prioridade real depende
de quantos clientes pagantes já existem: com poucos, conferência manual
ainda é viável; a automação compensa a partir de ~5-10 assinantes ativos.

## 9. Não implementado

Documento apenas. Nenhum código, webhook ou conta Asaas foi criado a partir
desta pesquisa.
