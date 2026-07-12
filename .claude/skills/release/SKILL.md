---
name: release
description: Checklist objetivo de prontidão para produção (deploy, rollback, backup, monitoramento, alertas, logs, healthcheck, escalabilidade) — responde diretamente "dá pra colocar cliente real nisso agora?". Use antes de publicar uma versão nova, registrar domínio público, ou dar acesso à produção pra um cliente pagante.
---

Gate de decisão pré-produção — não é uma auditoria ampla, é uma checklist
binária/objetiva focada numa pergunta: **o sistema está pronto para
receber tráfego/dados de um cliente real agora?** Roda sob demanda
(`/release`), tipicamente antes de: publicar a primeira venda real,
registrar domínio público, ou fazer deploy de uma mudança que toca
infraestrutura/banco.

## Regras

- Somente leitura. Reporta o estado; não corrige nada sozinho.
- Cada item é ✅ (pronto) / ⚠️ (existe mas incompleto/não testado) / ❌
  (não existe). Nada de "parcial genérico" sem dizer o que falta
  especificamente.
- Terminar sempre com um veredito direto: **PODE** publicar / **PODE COM
  RESSALVAS** (lista as ressalvas) / **NÃO PODE** (lista os bloqueadores).
  Não deixar essa pergunta implícita — é o propósito do skill.

## Itens do checklist

1. **Deploy automatizado** — `deploy.sh` existe e é repetível
   (`git fetch && git reset --hard origin/main && docker compose up -d
   --build`)? Foi executado com sucesso documentado recentemente (checar
   `git log`/memória de sessão para a última execução confirmada)?
2. **Rollback** — se o deploy mais recente quebrar, existe um jeito
   definido de voltar (tag/commit anterior + reexecutar `deploy.sh`, ou
   algo mais automatizado)? Se o único plano é "dar `git reset` manual pro
   commit anterior na VM", classificar ⚠️ e dizer isso explicitamente.
3. **Backup** — rotina de backup do Postgres de produção (ver também
   `/security`, item 11). Sem isso, ❌ automático — é bloqueador.
4. **Monitoramento** — existe algo observando se `backend`/`db`/
   `cloudflare_tunnel` estão de pé (além do `healthcheck` do Docker
   Compose)? Lembrar que este projeto tem um guardrail explícito no
   `ROADMAP.md` contra adicionar Prometheus/Grafana/Zabbix prematuramente
   — reportar ❌/⚠️ sem sugerir isso como correção; a correção certa aqui
   pode ser algo mais leve (ex.: um cron simples de curl no `/health` com
   alerta via webhook).
5. **Alertas** — se algo cair, alguém é avisado, ou só se descobre quando
   um cliente reclamar? Verificar se existe qualquer integração de alerta
   (mesmo que simples).
6. **Logs centralizados** — os logs do `backend`/`cloudflare_tunnel` ficam
   só dentro do container (perdidos no rebuild) ou vão pra algum lugar
   persistente/consultável?
7. **Healthcheck** — `docker-compose.prod.yml` tem healthcheck configurado
   pro `backend` e pro `db`? `GET /health` responde o que é esperado?
8. **Escalabilidade** — não é sobre Kubernetes; é uma pergunta prática:
   quantos clientes simultâneos esse setup aguenta sem problema óbvio
   (1 instância FastAPI, 1 Postgres pequeno)? Isso é 🟡 informativo, não
   bloqueador, pra um SaaS em fase MEI/pré-15-vendas — não recomendar
   infra de escala aqui, só documentar o teto realista atual.
9. **Migrations em dia** — `alembic` está com todas as migrations
   aplicadas na revisão mais recente? (Cruzar com o que `/audit` seção 18
   já apurou, se tiver rodado recentemente, em vez de reinvestigar do
   zero.)
10. **Variáveis de ambiente de produção** — `.env` real na VM tem todas as
    chaves que `.env.example` declara como obrigatórias, sem nenhum
    placeholder tipo `"sua-chave-aqui"` sobrando? (Não imprimir os
    valores — só confirmar presença/ausência.)

## Formato de saída

```
Produção

Deploy automatizado    ✅/⚠️/❌   <detalhe>
Rollback                ✅/⚠️/❌   <detalhe>
Backup                  ✅/⚠️/❌   <detalhe>
Monitoramento           ✅/⚠️/❌   <detalhe>
Alertas                 ✅/⚠️/❌   <detalhe>
Logs centralizados      ✅/⚠️/❌   <detalhe>
Healthcheck             ✅/⚠️/❌   <detalhe>
Escalabilidade          🟡 informativo — <teto realista atual>
Migrations em dia       ✅/⚠️/❌   <detalhe>
Env vars de produção    ✅/⚠️/❌   <detalhe>

Veredito: PODE / PODE COM RESSALVAS / NÃO PODE publicar
<lista de bloqueadores ou ressalvas, se houver>
```
