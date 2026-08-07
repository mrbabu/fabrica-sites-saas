# Fábrica de Sites SaaS - Contexto do Projeto

## Visão Geral
Plataforma SaaS automatizada baseada em IA Multi-Agente. O sistema gera e publica sites profissionais em menos de 30 segundos injetando variáveis de clientes em uma única estrutura de template padronizada (HTML/Tailwind), controlada por arquivos JSON.

## Arquitetura do Sistema
1. **Backend/Gateway:** `backend/app.py` expõe o Agente Construtor como API REST (FastAPI), pronta para ser chamada pelo n8n. Deve atuar estritamente como gateway — validação (via `backend/schema_validator.py`) e repasse, sem lógica de negócio pesada.
2. **Normalização de assets:** `backend/image_utils.py` já baixa e normaliza logos de clientes (Pillow) para um formato padrão antes de injetar no `site-config.json` (salvos em `assets/logos/`, na raiz, pois são servidos pelo frontend estático).
3. **Deploy:** todo código Python vive em `backend/` justamente para ficar fora do escopo de build da Vercel — a raiz do repo (`index.html`, `vendas.html`, `site-config.json`, `vendas-config.json`, `assets/`) é hospedada na Vercel como site estático puro (sem `vercel.json`, sem função serverless). O backend FastAPI (`backend/app.py`) roda separado, numa VM Oracle Cloud própria com arquitetura Zero Trust — Tailscale para administração da máquina, Cloudflare Tunnel para o tráfego HTTP, nenhuma porta exposta à internet (ver `infra/zero_trust_deploy.md` e `docker-compose.prod.yml`); deploy via `docker compose -f docker-compose.prod.yml up -d --build backend`. Render/Railway foram cogitados e descartados; não usar mais o runtime `@vercel/python`, ele causava `FUNCTION_INVOCATION_FAILED` (filesystem efêmero incompatível com as escritas em `configs/`). Não migrar a estratégia de deploy sem decisão explícita.

## Política de Deploy

Três estados possíveis, do menos ao mais crítico:

1. **Deploy Experimental** — só permitido quando existir um ambiente de infraestrutura
   explicitamente separado da produção (VM distinta, stack Docker distinta, namespace,
   compose próprio, ou staging de fato). Objetivo: validar infraestrutura, CI/CD, geração
   de sites, integrações. Nunca usar dados de produção.
2. **Deploy de Homologação** — permitido só depois de QA verde, CI verde e smoke tests
   aprovados. Destinado exclusivamente a validação funcional.
3. **Deploy de Produção** — permitido só com benchmark ≥95%, branches reconciliadas,
   nenhuma regressão conhecida, ambiente aprovado.

**Regra obrigatória:** se existir apenas um único ambiente de deploy e ele for compartilhado
com produção, esse ambiente conta como produção, independentemente do nome que a tarefa em
questão use pra ele. Hoje esse é o caso real do projeto — existe só `docker-compose.prod.yml`,
sem stack/compose isolado pra teste (ver item 3 de Arquitetura do Sistema, acima).

Não executar `docker compose up`, `docker compose pull`, `docker compose restart`,
`kubectl apply`, `terraform apply` ou operação equivalente nesse ambiente sem evidência
objetiva de que (a) existe um ambiente isolado pra teste, ou (b) houve autorização explícita
do dono do projeto pra alterar a infraestrutura compartilhada especificamente. Autorização
genérica de "trabalhar de forma autônoma" ou "modo sem interrupções" não conta como essa
autorização explícita — a ação de deploy em si precisa ser confirmada.

Sem essa evidência: documentar o bloqueio, continuar todas as tarefas locais (desenvolvimento,
testes, QA, documentação, refatorações), e encerrar só a etapa de deploy.

## Diretrizes de Desenvolvimento
- Manter código limpo, modular e focado em altíssima performance para carregamento rápido.
- Toda e qualquer customização de cliente deve residir obrigatoriamente no arquivo JSON de configuração, nunca hardcoded no HTML.
- Dados de cliente (nome, contato, logo) são sensíveis: tratar com validação estrita na entrada (`backend/app.py`/`backend/schema_validator.py`) e nunca logar em texto plano.
- Para tarefas simples (formatação de JSON, ajustes pontuais de template), prefira soluções diretas — evite over-engineering ou abstrações não pedidas.

## Convenção de Fonte da Verdade

Origem: revisão de 2026-08-06 que encontrou, no próprio processo de trabalho,
afirmações citadas como "decisão do projeto" que na verdade só existiam em
memória de sessão de um agente, nunca formalizadas aqui.

- Memória de sessão (de qualquer agente) nunca constitui decisão do projeto —
  é contexto de trabalho, não fato normativo.
- Uma decisão só é vigente quando registrada em `CLAUDE.md`, `ROADMAP.md` ou
  na DoPS (`docs/definition-of-professional-site.md`). Até lá, citar
  explicitamente como "discussão", "hipótese" ou "decisão pendente" — nunca
  como se já estivesse decidido.
- Caso real de produção confirmado diretamente pelo responsável do projeto
  conta como evidência, mesmo sem artefato anexado — registrar como "caso de
  produção informado pelo responsável, sem artefato anexado", não tratar com
  a mesma reserva que uma alegação não verificada de terceiro.
- Benchmark reproduzível (arquivo em `backend/benchmark/`) conta como
  evidência.
- Hipótese ou proposta (própria ou de terceiro, colada ou não) não conta como
  evidência até virar um dos itens acima.

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
