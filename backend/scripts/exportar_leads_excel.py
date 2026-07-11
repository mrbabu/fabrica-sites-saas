#!/usr/bin/env python3
"""
Exporta o CSV de leads de uma cidade para .xlsx (cabeçalho em negrito,
colunas ajustadas, primeira linha congelada) — pra abrir direto no Excel.

Uso: python exportar_leads_excel.py [cidade]
Cidades disponíveis: as mesmas de buscar_leads_google_maps.py (vitoria, paraty).
"""

import csv
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buscar_leads_google_maps import CIDADES


def exportar(csv_path: Path) -> Path:
    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"

    for r in rows:
        ws.append(r)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for i, _ in enumerate(rows[0], 1):
        largura = max(len(str(row[i - 1])) for row in rows) + 2
        ws.column_dimensions[get_column_letter(i)].width = min(largura, 60)

    ws.freeze_panes = "A2"

    xlsx_path = csv_path.with_suffix(".xlsx")
    wb.save(xlsx_path)
    return xlsx_path


def main():
    cidade = sys.argv[1] if len(sys.argv) > 1 else "vitoria"
    if cidade not in CIDADES:
        print(f"Erro: cidade '{cidade}' desconhecida. Opções: {', '.join(CIDADES)}")
        sys.exit(1)

    csv_path = CIDADES[cidade]["csv"]
    if not csv_path.exists():
        print(f"Erro: {csv_path} não existe ainda. Rode buscar_leads_google_maps.py {cidade} primeiro.")
        sys.exit(1)

    xlsx_path = exportar(csv_path)
    print(f"Exportado: {xlsx_path}")


if __name__ == "__main__":
    main()
