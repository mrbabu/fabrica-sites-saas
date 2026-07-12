---
name: product
description: Avalia experiência do usuário e conversão — não código. Landing page, demonstração pública, fluxo "gerar antes de cadastrar", templates, portfólio/FAQ/SEO, clareza do diferencial frente a concorrentes. Use quando o usuário quiser saber se o produto converte/comunica bem, não se o código está certo.
---

Único skill de governança focado em **produto/conversão**, não em código.
Enquanto `/audit`/`/security`/`/release` perguntam "está certo tecnicamente?",
`/product` pergunta "um visitante entende a oferta e converte?".

## Escopo — decidido explicitamente em sessão (não expandir sem reconfirmar)

O `ROADMAP.md` mantém o **Guardrail #2** (não automatizar/self-service antes
de 15-20 vendas manuais fechadas). Isso define o que este skill avalia e o
que fica **fora de escopo por decisão, não por esquecimento**:

**Dentro do escopo (Fase 2 — "tudo que aumenta conversão e valida o
produto, sem automatizar a operação comercial"):**
- Landing page de alta conversão (`vendas.html`/`vendas-config.json`)
- Demonstração pública sem login (fluxo de ver um site gerado, hoje via
  preview local — ver `feedback_lovable_deprecated`/método de preview
  documentado em memória de sessão)
- Fluxo "gerar antes de cadastrar" (gerar um site de exemplo pro lead ver
  antes de qualquer compromisso)
- Templates premium (`index.html`, o template que o cliente final recebe)
- Página de planos e diferenciais, com contratação **ainda manual**
- Portfólio, FAQ e conteúdo para SEO
- Melhorias de UX da demonstração

**Fora de escopo até bater o gate de 15-20 clientes pagantes — se este
skill encontrar que algo aqui "falta", reportar como decisão de fase, não
como gap:**
- Dashboard completo do cliente
- Assinatura self-service / checkout automático
- Compra de domínio / provisionamento automático
- Qualquer automação da operação de vendas

Quando o gate for atingido e o `ROADMAP.md` for revisitado pra abrir a fase
de autoatendimento, esta lista muda — não assumir que é permanente.

## Como avaliar

Ler o que já existe (`vendas.html`, `vendas-config.json`, `index.html`,
`site-config.json` de exemplo, `docs/fase2_scripts_whatsapp.md`,
`lovable_prompts/` se ainda relevante) e responder, com evidência concreta
(não opinião solta):

1. **Landing/página de vendas** — em menos de 1 minuto de leitura, dá pra
   entender o que é o produto, pra quem é, e qual o próximo passo? O CTA
   principal é claro e único, ou compete com vários CTAs?
2. **Demonstração pública sem login** — hoje existe um jeito de um lead ver
   um site gerado sem pedir nada em troca? Qual é o atrito real desse
   caminho (quantos cliques/passos até ver o resultado)?
3. **Fluxo "gerar antes de cadastrar"** — o `POST /api/v1/generate-site`
   já permite isso tecnicamente (ver `/audit`), mas existe uma interface
   voltada pro lead usar isso diretamente, ou hoje é só uma chamada de API
   que alguém do time dispara manualmente? Reportar o estado real, não o
   que seria ideal.
4. **Templates premium** — o template único (`index.html`) sustenta a
   promessa de "site profissional" pro nicho de clínicas de alto padrão?
   (Pode invocar a skill `frontend-design` ou `ui-ux-pro-max` deste mesmo
   projeto pra uma opinião de design mais fundamentada, em vez de reinventar
   critério de design aqui.)
5. **Página de planos/diferenciais** — o preço (R$149/mês, decidido no
   `ROADMAP.md` Fase 0) e os diferenciais estão comunicados claramente em
   algum lugar visível pro lead, mesmo sendo contratação manual?
6. **Portfólio/FAQ/SEO** — os demos existentes (`lovable_prompts/`, ou
   qualquer site publicado) estão referenciados na página de vendas? A FAQ
   responde as objeções reais já documentadas em
   `docs/fase2_scripts_whatsapp.md`?
7. **Diferencial frente a concorrentes** — está explícito em algum texto
   visível (não só na cabeça do fundador) por que contratar isso em vez de
   outra agência/freelancer/Wix?

## O que NÃO fazer

- Não avaliar dashboard, assinatura self-service, checkout, domínio ou
  automação de vendas como "faltando" — são gate, não gap. Se quiser
  registrar que isso é o próximo passo depois do gate, apontar pro
  `ROADMAP.md`, não tratar como item deste relatório.
- Não editar nenhum arquivo — isso é diagnóstico. Se a saída indicar uma
  reescrita de `vendas.html`, isso vira uma tarefa de implementação
  separada, com plano próprio.
- Não confundir com `/audit` seção 6 (Frontend) — aquela seção é sobre
  responsividade/performance técnica; este skill é sobre se o conteúdo e
  o fluxo convertem.

## Formato de saída

Resumo executivo (2-3 frases: o funil converte hoje ou tem atrito
óbvio?), seguido de uma lista por item (1-7 acima) com achado + sugestão
concreta, e uma lista final "Maior alavancagem agora dentro da Fase 2" com
no máximo 3 itens.
