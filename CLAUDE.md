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

## QA — esteira automatizada

Ponto de entrada único: `python backend/qa.py` (só as suítes rápidas,
determinísticas, ~13s) — é o que o hook `.githooks/pre-commit` e o CI
(`.github/workflows/ci.yml`) executam. `--todas` inclui as lentas,
`--lista` mostra o registro. Ativar o hook num clone novo:
`git config core.hooksPath .githooks`.

Regra que separa os dois grupos: **suíte no gate não pode depender de rede,
servidor de pé, LLM real ou banco.** Falha nessas condições não prova nada
sobre o commit. Quem precisa de LLM real (`test_agentes_llm.py`, benchmark
de qualidade em 50 nichos) fica em `--lentas`.

`backend/snapshots/*.json` são baseline versionado, não artefato gerado —
há uma exceção explícita no `.gitignore` (que tem um `*.json` amplo).
Atualizar após mudança intencional: `ATUALIZAR_SNAPSHOTS=1 pytest
backend/test_snapshots.py`, e **revisar o diff antes de commitar**.

### Pipeline real de geração (importante para escrever teste ou benchmark)

```
entrada -> IA #1 (paleta, max_tokens=512) -> IA #2 (config, 4096)
        -> _autocorrigir() -> _preencher_fallbacks() -> ValidadorSchema
```

Duas consequências que já causaram teste errado:

1. **São duas chamadas de IA distintas.** Contar as duas juntas mede retry
   errado — `MAX_TENTATIVAS_GERACAO` só governa a segunda.
2. **O schema valida a saída do PIPELINE, não a do modelo.** `_autocorrigir`
   reconstrói `siteTitle`, `icon` e `fontPair`; `_preencher_fallbacks`
   reescreve `metadata` inteiro e preenche imagens/contato ausentes. Um valor
   inválido nesses campos nunca chega ao validador — para testar validação de
   verdade, use um campo fora dessa lista (ex.: `faq`).

Dois pontos sem enforcement determinístico (achados pela suíte de snapshot,
registrados aqui porque afetam decisão de produto, não só de teste):

- `company.name` não é forçado pelo pipeline — vem do que o modelo devolver.
- A **cor automática por nicho** (commit `4f54580`) entra apenas no prompt
  (`agent_construtor.py:204`). Como `colors` é campo obrigatório em
  `_validar_schema`, o valor final vem do modelo: a cor derivada é
  instrução, não garantia. A derivação em si tem teste
  (`test_image_utils.py`); o que falta é enforcement no config final.

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
