---
name: audit
description: Auditoria técnica completa e recorrente do projeto — lê todo o repo e toda a documentação (.md), inspeciona o código implementado, compara documentação x implementação, lista testes existentes, aponta débitos técnicos/riscos e gera relatório executivo + backlog priorizado. Use quando o usuário pedir uma auditoria, um raio-x do projeto, "quanto já foi feito", ou quiser conferir se a documentação ainda bate com o código antes de planejar a próxima sprint.
---

Auditoria somente-leitura de governança do projeto — a varredura **completa**
e mais lenta (minutos, não segundos). Roda sob demanda (`/audit`),
tipicamente a cada marco relevante (fim de fase do `ROADMAP.md`, antes de
retomar o projeto depois de um hiato, ou quando o usuário suspeitar que a
documentação divergiu do código).

## Skills irmãos (não duplicar o trabalho deles aqui)

Este projeto tem 5 skills de governança, cada um com cadência e escopo
diferentes — usar o certo em vez de sempre puxar o `/audit` completo:

- **`/status`** — resumo rápido (segundos), baseado em sinais baratos
  (checkboxes do `ROADMAP.md` + `git log` + existência de arquivo-chave).
  Sem leitura profunda de código. Uso diário.
- **`/audit`** (este skill) — varredura completa, lê o repo inteiro,
  compara doc x código, gera as 21 seções abaixo. Uso pontual/marco.
- **`/security`** — só a dimensão de segurança, em profundidade (headers,
  rate limit, CORS, exposição de porta, etc.). Mais rápido que `/audit`
  quando a dúvida é só "isso é seguro pra produção?".
- **`/release`** — checklist objetivo de prontidão pra produção
  (deploy/rollback/backup/monitoramento/alertas/healthcheck). Rodar antes
  de publicar uma versão nova ou dar acesso a um cliente real.
- **`/roadmap`** — o único que **edita** um arquivo (`ROADMAP.md`): sincroniza
  o checklist do roadmap com o estado real observado no código.

A seção 9 (Segurança) e a seção 21 (Prontidão pra Produção) deste relatório
devem ficar **resumidas** (uma tabela curta) — se o usuário quiser o
detalhe fundo de qualquer uma das duas, aponte pra `/security` ou
`/release` em vez de replicar a investigação aqui.

## Regras inegociáveis

- **Nunca altera arquivos, nunca commita, nunca dá push.** Só leitura
  (`Read`, `Glob`, `Grep`, `git log`/`git status`/`git diff` — nada além
  disso).
- **Verifica o estado real antes de confiar em qualquer doc ou memória.**
  `CLAUDE.md`/`README.md`/os `.md` históricos já divergiram do código real
  mais de uma vez neste projeto — trate-os como hipótese a confirmar, não
  como fonte de verdade. Para infraestrutura, cheque artefatos concretos
  (`ACESSO-VM-TAILSCALE.txt`, `infra/*.md`, `docker-compose*.yml`) em vez
  de só citar o que a documentação afirma.
- Entrega **primeiro o relatório completo**; só depois de o usuário revisar
  é que qualquer item vira plano de execução (usar o fluxo normal de plano,
  não pular direto pra implementação).

## Como rodar

Delegue a exploração para um fork/subagente somente-leitura (mantém o
contexto principal livre do ruído de dezenas de leituras de arquivo, mas o
relatório final volta inteiro pra conversa). Instrua o fork a:

1. **Ler todo o repositório** relevante: `backend/` (app.py,
   schema_validator.py, agent_construtor.py, ai_provider.py,
   image_utils.py, metrics.py, db.py, models_db.py, repository.py,
   alembic/, agents/, scripts/, routers/, tests), `infra/`,
   `docker-compose*.yml`, `Dockerfile`, `entrypoint.sh`, `deploy.sh`,
   `index.html`, `site-config.json`, `vendas.html`, `vendas-config.json`,
   `leads/`, `.env.example`, `.gitignore`.
2. **Ler toda a documentação**: `ROADMAP.md`, `CLAUDE.md` (raiz e
   `backend/agents/CLAUDE.md` se existir), `README.md`, tudo em `docs/`, e
   qualquer `.md` histórico solto na raiz (ex.: `FASE1.md`, `SETUP.md`,
   etc. — a lista muda com o tempo, listar o que existir de fato via
   `Glob "*.md"` em vez de assumir os mesmos nomes de sempre).
3. Rodar `git log --oneline -50` e `git status` pra situar o estado atual.
4. **Comparar documentação x implementação** decisão por decisão — não só
   "o que existe", mas "o que cada doc afirma que existe/está decidido" vs
   "o que o código realmente faz hoje".
5. Listar/rodar os testes existentes (não é preciso rodar chamadas de IA
   reais que custem dinheiro — listar e descrever o que cada teste cobre já
   basta, a menos que o usuário peça explicitamente pra executar).
6. Classificar cada funcionalidade/decisão em: implementada, parcial, não
   iniciada, abandonada, ou substituída por outra solução — com o motivo
   da divergência quando houver.
7. Apontar débitos técnicos e riscos, classificados por severidade.

## Estrutura do relatório

Reaproveitar a estrutura já validada nas auditorias anteriores deste
projeto (16 + 1 seções):

1. Resumo Executivo (estado geral, % de conclusão por fase do
   `ROADMAP.md`, principais riscos, próximos passos prioritários)
2. Arquitetura Atual (diagrama real, divergências entre planejado x
   implementado)
3. Comparação com a Visão do Produto (tabela ✅/🟡/🔴 por funcionalidade)
4. Inventário Completo (tabela módulo → finalidade → arquivos →
   dependências → status)
5. Backend
6. Frontend
7. Infraestrutura
8. Banco de Dados
9. Segurança (tabela item → classificação de risco → detalhe)
10. Testes (o que existe, o que falta, prioridade do que deveria existir)
11. Código Morto
12. Débito Técnico (lista priorizada)
13. Checklist Geral (tabela funcionalidade → status → arquivos → precisa
    testes? → bloqueia produção? → prioridade)
14. Roadmap Atualizado (fases, com base no estado REAL observado)
15. Comparação com o Planejamento Original (o que mudou e por quê)
16. Próxima Sprint (lista única priorizada: descrição, impacto,
    dificuldade, tempo estimado, dependências, ordem recomendada)
17. **Decisões Arquiteturais** — tabela: Documento | Decisão | Status
    (implementada/parcial/não iniciada/abandonada/substituída) | Arquivos
    relacionados | Impacto | Próxima ação. Cobrir tanto decisões técnicas
    (`CLAUDE.md`) quanto decisões de negócio/guardrails (`ROADMAP.md`).
18. **Saúde do Código** — varrer o repo por:
    - `TODO`/`FIXME`/`XXX`/`HACK` no código (`Grep` por esses termos em
      `backend/**/*.py`, `index.html`), com arquivo:linha.
    - Arquivos órfãos (scripts em `backend/scripts/` que nada mais importa
      nem nenhuma skill referencia; `.md` soltos sem link de nenhum outro
      doc).
    - Rotas do FastAPI declaradas em `app.py`/`routers/` que nada no
      frontend/skills/scripts chama.
    - Dependências em `requirements.txt` sem nenhum `import` correspondente
      no código (e o inverso: imports sem entrada em `requirements.txt`).
    - Migrations do Alembic pendentes (`alembic history` vs a revisão
      atual, se dá pra checar sem precisar de banco vivo — senão, comparar
      os arquivos de migration com o que os `models_db.py` declaram).
    - Variáveis de `.env.example` nunca lidas via `os.environ`/`os.getenv`
      no código (e o inverso).
    - Duplicação de código relevante (ex.: o caso já resolvido de
      `_slugificar` duplicado entre `image_utils.py` e `agents/vendedor.py`
      — procurar por padrões parecidos, não só esse caso específico).
    - Funções muito grandes/complexas (heurística simples: qualquer função
      com mais de ~80 linhas ou aninhamento profundo — listar candidatas,
      não é preciso rodar ferramenta de complexidade ciclomática).
19. **Segurança (resumo)** — tabela curta Item → ✅/⚠️/❌ → observação de
    uma linha (API Keys, Secrets no Git, Docker, Firewall, Cloudflare
    Tunnel, PostgreSQL exposto, Headers HTTP, Rate Limit, CORS, SSL,
    Backups, Logs sensíveis). Para o detalhe de cada item, rodar `/security`.
20. **Testabilidade** — tabela de cobertura *funcional* estimada por área
    (Landing Page, Backend/API, Webhook, Dashboard, IA/motor, Deploy,
    Domínio, Pagamento — ajustar a lista conforme os módulos reais do
    inventário da seção 4), com nota clara de que é estimativa por
    inspeção (existe teste? é manual ou automatizado? já rodou com sucesso
    documentado em algum commit/memória?), não medição de cobertura de
    linha real (não há `pytest-cov` configurado neste projeto — se isso
    mudar, atualizar esta seção pra usar o número real). Listar
    separadamente: testes automatizados existentes, testes só manuais
    (scripts com `print`/smoke test), e funcionalidades nunca testadas.
21. **Prontidão para Produção (resumo)** — tabela curta Item → ✅/⚠️/❌
    (Deploy automatizado, Rollback, Backup, Monitoramento, Alertas, Logs
    centralizados, Healthcheck, Escalabilidade). Para o checklist objetivo
    completo com critério de "pode publicar ou não", rodar `/release`.

## Depois do relatório

Não decidir sozinho o que implementar. Perguntar ao usuário qual item do
backlog (seção 16) ele quer transformar em plano de execução — cada plano
de implementação é um passo separado, com sua própria revisão.
