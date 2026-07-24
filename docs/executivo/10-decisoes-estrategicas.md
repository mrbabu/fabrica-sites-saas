# 10 — Decisões Estratégicas do Projeto

## Por que cada decisão de arquitetura foi tomada

| Decisão | Por quê | Onde está |
|---|---|---|
| HTML estático + Tailwind via CDN, sem build | O site institucional (`vendas.html`) e o template de cliente (`index.html`) nunca precisam de build/bundler pra funcionar — cada mudança de conteúdo é só editar um JSON. Menos infraestrutura, menos coisa pra quebrar, deploy é literalmente `git push` | `index.html`, `vendas.html`, ausência de `vercel.json`/`package.json` de app |
| Sem React/Next.js | O produto vendido (site do cliente) e a landing não têm necessidade de interatividade complexa que justifique um framework — foi uma proposta externa avaliada e rejeitada explicitamente durante o redesign da landing (2026-07-22) | Histórico de decisão registrado em memória de projeto |
| Sem dashboard interno grande | Login vai direto pro Site Constructor — decisão de manter simples até haver volume de dado que realmente precise de um painel | `backend/routers/demo.py`, ausência de rota `/dashboard` |
| Zero Trust (Tailscale + Cloudflare Tunnel + Oracle, NSG fechado) | Nenhuma porta de entrada exposta na VM — o único jeito de acessar é por uma rede privada (administração) ou por um túnel de saída (tráfego HTTP). Elimina a superfície de ataque de portas abertas na internet | `docker-compose.prod.yml`, `infra/zero_trust_deploy.md` |
| Cloudflare Tunnel em vez de porta pública | Permite servir HTTP sem NUNCA abrir uma porta de entrada na VM — o tráfego sai de dentro da VM em direção ao Cloudflare, não o contrário | `infra/zero_trust_deploy.md` |
| Oracle Cloud (não Render/Railway como planejado originalmente) | Substituição de infraestrutura já feita na prática (`docker-compose.prod.yml` real, VM provisionada) — decisão tomada mas **nunca propagada de volta pros documentos** (`CLAUDE.md`/`ROADMAP.md` ainda citam a opção antiga) | `infra/` |
| Vercel pro frontend estático | Deploy automático a cada `git push`, zero servidor pra manter pro que não precisa de servidor | Configuração do projeto na Vercel (fora do repo) |
| DFY ("Done For You" — a equipe gera e entrega, o cliente não mexe em nada) | O cliente-alvo (pequeno negócio local) não quer aprender ferramenta nenhuma — quer o site pronto e funcionando | `docs/playbook_dfy_v1.md` |
| Sem over-engineering / abstração prematura | Princípio explícito do `CLAUDE.md`: "para tarefas simples, prefira soluções diretas" — reforçado nesta mesma semana ao rejeitar um "Business Rules Engine" completo em favor de uma correção de poucas linhas | `CLAUDE.md`, ver caso concreto abaixo |
| Fonte única de preço (`vendas-config.json`) | Eliminar duplicação de dado sem criar uma camada de configuração nova — o backend passou a ler o mesmo arquivo que a landing usa, em vez de ter o preço hardcoded duas vezes | `backend/routers/hunter.py::_preco_base()`, `Dockerfile` |
| Congelamento do Agente Construtor | O motor de geração atingiu 100% de taxa de sucesso em teste (`CLAUDE.md`) — mexer sem necessidade explícita é risco puro, sem ganho | `CLAUDE.md`, `backend/agent_construtor.py` |

## Caso concreto desta semana: o Business Rules Engine que não foi construído

Um exemplo real e recente de disciplina de escopo, útil pra ilustrar como decisões como as acima são tomadas na prática: ao corrigir uma duplicação de preço entre a landing e o Hunter, uma proposta externa sugeriu construir um "Business Rules Engine" completo — 8 arquivos novos, YAML de regras, motor de workflow, scoring, mandato de 90% de cobertura de teste. A avaliação, usando o mesmo critério de sempre (ajuda a vender? ajuda a operação hoje? é proporcional ao estágio da empresa?), rejeitou a proposta: o projeto tem **um plano de preço real e zero clientes pagantes documentados** — construir uma "engine de regras" pra esse estágio seria meses de trabalho de infraestrutura sem nenhum cliente novo em troca. A correção real aplicada foi de duas linhas de lógica: o Hunter passou a ler o preço do mesmo arquivo que a landing já usa (`vendas-config.json`), sem criar nenhum arquivo de configuração novo.

## O que NÃO devemos fazer (armadilhas já identificadas no histórico do projeto)

| Armadilha | Por que é uma armadilha aqui |
|---|---|
| Criar módulos "porque um dia vão ser úteis" | A regra adotada é: 1 consumidor mantém a lógica local; 2 consumidores, considera extrair; só com 3+ consumidores reais vale extrair um módulo compartilhado |
| Engine de regras de negócio genérica | Ver caso concreto acima — resolve um problema que a empresa ainda não tem, ao custo de meses de trabalho sem cliente novo |
| Dashboard gigante antes de ter dado pra mostrar | Fase 4 do roadmap é justamente isso — deliberadamente adiada até haver volume real |
| Microserviços | O projeto inteiro roda num container de backend + um Postgres — dividir isso em serviços separados não resolve nenhum problema real de escala que exista hoje |
| Frameworks sem necessidade (React, Next.js, etc.) | Rejeitado explicitamente ao redesenhar a landing — HTML+Tailwind estático já atende |
| Abstrações prematuras em geral | O `agent_construtor.py` está congelado justamente pra evitar isso — funciona, não mexer sem necessidade |
| Duplicação de dado (preço, config) | Já aconteceu uma vez (preço hardcoded no Hunter) e foi corrigido — o aprendizado é checar isso proativamente em qualquer novo código que leia dado "de negócio" |
| Acoplamento entre a landing (Vercel) e o backend (VM) | A landing funciona hoje mesmo se a VM cair — qualquer mudança que crie essa dependência nova é uma regressão de resiliência, não uma melhoria |
| Automatizar venda ou WhatsApp antes da hora | Os dois guardrails mais críticos do projeto — violar qualquer um dos dois tem custo alto (banimento de canal, ou vender mal em escala com script não testado) |

## Inconsistências entre documentação e código encontradas nesta auditoria

Listadas para conhecimento — não corrigidas automaticamente, por decisão de processo (o skill de auditoria deste projeto nunca corrige, só reporta):

1. `.env` local tem `DATABASE_URL` apontando pra uma VM Oracle (`147.15.73.239`) que a própria documentação de infraestrutura (`infra/zero_trust_deploy.md`) registra como **já desligada** — não é um firewall bloqueando, é uma referência a uma máquina que não existe mais.
2. `CLAUDE.md` e `ROADMAP.md` ainda descrevem o backend como pendente de deploy em Render/Railway — a infraestrutura real (Oracle Zero Trust) já está implantada há tempo e nunca foi refletida de volta nesses dois documentos.
3. 8 arquivos `.md` na raiz do repositório (`AGENT_CONSTRUTOR.md`, `RESUMO_EXECUTIVO.md`, `FASE1.md`, `FASE2.md`, `FASE2_FINALIZADA.md`, `SETUP.md`, `API_DOCS.md`, `AGENTS.md`) descrevem uma versão do produto anterior à reorganização em `backend/` — mencionam `ANTHROPIC_API_KEY` como única IA e um modelo fixo antigo, sem qualquer menção a Postgres, Hunter ou Zero Trust.
4. `AGENTS.md` (raiz) referencia um arquivo (`backend/agents/AGENTS.md`) que não existe — o arquivo real chama `backend/agents/CLAUDE.md`.
5. `ROADMAP.md` lista "15-20 vendas fechadas" como pendência, mas não há em nenhum lugar do repositório um número real de vendas já fechadas até hoje — não dá pra saber quanto falta.
6. `docs/hunter_online_spec.md` se descreve como "não implementado", mas parte do que descreve como evolução futura (o pipeline de status manual) **já está implementado e em produção**.
