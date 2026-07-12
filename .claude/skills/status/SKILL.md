---
name: status
description: Resumo executivo rápido (segundos, não minutos) do progresso do projeto — % de conclusão por área, última sprint, o que está em andamento e a próxima sprint, baseado em sinais baratos (checkboxes do ROADMAP.md + git log), sem leitura profunda de código. Use quando o usuário quiser saber "como tá o projeto" no dia a dia, sem precisar da auditoria completa.
---

Dashboard rápido de status — o oposto de `/audit` em cadência: uso diário,
resposta em segundos. Não faz varredura de código, não abre um fork/
subagente, não lê arquivo por arquivo. Se o usuário quiser profundidade
(débito técnico, segurança detalhada, decisões arquiteturais), redirecionar
pra `/audit`, `/security` ou `/release` — não tentar replicar isso aqui.

## Regras

- **Rápido de propósito.** No máximo: 1 leitura do `ROADMAP.md`, 1
  `git log --oneline -15`, e um punhado de `Glob`/checagem de existência
  de arquivo pra áreas que não têm sinal nenhum no ROADMAP (ex.: Dashboard,
  Domínios, Pagamento). Nada de `Grep` extenso nem leitura de `backend/`
  arquivo por arquivo — isso é o trabalho do `/audit`.
- **Deixar claro que é estimativa.** Os percentuais vêm de checkboxes
  marcados/não marcados no `ROADMAP.md` e de sinais indiretos (arquivo
  existe ou não), não de uma auditoria linha a linha. Terminar sempre com
  uma linha tipo "estimativa rápida — pra número validado, rode `/audit`".
- Não editar nenhum arquivo.

## Como calcular os percentuais

1. Ler `ROADMAP.md` inteiro (é curto, cabe numa leitura só). Contar
   `- [x]` vs `- [ ]` por fase (Fase 0-4) pra dar o "Conclusão Geral" e o
   percentual de cada fase.
2. Mapear fases/itens do roadmap pras áreas do produto (a lista de áreas
   abaixo é o padrão deste projeto — ajustar só se a estrutura do roadmap
   mudar muito):
   - **Infraestrutura** — Fase 1 (deploy) + `infra/`/`docker-compose.prod.yml`
     existirem e o `ROADMAP.md` marcar deploy como concluído.
   - **Backend** — itens de Fase 1 relacionados a `agent_construtor.py`/
     `schema_validator.py`/API/Postgres.
   - **Frontend / Landing Page** — existência e não-obsolescência aparente
     de `index.html` (não precisa reler o conteúdo, só confirmar que existe
     e ver a data do último commit que o tocou via `git log -1 -- index.html`).
   - **Dashboard** — checagem rápida de existência (`Glob` por `dashboard`/
     `painel` em nomes de arquivo/rota); se nada aparecer, 0%.
   - **IA** — Fase 1 (motor congelado = alto %) + Fase 3 (agentes,
     normalmente baixo/médio, conforme checkboxes `[~]`/`[ ]`).
   - **Webhook** — Fase 3, item do Hunter/webhook WhatsApp.
   - **Banco** — Fase 1, item de persistência Postgres.
   - **Deploy** — Fase 1, item de hospedagem em produção.
   - **Segurança** — não estimar aqui; se o usuário perguntar segurança
     especificamente, redirecionar pra `/security`.
   - **Testes** — proporção de scripts de teste existentes
     (`backend/test_*.py`, skills de simulação) vs áreas sem nenhum teste
     conhecido — estimativa grosseira, não uma métrica real.
   - **Documentação** — proporção de docs "vivos" (`ROADMAP.md`,
     `CLAUDE.md`, `README.md`) vs `.md` soltos potencialmente obsoletos na
     raiz (contagem simples via `Glob "*.md"`).
3. "Última sprint" = últimos 5-8 commits do `git log --oneline`, resumidos
   em 1 linha cada (não copiar a mensagem crua se for longa).
4. "Em andamento" = itens do `ROADMAP.md` com `[~]` (parcial) mais qualquer
   coisa citada como "próximo passo" na sessão atual, se houver.
5. "Próxima sprint" = primeiros itens não marcados do `ROADMAP.md`, na
   ordem em que aparecem (a ordem do roadmap já reflete prioridade).

## Formato de saída

```
Projeto: <nome>

Conclusão Geral: XX%

Infraestrutura     XX%
Backend            XX%
Frontend           XX%
Landing Page       XX%
Dashboard          XX%
IA                 XX%
Webhook            XX%
Banco              XX%
Deploy             XX%
Testes             XX%
Documentação       XX%

Última sprint
✔ <commit resumido>
✔ <commit resumido>

Em andamento
• <item [~] do ROADMAP.md>

Próxima sprint
1. <primeiro item [ ] do ROADMAP.md>
2. <segundo item>
...

(estimativa rápida por checkboxes do ROADMAP.md + git log — para número
validado por leitura de código, rode /audit)
```
