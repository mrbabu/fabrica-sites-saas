---
name: retomar-sessao
description: Carrega o estado mais recente do projeto Fábrica de Sites SaaS a partir da memória (MEMORY.md + arquivos de projeto/feedback mais recentes) e do repositório (git status, git log, ROADMAP.md), e devolve um briefing curto de onde a última sessão parou — pendências, decisões em aberto, guardrails a respeitar. Use no início de uma sessão nova para retomar de onde parou sem precisar reexplicar contexto.
---

Briefing de retomada — o oposto de `/gravar-sessao`. Só lê e resume, não
grava nada. Objetivo: em poucos segundos, o usuário sabe exatamente onde
parou, sem ter que reexplicar o que já foi decidido.

## Regras

- **Só leitura.** Não editar `MEMORY.md`, arquivos de memória, código ou
  `ROADMAP.md` neste comando — se algo estiver desatualizado, sinalizar no
  briefing e sugerir rodar `/gravar-sessao` ou `/roadmap`, não corrigir
  sozinho.
- Priorizar os arquivos de memória mais recentes/mais relevantes para
  estado corrente (tipicamente os `project_*` mais novos, principalmente
  qualquer um com "handoff" ou data recente no nome/descrição), não ler
  todo o histórico de memória em profundidade.
- Verificar atualidade antes de repetir uma memória como fato: cruzar com
  `git log --oneline -10` e `git status` — se a memória diz "não
  commitado" mas o git mostra commitado (ou vice-versa), reportar a versão
  real do git, não a da memória.

## Como fazer

1. Ler `MEMORY.md` inteiro (índice).
2. Abrir os arquivos de memória mais recentes/relevantes para estado atual
   (normalmente os últimos 2-4 `project_*`, mais qualquer `feedback_*`
   citado neles via `[[link]]`).
3. Rodar `git status` e `git log --oneline -10` para checar: mudanças não
   commitadas batem com o que a memória descreve como pendente? Algo que a
   memória marcava como "em aberto" já foi resolvido em commit recente?
4. Dar uma olhada rápida em `ROADMAP.md` (só os itens `[~]` e o topo dos
   `[ ]`) para saber a próxima sprint oficial, sem duplicar o trabalho do
   `/status`.
5. Montar o briefing e apresentar — não tomar nenhuma ação além disso
   (não commitar, não implementar, não perguntar "quer que eu continue" a
   menos que haja mesmo uma decisão pendente clara).

## Formato de saída

```
Onde a última sessão parou (<data/commit mais recente>):

O que aconteceu:
- <resumo curto>

Pendente / não commitado (confirmado via git status):
- <arquivo ou tema>

Decisões em aberto (da memória):
- <decisão> — <o que falta definir>

Guardrails ativos a respeitar:
- <regra curta, ex.: Guardrail #2, anti-fabricação, domínio como add-on>

Próximo passo sugerido:
<uma frase — sugestão, não execução automática>
```
