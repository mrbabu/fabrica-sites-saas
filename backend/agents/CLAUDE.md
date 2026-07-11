# Agentes Especializados

Em construção — esqueleto inicial com classes e interfaces, ainda sem
lógica de negócio:
1. **`hunter.py`** — captura e limpeza de leads recebidos via WhatsApp.
2. **`vendedor.py`** — conecta com o Lovable e envia o link de demonstração ao lead.
3. **`financeiro.py`** — monitoramento e conciliação de pagamentos via PIX.

Esses agentes devem se comunicar via o mesmo contrato JSON (`site-config.json` /
payload de lead), seguindo o princípio de "JSON Schema Driven" já usado pelo Agente
Construtor (ver `ROADMAP.md`, Fase 3 — Automação por Agentes de IA).

**Antes de mexer em qualquer um desses três agentes, ler os guardrails no topo do
`ROADMAP.md`** — em especial: `vendedor.py` só pode responder conversas iniciadas
pelo lead (nunca disparar outbound frio, sob risco de banimento do WhatsApp), e a
automação de vendas em si não deve substituir o processo manual antes de 15-20
vendas fechadas (Fase 2 do plano de negócio).
