# Manual do Operador de Vendas — Fábrica de Sites AI

> **Versão:** 2.0 | **Última atualização:** Julho 2026
> **Status:** Baseado 100% no código implementado no repositório

---

## Sumário

1. [O Que Vendemos](#1-o-que-vendemos)
2. [Por Que o Cliente Compra](#2-por-que-o-cliente-compra)
3. [Seu Fluxo de Trabalho](#3-seu-fluxo-de-trabalho)
4. [Ferramentas Disponíveis Hoje](#4-ferramentas-disponíveis-hoje)
5. [Passo a Passo: Prospecção de Leads](#5-passo-a-passo-prospecção-de-leads)
6. [Passo a Passo: Validação de Leads](#6-passo-a-passo-validação-de-leads)
7. [Passo a Passo: Geração de Demo (Nosso Gerador)](#7-passo-a-passo-geração-de-demo-nosso-gerador)
8. [Passo a Passo: Usar o Lovable](#8-passo-a-passo-usar-o-lovable)
9. [Comparação: Nosso Gerador vs Lovable](#9-comparação-nosso-gerador-vs-lovable)
10. [Passo a Passo: Follow-Up](#10-passo-a-passo-follow-up)
11. [Interface Web: Passo a Passo Completo](#11-interface-web-passo-a-passo-completo)
12. [Regras de Ouro (Guardrails)](#12-regras-de-ouro-guardrails)
13. [Dicas de Abordagem e Mensagens](#13-dicas-de-abordagem-e-mensagens)
14. [Funcionalidades Disponíveis Hoje vs Planejadas](#14-funcionalidades-disponíveis-hoje-vs-planejadas)

---

## 1. O Que Vendemos

A **Fábrica de Sites AI** cria sites profissionais automaticamente para negócios locais. Em menos de 30 segundos, um site completo é gerado com:

- Textos persuasivos adaptados ao nicho do negócio
- SEO otimizado para buscas no Google (aparece quando alguém pesquisa "dentista em [cidade]")
- Botão de WhatsApp flutuante para o cliente receber contatos direto no site
- Design responsivo (funciona perfeitamente no celular e no computador)
- Cores e identidade visual personalizadas

**Exemplo real de sites gerados:**
- [Alumi Odontologia Integrada](https://alumi-sparkle-site.lovable.app) — Odontologia em Vitória
- [Studio Vertice Fisioterapia](https://studio-vertice-flow.lovable.app) — Fisioterapia em Vitória

---

## 2. Por Que o Cliente Compra

Negócios locais (dentistas, fisioterapeutas, pousadas, restaurantes) **não têm site próprio**. Quando alguém pesquisa no Google, o negócio não aparece — o cliente perde dinheiro todos os dias.

**O que oferecemos:**
- Site profissional que aparece no Google
- WhatsApp integrado para receber contatos
- Entrega em minutos, não semanas
- Preço acessível: **R$ 149/mês** (consulte `vendas-config.json` para valores atualizados)

**O que NÃO vendemos:**
- Sites que ficam guardados no computador (funciona no celular e no Google)
- Templates genéricos (cada site é personalizado com IA)
- Solução cara e demorada (não somos agência tradicional)

---

## 3. Seu Fluxo de Trabalho

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  1. PROSPECTAR  │ →  │  2. VALIDAR      │ →  │  3. GERAR DEMO      │
│  (buscar leads  │    │  (confirmar se   │    │  (criar site-demo   │
│   sem site)     │    │   ainda existe)  │    │   personalizado)    │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         ↓                                            ↓
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  4. CONTATAR    │ →  │  5. MOSTRAR DEMO │ →  │  6. FECHAR VENDA    │
│  (WhatsApp      │    │  (comparar       │    │  (PIX + deploy      │
│   manual)       │    │   resultados)    │    │   definitivo)       │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

---

## 4. Ferramentas Disponíveis Hoje

### Interface Web (navegador) — Forma recomendada

| Rota | O que faz | Requer login |
|------|-----------|--------------|
| `/demo/login` | Tela de acesso | Não (é o próprio login) |
| `/hunter` | Buscar leads via Google Places | Sim |
| `/hunter/leads` | Pipeline de leads com filtros e status | Sim |
| `/hunter/leads/{id}/status` | Atualizar status de um lead | Sim |
| `/hunter/leads/{id}/vincular-demo` | Vincular demo gerada a um lead | Sim |
| `/hunter/exportar` | Exportar leads filtrados para Excel (.xlsx) | Sim |
| `/demo` | Formulário para gerar demo DFY | Sim |
| `/demo/preview/{slug}` | Preview renderizado do site gerado | Sim |
| `/demo/lista` | Lista de todas as demos geradas | Sim |

### Scripts (terminal) — Para quem prefere linha de comando

| Script | Caminho | O que faz | Precisa de .env |
|--------|---------|-----------|-----------------|
| `buscar_leads_google_maps.py` | `backend/scripts/` | Busca leads via Google Places API | `GOOGLE_MAPS_API_KEY` |
| `validar_leads_google_maps.py` | `backend/scripts/` | Revalida leads pendentes contra o Google Maps | `GOOGLE_MAPS_API_KEY` + `DATABASE_URL` |
| `checklist_followup.py` | `backend/scripts/` | Lista leads que precisam de contato hoje | Não |
| `gerar_demo_dfy.py` | `backend/scripts/` | Gera um site-demo personalizado via IA | `ANTHROPIC_API_KEY` (ou Ollama) |
| `exportar_leads_excel.py` | `backend/scripts/` | Exporta leads do Postgres para .xlsx | `DATABASE_URL` |

### Ferramentas complementares

| Ferramenta | Caminho | O que faz |
|------------|---------|-----------|
| `prompt_builder.py` | `backend/` | Extrai do site-config um prompt para Lovable |
| `lovable_adapter.py` | `backend/` | Monta URL do Lovable com prompt + imagens |
| `gerar_portfolio_lovable.py` | `backend/scripts/` | Gera portfolio seed de 3 demos para Lovable |

---

## 5. Passo a Passo: Prospecção de Leads

### Via interface web (recomendado)

1. Acesse `https://seudominio.com/demo/login` e faça login
2. Navegue até `https://seudominio.com/hunter`
3. Preencha o formulário:
   - **Nicho:** selecione o segmento (ex: Odontologia)
   - **Local:** digite a cidade ou bairro (ex: Vitória)
   - **Quantidade:** quantos leads buscar (1-20, padrão 20)
4. Clique em **"Buscar oportunidades"**
5. Aguarde ~5 segundos — os leads aparecerão na tela
6. Clique em **"Copiar mensagem"** ao lado de cada lead para copiar o texto de abordagem

### Via terminal

```bash
# Buscar todos os nichos configurados para Vitória
python backend/scripts/buscar_leads_google_maps.py vitoria

# Buscar todos os nichos configurados para Paraty
python backend/scripts/buscar_leads_google_maps.py paraty

# Buscar um nicho específico em um bairro específico
python backend/scripts/buscar_leads_google_maps.py vitoria --nicho "Odontologia" --bairro "Jardim da Penha, Vitória - ES"
```

### Cidades e nichos configurados

O arquivo `backend/data/buscas_leads.json` define as combinações disponíveis:

**Vitória (ES):**
| Nicho | Bairros |
|-------|---------|
| Odontologia | Jardim da Penha, Praia do Canto, Centro/Vila Velha |
| Fisioterapia | Jardim da Penha, Praia do Canto, Centro/Vila Velha |

**Paraty (RJ):**
| Nicho | Local |
|-------|-------|
| Pousada | Paraty |
| Restaurante | Paraty |
| Agência de Turismo | Paraty |
| Pedreiro | Paraty |
| Estacionamento | Paraty |

### O que o sistema faz automaticamente

1. Consulta o Google Places API pela combinação nicho + localização
2. **Remove** negócios que já têm website próprio
3. **Remove** negócios que estão marcados como fechados
4. Salva os leads válidos no Postgres (fonte de verdade) e no CSV correspondente
5. Retorna o resultado na tela

### Limites técnicos

- Máximo de **60 resultados** por busca (3 páginas de 20)
- Rate limiting automático (1-2 segundos entre chamadas)
- Dados vêm apenas do Google Places (Instagram/Facebook não são coletados)

---

## 6. Passo a Passo: Validação de Leads

### Por que validar

O Google Maps pode mostrar negócios que:
- Fecharam mas ainda aparecem no mapa
- Criaram site depois que capturamos o lead
- Mudaram de telefone

**Validar evita tempo perdido entrando em contato com leads frios.**

### Via terminal

```bash
# Validar leads pendentes de Vitória
python backend/scripts/validar_leads_google_maps.py vitoria

# Validar leads pendentes de Paraty
python backend/scripts/validar_leads_google_maps.py paraty
```

### O que aparece no relatório

O script imprime para cada lead:
- `[OK]` — negócio ativo, sem site, pronto para contato
- `[ATENÇÃO]` — empresa não encontrada, já tem site, ou está fechada

### Status que gera ALERTA (não contate)

| Status no relatório | Significado |
|---------------------|-------------|
| Não encontrado | O negócio sumiu do Google Maps |
| Já tem site | O negócio criou um site depois que capturamos |
| Fechado | O negócio está marcado como fechado |

**Este script é apenas leitura — não altera nenhum dado no banco.**

---

## 7. Passo a Passo: Geração de Demo (Nosso Gerador)

### Quando gerar uma demo

- Quando o lead **demonstra interesse** no serviço
- Quando você quer **mostrar na prática** como o site ficaria
- Para comparar com o resultado do Lovable (veja seção 9)

### Via interface web

1. Acesse `https://seudominio.com/demo`
2. Preencha o formulário:
   - **Nome da empresa:** nome completo do negócio
   - **Tipo de negócio:** nicho/segmento
   - **Cidade:** localização
   - **WhatsApp:** telefone com código do país
   - **Cor:** escolha uma cor (opcional — padrão é verde-água `#0D9488`)
   - **Descrição do negócio:** informações extras (opcional)
   - **Fotos de portfolio:** URLs de imagens do cliente (opcional)
3. Clique em **"Gerar site"**
4. Aguarde ~30 segundos
5. O preview do site gerado aparece automaticamente em `/demo/preview/{slug}`

### Via terminal

```bash
python backend/scripts/gerar_demo_dfy.py \
  --nome "Clínica Sorriso" \
  --nicho "Odontologia" \
  --cor "#0D9488" \
  --localizacao "Jardim da Penha, Vitória - ES" \
  --whatsapp "+5527997772633"
```

**Parâmetros:**

| Parâmetro | Obrigatório | Descrição | Exemplo |
|-----------|-------------|-----------|---------|
| `--nome` | Sim | Nome completo do negócio | `"Clínica Sorriso"` |
| `--nicho` | Sim | Segmento do negócio | `"Odontologia"` |
| `--localizacao` | Sim | Bairro + Cidade + Estado | `"Jardim da Penha, Vitória - ES"` |
| `--whatsapp` | Sim | Telefone com código do país | `"+5527999998888"` |
| `--cor` | Não | Cor principal em hex (padrão: `#6366f1`) | `"#0D9488"` |
| `--saida` | Não | Caminho do arquivo JSON de saída | `"configs/meu-site.json"` |

### O que acontece quando você gera

1. A IA recebe os dados do negócio
2. Gera textos persuasivos para cada seção (hero, serviços, diferenciais, FAQ)
3. Cria uma paleta de cores harmoniosa baseada na cor escolhida
4. Otimiza tudo para SEO local (palavra-chave + cidade)
5. Salva o arquivo JSON em `configs/` no Postgres
6. O preview fica disponível em `/demo/preview/{slug}`

### Escolha de cores por nicho

| Nicho | Cor sugerida | Código |
|-------|--------------|--------|
| Odontologia | Verde-água | `#0D9488` |
| Fisioterapia | Azul | `#2563EB` |
| advocacia | Azul marinho | `#1E3A5F` |
| Restaurante | Vermelho | `#DC2626` |
| Pousada/Hotel | Verde escuro | `#1F5745` |
| Padaria | Laranja | `#EA580C` |
| Salão de beleza | Rosa | `#EC4899` |
| Academia | Vermelho escuro | `#991B1B` |
| Pet shop | Verde lima | `#65A30D` |

---

## 8. Passo a Passo: Usar o Lovable

### O que é o Lovable

O Lovable é uma ferramenta externa que gera sites a partir de prompts de texto. Nós usamos como **comparação visual** — para o operador entender qual resultado é melhor.

### Como gerar um prompt para o Lovable

1. Gere a demo com nosso gerador (veja seção 7)
2. O sistema automaticamente extrai o conteúdo textual do site-config.json
3. O prompt ficará pronto para você copiar

### Via script

```bash
# Gerar portfolio seed (3 demos prontas para Lovable)
python backend/scripts/gerar_portfolio_lovable.py
```

Os prompts são salvos em `lovable_prompts/<slug>.txt` — prontos para colar no chat do Lovable.

### Como usar no Lovable

1. Acesse [lovable.dev](https://lovable.dev)
2. Crie uma conta (gratuita)
3. Cole o prompt no chat
4. O Lovable gera um site com suas próprias imagens
5. Compare com o resultado do nosso gerador

### Importante

- O Lovable **não usa nossas imagens** — ele escolhe as imagens dele
- Cada usuário gera o projeto **na sua própria conta** do Lovable
- O resultado do Lovable serve como **benchmark visual** — para comparar qual fica melhor

---

## 9. Comparação: Nosso Gerador vs Lovable

| Aspecto | Nosso Gerador | Lovable |
|---------|---------------|---------|
| **Imagens** | Usa nosso Image Engine (imagens curadas por nicho) | Lovable escolhe imagens genéricas |
| **Texto** | IA gera textos persuasivos adaptados ao nicho | Prompt define o texto |
| **SEO** | Otimizado para buscas locais (palavra-chave + cidade) | Depende do prompt |
| **WhatsApp** | Botão flutuante configurado automaticamente | Precisa configurar manualmente |
| **Velocidade** | ~30 segundos | ~1-2 minutos |
| **Custo** | R$ 149/mês (plano do cliente) | Gratuito (limitado) ou pago |
| **Deploy** | Precisa de deploy manual (Vercel) | Hospedado no Lovable |
| **Controle** | Total (podemos editar o JSON) | Limitado (template do Lovable) |

### Quando usar cada um

- **Use nosso gerador** quando quiser o resultado final para o cliente
- **Use o Lovable** para comparar visualmente e mostrar ao lead que temos opção melhor

---

## 10. Passo a Passo: Follow-Up

### Checklist de follow-up

**Via terminal:**

```bash
python backend/scripts/checklist_followup.py
```

Este script lê os CSVs de leads e mostra:
- **Leads nunca contatados** — precisam do primeiro contato
- **Leads sem resposta há mais de 48h** — precisam de follow-up

Para cada lead, o script mostra um **gancho de mensagem sugerido** — adapte antes de enviar.

### Como usar o checklist

1. Rode o comando toda **manhã**
2. Comece pelos **NUNCA CONTATADOS** (são prioridade)
3. Depois atenda os **SEM RESPOSTA HÁ MAIS DE 48H**
4. Copie o gancho sugerido e **personalize** para sua voz
5. **Nunca envie mensagem idêntica** — personalização aumenta resposta

### Via interface web

1. Acesse `/hunter/leads`
2. Filtre por status **"pendente"** para ver quem nunca foi contatado
3. Filtre por status **"contatado"** para ver quem precisa de follow-up
4. Clique em **"1o contato"** ou **"Oferta"** para copiar a mensagem sugerida

---

## 11. Interface Web: Passo a Passo Completo

### Acesso

1. Acesse `https://seudominio.com/demo/login`
2. Digite seu usuário e senha
3. Clique em **Entrar**

A sessão dura **15 minutos** — após isso, é necessário fazer login novamente.

### Fluxo completo no navegador

#### Passo 1: Buscar leads
1. Navegue para `/hunter`
2. Preencha: Nicho + Local + Quantidade
3. Clique em **"Buscar oportunidades"**
4. Os leads aparecem com telefone, endereço e botão "Copiar mensagem"

#### Passo 2: Gerenciar pipeline
1. Navegue para `/hunter/leads`
2. Veja todos os leads com filtros (nicho, cidade, status, busca textual)
3. Para cada lead:
   - Clique em **"1o contato"** para copiar mensagem de abordagem
   - Clique em **"Oferta"** para copiar mensagem com preço (só aparece após status "respondeu")
   - Atualize o status usando o seletor (pendente → contatado → respondeu → demo_enviada → cliente)
   - Clique em **"gerar demo"** para ir direto ao formulário com dados preenchidos

#### Passo 3: Gerar demo
1. Navegue para `/demo` (ou clique "gerar demo" no pipeline)
2. O formulário já vem preenchido com dados do lead
3. Complete com WhatsApp e cor preferida
4. Clique em **"Gerar site"**
5. Aguarde ~30 segundos
6. O preview aparece em `/demo/preview/{slug}`

#### Passo 4: Ver demos geradas
1. Navegue para `/demo/lista`
2. Veja tabela com todas as demos: empresa, nicho, data, links
3. Clique em **"ver site"** para abrir o preview
4. Clique em **"ver no Lovable"** para comparar (se disponível)

#### Passo 5: Exportar leads
1. Navegue para `/hunter/leads`
2. Aplique os filtros desejados
3. Clique em **"Exportar XLS"**
4. O arquivo `.xlsx` é baixado automaticamente

### Status dos leads

| Status | Significado | Próxima ação |
|--------|-------------|--------------|
| `pendente` | Lead novo, ainda não contatado | Enviar 1º contato |
| `contatado` | Mensagem enviada, aguardando resposta | Aguardar 48h, fazer follow-up |
| `respondeu` | Lead respondeu positivamente | Gerar e enviar demo |
| `demo_enviada` | Demo enviada, aguardando decisão | Follow-up em 48h |
| `cliente` | Fechou contrato! | Deploy do site definitivo |
| `descartado` | Lead não é viável | Nenhuma ação |

---

## 12. Regras de Ouro (Guardrails)

Estas regras **NÃO podem ser quebradas**:

### ❌ NUNCA faça isso

| Regra | Por quê |
|-------|---------|
| **Não envie WhatsApp em massa** | Todo contato é manual e humano. A IA só responde conversas INICIADAS pelo lead |
| **Não automatize vendas antes de 15-20 assinaturas** | Precisamos de validação manual primeiro |
| **Não invente dados** | Nada de depoimentos, telefones, endereços ou redes sociais fictícios |
| **Não publique site sem revisão humana** | Sempre confira antes de entregar ao cliente |
| **Não use WhatsApp comercial do Google Maps como confirmado** | O telefone pode não ter WhatsApp |

### ✅ SEMPRE faça isso

| Regra | Por quê |
|-------|---------|
| **Valide leads antes de contatar** | Evita tempo perdido com negócios fechados |
| **Personalize cada mensagem** | Mensagens genéricas têm taxa de resposta baixa |
| **Acompanhe o funil** | Atualize o status de cada lead após contato |
| **Use o checklist de follow-up** | Leads esquecidos = vendas perdidas |
| **Confirme dados com o cliente** | Antes de gerar demo, peça confirmação de nome, telefone e nicho |

### ⚠️ Atenção financeira

- **Teto do MEI:** R$ 81.000/ano — se faturar mais, migre para ME ou Simples Nacional
- **Preço base:** R$ 149/mês (consulte `vendas-config.json` para valores atualizados)
- **Forma de pagamento:** PIX

---

## 13. Dicas de Abordagem e Mensagens

### Template de primeiro contato (WhatsApp)

> "Oi! Vi a **[Nome do Negócio]** aqui em **[Bairro]** — reparei que vocês não têm site ainda. A gente cria sites profissionais para negócios locais em menos de 30 segundos, com WhatsApp integrado e otimizado para aparecer no Google. Posso te mostrar como ficaria o site da sua empresa?"

### Template de follow-up (após 48h sem resposta)

> "Oi! Só um retorno rápido sobre a **[Nome do Negócio]** — sei que a rotina é corrida. Caso queira ver uma demo gratuita do site, é só me responder aqui. Sem compromisso!"

### Regras de ouro na abordagem

1. **Comece com empatia** — Mostre que você conhece o negócio
2. **Seja específico** — Mencione o bairro/nicho, não seja genérico
3. **Proponha valor** — "Site em 30 segundos" é mais forte que "a gente faz sites"
4. **Não venda ainda** — O primeiro contato é para agendar uma conversa/demo
5. **Respeite o não** — Se o lead não quiser, agradeça e siga em frente

---

## 14. Funcionalidades Disponíveis Hoje vs Planejadas

### ✅ Implementadas e funcionais

| Funcionalidade | Status | Como acessar |
|----------------|--------|--------------|
| Busca de leads via Google Places | ✅ Funcional | `/hunter` ou `buscar_leads_google_maps.py` |
| Validação de leads | ✅ Funcional | `validar_leads_google_maps.py` |
| Pipeline de leads com status | ✅ Funcional | `/hunter/leads` |
| Geração de demo DFY (IA) | ✅ Funcional | `/demo` ou `gerar_demo_dfy.py` |
| Preview de sites gerados | ✅ Funcional | `/demo/preview/{slug}` |
| Lista de demos geradas | ✅ Funcional | `/demo/lista` |
| Exportação para Excel | ✅ Funcional | `/hunter/exportar` ou `exportar_leads_excel.py` |
| Checklist de follow-up | ✅ Funcional | `checklist_followup.py` |
| Geração de prompts para Lovable | ✅ Funcional | `prompt_builder.py` + `lovable_adapter.py` |
| Login com sessão | ✅ Funcional | `/demo/login` |
| WhatsApp webhook (recebe, não responde) | ✅ Funcional | `/api/v1/whatsapp/webhook` |
| Template de site responsivo | ✅ Funcional | `index.html` |

### 🔨 Planejadas / Em construção

| Funcionalidade | Status | Observação |
|----------------|--------|------------|
| Envio automático de WhatsApp | ❌ Não implementado | Guardrail: só responde conversas iniciadas pelo lead |
| Integração HTTP com Lovable | ❌ Não implementado | O Lovable não tem API pública — fluxo é manual (copiar/colar prompt) |
| Conciliação de pagamentos PIX | ⚠️ Esqueleto | `financeiro.py` existe mas não está conectado a gateway real |
| Agente Hunter via webhook WhatsApp | ⚠️ Esqueleto | `hunter.py` existe mas não está integrado ao webhook real |
| Envio de link de demo via WhatsApp | ⚠️ Esqueleto | `vendedor.py` monta payload mas não envia HTTP |

---

*Manual baseado no código-fonte do repositório. Última auditoria: Julho 2026.*
*Dúvidas? Fale com o time técnico.*
