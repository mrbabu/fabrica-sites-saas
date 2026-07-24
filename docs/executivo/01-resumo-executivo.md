# 01 — Resumo Executivo

> Base factual: auditoria técnica completa somente-leitura do repositório inteiro, realizada em 2026-07-24 (backend/, frontend, infra/, docs/, histórico de commits). Toda afirmação abaixo tem origem rastreável em código ou documentação real — nada foi suposto. Onde a informação é interpretação/estratégia (não um fato de código), está marcado como tal.

## O que é a empresa, hoje

A **Fábrica de Sites AI** é uma operação de duas partes que já funcionam de verdade, mais uma terceira em esqueleto:

1. **Um motor de geração de sites via IA** (`backend/agent_construtor.py`) que recebe dados de um negócio e devolve um site completo (textos, estrutura, imagens, SEO) em minutos — **congelado por decisão** (estável, sem refatoração sem necessidade explícita, ver `CLAUDE.md`).
2. **Um sistema de prospecção e CRM manual** (`backend/routers/hunter.py`, "Hunter Online") que busca empresas sem site via Google Places, guarda tudo em Postgres, e dá um pipeline de status (`pendente → contatado → respondeu → demo_enviada → cliente → descartado`) pra um humano trabalhar os leads manualmente — com dois templates de mensagem prontos pra copiar/colar, nunca enviados automaticamente.
3. **Três agentes especializados** (`backend/agents/hunter.py`, `vendedor.py`, `financeiro.py`) com lógica de negócio real (scoring, conciliação de pagamento, geração de mensagem), mas com **toda integração externa mockada** — nenhum dispara WhatsApp de verdade, nenhum processa pagamento de verdade ainda.

**Estado geral, por fase do `ROADMAP.md`:**

| Fase | O que é | Estado real |
|---|---|---|
| Fase 0 — Fundação | Nicho + região definidos, portfólio semente gerado | ✅ Concluída |
| Fase 1 — MVP técnico | Motor de geração + persistência + deploy | 🟢 ~85% — falta só atualizar a documentação (o backend já está em produção, só que numa infra diferente da planejada — ver seção "Inconsistências" abaixo) e a cobrança recorrente |
| Fase 2 — Vendas manuais | Fechar 15-20 clientes usando o Hunter pra prospectar | 🟡 Em andamento — infraestrutura pronta, gargalo é comercial, não técnico |
| Fase 3 — Automação por agentes | Plugar integrações reais nos 3 agentes | 🟡 Esqueleto pronto, 0% das integrações externas reais |
| Fase 4 — Escala | Dashboard de negócio, métricas, crescimento | 🔴 Não iniciada |

## O achado mais importante desta auditoria

**A capacidade técnica está à frente da capacidade comercial.** O Hunter consegue prospectar em volume (uma busca no Google Places já traz dezenas de leads por execução, `backend/scripts/buscar_leads_google_maps.py`), o motor de geração cria uma demo em minutos, e a infraestrutura (Postgres + Docker + Zero Trust) aguenta multiplicar esse volume sem mudança de código. O que ainda não existe é o *throughput* comercial — não há, em nenhum lugar do repositório (CSV, banco, documento), um número real de vendas fechadas até hoje. O gargalo do negócio, hoje, é humano: quantas conversas de WhatsApp por dia a operação consegue sustentar, não quantos leads o sistema consegue encontrar.

## Riscos que mais merecem atenção do sócio

1. **CORS aberto (`allow_origins=["*"]`, `backend/app.py:89`)** e **ausência de rate limit** em qualquer endpoint — hoje não é um problema prático (baixo tráfego), mas é dívida que cresce em risco proporcionalmente ao sucesso comercial.
2. **Nenhum backup de banco documentado** — hoje toda a base de leads/sites vive em um único Postgres na VM Oracle, sem rotina de backup identificada no repositório.
3. **Documentação central desatualizada**: `CLAUDE.md` e `ROADMAP.md` ainda descrevem uma decisão de infraestrutura (Render/Railway) que foi substituída há tempo pela VM Oracle Zero Trust — risco de alguém (humano ou IA) tomar decisão futura baseada nessa informação errada.
4. **Guardrails comerciais críticos estão sendo respeitados hoje** (nunca WhatsApp automático, nunca depoimento fabricado, nunca venda automatizada antes do gate de 15-20 clientes) — o risco aqui não é técnico, é de disciplina: são regras que dependem de continuar sendo seguidas conforme o código evolui.

*(Detalhe completo de cada risco em [07-riscos.md](07-riscos.md).)*

## Próximos passos priorizados (visão técnica)

1. Corrigir a `DATABASE_URL` do ambiente local (aponta pra uma VM Oracle que já foi desligada, ver inconsistência #1 no relatório de auditoria).
2. Atualizar `CLAUDE.md`/`ROADMAP.md` pra refletir a infraestrutura real (Zero Trust Oracle, não Render/Railway).
3. Restringir CORS e adicionar rate limit básico nos endpoints protegidos por API key.
4. Arquivar/remover a documentação obsoleta da raiz (8 arquivos `.md` de uma versão anterior do produto, pré-reorganização em `backend/`).

*(Este é o backlog técnico. O backlog comercial — o que realmente destrava crescimento — está em [06-roadmap-executivo.md](06-roadmap-executivo.md) e nasce da constatação da seção anterior: o gargalo é vender, não construir.)*

## Modelo comercial, em uma frase

*(Esta seção é síntese estratégica, não um fato extraído de código — a origem dos dados é `vendas-config.json` para posicionamento/preço e a memória de decisões de negócio do projeto.)*

Vendemos um site profissional gerado por IA para pequenos negócios locais sem presença digital (hoje: clínicas na Grande Vitória-ES e prestadores de serviço em Paraty-RJ, `vendas-config.json.faq`), por **R$149/mês** (`vendas-config.json.pricing.base`), sem contrato de fidelidade, com domínio próprio como opcional pago à parte. O diferencial não é só "site bonito" — é que quem vende também tem a máquina de prospecção (Hunter) rodando por trás, o que uma agência ou freelancer comum não tem.

## Como este documento se conecta aos outros

| Documento | O que cobre |
|---|---|
| [02-arquitetura.md](02-arquitetura.md) | Como o sistema funciona de ponta a ponta, com diagramas |
| [03-regras-de-negocio.md](03-regras-de-negocio.md) | Toda regra de negócio implementada, com arquivo/função |
| [04-fluxos-e-modelo-comercial.md](04-fluxos-e-modelo-comercial.md) | O fluxo do lead até virar cliente, gargalos, diferenciais |
| [05-kpis.md](05-kpis.md) | Métricas que deveriam existir (hoje quase nada é medido) |
| [06-roadmap-executivo.md](06-roadmap-executivo.md) | Prioridades em 30/90/180/360 dias |
| [07-riscos.md](07-riscos.md) | Riscos técnicos, comerciais, financeiros, operacionais |
| [08-plano-melhoria-dados-e-experimentos.md](08-plano-melhoria-dados-e-experimentos.md) | O que medir, como, e experimentos concretos |
| [10-decisoes-estrategicas.md](10-decisoes-estrategicas.md) | Por que as decisões técnicas foram tomadas, e o que evitar |

A apresentação de slides para o sócio está publicada separadamente (ver mensagem de entrega).
