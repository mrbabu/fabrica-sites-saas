---
name: gravar-sessao
description: Revisa a sessão atual e persiste no sistema de memória (tipos project/feedback/user/reference) tudo que for decisão de negócio, correção de abordagem confirmada, ou contexto de projeto ainda não registrado — atualiza os arquivos de memória por tópico e o índice MEMORY.md. Use quando o usuário disser "grava isso", "salva o que decidimos", ou quiser fechar um checkpoint da sessão antes de encerrar.
---

Checkpoint explícito de memória — o oposto de salvar memória de forma
implícita ao longo da conversa. Quando o usuário chama este comando, ele
quer ter certeza de que nada relevante da sessão atual ficou de fora antes
de fechar o terminal.

## Regras

- Usar os mesmos critérios de tipo/exclusão já definidos globalmente para
  memória (arquivos em
  `C:\Users\Familia Melo\.claude\projects\E--fabrica-sites-saas\memory\`):
  tipos `user`, `feedback`, `project`, `reference`; nunca salvar padrão de
  código, histórico de git, receita de bug, ou o que já está em
  `CLAUDE.md`/`ROADMAP.md`.
- **Atualizar em vez de duplicar.** Antes de criar um arquivo novo, checar
  se já existe um arquivo de memória cobrindo o mesmo tópico (ver
  `MEMORY.md`) e editar esse arquivo em vez de criar outro.
- Decisões de negócio corrigidas pelo usuário na própria sessão (ex.: "não
  é assim, é assim") valem mais que a primeira formulação — registrar a
  versão final, não as duas.
- Não gravar tarefa em andamento/estado efêmero da conversa atual (isso é
  para plano/tasks, não para memória).

## Como fazer

1. Ler `MEMORY.md` (índice) para saber o que já está coberto.
2. Varrer a sessão atual em busca de:
   - decisões de negócio tomadas ou corrigidas (preço, escopo, prioridade,
     modelo de entrega);
   - feedback do usuário sobre como trabalhar (correção ou confirmação de
     abordagem);
   - fatos de projeto não deriváveis do código (motivação, prazo,
     combinado com terceiros);
   - referências a sistemas externos citadas pela primeira vez.
3. Para cada item: se já existe arquivo cobrindo o tópico, editar esse
   arquivo (atualizar `description` no frontmatter se o conteúdo mudou o
   suficiente). Senão, criar arquivo novo com frontmatter
   `name`/`description`/`metadata.type`.
4. Atualizar `MEMORY.md` com uma linha por arquivo novo ou por arquivo cujo
   resumo mudou (≤150 caracteres cada).
5. Reportar ao usuário, em lista curta, o que foi gravado/atualizado
   (nome do arquivo + uma frase) — não repetir o conteúdo inteiro no chat.

## Formato de saída

```
Gravado nesta sessão:
- <arquivo.md> (novo|atualizado) — <uma frase do que mudou>
- <arquivo.md> (novo|atualizado) — <uma frase do que mudou>

MEMORY.md atualizado.
```

Se não houver nada novo de fato para gravar (sessão só leu/discutiu, sem
decisão nova), dizer isso diretamente em vez de forçar uma entrada de
memória artificial.
