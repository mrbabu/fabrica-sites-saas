---
name: gerar-portfolio-lovable
description: Gera demos do portfólio semente (Fase 0) chamando o Agente Construtor de verdade e produzindo um prompt pronto pra colar no Lovable. Use quando o usuário pedir para gerar/regenerar as demos de portfólio ou adicionar um novo site semente ao portfólio de vendas.
---

Executa `backend/scripts/gerar_portfolio_lovable.py`, que roda
`AgenteConstrutor.gerar_config_site()` (chamada real de IA, ~30s por site) e
`AgenteVendedor.conectar_lovable()` pra cada seed em `SEEDS_PORTFOLIO`,
salvando em `lovable_prompts/<slug>.txt` (prompt) e `<slug>.json`
(site-config, pra auditoria).

## Como rodar

```bash
python backend/scripts/gerar_portfolio_lovable.py       # todas as seeds
python backend/scripts/gerar_portfolio_lovable.py 1      # só a primeira
```

## Adicionar uma seed nova

Edite a lista `SEEDS_PORTFOLIO` no topo do script. Mantenha `nicho` e
`regiao` curtos (nicho ~20 caracteres, região ~25) — combos longos estouram
o limite de 60 caracteres do `siteTitle` gerado e o agente falha mesmo com
retry (ver nota no próprio arquivo).

## O que NÃO fazer

Não editar `backend/agent_construtor.py` para "melhorar" a geração —
está congelado por decisão explícita (`CLAUDE.md`). Este script é
demo/vendas, não o pipeline de produção do cliente final.
