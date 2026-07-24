# 05 — KPIs

> Importante: nenhum dashboard de métricas de negócio existe hoje no código (confirmado na auditoria — Fase 4 do `ROADMAP.md`, "não iniciada"). O que existe é `backend/metrics.py`, que grava eventos técnicos em arquivo local (log + JSON), sem agregação nem visualização. Os KPIs abaixo são um **framework proposto**, não uma métrica já calculada em algum lugar — cada um indica de onde o dado viria, com base no que já está no banco hoje.

## Aquisição

| KPI | Como calcular | De onde vem o dado hoje |
|---|---|---|
| Leads encontrados | `COUNT(*)` em `hunter_leads` | Já existe na tabela (`backend/models_db.py::HunterLead`) |
| Leads por busca | `hunter_buscas.quantidade` vs. leads salvos de fato | Já existe (`hunter_buscas`) |
| Leads por nicho/cidade | `GROUP BY nicho, cidade` em `hunter_leads` | Já existe |

## Conversão

| KPI | Como calcular | De onde vem o dado hoje |
|---|---|---|
| Taxa de resposta | `status != 'pendente'` ÷ total | Já existe (campo `status`) |
| Taxa de demonstração | `status IN ('demo_enviada','cliente')` ÷ `status = 'respondeu'` | Já existe |
| Taxa de venda | `status = 'cliente'` ÷ total contatado | Já existe |
| Tempo médio pendente→cliente | `updated_at` só grava a última mudança, **não** um histórico — precisaria de uma tabela de histórico de status pra medir isso direito | **Não existe hoje** — `hunter_leads` só guarda o status atual, não transições anteriores |

## Operação

| KPI | Como calcular | De onde vem o dado hoje |
|---|---|---|
| Demos geradas por dia/semana | `COUNT(*)` em `sites` por `created_at`(⚠ campo a confirmar no schema real de `sites`) | Parcial — a tabela existe, mas não há confirmação de campo de data de criação lido na auditoria |
| Tempo de geração de demo | Não instrumentado | **Não existe** — precisaria logging de início/fim ao redor de `AgenteConstrutor.executar()` |

## Financeiro

| KPI | Como calcular | De onde vem o dado hoje |
|---|---|---|
| MRR (receita recorrente mensal) | `clientes ativos × R$149` (hoje sem variação de plano) | **Não existe tabela de assinatura** — `docs/fluxo_financeiro_recorrencia.md` propõe isso, zero código ainda |
| Churn | Clientes que saem ÷ total | **Não existe** — depende da tabela de assinatura acima existir primeiro |
| CAC (custo de aquisição) | Custo de operação (tempo humano + Google Places API) ÷ clientes fechados | **Não existe** — nenhum dado de custo por lead é registrado hoje |
| Ticket médio / LTV | Depende de MRR + churn existirem | **Não existe** |

## Produto

| KPI | Como calcular | De onde vem o dado hoje |
|---|---|---|
| Sites gerados com sucesso na 1ª tentativa | `MAX_TENTATIVAS_GERACAO` (`agent_construtor.py`) já registra retry — dá pra contar quantas gerações precisaram de mais de 1 tentativa | Parcial — o mecanismo de retry existe, mas não há um contador agregado persistido |
| Taxa de erro de geração | Idem acima | Parcial |

## Satisfação

| KPI | Como calcular | De onde vem o dado hoje |
|---|---|---|
| Qualquer medida de satisfação do cliente final | — | **Não existe nenhum mecanismo de coleta** — nenhuma pesquisa, nenhum campo de feedback em nenhuma tabela |

## Leitura honesta desta seção

A maior parte do funil **comercial** (aquisição → conversão) já tem o dado bruto disponível no Postgres hoje — só falta uma consulta e uma visualização, não uma mudança de arquitetura. A maior lacuna real está no lado **financeiro** (nenhuma tabela de assinatura/pagamento existe) e no **histórico de transições de status** (só o estado atual é guardado, perdendo a linha do tempo de cada lead). Ver [08-plano-melhoria-dados-e-experimentos.md](08-plano-melhoria-dados-e-experimentos.md) pra como fechar essas lacunas sem over-engineering.
