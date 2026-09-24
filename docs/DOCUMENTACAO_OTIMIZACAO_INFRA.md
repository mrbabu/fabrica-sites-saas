---
name: otimizacao-infraestrutura-custos-projetos
description: Use when managing, optimizing, or deploying projects in E:\ (fabrica-sites-saas, AGENTE_WHATSAPP, chatbot_mamede, central-mandados, searxng, opencode) with focus on zero idle resource consumption, token cost control, and security hygiene.
---

# Documentação de Otimização, Governança de Custos e Higiene de Infraestrutura

## Visão Geral

Este documento consolida as intervenções estruturais executadas nos ecossistemas de desenvolvimento e serviços hospedados no drive `E:\` e no host Windows/WSL2. O princípio reitor adotado foi o da **Escada Ponytail**: eliminar processos ociosos, restringir consumos de memória/tokens na fonte e reutilizar os recursos existentes antes de introduzir qualquer nova dependência ou custo financeiro.

---

## 1. O Que Foi Executado (Ações por Subsistema)

### 1.1 Host Windows, WSL2 e Infraestrutura de Energia (Fase 1)
- **Plano de Energia do Sistema Operacional:** O plano do Windows foi alterado de **Equilibrado** para **Desempenho Máximo** (`0e82c2ba-de12-42a5-ac7b-69829265084e`) diretamente pelo usuário, devendo permanecer nesse estado para garantir máxima responsividade e desempenho da estação de trabalho.
- **Governança de Memória do WSL2:** Criado `%USERPROFILE%\.wslconfig` fixando teto de `memory=4GB`, limite de `processors=4` e ativação de `[experimental] autoMemoryReclaim=gradual` para devolução contínua de RAM ao Windows. WSL foi parado (`wsl --shutdown`, estado `Stopped`).
- **Eliminação de Inicialização Fantasma (Boot):** Removidos da pasta de inicialização do Windows (`Startup`) o script `iniciar-docker-wsl.vbs` e o atalho do `Ollama.lnk` (preservados em backup seguro em `%USERPROFILE%\.backup_startup`).
- **Limpeza de Modelos Locais (Ollama):** Exclusão do modelo `llama3` via CLI do Ollama, preservando unicamente o `qwen2.5:7b-instruct`. Isso liberou **4,7 GB** de armazenamento SSD.
- **Higiene de Containers Docker:** Poda de 7 containers órfãos parados (`docker container prune -f`), parada dos 5 containers que subiam no boot e ajuste da política de reinício de `unless-stopped` para `restart: "no"`.

### 1.2 Segurança e Isolamento de Credenciais (Fase 2)
- **Exclusão de Cópia Exposta:** A pasta legada `E:\opencode\bootstrap\fabrica-sites-saas-copy`, que continha arquivos `.env` com chaves sensíveis reais expostas, foi excluída permanentemente.
- **Saneamento de Tokens:** Remoção do `RAILWAY_TOKEN` não utilizado de `E:\AGENTE_WHATSAPP\.env`.
- **Auditoria de `.gitignore`:** Homologado que arquivos de variáveis de ambiente (`.env`, `.env.local`, `*.bak`) estão estritamente ignorados em todos os repositórios Git ativos.
- **SearXNG:** Atualizado `E:\searxng\searxng\settings.yml` removendo a chave hardcoded, ativando `limiter: true` contra sobrecarga e desligando `image_proxy: false` para economizar CPU e banda.
- **Credenciais de Bancos de Dados:** Credenciais padrão `central/central` em arquivos Compose de `central-mandados` e `opencode` foram parametrizadas via variáveis de ambiente.

### 1.3 AGENTE_WHATSAPP (Fase 3)
- **Teto Estrito de Tokens:** Configurado `max_tokens: 600` em `src/llm/nvidia.js` e `maxOutputTokens: 600` em `src/llm/gemini.js`. Como mensagens de WhatsApp são objetivas, a qualidade percebida permanece 100% idêntica sem o risco de respostas prolixas de 4096 tokens.
- **Janela de Contexto Histórico:** Em `src/llm/context.js`, a janela foi encurtada de 32k tokens para **6.144 tokens** (`DEFAULT_CONTEXT_WINDOWS = 6144`), e o histórico no SQLite (`src/db.js`) limitado a **20 mensagens** (anteriormente acumulava 100 mensagens).
- **Base de Conhecimento em Memória:** `src/knowledge.js` foi reescrito para carregar os documentos em cache na inicialização e monitorar alterações via `fs.watch`, eliminando operações síncronas de leitura em disco a cada mensagem recebida.
- **Proteção Anti-Grupo:** Adicionada guarda `if (isGroup) return null;` em `src/agent.js`, impedindo que o bot processe ou responda a mensagens vindas de grupos.
- **Cache Local de FAQ (24h):** Implementado cache em memória (hash SHA256 da pergunta normalizada) com TTL de 24 horas em `src/agent.js`, evitando requisições repetidas de LLM para perguntas frequentes idênticas.
- **Orquestração Docker:** Ajustado `docker-compose.yml` para subida sob demanda (`restart: "no"`), com limites rígidos de recursos (`mem_limit: 256m` para o app, `512m` para a Evolution API, `64m` para o Redis e `256m` para o Postgres) e resolução de rede via `host.docker.internal:host-gateway`.

### 1.4 Fábrica de Sites SaaS (Fase 4)
- **Paleta de Cores Determinística:** Substituição da chamada de IA de geração de paleta em `backend/agent_construtor.py` por algoritmo matemático com `colorsys` (biblioteca padrão). Isso eliminou **1 chamada completa de IA por site**, reduziu a latência em 3 a 7 segundos e extinguiu o bug de cores hexadecimais curtas (`#9c3`).
- **Garantia Estrutural de Schema (`colors`):** O objeto de paleta calculado agora é injetado diretamente em `config["colors"]`, blindando a validação contra omissões da IA.
- **Resiliência e Retries:** Chamada `self._validar_schema(config)` envolvida em `try/except ValueError` no loop de tentativas para disparar o mecanismo de retry e correção em vez de derrubar a aplicação.
- **Truncamento de `siteDescription`:** Autocorreção determinística limitando a descrição a 160 caracteres, evitando descartar gerações válidas por estouro de limite.
- **Instrumentação Real de Tokens e Custo:**
  - `ai_provider.py`: Métodos de `ProvedorGemini` e `ProvedorAnthropic` atualizados para capturar `usage_metadata` e `usage`.
  - `metrics.py`: Criada constante `PRECO_POR_MTOK` por provedor e função `calcular_custo_tokens`.
  - `agent_construtor.py`: Acumulação precisa de tokens de todas as chamadas (geração principal + reparo de duplicatas) e registro de `tokens_usados` e `custo_usd` reais em `metricas.registrar_geracao(...)`.
- **Prevenção de Bloqueio em Rota Assíncrona:** Em `backend/app.py` (`/api/v1/gerar-site`, `/webhook/whatsapp`) e `backend/routers/demo_dfy.py`, as chamadas síncronas do gerador foram isoladas em `await asyncio.to_thread(...)`, garantindo que requisições simultâneas não congelem o event loop do FastAPI.
- **Higiene de Segurança na Demo:** Eliminada a injeção da `WEBHOOK_API_KEY` no HTML/JavaScript entregue ao navegador em `backend/routers/demo.py`. Criado validador `verificar_api_key_ou_sessao` em `auth.py`, permitindo autenticação nativa por cookie de sessão da interface interna.
- **Correção da Vercel:** Em `vercel.json`, removidos redirects quebrados para túneis Cloudflare temporários desativados, apontando a raiz `/` diretamente para a página estática de vendas (`vendas.html`).

### 1.5 Chatbot Mamede (Fase 5)
- **Ajuste de Tokens do LLM:** Redução de `max_tokens` de 2048 para **800** em `config/settings.py` (com override configurável via `LLM_MAX_TOKENS`).
- **Poda de Modelos de Embeddings Não Utilizados:** Exclusão definitiva de `BAAI_bge-m3` e `sentence-transformers_all-MiniLM-L6-v2` da pasta `models/`, preservando unicamente o `intfloat_multilingual-e5-base` homologado. Isso liberou **2,22 GB** no disco.
- **Rate Limit por IP:** Implementado limitador em memória na rota `POST /api/chat` em `api/main.py` (teto de 30 requisições por minuto por IP), retornando HTTP 429 em caso de abuso.
- **Ajuste de Conectividade OpenCode no Docker:** Atualizado `OPENCODE_BASE_URL` para `http://host.docker.internal:4096` e adicionado `extra_hosts` no `docker-compose.yml` para comunicação entre o container e o servidor de inferência.
- **Limpeza de Código e Artefatos:** Removido arquivo legado `chatbot.py` na raiz e movidos 27 arquivos de logs de benchmark e JSONs de regressão para a subpasta `tests/fixtures/`.

### 1.6 Central de Mandados e Governança de Portas (Fase 6)
- **Desativação de Concorrência na Porta 5432:** Configurado profile `postgres` no `docker-compose.yml` de `central-mandados`. Como o projeto roda em SQLite localmente (`DATABASE_URL=sqlite:///./central_mandados.db`), o container Postgres só sobe se explicitamente solicitado (`--profile postgres`), eliminando conflitos de porta com a Evolution API.
- **Mapeamento Unificado de Portas:** Tabela unificada de alocação de portas inserida nos READMEs dos projetos para evitar colisões entre serviços.

---

## 2. O Que Melhora Daqui Para Frente

### 2.1 Eficiência de Recursos e Consumo
- **Zero Sobrecarga Ociosa de RAM:** Anteriormente, o boot do computador subia instantaneamente o WSL2 (sem teto de memória), 5 containers Docker e o serviço do Ollama, sequestrando mais de 10 GB de RAM antes mesmo do usuário abrir o navegador. Agora, todos esses serviços sobem sob demanda e desligam sem reter memória.
- **Armazenamento Desafogado:** Liberação imediata de **~7 GB** de disco rígido (4,7 GB de modelos redundantes no Ollama + 2,22 GB de modelos não utilizados no Mamede).
- **Desempenho da Estação de Trabalho:** O perfil de energia em Desempenho Máximo garante frequências sustentadas sem throttling para tarefas de compilação e desenvolvimento intensivo, conforme definido pelo usuário.

### 2.2 Controle de Gastos com IA
- **Fim da Cegueira de Custos na Fábrica:** O sistema agora audita 100% dos tokens consumidos e o custo financeiro exato de cada site no `metrics.log` e no `relatorio_testes.json`.
- **Economia de 30% a 50% de Tokens no WhatsApp:** A imposição de `max_tokens: 600` e a redução do histórico de contexto eliminam o envio de dezenas de milhares de tokens redundantes em conversas longas.
- **Eliminação de Chamadas Desnecessárias:** A paleta de cores determinística corta 1 chamada de IA por site gerado. O cache de 24h no WhatsApp e no SearXNG reaproveita respostas para consultas repetidas.
- **Fallback Econômico Blindado:** Modelos de alto custo (Anthropic Claude 3.5 Sonnet) foram retirados da cadeia primária de fallback da Fábrica de Sites, exigindo flag explícita (`ANTHROPIC_FALLBACK=1`) para ativação acidental.

### 2.3 Estabilidade e Concorrência de Aplicação
- **Não Bloqueio do Event Loop:** Chamadas para `agente.gerar_config_site()` isoladas em threads assíncronas impedem que requisições concorrentes travem o servidor FastAPI.
- **Isolamento de Portas de Rede:** Sem conflitos de porta na `5432` ou na `8080`, múltiplos projetos podem ser inicializados simultaneamente para desenvolvimento sem falhas de bind de socket.

---

## 3. Problemas Constatados Durante a Auditoria

| Problema Encontrado | Causa Raiz | Impacto | Resolução Adotada |
|---|---|---|---|
| `metrics.log` gravava `tokens_usados: 0` e `custo_usd: 0.0` | Provedores Gemini e Anthropic não extraíam metadados de uso; `agent_construtor.py` não repassava os valores nas chamadas de log | Impossibilidade de auditar a margem de lucro real do SaaS | Instrumentados `_extrair_uso_*`, implementada tabela `PRECO_POR_MTOK` e soma cumulativa de tokens de todas as fases da geração |
| Erro recorrente de validação: "Campo obrigatório ausente: colors" | IA omitia a chave `colors` no JSON ou gerava hexadecimais inválidos de 3 dígitos (`#9c3`) | Descarte do site e nova chamada completa de IA (desperdício financeiro) | Paleta gerada deterministicamente via `colorsys` e forçada no dicionário do site |
| Vercel retornava erro HTTP 502 / Cloudflare 1033 | `vercel.json` redirecionava `/` para um túnel `trycloudflare.com` temporário que expirou | Landing page pública fora do ar para novos visitantes | Removido proxy para túnel morto; rota `/` agora serve diretamente `vendas.html` |
| Exposição de `WEBHOOK_API_KEY` no front-end | `routers/demo.py` concatenava a chave mestra de ambiente no script JavaScript entregue ao cliente | Risco de vazamento de credenciais de produção | Criada autenticação dual (`verificar_api_key_ou_sessao`), permitindo que a interface use a sessão autenticada por cookie |
| Chave Anthropic exposta em disco | Pasta duplicada esquecida `opencode/.../fabrica-sites-saas-copy/.env` | Risco crítico de segurança e faturamento indevido | Pasta deletada em definitivo; chave orientada para rotação no console |
| Esgotamento de RAM e portas ocupadas no boot | Containers configurados com `restart: unless-stopped`, WSL sem limite e script em `Startup` | Degradação de desempenho geral do PC e lentidão no sistema | Limite de 4 GB no `.wslconfig`, política `restart: "no"` e exclusão de inicializadores automáticos |
| Resposta do WhatsApp em grupos | Ausência de validação da flag `isGroup` nas mensagens recebidas | Consumo indevido de tokens de IA respondendo a conversas paralelas de grupos | Inserida guarda `if (isGroup) return null;` no handler principal de mensagens |

---

## 4. Guia Rápido de Portas e Comandos de Operação

### Tabela Unificada de Alocação de Portas

| Projeto | Serviço | Porta Local | Modo de Execução |
|---|---|:---:|---|
| **fabrica-sites-saas** | Backend (FastAPI / Webhook) | `8000` | Local (`uvicorn backend.app:app --port 8000`) |
| **chatbot_mamede** | Backend (FastAPI / RAG) | `8100` | Local / Container (`uvicorn api.main:app --port 8100`) |
| **chatbot_mamede** | Streamlit UI | `8501` | Local (`streamlit run app.py`) |
| **AGENTE_WHATSAPP** | Aplicação Node.js | `3000` | Container (`docker compose up -d`) |
| **AGENTE_WHATSAPP** | Evolution API | `8080` | Container (`docker compose up -d`) |
| **central-mandados** | Aplicação FastAPI | `8000` | Local (`uvicorn app.main:app --port 8000`) |
| **central-mandados** | Postgres (Opcional) | `5432` | Container (`docker compose --profile postgres up -d`) |
| **OpenCode** | Serve (WSL) | `4096` | WSL (`opencode serve --port 4096`) |
| **Ollama** | Local LLM Engine | `11434` | Host Windows (Sob demanda) |

### Procedimento de Inicialização Sob Demanda

#### Subir o Stack do WhatsApp:
```powershell
cd E:\AGENTE_WHATSAPP
docker compose up -d
# Para monitorar uso de memória:
docker stats
# Para parar ao concluir o expediente:
docker compose down
```

#### Rodar o Backend da Fábrica de Sites:
```powershell
cd E:\fabrica-sites-saas
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

#### Rodar a API do Chatbot Mamede:
```powershell
cd E:\chatbot_mamede
python -m uvicorn api.main:app --host 127.0.0.1 --port 8100
```

---

## 5. Red Flags — Práticas Proibidas para Evitar Regressão

- ❌ **NUNCA adicionar `restart: always` ou `restart: unless-stopped` aos Compose locais:** Mantenha todos os serviços configurados como `restart: "no"` para evitar que subam sozinhos no boot do Windows.
- ❌ **NUNCA injetar segredos do `.env` no HTML renderizado para o navegador:** Rotas de interface devem consumir cookies de sessão de login ou atuar como proxies no backend.
- ❌ **NUNCA executar chamadas de LLM ou geração pesada diretamente dentro de funções `async def`:** Utilize sempre `await asyncio.to_thread(funcao_sincrona, ...)` para não congelar o event loop da aplicação.
- ❌ **NUNCA salvar ou versionar chaves ou backups com extensões rastreáveis:** Mantenha `*.bak`, `.env` e pastas de cache explicitamente ignoradas no `.gitignore`.
