# Benchmark visual — nosso gerador vs. Lovable

Processo manual, sem código, pra usar o Lovable como inspiração pra
melhorar as buscas de imagem do Image Engine (`backend/data/niches.json`)
com critério — sem violar o congelamento do Image Engine v2
(`CLAUDE.md`/`ROADMAP.md`: só expansão de dados a partir de evidência
real, nenhuma arquitetura nova).

## Fluxo

1. Gerar o site normalmente (nosso gerador).
2. Clicar em "gerar no Lovable" na listagem de demos (`/demo/lista`).
3. Copiar `TEMPLATE.md` pra um arquivo novo dentro da subpasta do nicho
   (ex.: `padaria/2026-07-26-paraty.md` — cria a subpasta se ainda não
   existir) e registrar as observações — o que o Lovable mostrou de
   diferente do nosso resultado.
4. Repetir esse processo ao longo do tempo. Só quando o **mesmo padrão**
   aparecer em várias comparações do mesmo nicho (não numa comparação
   isolada), ele vira candidato a mudança real — é justamente pra isso
   que os arquivos ficam agrupados por nicho: fica fácil abrir a pasta
   e ver todas as comparações daquele segmento juntas.
5. Nesse ponto, atualizar `backend/data/niches.json` manualmente
   (`base_queries`/`forbidden`/aliases da categoria), rodar
   `python backend/test_image_utils.py` (tem que continuar 100%
   passando) e conferir a taxa de fallback com
   `python backend/gerar_stats.py`.

## Organização

```
docs/benchmark_visual/
  README.md
  TEMPLATE.md
  padaria/
    2026-07-26-paraty.md
  clinica/
    2026-07-29-serra.md
  academia/
    2026-08-01-vila-velha.md
```

Vantagem prática: cada mudança em `niches.json` fica com uma justificativa
documentada e consultável depois ("por que tiramos storefront de padaria?"
→ abre `padaria/` e lê as comparações que motivaram a mudança).

## Por que não é automatizado (ainda)

Só vale formalizar em código depois que esse processo manual provar que
é usado de verdade e repetidamente — mesma lógica de todo o resto do
projeto (ex.: Image Engine v2 só ganhou ranking/telemetria depois que o
v1 simples mostrou necessidade real). Ver `docs/benchmark_visual/*.md`
como o histórico bruto dessas observações; se um dia isso virar hábito
comprovadamente útil, decide-se então se compensa um script/arquivo
estruturado.
