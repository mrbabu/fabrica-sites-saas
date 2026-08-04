# Roadmap de implementação — Definition of Professional Site

Guia de execução para transformar `docs/definition-of-professional-site.md`
(DoPS) em pipeline. Documento de planejamento: **nenhum código foi escrito,
nenhum critério foi implementado, nenhum commit foi criado.**

Premissa central, herdada da DoPS e reforçada aqui:

> O Quality Gate deixa de ser documentação e vira **etapa do pipeline**.
> Mas ele entra no pipeline em **duas etapas separadas**: primeiro medindo,
> depois bloqueando. Inverter essa ordem quebra a geração.

---

## 0. Três decisões que precedem qualquer implementação

Antes do roadmap, três conflitos com decisões já registradas no projeto. Não
são impedimentos — são pontos que exigem decisão explícita para não virarem
retrabalho.

### 0.1 O congelamento do Image Engine v2 conflita com IMG-01

`docs/benchmark_visual/README.md` registra o congelamento nestes termos:
*"só expansão de dados a partir de evidência real, nenhuma arquitetura nova"*
(referenciando `CLAUDE.md` e `ROADMAP.md`).

IMG-01 — separar ranking de **pertinência ao negócio** de ranking de
**adequação visual** — é arquitetura nova em `backend/image_utils.py`. Portanto
**está bloqueado pelo congelamento vigente**.

Isso não é um argumento para ignorar o congelamento. É o oposto: o próprio
README define o caminho de desbloqueio — *"só quando o mesmo padrão aparecer em
várias comparações do mesmo nicho, ele vira candidato a mudança real"*. A Fase 0
deste roadmap produz exatamente essa evidência em formato contável. **Decisão
necessária:** IMG-01 só sai do papel depois que a Fase 0 mostrar N falhas de
enquadramento medidas, e com quebra explícita do congelamento registrada.

### 0.2 O congelamento do `agent_construtor.py` NÃO bloqueia a Fase 1

`CLAUDE.md` marca o motor como estável e diz que ele *"não deve receber
refatoração adicional sem necessidade explícita"*. Isso poderia ser lido como
bloqueio das correções determinísticas de texto — não é.

O mesmo `CLAUDE.md` designa `_autocorrigir()` como o lugar canônico de
*"corrigir deterministicamente"* problemas recorrentes do modelo, e a regra de
que lógica de confiabilidade do pipeline vive dentro de `gerar_config_site()`.
TXT-01, TXT-04, IMG-02 e afins são **exatamente o caso de uso previsto** para
essa função — estender `_autocorrigir` é seguir a arquitetura documentada, não
refatorá-la. Nenhuma quebra de congelamento é necessária na Fase 1.

### 0.3 O cache de imagens precisa ser invalidado por data, não por "já rodou"

`backend/cache/imagens_categorias.json` é de 28/07 e `telemetria_imagens.jsonl`
tem 764 KB de histórico. Qualquer medição de baseline (Fase 0) ou correção no
Image Engine (Fase 5) que rode contra esse cache vai **misturar resultados
pré-correção e pós-correção silenciosamente**, e a métrica vai mentir.

Regra para todas as fases que tocam imagem: invalidar o cache pela **linha do
tempo da correção** (tudo anterior ao commit da mudança é descartado), nunca
confiar em "essa categoria já foi resolvida".

---

## 1. Escala de risco de regressão

A DoPS classifica impacto e esforço. O roadmap acrescenta a dimensão que decide
a **ordem**: o quanto a mudança pode quebrar o que já funciona.

| Nível | Definição | Rollback |
|---|---|---|
| **R1** | Só observa. Não altera nenhum byte do output gerado. | Trivial — remover a chamada. |
| **R2** | Altera output de forma determinística e localizada (um campo, um componente). Efeito previsível e inspecionável. | Trivial — reverter arquivo único. |
| **R3** | Altera output de forma difusa: muda o que o modelo gera ou o que a paleta produz, afetando **todos** os sites de uma vez. | Médio — reverter é fácil, detectar que quebrou não é. |
| **R4** | Altera estrutura de layout ou de seleção de imagem. Todo site muda visualmente. | Caro — exige regerar e reavaliar o corpus. |

**Regra de ordenação:** dentro do mesmo patamar de impacto, R menor vai antes.
Um R3 nunca entra antes de existir instrumentação capaz de detectar que ele
regrediu algo.

---

## 2. Matriz de implementação

Colunas: impacto (DoPS) · esforço (DoPS) · arquivo responsável · dependências ·
automação · risco de regressão · lote.

### 2.1 Critérios de correção determinística

| ID | Imp. | Esf. | Arquivo | Dependências | Autom. | Risco | Lote |
|---|---|---|---|---|---|---|---|
| TXT-01 | P0 | E1 | `agent_construtor._autocorrigir` | — | AUTO | **R2** | 1.A |
| TXT-04 | P0 | E1 | `agent_construtor._autocorrigir` + `schema_validator` | — | AUTO | **R2** | 1.A |
| IMG-02 | P0 | E1 | `agent_construtor._preencher_fallbacks` | — | AUTO | **R2** | 1.A |
| TXT-05 | P2 | E1 | `agent_construtor._truncar_para_limite` | — | AUTO | **R2** | 1.A |
| TXT-06 | P2 | E1 | `agent_construtor._autocorrigir` | — | AUTO | **R2** | 1.A |
| VIS-03 | P2 | E1 | `agent_construtor._autocorrigir` | — | AUTO | **R2** | 1.A |

### 2.2 Critérios de template/CSS isolados

| ID | Imp. | Esf. | Arquivo | Dependências | Autom. | Risco | Lote |
|---|---|---|---|---|---|---|---|
| LAY-03 | P1 | E1 | `index.html` `.ticker-*` (l. 38-43) | — | AUTO | **R2** | 1.B |
| LAY-04 | P2 | E1 | `index.html` `tickerItems()` (l. 425) | — | AUTO | **R2** | 1.B |
| CNF-04 | P1 | E1 | `index.html` `<head>` + `metadata` | — | AUTO | **R2** | 1.B |
| LAY-07 | P3 | E1 | `index.html` render de seções | — | AUTO | **R2** | 7 |
| VIS-04 | P2 | E1 | `index.html` carga de fontes | — | AUTO | **R2** | 7 |
| TEC-01 | P2 | E2 | `index.html` (build de CSS) | — | AUTO | **R3** | 7 |
| TEC-03 | P2 | E1 | `index.html` + infra | — | AUTO | **R1** | 7 |

### 2.3 Critérios de validação pura (não alteram output)

| ID | Imp. | Esf. | Arquivo | Dependências | Autom. | Risco | Lote |
|---|---|---|---|---|---|---|---|
| CNF-01 | P0 | E2 | novo `quality_gate` + `schema_validator` | — | AUTO | **R1** | 1.C |
| CNF-02 | P0 | E2 | novo `quality_gate` (compara com input do Hunter) | — | AUTO | **R1** | 1.C |
| CNF-03 | P0 | — | já garantido por design | — | AUTO | **R1** | 0 |
| IMG-05 | P1 | E1 | `quality_gate` (HTTP HEAD) | — | AUTO | **R1** | 1.C |
| IMG-04 | P2 | E1 | `quality_gate` (metadados Unsplash) | — | AUTO | **R1** | 1.C |
| IMG-06 | P2 | E1 | `image_utils.normalizar_logo` | — | AUTO | **R1** | 7 |
| TEC-02 | P1 | E2 | `quality_gate` render | L0 | AUTO | **R1** | 2 |
| TEC-04 | P2 | E2 | `quality_gate` render (Lighthouse) | L0 | AUTO | **R1** | 7 |
| LAY-06 | P1 | E2 | `quality_gate` render (375px) | L0 | AUTO | **R1** | 2 |

### 2.4 Critérios de prompt (efeito difuso)

| ID | Imp. | Esf. | Arquivo | Dependências | Autom. | Risco | Lote |
|---|---|---|---|---|---|---|---|
| TXT-02 | P0 | E2 | prompt em `gerar_config_site` + validador | **L0, L3** | AUTO | **R3** | 4 |
| TXT-03 | P1 | E2 | prompt | **TXT-02** | SEMI | **R3** | 4 |
| TXT-09 | P2 | E1 | prompt + blacklist | **L0** | AUTO | **R3** | 4 |
| TXT-08 | P2 | E2 | prompt | **L0** | SEMI | **R3** | 4 |
| TXT-07 | P0 | — | prompt (já garantido p/ depoimentos) | — | AUTO | **R1** | 0 |

### 2.5 Critérios de paleta e imagem (efeito global)

| ID | Imp. | Esf. | Arquivo | Dependências | Autom. | Risco | Lote |
|---|---|---|---|---|---|---|---|
| VIS-01 | P1 | E2 | `agent_construtor.gerar_paleta_cores` | **L0** | AUTO | **R3** | 5 |
| VIS-02 | P2 | E2 | `gerar_paleta_cores` | VIS-01 | AUTO | **R3** | 5 |
| IMG-03 | P1 | E3 | `index.html renderHero` (l. 399-402) | **IMG-01** | SEMI | **R4** | 6 |
| IMG-07 | P2 | E1 | `image_utils._rankear_imagens` (dados) | §0.1, §0.3 | AUTO | **R3** | 6 |
| IMG-01 | **P0** | **E4** | `image_utils` — ranking novo | **§0.1, §0.3, L0** | MANUAL→SEMI | **R4** | 6 |

### 2.6 Critérios de layout estrutural

| ID | Imp. | Esf. | Arquivo | Dependências | Autom. | Risco | Lote |
|---|---|---|---|---|---|---|---|
| LAY-05 | P1 | E2 | `quality_gate` (métrica de densidade) | L0 | AUTO | **R1** | 3 |
| LAY-01 | P1 | E3 | `index.html` (padding de todas as seções) | **LAY-05** | AUTO | **R4** | 6 |
| LAY-02 | P1 | E2 | `index.html` render de seções | **LAY-05** | AUTO | **R4** | 6 |

---

## 3. Critérios completamente independentes

"Independente" = não compartilha região de arquivo com outro item, não depende
de métrica que ainda não existe, e pode ser revertido sozinho sem desfazer
nenhum outro.

**11 critérios são totalmente independentes** e podem ser implementados em
qualquer ordem, inclusive em paralelo:

| Critério | Região exclusiva |
|---|---|
| TXT-01 | bloco novo em `_autocorrigir` |
| TXT-04 | bloco novo em `_autocorrigir` |
| TXT-06 | bloco novo em `_autocorrigir` |
| VIS-03 | já tem bloco próprio em `_autocorrigir` (só estender) |
| IMG-02 | `_preencher_fallbacks` |
| LAY-03 | CSS `.ticker-*` |
| LAY-04 | `tickerItems()` |
| CNF-04 | `<head>` do template |
| TEC-03 | chave de API no HTML |
| IMG-06 | `normalizar_logo` |
| LAY-07 | ordem de fundo das seções |

**Acoplados (não podem ser paralelizados):**

- Todo o grupo de **prompt** (TXT-02/03/08/09) compete pela mesma string de
  instruções. Mexer em dois ao mesmo tempo torna impossível atribuir a causa de
  uma regressão. Sequencial, obrigatoriamente.
- **LAY-01/02** dependem da métrica de densidade que LAY-05 define.
- **IMG-03** depende de IMG-01: corrigir o overlay antes de corrigir a seleção
  do hero é otimizar o disfarce em vez do problema.
- **VIS-02** depende de VIS-01 (mesma função de paleta).

---

## 4. Fases

### Fase 0 — Instrumentação (pré-requisito absoluto)

**Risco R1. Esforço E2–E3. Não corrige nada.**

Constrói o Quality Gate em **modo relatório**: lê um `site-config.json`, aplica
os critérios AUTO do Estágio 1 da DoPS e emite contagem de falhas. Não bloqueia,
não corrige, não altera output.

Entrega desta fase é exatamente a planilha proposta:

| ID | Critério | Implementado | Automatizado | Falhas no corpus | Impacto |
|---|---|---|---|---|---|
| IMG-01 | Hero adequado | ❌ | ❌ | *(medir)* | Muito Alto |
| TXT-01 | Texto duplicado | ❌ | ✅ | *(medir)* | Alto |
| … | | | | | |

**Corpus.** Os 9 configs em `configs/` são ponto de partida, mas são poucos e
enviesados (vários são testes do mesmo nicho). A fase precisa de ~30 configs
cobrindo nichos distintos, gerados via `backend/scripts/gerar_demo_dfy.py`.
Isso tem custo de API — é a única decisão de custo real do roadmap inteiro e
deve ser aprovada antes, não durante.

**Por que primeiro:** sem baseline, nenhuma correção posterior é demonstrável.
"Consertamos os textos duplicados" vira opinião; "12 → 0 em 30 sites" vira fato.
E é R1: literalmente não pode quebrar nada.

---

### Fase 1 — Quick Wins determinísticos

**Risco R2. Rollback por arquivo único. Todos E1.**

Três lotes independentes entre si, executáveis em qualquer ordem.

**Lote 1.A — Correções de texto e imagem no motor** (`agent_construtor.py`)
`TXT-01` · `TXT-04` · `IMG-02` · `TXT-05` · `TXT-06` · `VIS-03`
Todos dentro de `_autocorrigir`/`_preencher_fallbacks`, cada um em bloco próprio.
Cobre 3 dos 9 critérios P0 da DoPS ao custo de ~6 blocos de código curtos.

**Lote 1.B — Bugs visuais confirmados** (`index.html`)
`LAY-03` (ticker cortado) · `LAY-04` (ticker redundante) · `CNF-04` (preview WhatsApp)
São os únicos defeitos que a auditoria observou diretamente na tela. Rollback é
reverter um arquivo.

**Lote 1.C — Validações de contato** (`quality_gate`, modo relatório)
`CNF-01` · `CNF-02` · `IMG-05` · `IMG-04`
R1 — só valida. Entram aqui porque CNF-01/02 são P0 e a falha deles é perda
total da venda.

**Por que antes do gate bloqueante:** se o gate for ligado com a taxa de falha
atual, cada geração vai reprovar, esgotar as 3 tentativas de
`MAX_TENTATIVAS_GERACAO` e **falhar**. A Fase 1 derruba a taxa de falha primeiro;
só então o bloqueio é seguro.

---

### Fase 2 — Gate de render

**Risco R1. Esforço E2.**

Estágio 2 da DoPS: headless em 320/375/768/1280px, ainda em modo relatório.
`LAY-06` · `TEC-02` · verificação visual de `LAY-03` pós-correção.

Valida que o Lote 1.B realmente resolveu o ticker em todos os viewports — não
só no que foi inspecionado.

---

### Fase 3 — Ligar o gate como bloqueante

**Risco R3. Esforço E2. É a virada de chave do projeto.**

Move o Quality Gate para dentro do laço de retry em `gerar_config_site()` —
posição já prescrita por `CLAUDE.md` para lógica de confiabilidade. Reprovação
passa a gerar nova tentativa em vez de site ruim entregue.

`LAY-05` entra aqui: define a métrica de densidade e marca sites abaixo do
limiar como "modo compacto" (ainda sem mudar layout).

**Pré-condição objetiva:** taxa de reprovação do corpus < 20% após a Fase 1.
Acima disso, o bloqueio transforma reprovação em falha de geração.
**Checkpoint obrigatório:** `python backend/test_agentes.py 10` precisa manter
taxa de sucesso ≥ 95% (a meta que o motor já atingiu com 100%).

---

### Fase 4 — Prompt

**Risco R3. Sequencial, um critério por vez.**

`TXT-02` (FAQ genérico — P0) → `TXT-03` → `TXT-09` → `TXT-08`

Só depois da Fase 3 porque mudança de prompt afeta **todo** o texto gerado, e
sem o gate medindo não há como saber se corrigir o FAQ degradou os serviços ou
os diferenciais. Cada critério entra isolado, com re-medição do corpus entre um
e outro.

---

### Fase 5 — Paleta e contraste

**Risco R3. Esforço E2.**

`VIS-01` (contraste AA) → `VIS-02` (coerência de matiz)

Toca `gerar_paleta_cores`, que alimenta todos os sites. Como a cor é derivada do
nicho automaticamente (mudança recente, commit `4f54580`), o risco é sistêmico:
uma correção de contraste mal calibrada muda a cor de todos os sites de uma vez.
Exige re-render do corpus inteiro.

---

### Fase 6 — Investimentos estruturais

**Risco R4. Duas frentes independentes, cada uma com escopo próprio.**

**Frente A — IMG-01: ranking duplo**
Separar *business relevance* de *visual suitability*: a pergunta do hero deixa de
ser "essa foto representa uma igreja?" e passa a ser "essa foto funciona como
banner?". Depende de §0.1 (quebra de congelamento) e §0.3 (invalidação de cache).
`IMG-03` e `IMG-07` vêm junto, depois.

**Frente B — Densidade adaptativa: LAY-01 + LAY-02**
Padding e omissão de seção passam a escalar com o orçamento de conteúdo definido
em LAY-05. Muda o layout de todo site gerado.

Nenhuma das duas entra sem aprovação incremental com checkpoint — é mudança
visual de produção.

---

### Fase 7 — Polimento

Resto dos P2/P3: `LAY-07` · `VIS-04` · `IMG-06` · `TEC-01` · `TEC-03` · `TEC-04`.
Só faz sentido com os gates das Fases 0–3 de pé; sem gate, cada correção pontual
regride na geração seguinte.

---

## 5. Checkpoints de teste por fase

| Fase | Checkpoint de entrada | Checkpoint de saída | Não pode regredir |
|---|---|---|---|
| **0** | Corpus de ~30 configs aprovado e gerado | Planilha de baseline preenchida com contagem por critério | — (R1) |
| **1.A** | Baseline da Fase 0 | Falhas de TXT-01/04, IMG-02 = 0 no corpus | `test_agentes.py 10` ≥ 95% |
| **1.B** | — | Ticker íntegro em 320/375/768/1280; preview de link válido | Render visual das 9 demos existentes |
| **1.C** | — | CNF-01/02 = 0 falhas ou lista explícita de leads com dado ruim | — (R1) |
| **2** | Fase 1.B aplicada | Zero overflow, zero erro de console no corpus | — (R1) |
| **3** | Reprovação do corpus < 20% | Gate bloqueando; nenhum site novo publicado com P0 aberto | `test_agentes.py 10` ≥ 95% — **crítico** |
| **4** | Gate bloqueante ativo | FAQ genérico = 0; re-medição completa entre cada critério | Nenhum outro critério TXT sobe |
| **5** | Corpus re-medido | Contraste AA em 100% do corpus | Nenhuma cor de nicho vira irreconhecível |
| **6.A** | §0.1 decidido, cache invalidado | Falhas de enquadramento medidas caem | `test_image_utils.py` 100%; `gerar_stats.py` sem alta de fallback |
| **6.B** | LAY-05 medindo | Sites de baixo conteúdo deixam de parecer vazios | Sites de alto conteúdo não ficam apertados |
| **7** | Fases 0–3 estáveis | Lote fechado | Nada |

Testes já existentes que servem de rede de segurança em todas as fases:
`backend/test_image_utils.py` (100% obrigatório), `backend/test_agentes.py`,
`backend/gerar_stats.py` (taxa de fallback de imagem).

---

## 6. Justificativa da ordem

A ordem não segue impacto puro — segue **risco crescente sob instrumentação
crescente**:

```
Fase 0   R1   mede, não muda nada
Fase 1   R2   muda pouco, de forma previsível, já medindo
Fase 2   R1   mede o que a Fase 1 mudou
Fase 3   R3   passa a bloquear — só com taxa de falha já baixa
Fase 4   R3   muda o modelo — só com gate detectando regressão
Fase 5   R3   muda a paleta global — só com corpus re-renderizável
Fase 6   R4   muda estrutura — só com tudo acima medindo
```

Três decisões de ordem que contrariam a intuição, e por quê:

**1. IMG-01 é o maior impacto do documento e vai na Fase 6, não na 1.**
É P0 e é o defeito percebido em menos de 2 segundos. Mas é E4, R4, esbarra num
congelamento vigente (§0.1) e não tem validação automática. Colocá-lo primeiro
significaria abrir a frente mais cara e mais arriscada sem nenhum instrumento
para medir se ela deu certo. As Fases 0–3 custam pouco e produzem justamente a
evidência que o congelamento exige para ser quebrado.

**2. O gate entra em duas etapas, e o bloqueio vem depois das correções.**
Ligar o bloqueio com a taxa de falha atual esgota `MAX_TENTATIVAS_GERACAO` e
converte "site com defeito" em "geração falhou" — troca um problema visível por
um problema pior. Medir → corrigir o barato → bloquear.

**3. Prompt vem depois de template e motor, apesar de TXT-02 ser P0.**
Correção determinística tem efeito atribuível; mudança de prompt tem efeito
difuso. Fazer a difusa primeiro contamina a medição de todas as outras.

**Maior ganho de percepção pelo menor esforço:** Fase 1 completa. Seis blocos
curtos em `_autocorrigir`, dois ajustes de ticker e um `<head>` — tudo E1, tudo
R2, tudo revertível por arquivo — eliminam 3 dos 9 critérios P0 e os dois únicos
defeitos visuais que a auditoria observou diretamente.

---

## 7. Emenda proposta à DoPS: família PRS + Authenticity Score

Sua observação sobre a sétima família procede e tem um encaixe direto no repo
que vale registrar: **`docs/benchmark_visual/` já é o processo de medição de
percepção**, criado justamente para isso. O `TEMPLATE.md` de lá já pontua
*"Imagens (aderência ao nicho, enquadramento, iluminação)"*. A família PRS não
precisa de infraestrutura nova — precisa ser formalizada a partir do que já é
preenchido lá à mão.

Proposta de critérios, prontos para entrar na DoPS §2 como seção 2.7:

| ID | Critério | Impacto | Camada | Validação |
|---|---|---|---|---|
| PRS-01 | A imagem é **culturalmente coerente** com o negócio (restaurante brasileiro não usa foto de sushi). | **P0** | Image Engine + `niches.json` | MANUAL → SEMI (via `forbidden` por cultura/região) |
| PRS-02 | O **tom emocional** da imagem bate com o nicho (escola infantil não usa foto escura, cinza, com pessoas sérias). | **P1** | Image Engine | MANUAL → SEMI (luminância + saturação por perfil de nicho) |
| PRS-03 | A **escala aparente** do negócio no site bate com a escala real (bairro não parece corporação). | **P1** | Prompt + Image Engine | MANUAL |
| PRS-04 | O site não projeta **prova social maior do que a real** (equipe enorme, prédio grande, 25 avaliações). | **P0** | Prompt + Image Engine | SEMI |
| PRS-05 | O texto soa como **o dono falaria**, não como material institucional de multinacional. | P2 | Prompt | MANUAL |

E a separação de nota que você propôs, que eu acho o ponto mais forte da sua
devolutiva — porque as duas notas podem se mover em direções opostas:

```
Professional Score   = IMG + TXT + LAY + VIS + TEC   (parece bem-feito?)
Authenticity Score   = CNF + PRS                     (parece verdadeiro?)
```

Um site pode subir em Professional e **cair** em Authenticity ao mesmo tempo:
foto de stock impecável, prosa institucional polida, prova social inflada. Uma
nota só esconderia essa troca; duas notas a expõem. Isso também dá nome ao
guardrail antifabricação que o projeto já tem (`CNF-03`, depoimentos nunca
inventados): ele deixa de ser uma regra avulsa e passa a ser a base de uma das
duas notas.

**Não apliquei essa emenda na DoPS** — você declarou o documento concluído, e
alterá-lo por conta própria seria decidir no seu lugar. Se aprovar, o PRS entra
como §2.7 e o Authenticity Score como §3.1, e a matriz de cobertura passa de 34
para 39 critérios.

---

## 8. Resumo executivo

| Fase | O que faz | Risco | Esforço | Critérios |
|---|---|---|---|---|
| 0 | Mede baseline (a planilha) | R1 | E2–E3 | — |
| 1 | Quick wins determinísticos | R2 | 9× E1 | 13 |
| 2 | Gate de render | R1 | E2 | 2 |
| 3 | **Gate passa a bloquear** | R3 | E2 | 1 |
| 4 | Prompt | R3 | 4× E2 | 4 |
| 5 | Paleta e contraste | R3 | E2 | 2 |
| 6 | IMG-01 + densidade adaptativa | R4 | E3–E4 | 5 |
| 7 | Polimento | R2 | E1 cada | 6 |

**Ponto de decisão imediato:** aprovar (ou não) o custo de API para gerar o
corpus de ~30 configs da Fase 0. É o único gasto real do roadmap e o
pré-requisito de tudo que vem depois.
