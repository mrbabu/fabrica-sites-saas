# 07 — Riscos

> Baseado na auditoria de 2026-07-24. Probabilidade e impacto são estimativas qualitativas (Baixo/Médio/Alto), não um cálculo formal.

## Riscos técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| CORS aberto (`allow_origins=["*"]`, `backend/app.py:89`) explorado por outro domínio | Baixa hoje (baixo tráfego) | Médio | Restringir a origens conhecidas antes de crescer volume |
| Ausência de rate limit em `/api/v1/generate-site` e nos webhooks | Baixa hoje | Médio-Alto (custo de API de IA em caso de abuso) | Adicionar rate limit básico por IP/API key |
| Sem backup documentado do Postgres de produção | Média (qualquer falha de disco/operação humana) | **Alto** — perda de todos os leads e sites gerados | Rotina de backup automatizado, mesmo que simples (dump diário) |
| Container do backend roda como root (`Dockerfile` sem `USER` não-root) | Baixa | Médio (se houver RCE, o blast radius é maior) | Adicionar usuário não-root na imagem |
| `hunter_leads.slug_demo` sem FK real pra `sites.slug` | Já acontece hoje (dado solto) | Baixo-Médio (perda de rastreabilidade, não de dado) | Adicionar FK real quando o volume justificar o refactor |
| Sessão de login interno de 15 min pode ser curta pro fluxo de geração | Média (fricção operacional) | Baixo | Ajustar duração se virar reclamação recorrente do operador |

## Riscos comerciais

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Banimento do número de WhatsApp por envio indevido | Baixa **enquanto o guardrail de nunca automatizar envio for respeitado** | **Crítico** — perde o canal de vendas inteiro | Manter a disciplina de mensagem manual até ter BSP oficial + opt-in real |
| Automatizar vendas antes do gate de 15-20 clientes | Só acontece se alguém decidir pular o guardrail | Alto (vender mal, em escala, com script não validado) | Manter o gate como decisão consciente, não just "porque dá pra automatizar" |
| Nenhum dado de quantas vendas foram fechadas até hoje | Já é realidade | Médio (decisão estratégica sem visibilidade real do funil) | Registrar manualmente até existir instrumentação |
| Processo de publicação manual do site do cliente não escala | Cresce com o volume de clientes | Médio | Revisitar quando o volume de clientes justificar (ver roadmap 90 dias) |

## Riscos financeiros

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Cobrança recorrente 100% manual | Já é realidade | Alto — vazamento de receita por esquecimento | Priorizar cobrança automatizada assim que houver volume que justifique (Asaas já recomendado) |
| Sem CAC/LTV calculado | Já é realidade | Médio — decisão de investimento em aquisição sem base de dado | Instrumentar o funil (ver KPIs) antes de qualquer decisão de investir mais em prospecção |

## Riscos operacionais

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Documentação central (`CLAUDE.md`/`ROADMAP.md`) desatualizada sobre a infraestrutura real | Já é realidade | Médio — decisão futura (humana ou de IA) baseada em informação errada | Atualizar os dois documentos pra refletir Oracle Zero Trust |
| 8 documentos obsoletos na raiz do repo, de uma versão anterior do produto | Já é realidade | Baixo-Médio — risco de alguém seguir instrução desatualizada | Arquivar/remover, não fica ambíguo pra próxima pessoa que ler |
| Nenhum monitoramento/alerta em produção (só log local em arquivo dentro do container) | Já é realidade | Médio — um problema em produção só é percebido se alguém for olhar manualmente | Considerar alerta simples (mesmo que só um healthcheck externo) quando o negócio depender mais da disponibilidade |
| Dependência de uma única pessoa saber operar o deploy (SSH manual via Tailscale) | Já é realidade | Médio (bus factor) | Documentar o processo de deploy de forma que outra pessoa consiga repetir (`infra/zero_trust_deploy.md` já existe — validar se está atualizado e completo) |
