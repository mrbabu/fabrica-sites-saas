# 🏗️ ROADMAP - Fábrica de Sites SaaS

## Contexto

Este roadmap segue as fases do **plano de negócio** (WaaS para MEIs/pequenos
negócios, venda ativa por WhatsApp com agentes de IA) — não é mais uma lista
técnica isolada. Cada fase de negócio tem suas tarefas de engenharia
correspondentes. Ver também `CLAUDE.md` para o estado atual do código.

## ⚠️ Guardrails (não pular, mesmo sob pressão de prazo)

1. **Não automatizar outreach frio no WhatsApp.** Disparo em massa por
   números comuns = risco de banimento pela Meta em dias. A API oficial exige
   opt-in do destinatário. Agentes de IA só podem responder conversas
   **iniciadas pelo lead** (inbound) até existir um canal de entrada seguro
   (ex.: anúncio pago levando o lead a chamar primeiro).
2. **Não automatizar vendas antes de 15-20 assinaturas fechadas
   manualmente** (Fase 2). O agente de vendas precisa ser treinado com
   objeções e scripts reais, não hipotéticos.
3. **Acompanhar o teto do MEI** (R$81 mil/ano) — a meta de 100 assinantes
   estoura esse teto rápido. Migrar para ME/Simples Nacional proativamente.
4. **Métricas de negócio, não só técnicas**, assim que houver assinantes
   reais: CAC, churn mensal (>5%/mês quebra a meta de 100 assinantes), horas
   de produção por site.

---

## Fase 0 — Fundação do negócio

- [x] Hipótese inicial de nicho definida (2026-07-10): **Clínicas
      Médicas/Saúde na Grande Vitória-ES** (odontologia, fisioterapia,
      dermatologia) — forte dependência de SEO local pra atrair paciente
      novo, o diferencial central do produto, e ticket/recorrência mais
      estável que nichos sazonais. Foi o ponto de partida da Fase 0 e
      orientou o portfólio semente e a primeira coleta de leads — não é
      mais tratada como decisão de nicho único obrigatório (ver Fase 2 e
      `docs/nichos_validacao.md`).
- [ ] Estrutura jurídica: MEI para começar, plano de migração para ME/Simples
      antes de estourar o teto
- [ ] Preço definido — planilha de cenários aponta **R$149/mês** como ponto
      ideal (R$99 exige mais que o dobro de assinantes pra bater a meta de
      lucro; R$199 reduz a base potencial)
- [x] Portfólio semente: 3 sites demo do nicho escolhido (Jardim da Penha,
      Praia do Canto, Enseada do Suá), gerados via
      `backend/scripts/gerar_portfolio_lovable.py` — prompts prontos pro
      Lovable + JSON de auditoria em `lovable_prompts/` (gitignored)

---

## Fase 1 — MVP de produto (técnico) — maior parte CONCLUÍDA

- [x] `backend/agent_construtor.py` estável: retry + autocorreção,
      100% de sucesso em teste de 10 nichos (frozen, ver `CLAUDE.md`)
- [x] `backend/schema_validator.py` (Pydantic) com schema expandido: SEO/OG,
      diferenciais, FAQ, rodapé dinâmico
- [x] Fallbacks determinísticos de imagem — nenhum campo de logo/avatar/
      background fica vazio (LoremFlickr + pravatar.cc)
- [x] Persistência em Postgres (tabela `sites`, SQLAlchemy + Alembic)
      substituindo `configs/*.json`
- [x] Frontend estático (`index.html` + `site-config.json`) no ar via Vercel
- [ ] Backend FastAPI hospedado em produção (Render/Railway) — hoje só roda
      local
- [ ] **Cobrança recorrente + régua de inadimplência + auto-suspensão**
      (Asaas ou Mercado Pago Assinaturas) — ainda não iniciado. Segundo o
      plano de negócio, isso resolve ~80% do "agente financeiro" sem
      código próprio e é a peça que falta pro MVP de produto fechar
- [ ] Campos de assinatura na tabela `sites` (plano, status de pagamento,
      domínio do cliente) quando a cobrança acima existir

---

## Fase 2 — Vendas manuais (GATE — ver guardrail #2)

**Mudança de escopo (2026-07-12):** a validação comercial deixou de
buscar confirmação de um nicho único pré-definido e passou a testar
múltiplos segmentos/regiões encontrados via Google Maps (infraestrutura
de coleta já preparada pra múltiplos mercados). O objetivo é identificar
quais segmentos têm maior aderência comercial pra oferta DFY antes de
decidir se a operação deve ser especializada em um segmento específico
ou manter uma abordagem multi-segmento. Critérios de avaliação, segmentos
testados e resultados: `docs/nichos_validacao.md`. Processo comercial
completo: `docs/playbook_dfy_v1.md`.

- [x] Geração de leads via Google Places API oficial
      (`backend/scripts/buscar_leads_google_maps.py`), filtrando quem não
      tem site — Facebook/Instagram/GetNinjas ficaram de fora por risco de
      ToS/anti-bot (Meta persegue scraping ativamente) e, no caso do
      GetNinjas, por ser a base de leads paga de um concorrente direto;
      descoberta nesses canais continua manual (`docs/fase2_scripts_whatsapp.md`)
- [ ] 15-20 vendas fechadas manualmente, idealmente mostrando um mockup do
      site pronto na primeira mensagem
- [ ] Documentar objeções e scripts reais — vira o material de treino dos
      agentes da Fase 3
- **Critério de saída**: 15-20 clientes pagantes, churn baixo nos 2
  primeiros meses, produção < 5h/site

### Escopo de produto dentro da Fase 2 (decidido 2026-07-12, ver skill `/product`)

Guardrail #2 mantido — nada de dashboard/self-service antes do gate acima.
"Produto" nesta fase significa tudo que aumenta conversão e valida a oferta
**sem automatizar a operação comercial**:

- [ ] Landing page de alta conversão (`vendas.html`)
- [ ] Demonstração pública sem login
- [ ] Fluxo "gerar antes de cadastrar"
- [~] Templates premium (`index.html`) — redesign completo aplicado
      (tipografia, faixa-ticker de assinatura, hero em duotone com as
      cores do cliente, motion, carrossel de serviços; commit `3ab4feb`,
      2026-07-14). Ainda é um único template, não múltiplas opções —
      "premium" aqui é uma direção visual, não variantes selecionáveis
- [ ] Página de planos e diferenciais (contratação ainda manual)
- [ ] Portfólio, FAQ e conteúdo para SEO
- [~] Melhorias de UX da demonstração — campo de contexto livre sobre o
      negócio e campo de URLs manuais de portfólio (fotos reais do
      cliente substituem o stock photo no hero/seções, mesmo padrão do
      `logo_url`) adicionados ao `/demo` (commit `3123628`, 2026-07-14)

Fora de escopo até bater o gate de 15-20 clientes pagantes: dashboard
completo, assinatura self-service/checkout automático, compra/provisionamento
automático de domínio, automação de vendas. Revisitar esta lista quando o
gate for atingido.

---

## Fase 3 — Automação por agentes de IA (ordem por segurança, não conveniência)

- [~] `backend/agents/hunter.py` — extração de lead via regex a partir de
      texto de WhatsApp (lógica real; sem integração de webhook real ainda)
- [~] `backend/agents/vendedor.py` — `conectar_lovable()` e
      `enviar_link_demonstracao()` implementados, porém mockados (sem
      chamada real ao WhatsApp Business API). **Só pode operar em
      conversas iniciadas pelo lead** (guardrail #1)
- [~] `backend/agents/financeiro.py` — conciliação PIX real e testada;
      `monitorar_pagamento()` só parseia webhook recebido, sem chamada a
      gateway real ainda
- [ ] Integração com BSP **oficial** do WhatsApp (360dialog/Twilio/Gupshup)
      — não Z-API nem outras soluções não-oficiais
- [ ] Fechar o gap de contrato `referencia_id` entre Hunter → Vendedor →
      Financeiro (hoje nenhum dos dois primeiros produz esse campo, o que
      bloqueia o pipeline ponta a ponta)
- [ ] Wiring n8n dos 3 agentes

---

## Fase 4 — Escala

- [ ] Métricas de negócio visíveis (CAC, churn, receita/assinante) — não
      só métricas técnicas de geração de site
- [ ] Relatórios mensais de valor pro cliente (visitas, cliques no
      WhatsApp) — reduz churn mostrando resultado
- [ ] Replicar o playbook para novo nicho/cidade

---

## Princípios arquiteturais (mantidos)

1. **JSON Schema Driven** — o template HTML depende só do `site-config.json`;
   toda customização de cliente vive no JSON, nunca hardcoded.
2. **Validação rigorosa** — a IA preenche um contrato (schema) já definido;
   o validador rejeita qualquer coisa fora dele.
3. **Idempotência** — reexecutar não duplica (ex.: `upsert_site` por slug).
4. **Observabilidade** — geração e validação são logadas (`metrics.py`).

Infraestrutura de escala enterprise (RabbitMQ/Redis, ELK, Prometheus/
Grafana, múltiplos templates simultâneos) foi removida deste roadmap por
ser prematura para a fase atual (MEI/fundador solo) — revisitar só quando
o volume de assinantes justificar, não antes.

---

## 📚 Documentação Viva

Este roadmap é atualizado conforme as fases avançam. Fase de negócio
concluída = próxima fase priorizada, não a lista técnica antiga.
