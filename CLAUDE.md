# Fábrica de Sites SaaS - Contexto do Projeto

## Visão Geral
Plataforma SaaS automatizada baseada em IA Multi-Agente. O sistema gera e publica sites profissionais em menos de 30 segundos injetando variáveis de clientes em uma única estrutura de template padronizada (HTML/Tailwind), controlada por arquivos JSON.

## Arquitetura do Sistema
1. **Agente Construtor (MVP):** Atua como preenchedor inteligente. Recebe dados brutos (nome, nicho, cor) e cospe a estrutura de dados em um arquivo `site-config.json`.
2. **Template Base:** Estrutura estática universal em HTML/Tailwind que renderiza dinamicamente as variáveis contidas no `site-config.json`.
3. **Backend/Gateway:** `backend/app.py` expõe o Agente Construtor como API REST (FastAPI), pronta para ser chamada pelo n8n. Deve atuar estritamente como gateway — validação (via `backend/schema_validator.py`) e repasse, sem lógica de negócio pesada.
4. **Normalização de assets:** `backend/image_utils.py` já baixa e normaliza logos de clientes (Pillow) para um formato padrão antes de injetar no `site-config.json` (salvos em `assets/logos/`, na raiz, pois são servidos pelo frontend estático).
5. **Automação (n8n):** Orquestra webhooks e integrações externas.
6. **Deploy:** todo código Python vive em `backend/` justamente para ficar fora do escopo de build da Vercel — a raiz do repo (`index.html`, `site-config.json`, `assets/`) é hospedada na Vercel como site estático puro (sem `vercel.json`, sem função serverless). O backend FastAPI (`backend/app.py`) roda separado, em uma plataforma de servidor real (Render/Railway) — não usar mais o runtime `@vercel/python`, ele causava `FUNCTION_INVOCATION_FAILED` (filesystem efêmero incompatível com as escritas em `configs/`). Não migrar a estratégia de deploy sem decisão explícita.

## Diretrizes de Desenvolvimento
- Manter código limpo, modular e focado em altíssima performance para carregamento rápido.
- Toda e qualquer customização de cliente deve residir obrigatoriamente no arquivo JSON de configuração, nunca hardcoded no HTML.
- Dados de cliente (nome, contato, logo) são sensíveis: tratar com validação estrita na entrada (`backend/app.py`/`backend/schema_validator.py`) e nunca logar em texto plano.
- Para tarefas simples (formatação de JSON, ajustes pontuais de template), prefira soluções diretas — evite over-engineering ou abstrações não pedidas.

## Status Congelado: Agente Construtor (Builder Engine)

**Estabilidade do motor CONCLUÍDA (parte técnica da Fase 1 do `ROADMAP.md`).**
`backend/agent_construtor.py` está estável e não
deve receber refatoração adicional sem necessidade explícita — é a base sobre a qual os
novos agentes especializados (`backend/agents/`) vão se apoiar.

Correção aplicada (commit "feat: builder engine stability fix 100% success rate"):
- `_autocorrigir()` — corrige deterministicamente `icon` vazio/inválido (fallback de
  emoji), sem custo de API.
- Retry automático (`MAX_TENTATIVAS_GERACAO = 3`) implementado **dentro de
  `gerar_config_site()`** (não em `executar()`), porque `test_agentes.py` chama
  `gerar_config_site()` diretamente, ignorando `executar()`. Qualquer nova lógica de
  confiabilidade/retry do pipeline de geração deve ser adicionada nesse mesmo nível.

Resultado da verificação (`python backend/test_agentes.py 10`, chamadas reais via Ollama
local): taxa de sucesso subiu de 50% (sem o fix) para **100%** — acima da meta de
>95%. Falhas resolvidas pelo retry: `siteTitle`/`siteDescription`/`ctaText`
longos demais e `subtitle` vazio (o modelo local às vezes não respeita os limites de
caracteres do prompt na primeira tentativa).

## Próxima Fase: Agentes Especializados

Em construção em `backend/agents/` — esqueleto inicial com classes e interfaces, ainda sem
lógica de negócio:
1. **`backend/agents/hunter.py`** — captura e limpeza de leads recebidos via WhatsApp.
2. **`backend/agents/vendedor.py`** — conecta com o Lovable e envia o link de demonstração ao lead.
3. **`backend/agents/financeiro.py`** — monitoramento e conciliação de pagamentos via PIX.

Esses agentes devem se comunicar via o mesmo contrato JSON (`site-config.json` /
payload de lead), seguindo o princípio de "JSON Schema Driven" já usado pelo Agente
Construtor (ver `ROADMAP.md`, Fase 3 — Automação por Agentes de IA).

**Antes de mexer em qualquer um desses três agentes, ler os guardrails no topo do
`ROADMAP.md`** — em especial: `vendedor.py` só pode responder conversas iniciadas
pelo lead (nunca disparar outbound frio, sob risco de banimento do WhatsApp), e a
automação de vendas em si não deve substituir o processo manual antes de 15-20
vendas fechadas (Fase 2 do plano de negócio).

## Roadmap de Desenvolvimento

Ver `ROADMAP.md` — fases alinhadas ao plano de negócio (Fase 0 a 4), com
checklist de status atual e os guardrails de segurança (WhatsApp, gate de
vendas manuais, teto do MEI) que qualquer trabalho nos agentes especializados
precisa respeitar.
