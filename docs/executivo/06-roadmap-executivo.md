# 06 — Roadmap Executivo

> Prioridades organizadas por horizonte de tempo. Baseado no estado real observado na auditoria (não no `ROADMAP.md` como está escrito hoje, que tem itens desatualizados — ver [10-decisoes-estrategicas.md](10-decisoes-estrategicas.md)). O critério de priorização é o mesmo já adotado no projeto: qualquer item passa pelo filtro *ajuda a vender? / ajuda a operação diária? / é só estética?* antes de entrar aqui.

## 30 dias

**Comercial**
- Focar 100% do tempo disponível em trabalhar o pipeline do Hunter que já existe — encontrar leads não é o gargalo, converter é.
- Registrar manualmente (mesmo que numa planilha simples) quantas vendas foram fechadas — hoje não há esse número em lugar nenhum do sistema, e é a métrica mais importante do negócio.

**Produto**
- Nenhuma mudança visual nova na landing — gate já registrado (só evoluir com feedback real de lead).

**Tecnologia**
- Corrigir `.env` local (`DATABASE_URL` aponta pra uma VM Oracle já desligada).
- Atualizar `CLAUDE.md`/`ROADMAP.md` pra refletir a infraestrutura Zero Trust real.
- Restringir CORS (`allow_origins=["*"]`) e adicionar rate limit básico.

**Operação**
- Nenhuma mudança de processo — o gargalo é volume de conversas humanas, não ferramenta.

**Marketing**
- Nenhum item novo — a landing v1 está no ar e o próprio processo já define que só muda de novo com sinal real de lead.

## 90 dias

**Comercial**
- Atingir o gate de 15-20 vendas fechadas manualmente (marco explícito do `ROADMAP.md` pra liberar qualquer automação de venda).

**Produto**
- Se o volume de clientes crescer, revisitar o processo manual de publicação (copiar projeto Vercel + apontar domínio) — hoje aceitável, não escala bem além de algumas dezenas de clientes.

**Tecnologia**
- Criar uma tabela de histórico de transições de status do Hunter (hoje só o estado atual é salvo) — sem isso, não dá pra medir tempo médio de conversão.
- Avaliar a primeira versão de uma tabela de assinatura (`customers`/`subscriptions`), mesmo que a cobrança em si continue manual no início.

**Operação**
- Se o volume justificar, considerar automatizar o **follow-up** (não a venda em si) do `AgenteVendedor` — ele já tem lógica pronta, só falta plugar.

**Marketing**
- Nenhum novo canal — validar o que já existe antes de multiplicar canal.

## 6 meses

**Comercial**
- Se o gate de 15-20 vendas foi atingido, avaliar ligar o `AgenteVendedor` de fato (troca de mock por chamada real), com acompanhamento humano próximo no início.

**Produto**
- Avaliar se a Biblioteca de Demos precisa do campo "status de negociação" (item já identificado numa auditoria anterior do app interno como o único achado de alto valor, ver `docs/` histórico do projeto).

**Tecnologia**
- Implementar cobrança recorrente real (Asaas é a recomendação já registrada em `docs/fluxo_financeiro_recorrencia.md`) — só depois de haver clientes suficientes pra justificar.
- Backup automatizado do Postgres de produção — hoje não existe nenhum mecanismo identificado.

**Operação**
- Se o volume de clientes exigir, revisitar o processo de publicação manual do site do cliente (ver 90 dias).

**Marketing**
- Reavaliar a landing com base em feedback real acumulado (não antes disso).

## 12 meses

**Comercial**
- Expandir nicho/região só depois de o modelo atual estar validado com receita recorrente real e sustentada.

**Produto**
- Avaliar Fase 4 (dashboard de negócio) — só faz sentido quando já existir volume de dado real o suficiente pra um dashboard ter algo a mostrar.

**Tecnologia**
- Reavaliar se algum dos três agentes especializados precisa de uma camada de configuração compartilhada — usando a regra já estabelecida no projeto (1 consumidor mantém local, 2 considera extrair, 3+ extrai).

**Operação**
- Se o volume de clientes justificar, considerar automação real da conciliação financeira (`AgenteFinanceiro` já tem a lógica pronta).

**Marketing**
- Considerar expansão de canal só com dado de CAC/LTV real em mãos — nenhum dos dois existe hoje (ver [05-kpis.md](05-kpis.md)).

---

**Princípio que atravessa todos os horizontes:** nenhum item aqui propõe nova arquitetura antes da hora. Cada item de 90+/6/12 meses só avança se o horizonte anterior comprovar que o volume real do negócio justifica — a mesma disciplina que já evitou construir um "Business Rules Engine" prematuro nesta mesma semana (ver [10-decisoes-estrategicas.md](10-decisoes-estrategicas.md)).
