---
name: roadmap
description: Sincroniza o checklist do ROADMAP.md com o estado real observado no código — marca itens concluídos que já foram implementados, sinaliza itens marcados como prontos que na verdade regrediram, e atualiza a lista de próxima sprint. É o único skill de governança deste projeto que edita um arquivo. Use quando o usuário disser que terminou algo e quiser refletir isso no roadmap, ou quiser recalibrar o backlog com base no que já existe.
---

Diferente de `/status`, `/audit`, `/security` e `/release` (todos
somente-leitura), este skill **edita `ROADMAP.md`** — é a única exceção
neste conjunto de skills de governança, porque `ROADMAP.md` se declara a
si mesmo como "Documentação Viva... atualizada conforme as fases avançam".

## Regras

- **Editar só o que tem evidência clara e verificável no código/repo.**
  "Cobrança recorrente implementada" só vira `[x]` se existir de fato
  código de integração com um gateway (Asaas/Mercado Pago) — não porque o
  usuário mencionou que pretende fazer isso.
- **Nunca marcar como concluído um item que depende de julgamento de
  negócio fora do repo** (ex.: "15-20 vendas fechadas manualmente",
  "estrutura jurídica MEI formalizada") — esses só o usuário sabe. Perguntar
  em vez de inferir, ou deixar como está e sinalizar como "não verificável
  pelo código".
- **Sempre mostrar o diff** do que mudou em `ROADMAP.md` antes/depois, num
  resumo curto — nunca editar silenciosamente sem listar as mudanças na
  resposta.
- Não mexer nos Guardrails (topo do arquivo) nem na seção "Princípios
  arquiteturais" — essas são decisões estáveis, não itens de progresso.
  Só o checklist de fases (`- [ ]`/`- [x]`/`- [~]`) e a lista de "próxima
  sprint" são o escopo deste skill.
- Preservar o formato exato do arquivo (mesma estrutura de seções,
  mesmo estilo de marcação `[x]`/`[ ]`/`[~]`) — usar `Edit`, não reescrever
  o arquivo inteiro.

## Como rodar

1. Ler `ROADMAP.md` inteiro.
2. Para cada item `- [ ]` ou `- [~]`, verificar no código/repo se agora há
   evidência de que está concluído, parcialmente feito, ou inalterado:
   - Itens técnicos (ex.: "Backend FastAPI hospedado em produção") — checar
     arquivos reais (`docker-compose.prod.yml`, `infra/`,
     `ACESSO-VM-TAILSCALE.txt`).
   - Itens de negócio (ex.: "15-20 vendas fechadas", "preço definido") —
     se não há como confirmar pelo repo, não alterar; opcionalmente
     perguntar ao usuário via `AskUserQuestion` se ele confirma que mudou.
3. Também checar o sentido contrário: algum item marcado `[x]` que uma
   mudança recente pode ter quebrado/revertido (raro, mas checar antes de
   assumir que "uma vez feito, sempre feito" — ex.: se `docker-compose.prod.yml`
   mudou de forma que reintroduziu uma porta pública que antes estava
   fechada).
4. Aplicar as mudanças com `Edit` (não `Write` do arquivo inteiro).
5. Atualizar a seção de fase atual em progresso, se fizer sentido, com uma
   nota curta de status (seguindo o estilo já usado no arquivo).
6. Reportar um resumo tipo:
   ```
   ROADMAP.md atualizado:
   - Fase 1: "[ ] Backend FastAPI hospedado em produção" → [x]
     (confirmado via infra/, docker-compose.prod.yml, ACESSO-VM-TAILSCALE.txt)
   - Fase 3: item do Hunter segue [~], nenhuma mudança (ainda sem webhook real)
   - Não alterado: "15-20 vendas fechadas" (não verificável pelo código —
     confirma que já bateu esse número?)
   ```

## O que NÃO fazer

- Não inventar percentual solto fora do formato de checkbox do arquivo —
  isso é o `/status`, não o `/roadmap`.
- Não adicionar itens novos ao roadmap por conta própria (isso é decisão
  de produto do usuário); só atualizar o status dos itens que já existem,
  a menos que o usuário peça explicitamente pra adicionar algo.
- Não commitar a mudança automaticamente — deixar `git add`/`git commit`
  pro usuário decidir, como qualquer outra edição de arquivo.
