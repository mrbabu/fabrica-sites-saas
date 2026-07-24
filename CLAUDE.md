# Fábrica de Sites SaaS - Contexto do Projeto

## Visão Geral
Plataforma SaaS automatizada baseada em IA Multi-Agente. O sistema gera e publica sites profissionais em menos de 30 segundos injetando variáveis de clientes em uma única estrutura de template padronizada (HTML/Tailwind), controlada por arquivos JSON.

## Arquitetura do Sistema
1. **Backend/Gateway:** `backend/app.py` expõe o Agente Construtor como API REST (FastAPI), pronta para ser chamada pelo n8n. Deve atuar estritamente como gateway — validação (via `backend/schema_validator.py`) e repasse, sem lógica de negócio pesada.
2. **Normalização de assets:** `backend/image_utils.py` já baixa e normaliza logos de clientes (Pillow) para um formato padrão antes de injetar no `site-config.json` (salvos em `assets/logos/`, na raiz, pois são servidos pelo frontend estático).
3. **Deploy:** todo código Python vive em `backend/` justamente para ficar fora do escopo de build da Vercel — a raiz do repo (`index.html`, `vendas.html`, `site-config.json`, `vendas-config.json`, `assets/`) é hospedada na Vercel como site estático puro (sem `vercel.json`, sem função serverless). O backend FastAPI (`backend/app.py`) roda separado, numa VM Oracle Cloud própria com arquitetura Zero Trust — Tailscale para administração da máquina, Cloudflare Tunnel para o tráfego HTTP, nenhuma porta exposta à internet (ver `infra/zero_trust_deploy.md` e `docker-compose.prod.yml`); deploy via `docker compose -f docker-compose.prod.yml up -d --build backend`. Render/Railway foram cogitados e descartados; não usar mais o runtime `@vercel/python`, ele causava `FUNCTION_INVOCATION_FAILED` (filesystem efêmero incompatível com as escritas em `configs/`). Não migrar a estratégia de deploy sem decisão explícita.

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

Ver `backend/agents/CLAUDE.md` (carrega automaticamente ao trabalhar nessa pasta).

## Roadmap de Desenvolvimento

Ver `ROADMAP.md` — fases alinhadas ao plano de negócio (Fase 0 a 4), com
checklist de status atual e os guardrails de segurança (WhatsApp, gate de
vendas manuais, teto do MEI) que qualquer trabalho nos agentes especializados
precisa respeitar.
