# Playbook DFY v1
## Fábrica de Sites IA

## 1. Objetivo
Transformar geração de sites em processo comercial repetível.

## 2. Oferta DFY

**Problema resolvido:** negócio local aparece no Google Maps mas perde
oportunidade por não ter presença digital profissional. O cliente não
compra IA — compra presença digital pronta pra gerar oportunidades.

**Entrega:** site responsivo, copy comercial, SEO básico, integração
WhatsApp, configuração visual, publicação.

**Domínio próprio (`.com.br`) é add-on opcional**, contratado à parte no
momento da adesão ao plano — não incluso por padrão na mensalidade base
(ver seção 8).

**Prazo:** alvo de 48-72h da coleta de dados até apresentação (referência
do plano de negócio original) — não é garantia contratual até validado em
campo.

**Modelo recorrente:** mensalidade recorrente.

**Hipótese de preço:** R$149/mês como referência interna de teste — não
apresentado como preço definitivo até validação comercial (ver seção 7).

### Não incluso inicialmente
Dashboard do cliente, upload self-service, gestão de conteúdo pelo
cliente, área administrativa SaaS — bloqueado até o gate da seção 8.

## 3. Estratégia de validação
Não existe nicho vencedor definido. Teste horizontal por segmentos.
Referência: `docs/nichos_validacao.md`.

## 4. Processo operacional DFY

```
Lead Google Maps
        |
        v
Análise da empresa (não tem site; site ruim; concorrentes melhores
posicionados; Google Meu Negócio sem conversão — demo só se houver
justificativa real de oportunidade)
        |
        v
Coleta de dados reais (nome, WhatsApp, localização — obrigatórios;
logo/fotos — opcional)
        |
        v
gerar_demo_dfy.py
        |
        v
Revisão humana
        |
        v
Apresentação
        |
        v
Follow-up (docs/fase2_scripts_whatsapp.md)
        |
        v
Registro dos resultados (docs/nichos_validacao.md)
```

## 5. Guardrails comerciais e técnicos

Nunca:
- inventar depoimentos;
- inventar avaliações de clientes;
- inventar telefone, WhatsApp ou e-mail;
- criar redes sociais inexistentes;
- publicar sem revisão humana.

Dados factuais do negócio devem vir do cliente ou de fontes confirmadas.

(Garantido em código por `backend/agent_construtor.py` — commit `ca96493`.)

## 6. Prospecção
Referência: `docs/fase2_scripts_whatsapp.md` — fonte oficial de abordagem,
mensagens, follow-up e regras de contato. Não duplicar aqui.

## 7. Métricas

**Métrica norte:** clientes pagantes por segmento testado. Não otimizar
só quantidade de leads, respostas ou demos — o objetivo é descobrir onde
existe disposição real de compra.

- leads encontrados = indicador operacional;
- respostas = indicador intermediário;
- demos = indicador de interesse;
- vendas pagantes = validação real.

**Comercial:** leads, contatos, respostas, reuniões, vendas.

**Produto:** tempo de geração, custo de IA, ajustes solicitados.

**Mercado:** conversão por segmento, ticket aceito, CAC — ver
`docs/nichos_validacao.md`.

## 8. Entrega final e domínio (pós-venda)

Processo ainda manual — aceitável no volume da fase de validação (15-20
vendas). Não existe automação de "cliente pagou → site publicado" hoje.

**Decisão: domínio `.com.br` próprio NÃO é fornecido por padrão no plano
base.** É um **add-on opcional**, oferecido como escolha no momento da
adesão (o cliente decide se quer pagar por isso ou não) — não faz parte
da entrega padrão da mensalidade de referência (seção 2). Sem o add-on, o
site é publicado em endereço da própria agência (esquema exato —
subdomínio por cliente, ex. `cliente.suamarca.com.br`, ou outro formato —
**ainda não definido**, ver aberto abaixo).

**Hospedagem: Vercel Pro**, não o plano Hobby/gratuito — o Hobby proíbe
uso comercial nos Termos de Serviço da Vercel, e isso deixa de ser
"projeto pessoal" assim que o cliente paga pela própria hospedagem.
Vercel Pro: US$20/mês por seat, inclui 1TB de banda + 10M requisições
edge/mês — cobre folgadamente os primeiros 15-20 clientes sem custo
adicional por domínio (sites institucionais estáticos são leves). CDN
global e SSL automático por projeto, sem taxa extra por domínio custom —
alinhado à promessa de performance do produto (ver `CLAUDE.md`). Preferido
sobre hospedagem compartilhada tradicional (ex.: Hostinger): mais rápido,
sem trabalho manual de upload por cliente, sem risco de "vizinho barulhento"
em servidor compartilhado. Essa escolha de hospedagem vale independente do
cliente contratar ou não o add-on de domínio próprio.

**Fluxo por cliente (manual por enquanto):**
1. Cliente fecha e paga (PIX manual) — nesse momento decide se quer o
   add-on de domínio `.com.br` próprio ou fica no endereço padrão da
   agência.
2. Se optou pelo add-on: registrar o domínio `.com.br` do cliente — **em
   aberto**: agência registra em nome do cliente ou o cliente registra e
   só aponta o DNS.
3. Criar um projeto Vercel próprio pro cliente (cópia do template
   `index.html` + o `site-config.json` gerado/revisado).
4. Apontar o domínio (próprio ou padrão da agência) no projeto Vercel.
5. Ativação e suporte via WhatsApp (já coberto na oferta, seção 2).

**Em aberto:**
- Preço do add-on de domínio próprio (custo do registro + margem, ou
  repasse direto).
- Esquema do endereço padrão pra quem não contrata o add-on (subdomínio da
  agência — formato exato não definido).
- Quem paga/registra o domínio quando o add-on é contratado — agência em
  nome do cliente, ou o cliente registra e só aponta o DNS.
- Se/quando vale a pena automatizar os passos 3-4 via API/CLI da Vercel
  (só depois de volume justificar — mesmo racional do gate da seção 9).

## 9. Critério para evolução SaaS

Somente após:
- 15-20 vendas DFY;
- processo repetível;
- entendimento das dores reais;
- identificação de segmento(s) vencedor(es) via `docs/nichos_validacao.md`.
