# Contexto — Fábrica de Sites SaaS (situação em set/2026)

Documento preparado para avaliação externa (Gemini). Todos os números
abaixo vêm dos arquivos reais do projeto — quando não há dado confirmado,
está marcado explicitamente como estimativa ou lacuna.

## 1. O que é o produto

WaaS (Website as a Service) para MEIs e pequenos negócios locais. O dono
informa nome, nicho e cor da empresa; um motor de IA (`agent_construtor.py`)
gera um site completo (copy, cores, serviços, SEO básico) em segundos,
publicado como página estática.

**Arquitetura:**
- Motor de geração: cadeia de provedores de IA com fallback — Gemini
  (primário) → NVIDIA NIM → Groq → Anthropic (opt-in) → Ollama local.
- Frontend: HTML/Tailwind estático, hospedado na Vercel.
- Backend: FastAPI, rodando em VM própria na Oracle Cloud (tier Always
  Free — a ser confirmado: `infra/zero_trust_deploy.md` e o script de
  provisionamento divergem sobre o shape exato da VM), arquitetura Zero
  Trust (Tailscale + Cloudflare Tunnel, sem porta exposta).
- Persistência: Postgres.
- **Atualização de 23-24/09/2026 (correção de bugs, ver changelog
  completo em `docs/DOCUMENTACAO_OTIMIZACAO_INFRA.md`):** a taxa de
  sucesso real medida (`relatorio_testes.json`, 04/08) era **10%, não
  100%** — causada majoritariamente pela IA omitindo a chave `colors`
  no JSON, sem retry. Corrigido (paleta calculada por código, não mais
  pela IA). Também corrigidos: bug que zerava o custo de IA no log
  (`tokens_usados: 0` em 100% das gerações), endpoints assíncronos que
  travavam com chamadas de IA síncronas, e exposição de chave em
  demo pública. Testes unitários (178) passam. **Validação ao vivo
  ainda pendente**: nesta rodada descobrimos que o modelo padrão do
  NVIDIA NIM saiu de linha (fim de vida em 26/08) e o `gemini-2.0-flash`
  também foi descontinuado pelo Google nesse meio-tempo — trocado para
  `gemini-3.6-flash` — e o saldo pré-pago da conta Gemini usada aqui
  está zerado no momento (mesma conta Google do Antigravity). Motor
  segue com correções de código prontas, mas sem uma geração real
  ponta-a-ponta confirmada até resolver o crédito da conta.

## 2. Estado comercial atual

- **64 leads mapeados** via Google Places API (empresas sem site,
  filtradas automaticamente): clínicas da Grande Vitória-ES e prestadores
  de Paraty-RJ.
- **Zero vendas fechadas até agora.** A tabela de validação de nichos
  (`docs/nichos_validacao.md`) está com todas as colunas de resultado
  vazias.
- Preço usado como referência de teste: **R$149/mês**, ainda não validado
  como preço final (testado contra cenários de R$99 e R$199 numa
  planilha interna, R$149 foi o ponto de equilíbrio).
- Meta do roadmap: 15-20 clientes pagantes fechados **manualmente** antes
  de automatizar qualquer parte da venda (isso é um gate explícito, não
  sugestão).

## 3. Guardrails já definidos (motivo: risco real identificado antes)

1. **Proibido disparo em massa no WhatsApp.** Risco de banimento do
   número pela Meta em poucos dias. Agentes de IA só podem responder
   conversas iniciadas pelo lead (inbound), até existir um canal de
   entrada seguro (ex.: anúncio pago).
2. **Proibido automatizar vendas antes das 15-20 vendas manuais.** O
   agente de vendas precisa ser treinado com objeções e scripts reais
   coletados em campo, não hipotéticos.
3. Atenção ao teto do MEI (R$81 mil/ano) — a meta de 100 assinantes
   estoura esse teto rapidamente; migração para ME/Simples Nacional já
   está prevista.

## 4. Estrutura de custo (auditada agora, set/2026)

**Fixo mensal, independe do número de clientes até ~15-20:**
| Item | Valor | Fonte |
|---|---|---|
| Vercel Pro (hospedagem — obrigatório para uso comercial, plano Hobby não permite) | US$20/mês (~R$115) | `docs/playbook_dfy_v1.md` |
| Servidor backend (Oracle Cloud, Always Free) | R$0 | confirmado em código/infra |

**Variável por cliente:**
| Item | Valor | Fonte |
|---|---|---|
| Taxa Asaas por cobrança PIX recebida | R$1,99/mês por cliente | `docs/fluxo_financeiro_recorrencia.md` |
| Domínio `.com.br` próprio (add-on opcional, não incluso por padrão) | ~R$40/ano se contratado | `docs/playbook_dfy_v1.md` |
| Geração do site via IA (Gemini) | agora instrumentado (ver nota abaixo) — valor real ainda não coletado por falta de crédito na conta | — |

**Margem estimada com 15 clientes a R$149/mês:**
Custo fixo por cliente (R$115÷15) + taxa Asaas ≈ **R$9,66/cliente/mês**.
Contra R$149 cobrados, margem bruta estimada **acima de 90%**.

### Lacuna encontrada na auditoria — corrigida, medição ainda pendente

O roadmap lista "custo de IA por site" como métrica obrigatória de
produto. Até 22/09/2026, o sistema de logging (`metrics.log`,
`relatorio_testes.json`) registrava `tokens_usados: 0` e `custo_usd: 0`
em 100% das gerações — bug de instrumentação: `ai_provider.py` captava
o uso de tokens só para alguns provedores, e `agent_construtor.py`
nunca repassava o valor para o log. **Corrigido em 23-24/09/2026**
(todos os provedores capturam uso real, valores somados e gravados).
Como o modelo primário é o mais barato do mercado (Gemini Flash) e o
custo de hospedagem é fixo (não escala por site gerado), a expectativa
segue sendo que esse custo seja marginal (dígitos de centavos por
site) — mas a **medição real de uma geração ao vivo ainda não foi
coletada**, porque o saldo pré-pago da conta Gemini usada no projeto
está zerado no momento (ver seção 1).

## 5. Conclusão da auditoria de custo vs. preço

**O preço de R$149/mês já cobre os custos com folga muito grande.** O
problema atual não é o preço não pagar a produção — é que ainda não
existe nenhuma venda fechada. Subir o preço para "cobrir custo" não tem
justificativa nos números; o gargalo real, confirmado pelo próprio
roadmap do projeto, é comercial (prospecção → conversão), não de
margem.

## 6. Contexto de negociação em aberto (não é dado do projeto, é situação pessoal)

Há uma conversa em andamento com uma pessoa chamada Bruno, ex-gestor de
vendas da Cosan Lubrificantes, que teve uma participação na concepção
original da ideia (o grau exato de autoria ainda não foi esclarecido
entre as partes). A intenção é conversar com ele sobre estruturar a
frente comercial (funil, script, tratamento de objeção) — ele tem
experiência de gestão de vendas que falta no projeto hoje.

## 7. O que eu (Raphael) preciso que você avalie

1. Existe algo na estrutura de custo acima que muda minha decisão de
   preço, além do que já está claro (preço não é o problema agora)?
2. Como estruturar uma peça de vendas "visual e chamativa" que ajude a
   converter os 64 leads já mapeados em clientes pagantes — já existe um
   esqueleto (`vendas.html`, geração de demo via Lovable), mas nunca foi
   testado com lead real.
3. Alguma recomendação sobre como abordar a conversa comercial com o
   Bruno, dado que o produto está pronto e o gargalo é 100% de execução
   de vendas?
