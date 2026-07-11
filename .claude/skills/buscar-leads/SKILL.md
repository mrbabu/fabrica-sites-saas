---
name: buscar-leads
description: Busca estabelecimentos sem site (leads) via Google Places API para uma cidade/mercado já configurado (vitoria ou paraty) e adiciona ao CSV de leads correspondente em leads/. Use quando o usuário pedir para captar, buscar ou gerar novos leads no Google Maps para um desses mercados.
---

Executa `backend/scripts/buscar_leads_google_maps.py`, que roda uma Text
Search da Google Places API (New) por nicho+bairro pré-configurados em
`CIDADES` (dentro do próprio script) e grava no CSV de leads da cidade,
sem duplicar entradas já existentes.

## Pré-requisito

`GOOGLE_MAPS_API_KEY` precisa estar definida no `.env` da raiz do repo
(Google Places API, New, ativada no projeto GCP). Sem isso o script falha
com uma mensagem clara — não precisa de tratamento extra.

## Como rodar

```bash
python backend/scripts/buscar_leads_google_maps.py vitoria
python backend/scripts/buscar_leads_google_maps.py paraty
```

Sem argumento, roda `vitoria` por padrão.

## Adicionar uma cidade/mercado nova

Edite o dicionário `CIDADES` em
`backend/scripts/buscar_leads_google_maps.py`, adicionando uma chave nova
com `csv` (caminho do arquivo em `leads/`) e `buscas` (lista de
`{"nicho": ..., "bairro": ...}`). Não precisa mexer no resto do script —
`validar_leads_google_maps.py` e `exportar_leads_excel.py` importam esse
mesmo dicionário.

## O que NÃO fazer

Não envia nenhuma mensagem — só popula o CSV. O contato com os leads
continua manual e humano (guardrail do `ROADMAP.md`: nunca outbound
automatizado no WhatsApp). Não expandir para Facebook/Instagram/GetNinjas
sem antes reler a análise de risco em `ROADMAP.md` (Fase 2) — essas
plataformas ficaram deliberadamente fora de escopo por risco de ToS/anti-bot
e, no caso do GetNinjas, por ser base de leads paga de um concorrente.
