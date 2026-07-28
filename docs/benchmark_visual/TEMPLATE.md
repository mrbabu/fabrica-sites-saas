<!--
Copie este arquivo pra dentro da subpasta do nicho (crie se não
existir), nomeado "AAAA-MM-DD-<cidade ou lead>.md"
(ex.: padaria/2026-07-26-paraty.md), e preencha depois de comparar os
dois sites. Ver README.md nesta pasta pro fluxo completo.
-->

# Benchmark visual — [Nicho]

- **Data:** AAAA-MM-DD
- **Slug do nosso site:** `/demo/preview/<slug>`
- **Link gerado no Lovable:** (cole aqui, se quiser preservar)

## Nota de escopo (desde 2026-07-27)

Este template deixou de ser só sobre imagem — cobre a experiência visual
completa, por decisão registrada em `project_image_engine_evolution_2026-07-27`
(memória). Preencha só as seções que fizerem sentido pro caso; não force
nota/comentário onde não há diferença perceptível.

## Nosso site vs. Lovable — por critério

Pontue 0-10 pra cada lado onde fizer sentido; a nota é só um resumo do
que está descrito, não uma métrica formal.

| Critério | Nosso site | Lovable | Observação |
|---|---|---|---|
| Hero (imagem, headline, hierarquia) | | | |
| Imagens (aderência ao nicho, enquadramento, iluminação) | | | |
| Tipografia (legibilidade, personalidade, hierarquia) | | | |
| Layout/composição de seções (ordem, ritmo, variação) | | | |
| Espaçamento/densidade | | | |
| CTA (posição, clareza, consistência) | | | |
| Cores/contraste | | | |
| Mobile | | | |
| Sensação de "profissional/premium" | | | |

## Observação

(1-3 frases por critério relevante: o que exatamente o Lovable acertou
ou errou frente ao nosso — sem inventar métrica, só descrição do que foi
visto. Se algo do Lovable parecer inventado/genérico — ex.: endereço,
horário, ano de fundação sem base real — registrar aqui também, é um
sinal a favor do nosso guardrail de nunca fabricar dado de cliente.)

## Já apareceu em outra comparação deste nicho?

- [ ] Não — é a primeira vez, só registrar e aguardar mais casos.
- [ ] Sim — ver `AAAA-MM-DD-<nicho>.md` anterior(es): ______
      → se sim, considerar uma mudança concreta: `backend/data/niches.json`
        (categoria: ______, campo: `base_queries`/`forbidden`/`aliases`) para
        imagem, ou o item correspondente da lista priorizada em
        `project_image_engine_evolution_2026-07-27` para tipografia/layout/CTA.
        Rodar `test_image_utils.py` + `gerar_stats.py` antes de commitar
        qualquer mudança em imagem.
