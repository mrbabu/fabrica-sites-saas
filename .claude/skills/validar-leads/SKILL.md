---
name: validar-leads
description: Revalida os leads reais de uma cidade (vitoria ou paraty) contra a Google Places API antes de qualquer contato manual — confirma que o estabelecimento ainda existe, não fechou e ainda não tem site. Use antes de começar a prospecção manual de uma leva de leads recém-capturada.
---

Executa `backend/scripts/validar_leads_google_maps.py`, que lê o CSV de
leads da cidade (ignorando linhas "Exemplo..." que são placeholders
sintéticos pré-existentes), refaz uma busca por nome+bairro pra cada lead e
imprime um relatório `[OK]`/`[ATENÇÃO]` por linha.

## Como rodar

```bash
python backend/scripts/validar_leads_google_maps.py vitoria
python backend/scripts/validar_leads_google_maps.py paraty
```

## Como interpretar o relatório

- `[OK]` — estabelecimento confirmado operacional, sem site, nome ainda bate.
- `[ATENÇÃO] ... já tem site: <url>` — pode ser falso positivo: um link
  `wa.me/...` (WhatsApp) às vezes aparece como `websiteUri` na Places API
  sem ser um site de verdade. Confira a URL antes de descartar o lead.
- `[ATENÇÃO] ... não encontrado mais no Maps` ou `status: ...` diferente de
  `OPERATIONAL` — provavelmente fechou ou o cadastro sumiu, descarte.

Nomes muito genéricos no relatório (ex.: uma linha com só o nome da cidade)
geralmente indicam captura ruim na busca original — vale checar visualmente
antes de contatar, o script não pega esse tipo de caso.

## O que NÃO fazer

Não envia nenhuma mensagem, é só uma segunda checagem read-only contra a
Places API.
