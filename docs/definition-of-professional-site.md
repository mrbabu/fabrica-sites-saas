# Definition of Professional Site (DoPS)

Padrão de qualidade objetivo para **todo site gerado pela Fábrica de Sites**.
Serve como critério de aceite do gerador: um site só pode ser entregue a um
lead se passar nos gates definidos aqui.

**Escopo.** Este documento trata da qualidade de *cada site de cliente gerado*
(`index.html` + `site-config.json`). Não trata da identidade visual da própria
Fábrica (`vendas.html`) — isso é `docs/design_system.md`, que continua sendo a
autoridade sobre paleta de marca, tipografia e motion system. Os dois se
complementam: o design system diz *como o produto se parece*; a DoPS diz
*quando um site gerado está bom o bastante para ser mostrado a alguém*.

**Origem.** Auditoria visual de 2026-08-03 sobre `configs/igreja-catolica-sao-camilo.json`
(demo real, motor atual). Fatos comprovados que motivaram este padrão:

- Imagem de hero pode ser correta para o negócio e ainda assim inadequada
  para banner principal (enquadramento).
- Existem textos duplicados entre seções.
- FAQ genérico reduz credibilidade.
- O ticker corta texto nas bordas.
- Sites com pouco conteúdo de entrada ficam visualmente vazios por causa do
  padding fixo.
- A causa é qualidade do **gerador**, não do provider de IA.

---

## 1. Princípio

> Um site parece profissional quando **nada nele denuncia que foi gerado
> automaticamente**. Não é "bonito" — é *ausência de sinais de automação*.

Os sinais de automação que o cliente percebe, em ordem de quanto tempo levam
para serem notados:

| Tempo até notar | Sinal | Efeito |
|---|---|---|
| < 2s | Imagem de hero errada/mal enquadrada | "isso não é do meu negócio" |
| < 5s | Texto repetido, placeholder visível | "isso foi cuspido por um robô" |
| < 10s | Página vazia, seções finas | "não tem conteúdo, não vale nada" |
| < 15s | FAQ genérico, CTA vago | "não entenderam o que eu faço" |
| ao clicar | WhatsApp/link quebrado | "não funciona" — perda total |

A DoPS ataca nessa ordem. Peso de impacto (`P0`…`P3`) é atribuído por *tempo
até o dano*, não por dificuldade técnica.

### Escala de impacto

| Nível | Definição |
|---|---|
| **P0 — Bloqueante** | Sozinho destrói a percepção de profissionalismo ou impede a venda. Site **não pode** ser entregue. |
| **P1 — Alto** | Percebido pelo lead na primeira leitura; reduz confiança mas não invalida. Corrigir antes de escalar volume. |
| **P2 — Médio** | Percebido em leitura atenta ou em dispositivos específicos. Acumula: 3 itens P2 juntos viram um P1. |
| **P3 — Baixo** | Polimento. Só depois de P0/P1 zerados. |

### Escala de validação

| Nível | Definição |
|---|---|
| **AUTO** | Verificável por código determinístico, sem julgamento. Vira gate de CI/pipeline. |
| **SEMI** | Verificável por heurística/proxy que pega a maioria dos casos, com falsos negativos aceitáveis. |
| **MANUAL** | Hoje exige olho humano (ou um mecanismo que ainda não existe, ex.: análise de composição de imagem). |

### Escala de esforço

| Nível | Definição |
|---|---|
| **E1** | Mudança pontual, arquivo único, < 2h. |
| **E2** | Meio dia; toca 2 arquivos ou exige teste de render. |
| **E3** | 1–2 dias; muda estrutura de template ou lógica de layout. |
| **E4** | Exige mecanismo novo (ex.: pool curado de heros, análise de imagem). |

---

## 2. Critérios

### 2.1 Imagem e mídia (IMG)

| ID | Critério objetivo | Impacto | Camada / arquivo | Validação |
|---|---|---|---|---|
| IMG-01 | A imagem de hero é adequada a **banner full-bleed**: assunto centralizado horizontalmente, sem elemento estrutural dominante fora do tema (grade, poste, carro), ponto focal fora da zona de texto central. | **P0** | Image Engine — `backend/image_utils.py` (`_rankear_imagens`, `obter_imagens_categoria`) + `index.html` (`renderHero`) | MANUAL hoje. SEMI possível: separar "pool hero" de "pool conteúdo" com critérios distintos. |
| IMG-02 | A imagem de hero **não se repete** em nenhuma outra seção da mesma página. | **P0** | agent_construtor — `_preencher_fallbacks` | **AUTO** (set de URLs) |
| IMG-03 | O overlay/gradiente do hero preserva legibilidade **sem descaracterizar a foto**: contraste do texto branco ≥ 4.5:1 e opacidade adaptada à luminância média da imagem, não fixa. | **P1** | Template/CSS — `index.html:399-402` | **SEMI** (calcular luminância média da imagem + razão de contraste) |
| IMG-04 | Imagem de hero com largura ≥ 1920px e proporção ≥ 16:9. | P2 | Image Engine | **AUTO** (metadados do Unsplash já vêm na resposta) |
| IMG-05 | Toda URL de imagem do config resolve HTTP 200 e é um tipo de imagem válido. | **P1** | Pipeline | **AUTO** |
| IMG-06 | Logo normalizado: altura padrão, sem distorção de proporção, fundo compatível com o header. | P2 | `image_utils.normalizar_logo` | **AUTO** (dimensões/formato) |
| IMG-07 | Nenhuma imagem contém termo proibido da categoria (stock genérico conflitante com o nicho). | P2 | Image Engine — `_rankear_imagens` (penalidade já existe) | **AUTO** (já implementado parcialmente) |

> **Nota sobre IMG-01.** É o único critério P0 sem caminho AUTO hoje, e é o de
> maior impacto. O motor valida *pertinência ao negócio* (a foto é da igreja),
> mas não *adequação ao papel* (serve como banner?) — são critérios diferentes,
> e hoje a mesma foto alimenta os dois usos.

### 2.2 Texto e conteúdo (TXT)

| ID | Critério objetivo | Impacto | Camada / arquivo | Validação |
|---|---|---|---|---|
| TXT-01 | Nenhum `title` ou `description` se repete entre `features`, `services`, `sections` e `faq` (comparação normalizada; similaridade ≥ 0.85 já conta como duplicata). | **P0** | agent_construtor — `_autocorrigir` + `backend/schema_validator.py` | **AUTO** |
| TXT-02 | Nenhuma pergunta de FAQ segue padrão-molde genérico ("Quais são as [X] que vocês oferecem?", "Como funciona?") nem se repete estruturalmente com outra. | **P0** | Prompt (`agent_construtor.gerar_config_site`) + validador | **AUTO** (blacklist de padrões + detecção de radical repetido) |
| TXT-03 | Toda resposta de FAQ contém ao menos **um dado concreto** presente no config: horário, endereço, telefone, prazo, nome de serviço. Resposta sem dado é considerada preenchimento. | **P1** | Prompt | **SEMI** (verificar interseção com campos do próprio config) |
| TXT-04 | Nenhum texto do template padrão vaza para produção ("Serviço 1", "Diferencial 1", "Nome Empresa", "Descrição da empresa"). | **P0** | Pipeline | **AUTO** (diff contra `ValidadorSchema.gerar_template()`) |
| TXT-05 | Limites de caracteres respeitados **sem truncamento no meio da palavra** e sem reticências órfãs. | P2 | `agent_construtor._truncar_para_limite` | **AUTO** |
| TXT-06 | Nome do negócio grafado de forma idêntica em `company.name`, `metadata.siteTitle`, `hero.title` e `footer.copyrightText`. | P2 | agent_construtor | **AUTO** |
| TXT-07 | Nenhuma alegação fabricada: depoimento, contagem de clientes, prêmio, "X anos de mercado" — só entra se veio do input. | **P0** | Prompt + `schema_validator` (`testimonials` já opcional por design) | **AUTO** para depoimentos; **SEMI** para alegações em prosa |
| TXT-08 | Português correto, com acentuação, sem resíduo de inglês vindo das queries do Image Engine. | P2 | Prompt | **SEMI** |
| TXT-09 | `cta.buttonText` e `hero.ctaText` são específicos do negócio (verbo + objeto), não genéricos ("Começar", "Saiba mais", "Clique aqui"). | P2 | Prompt | **AUTO** (blacklist) |

### 2.3 Layout e densidade (LAY)

| ID | Critério objetivo | Impacto | Camada / arquivo | Validação |
|---|---|---|---|---|
| LAY-01 | O espaçamento vertical **escala com o volume de conteúdo**. Padding fixo `py-20 md:py-28` só se aplica acima de um limiar de densidade; abaixo dele, o layout compacta. | **P1** | Template/CSS — `index.html:480,506,537,575,610,646` | **AUTO** (derivar "orçamento de conteúdo" do JSON e assertar a classe escolhida) |
| LAY-02 | Uma seção só é renderizada se tiver conteúdo mínimo viável (ex.: `sections[].content` ≥ N caracteres). Abaixo disso, **omitir** em vez de renderizar magra. | **P1** | Template + validador | **AUTO** |
| LAY-03 | Nenhum overflow horizontal e nenhum texto cortado nas bordas em 320/375/768/1280px — inclusive o ticker. | **P1** | CSS — `.ticker-*` em `index.html:38-43` | **AUTO** (headless: `scrollWidth <= clientWidth` + item do ticker inteiramente dentro do viewport) |
| LAY-04 | O ticker não repete informação já visível no hero imediatamente acima (tagline, avaliação). | P2 | Template — `tickerItems()` em `index.html:425` | **AUTO** (interseção de strings com hero) |
| LAY-05 | Composição mínima: hero + ao menos 3 blocos de conteúdo real. Abaixo disso, o site degrada para um layout **deliberadamente compacto**, não para um esqueleto esticado. | **P1** | Template + pipeline | **AUTO** |
| LAY-06 | Mobile 375px: hero legível sem zoom, alvos de toque ≥ 44px, nenhum elemento estourando. | **P1** | CSS | **AUTO** (headless) |
| LAY-07 | Duas seções consecutivas não usam a mesma cor de fundo (ritmo visual). | P3 | Template | **AUTO** |

### 2.4 Consistência visual (VIS)

| ID | Critério objetivo | Impacto | Camada / arquivo | Validação |
|---|---|---|---|---|
| VIS-01 | Todo par texto/fundo atinge contraste AA (4.5:1 corpo, 3:1 texto grande) — incluindo as cores derivadas da paleta automática. | **P1** | `agent_construtor.gerar_paleta_cores` + CSS | **AUTO** |
| VIS-02 | A paleta derivada mantém relação de matiz coerente entre `primary`, `primaryDark`, `secondary` e `accent` (sem par acidentalmente vibrante demais). | P2 | `gerar_paleta_cores` | **AUTO** |
| VIS-03 | Ícones consistentes em estilo, e nenhum ícone de fallback repetido em cards adjacentes. | P2 | `agent_construtor._autocorrigir` | **AUTO** |
| VIS-04 | `typography.fontPair` válido e ambas as fontes carregam de fato (sem FOUT para fonte de sistema). | P2 | Template | **AUTO** |

### 2.5 Confiança e conversão (CNF)

| ID | Critério objetivo | Impacto | Camada / arquivo | Validação |
|---|---|---|---|---|
| CNF-01 | Canais de contato funcionais: WhatsApp em E.164 válido com link testado, e-mail válido, link de mapa resolve. | **P0** | Pipeline + `schema_validator` | **AUTO** |
| CNF-02 | Endereço/localização **idênticos ao capturado pelo Hunter** — nenhum endereço inventado ou completado pela IA. | **P0** | agent_construtor + schema | **AUTO** (comparar com o input) |
| CNF-03 | `testimonials` vazio salvo se depoimentos reais foram fornecidos; nenhuma nota de avaliação fabricada. | **P0** | Já garantido por design | **AUTO** |
| CNF-04 | `metadata` produz um **link preview correto no WhatsApp** (og:title, og:description, og:image válida e com proporção certa) — é assim que o demo chega ao lead. | **P1** | Template `<head>` + `metadata` | **AUTO** |

### 2.6 Técnico (TEC)

| ID | Critério objetivo | Impacto | Camada / arquivo | Validação |
|---|---|---|---|---|
| TEC-01 | Sem Tailwind via CDN no site entregue ao cliente (o próprio console avisa que não é para produção); CSS resolvido em build ou arquivo estático. | P2 | Template | **AUTO** |
| TEC-02 | Zero erro de console e zero asset 404 na carga inicial. | **P1** | Pipeline | **AUTO** |
| TEC-03 | Nenhuma chave de API sem restrição de origem exposta no HTML público (hoje: Google Maps). | P2 | Template + infra | **AUTO** (grep + verificação de restrição) |
| TEC-04 | LCP < 2.5s em 4G simulado. | P2 | Template | **AUTO** (Lighthouse) |

---

## 3. Resumo de cobertura de validação

| | AUTO | SEMI | MANUAL | Total |
|---|---|---|---|---|
| **P0** | 7 | 1 | 1 (IMG-01) | **9** |
| **P1** | 9 | 2 | 0 | **11** |
| **P2** | 11 | 2 | 0 | **13** |
| **P3** | 1 | 0 | 0 | **1** |
| **Total** | **28** | **5** | **1** | **34** |

**Leitura:** 82% dos critérios são automatizáveis de forma determinística. O
único critério verdadeiramente manual (IMG-01) é justamente o de maior impacto
— é onde vale investir num mecanismo novo, não em mais regra.

---

## 4. Checklist de validação pré-deploy

Proposta de gate em três estágios. Um site só é publicado/enviado a um lead se
**todos os P0 passarem** e **no máximo 2 P2 ficarem abertos**. Qualquer P1
aberto exige aprovação humana explícita.

### Estágio 1 — Gate de JSON (sem browser, < 1s)

Roda sobre o `site-config.json` logo após `gerar_config_site()`, antes de
qualquer render. Barato o suficiente para entrar no laço de retry existente
(`MAX_TENTATIVAS_GERACAO`), transformando reprovação em nova tentativa em vez
de falha.

```
[ ] TXT-01  nenhum título/descrição duplicado entre seções
[ ] TXT-02  nenhuma pergunta de FAQ em padrão-molde genérico
[ ] TXT-04  nenhum texto do template padrão presente
[ ] TXT-07  testimonials vazio salvo se fornecido
[ ] TXT-05  nenhum truncamento no meio de palavra
[ ] TXT-06  nome do negócio consistente entre campos
[ ] TXT-09  CTA não genérico
[ ] IMG-02  hero não reutilizada em outra seção
[ ] IMG-04  hero ≥ 1920px e ≥ 16:9
[ ] CNF-01  WhatsApp/e-mail/mapa sintaticamente válidos
[ ] CNF-02  endereço idêntico ao input do Hunter
[ ] VIS-01  contraste AA em todos os pares da paleta
[ ] VIS-02  coerência de matiz da paleta
[ ] VIS-03  ícones sem repetição adjacente
[ ] LAY-05  ≥ 3 blocos de conteúdo real (ou marca o site como "modo compacto")
```

### Estágio 2 — Gate de render (headless, ~10s)

Roda sobre a página renderizada, em 320/375/768/1280px. Já existe browser
disponível no ambiente; não exige infra nova.

```
[ ] LAY-03  scrollWidth <= clientWidth em todos os viewports
[ ] LAY-03  nenhum item do ticker cortado nas bordas
[ ] LAY-04  ticker não repete conteúdo do hero
[ ] LAY-06  alvos de toque ≥ 44px; hero legível a 375px
[ ] LAY-01  padding coerente com o orçamento de conteúdo
[ ] LAY-02  nenhuma seção renderizada abaixo do conteúdo mínimo
[ ] LAY-07  sem duas seções consecutivas com mesmo fundo
[ ] IMG-03  contraste do texto do hero sobre a imagem real ≥ 4.5:1
[ ] IMG-05  todas as imagens carregam (HTTP 200)
[ ] VIS-04  ambas as fontes carregaram
[ ] TEC-02  zero erro de console, zero 404
[ ] TEC-01  sem Tailwind CDN
[ ] TEC-03  sem chave de API irrestrita no HTML
[ ] TEC-04  LCP < 2.5s
[ ] CNF-04  og:image resolve e tem proporção de preview correta
```

### Estágio 3 — Gate humano (1 item, ~15s)

Enquanto IMG-01 não tiver caminho automático, **um** ponto de julgamento
humano, com pergunta fechada:

```
[ ] IMG-01  "Essa imagem funcionaria como banner principal do site desse
            negócio?"  → Sim / Não, trocar
```

Um único ponto de decisão binária é operacionalmente viável no fluxo de
vendas; uma revisão visual aberta não é.

---

## 5. Ordenação por ROI de correção

ROI = (impacto percebido × frequência de ocorrência) ÷ esforço.
Ordenado do maior para o menor.

| # | Item | Impacto | Freq. | Esforço | Camada | Por que aqui |
|---|---|---|---|---|---|---|
| 1 | **TXT-01** dedupe entre seções | P0 | Alta | **E1** | agent_construtor | Comparação de strings; elimina o sinal "robô" mais visível por quase nada de esforço. |
| 2 | **TXT-04** blindagem contra texto de template | P0 | Baixa | **E1** | pipeline | Barato, e o dano quando ocorre é total. Seguro por construção. |
| 3 | **LAY-03 + LAY-04** ticker cortado e redundante | P1 | Alta | **E1** | CSS/template | Bug visual em 100% dos sites; correção isolada em um componente. |
| 4 | **IMG-02** hero não reutilizada | P0 | Média | **E1** | agent_construtor | Um `set`. |
| 5 | **TXT-02** FAQ genérico | P0 | Alta | **E2** | prompt + validador | Precisa de prompt novo *e* validador, senão o retry não converge. Alto impacto de credibilidade. |
| 6 | **CNF-01/CNF-02** contato e endereço validados | P0 | Média | **E2** | pipeline | Falha aqui é perda total da venda; validação é mecânica. |
| 7 | **CNF-04** preview de link no WhatsApp | P1 | Alta | **E1** | template | É o primeiro contato visual do lead com o demo — hoje não é verificado. |
| 8 | **VIS-01** contraste AA | P1 | Média | **E2** | paleta/CSS | Com cor derivada automaticamente do nicho, o risco é sistêmico, não pontual. |
| 9 | **IMG-01** enquadramento do hero | **P0** | Alta | **E4** | Image Engine | Maior impacto isolado do documento, mas exige mecanismo novo (pool hero separado com critérios de composição, ou análise de imagem). Fica atrás só por esforço. |
| 10 | **LAY-01/02/05** densidade adaptativa | P1 | Alta | **E3** | template/CSS | Resolve a sensação de "site vazio" de forma estrutural, mas mexe no layout inteiro — requer aprovação incremental. |
| 11 | **TXT-03** FAQ com dado concreto | P1 | Alta | **E2** | prompt | Depende de TXT-02 estar pronto; senão os dois competem no mesmo prompt. |
| 12 | **IMG-03** overlay adaptativo | P1 | Alta | **E3** | template/CSS | Melhora muito o hero, mas fica menos relevante se IMG-01 for resolvido antes. |
| 13 | **TEC-01/TEC-03** Tailwind CDN e chave exposta | P2 | 100% | **E2** | template/infra | Não bloqueia venda; é higiene técnica. |
| 14 | **TXT-05/06/08/09, VIS-02/03/04, LAY-07, IMG-04/06/07** | P2–P3 | Variada | E1 cada | diversas | Polimento; entram em lote depois dos gates estarem de pé. |

**Corte recomendado:** itens 1–7 formam um primeiro ciclo coerente (todo P0
automatizável + os dois bugs visuais confirmados), todos E1–E2, sem tocar em
estrutura de layout. Itens 9 e 10 são os dois investimentos grandes e devem ser
decididos separadamente, não empurrados junto.

---

## 6. Matriz de prioridades — impacto percebido × esforço

```
   ALTO IMPACTO
   PERCEBIDO
        ▲
        │  ┌──────────────────────────┬──────────────────────────┐
        │  │  FAZER PRIMEIRO          │  INVESTIMENTO PLANEJADO  │
        │  │  (alto impacto, E1–E2)   │  (alto impacto, E3–E4)   │
        │  │                          │                          │
        │  │  TXT-01  dedupe          │  IMG-01  enquadr. hero   │
        │  │  TXT-02  FAQ genérico    │  LAY-01/02/05 densidade  │
        │  │  TXT-04  anti-template   │  IMG-03  overlay adapt.  │
        │  │  IMG-02  hero repetida   │                          │
        │  │  LAY-03/04  ticker       │                          │
        │  │  CNF-01/02  contato      │                          │
        │  │  CNF-04  preview WhatsApp│                          │
        │  │  VIS-01  contraste       │                          │
        │  ├──────────────────────────┼──────────────────────────┤
        │  │  LOTE DE POLIMENTO       │  NÃO FAZER AGORA         │
        │  │  (baixo impacto, E1–E2)  │  (baixo impacto, E3–E4)  │
        │  │                          │                          │
        │  │  TXT-05/06/08/09         │  TEC-04  LCP             │
        │  │  VIS-02/03/04            │  (otimização de perf.    │
        │  │  LAY-07  ritmo de fundo  │   antes de existir       │
        │  │  IMG-04/06/07            │   tráfego real)          │
        │  │  TEC-01/03  higiene      │                          │
        │  └──────────────────────────┴──────────────────────────┘
        └──────────────────────────────────────────────────────► ESFORÇO
   BAIXO IMPACTO        E1 ─ E2                    E3 ─ E4
   PERCEBIDO
```

### Leitura da matriz

- **Fazer primeiro (8 itens, todos E1–E2):** cobre 100% dos P0 automatizáveis
  mais os dois defeitos visuais confirmados na auditoria. Nenhum deles toca
  estrutura de layout, então cada um pode ir isolado com checkpoint.
- **Investimento planejado (2 frentes):** IMG-01 e a densidade adaptativa são
  os dois únicos itens que exigem mecanismo/estrutura nova. São também os dois
  de maior teto de melhoria. Devem ser decididos como frentes próprias, com
  escopo negociado antes — não como continuação natural do lote anterior.
- **Polimento:** só faz sentido depois que os gates dos estágios 1 e 2
  existirem; sem gate, cada correção pontual regride na geração seguinte.
- **Não fazer agora:** performance é otimização sem sinal — não há tráfego real
  nem reclamação de lentidão. TEC-01/TEC-03 estão no lote de polimento por
  serem baratos e higiênicos, não por urgência.

---

## 7. Como este documento é usado

1. **Critério de aceite do gerador.** Qualquer evolução do motor
   (`agent_construtor.py`, Image Engine, template) só é considerada concluída
   quando não regride nenhum critério já coberto por gate.
2. **Fonte da lista de trabalho.** A seção 5 substitui o backlog visual ad-hoc.
   Itens novos entram aqui com ID, impacto, camada e validação antes de virar
   tarefa.
3. **Contrato de "pronto para vender".** O checklist da seção 4 é a resposta
   objetiva à pergunta "esse demo pode ser enviado ao lead?".

**Este documento não implementa nada.** Nenhum código, template ou config foi
alterado na sua criação.
