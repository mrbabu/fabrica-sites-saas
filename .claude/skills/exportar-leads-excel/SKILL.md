---
name: exportar-leads-excel
description: Converte o CSV de leads de uma cidade (vitoria ou paraty) para um .xlsx formatado (cabeçalho em negrito, colunas ajustadas, primeira linha congelada). Use quando o usuário pedir para exportar/ver os leads em Excel.
---

Executa `backend/scripts/exportar_leads_excel.py`, que lê o CSV
correspondente (mesmo dicionário `CIDADES` de `buscar_leads_google_maps.py`)
e gera um `.xlsx` no mesmo diretório (`leads/`).

## Como rodar

```bash
python backend/scripts/exportar_leads_excel.py vitoria
python backend/scripts/exportar_leads_excel.py paraty
```

Requer `openpyxl` instalado (`pip install openpyxl` se ainda não estiver no
ambiente — não é dependência do `backend/requirements.txt` porque é uma
tarefa administrativa pontual, não algo que a API em produção precisa).

## Erro comum

`PermissionError` ao salvar geralmente significa que o `.xlsx` já está
aberto no Excel — feche o arquivo e rode de novo.
