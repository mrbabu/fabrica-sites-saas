---
name: simular-esteira-agentes
description: Roda a simulação ponta a ponta Hunter -> Agente Construtor -> Vendedor para validar o contrato de payload (DadosLead) entre os três agentes. Use quando o usuário pedir para testar/simular o fluxo completo dos agentes especializados, ou depois de alterar o formato de DadosLead em qualquer um dos três.
---

Executa `backend/scripts/simular_esteira.py`. Hunter e Vendedor são
mockados (regex simples, sem HTTP real); o Agente Construtor é real e faz
uma chamada de IA de verdade (~1min), então este script serve tanto pra
validar o contrato de dados quanto pra fumegar o pipeline completo.

## Como rodar

```bash
python backend/scripts/simular_esteira.py
```

## Quando usar

- Depois de mudar campos em `AgenteHunter` (extração de lead via regex) ou
  em `AgenteVendedor` (`conectar_lovable`/`enviar_link_demonstracao`).
- Antes de considerar qualquer integração real de webhook (n8n) pronta —
  esse script é o jeito mais rápido de pegar um contrato quebrado sem
  precisar de infraestrutura externa.

## Limitação conhecida

Hunter e Vendedor ainda não produzem um `referencia_id` compartilhado — a
simulação não cobre o handoff pra `AgenteFinanceiro` (gap documentado no
`ROADMAP.md`, Fase 3).
