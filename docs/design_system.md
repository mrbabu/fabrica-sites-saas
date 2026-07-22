# Design System — Fábrica de Sites AI

Documenta como decisões explícitas o que hoje já existe implícito no código de
`vendas.html` e `index.html`, e resolve a inconsistência de paleta entre os
diferentes HTMLs do projeto. Não introduz nenhuma tecnologia nova — o projeto
continua 100% HTML + Tailwind (via CDN) + CSS/JS vanilla, sem build step, sem
framework (ver `CLAUDE.md`, seção "Arquitetura do Sistema" — deploy estático
puro na Vercel).

## Princípio orientador

A landing (`vendas.html`) deve vender a capacidade real da tecnologia, não
fingir uma maturidade comercial que ainda não existe. O alvo visual é
**startup SaaS premium em estágio inicial, mas tecnicamente séria** — não uma
empresa grande e consolidada. Prova real (screenshots, portfólio real, stack
real) substitui sinal social fabricado (depoimento, contagem de clientes,
faturamento). Ver `ROADMAP.md` (guardrails da Fase 2) e a seção "Fora de
escopo" abaixo para o que isso exclui na prática.

## Paletas de cor — duas por design, não por inconsistência

O projeto tem hoje **duas** paletas de cor intencionalmente distintas, mais
uma terceira fora de escopo:

1. **Paleta de marca** (`vendas-config.json.colors`) — usada só por
   `vendas.html`. É a identidade visual da própria "Fábrica de Sites" como
   empresa: verde-escuro `#1F5745`/`#163E31` + terracota `#C97B4A`, tom
   editorial.
2. **Paleta de cliente** (`site-config.json.colors`) — usada só por
   `index.html`, 100% dinâmica, definida por cada cliente no próprio JSON via
   `applyThemeColors()`. **Isso é o core value prop do produto e nunca deve
   ser "harmonizado" com a paleta de marca** — `CLAUDE.md` linha 13: "Toda e
   qualquer customização de cliente deve residir obrigatoriamente no arquivo
   JSON de configuração, nunca hardcoded no HTML."
3. **Paleta de ferramentas internas** (`backend/ui_common.py`, teal
   `#0D9488`/slate `#0f172a`) — existe, mas está **fora de escopo** deste
   documento: mecanismo de renderização diferente (Python f-strings, não HTML
   estático servido pela Vercel), ferramenta interna que o cliente final
   nunca vê.

## Tipografia — Fraunces e Bricolage Grotesque continuam distintas

`vendas.html` usa **Fraunces** (serif, `.font-display`) + Inter.
`index.html` usa **Bricolage Grotesque** (`.font-display`) + Inter.

**Decisão: não unificar.** `vendas.html` vende `index.html` — são duas
identidades diferentes (a agência vs. o que ela entrega ao cliente), do mesmo
jeito que uma agência de design não usa a fonte dos sites que ela entrega no
próprio site institucional. As duas páginas nunca coexistem na mesma sessão
do visitante, então não há custo de performance real em manter as duas
famílias — cada uma carrega só na sua própria página.

## Motion system

Taxonomia nomeada do que hoje já existe implícito no código:

| Nome | O que faz | Onde vive | Reduced-motion |
|---|---|---|---|
| `grain-overlay` | Textura sutil de ruído, `fixed`, `mix-blend-mode: overlay` | `assets/css/design-system.css` | Não animado, não precisa desligar |
| `reveal` / `.is-visible` | Fade + translateY ao entrar no viewport (`IntersectionObserver`) | CSS compartilhado + `initScrollReveal()` em `motion.js` | Aplica `.is-visible` direto, sem transição |
| `hero-in` / `word-reveal` | Entrada da hero no load + stagger de palavras do título | CSS compartilhado + `staggerWords()` em `motion.js` | Desliga animação, mantém opacidade 1 |
| `ticker` (`.ticker-clip`/`.ticker-wrap`/`.ticker-track`) | Faixa de texto em scroll horizontal contínuo, pausa no hover | CSS compartilhado + `renderTickerMarkup()` em `motion.js` | Desliga a animação (`.ticker-track { animation: none }`) |
| `magnetic` | CTA segue o cursor dentro de um raio, volta suave ao sair | CSS compartilhado + `initMagnetic()` em `motion.js` | Desliga o listener inteiro |
| `parallax` (`.hero-media`) | Imagem de fundo do hero translada proporcional ao scroll | CSS compartilhado + `initParallax()` em `motion.js` | Desliga o listener inteiro |
| `count-up` | Número anima de 0 até o valor real ao entrar em viewport | `initCountUp()` (generalizado) em `motion.js` | Mostra o valor final direto, sem animação |
| `whatsapp-pulse` / `wa-label-fade` | Pulso contínuo + rótulo alternante no botão flutuante | CSS compartilhado + `initWhatsAppLabel()` em `motion.js` | Desliga o pulso |

**Divergência encontrada e reconciliada:** `vendas.html` e `index.html` tinham
`@keyframes wordUp` com timing diferente (`0.6s ease` vs. `0.65s
cubic-bezier(.2,.7,.2,1)`) e o bloco `prefers-reduced-motion` de
`vendas.html` não cobria `.ticker-track`/`.magnetic` (que ela não tinha até
este redesign). **Decisão: adotar a versão de `index.html` como canônica**
para as duas páginas — é a mais recente, testada em produção (commit
`3ab4feb`, item `[~]` do `ROADMAP.md`).

## Extração compartilhada — `assets/css/design-system.css` + `assets/js/motion.js`

Ambos os arquivos são estáticos, servidos pela Vercel do mesmo jeito que
`assets/logos/*.png` hoje — sem bundler, sem build. Linkados via
`<link rel="stylesheet">` e `<script src="...">` (síncrono, sem
`defer`/`async`, carregado antes do script inline de cada página).

**Não fazem parte do compartilhado**: `<link>` de Google Fonts (ficam
page-specific, ver decisão de tipografia acima); o valor real de
`.font-display` (a *classe* existe no CSS compartilhado, mas o
`font-family` de cada página é declarado localmente, senão as duas fontes
carregariam nas duas páginas à toa); todas as funções `render*()` que
dependem do shape específico do JSON de cada página.

**Cache busting sem hash de build:** convenção manual de query string
(`design-system.css?v=1`, `motion.js?v=1`), incrementada a cada edição —
documentado no topo de cada arquivo.

## Fora de escopo desta passada

- Tabela de preços multi-tier além da estrutura Base/Opcionais/Garantia
  (decisão de precificação de negócio, não técnica).
- Depoimentos — zero clientes pagos hoje, mesmo com disclaimer de "avaliação
  de demonstração" o risco de parecer prova social fabricada é real.
- Seção "antes/depois" — não existe screenshot real de "antes" de nenhum
  lead capturado; fabricar um violaria o guardrail de anti-fabricação.
- Vídeo demonstrativo — produção de vídeo é trabalho separado, não faz parte
  de uma passada de código.
- Unificar a paleta de `backend/ui_common.py` — mecanismo de renderização
  diferente, ferramenta interna.
- "Demonstração pública sem login" — mudança de controle de acesso do
  backend, item separado do `ROADMAP.md`.
- Carrossel/portfólio com nichos fictícios — só os itens reais existentes em
  `vendas-config.json.portfolio[]` devem aparecer.

Registrado como backlog futuro (não deste redesign): vídeo demonstrativo
real, casos/depoimentos reais assim que existirem, mais demos de segmentos
conforme o portfólio real crescer.
