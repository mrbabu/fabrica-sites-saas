#!/usr/bin/env python3
"""
Importa os CSVs legados de leads (leads/clinicas_grande_vitoria.csv,
leads/prestadores_paraty.csv) pro Postgres — passo único de migração pra
adotar o banco como fonte de verdade (decisão de produto 2026-07-22, ver
docs/hunter_online_spec.md). Depois desta importação, o CSV vira só
mecanismo de export (backend/scripts/exportar_leads_excel.py).

Ignora linhas "Exemplo..." (placeholders sintéticos, nunca foram leads
reais) e usa o mesmo dedup por (nome_empresa, cidade) do resto do sistema
— rodar de novo não duplica.

Uso: python importar_leads_csv.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import SessionLocal
import repository

PASTA_LEADS = Path(__file__).resolve().parent.parent.parent / "leads"

# (arquivo, cidade) — cidade aqui é só um rótulo pro campo `cidade` da
# tabela; o dado real de local granular já está na coluna "bairro" do CSV.
CSVS = [
    (PASTA_LEADS / "clinicas_grande_vitoria.csv", "Grande Vitória - ES"),
    (PASTA_LEADS / "prestadores_paraty.csv", "Paraty - RJ"),
]

STATUS_VALIDOS_CSV = {"pendente", "contatado", "respondeu", "demo_enviada", "cliente", "descartado", "a validar"}


def main():
    if SessionLocal is None:
        print("Erro: DATABASE_URL não configurada.")
        sys.exit(1)

    db = SessionLocal()
    total_importados = 0
    try:
        for caminho_csv, cidade in CSVS:
            if not caminho_csv.exists():
                print(f"Aviso: {caminho_csv} não existe, pulando.")
                continue

            with caminho_csv.open(encoding="utf-8", newline="") as f:
                linhas = [r for r in csv.DictReader(f) if not r["nome"].startswith("Exemplo")]

            if not linhas:
                print(f"{caminho_csv.name}: nenhum lead real pra importar.")
                continue

            busca = repository.criar_busca_hunter(
                db, nicho="importação CSV", cidade=cidade, bairro=None, raio_km=None,
                quantidade_solicitada=len(linhas), origem="csv_import",
            )

            status_csv = (linhas[0].get("status") or "pendente").strip().lower()
            status_normalizado = status_csv if status_csv in STATUS_VALIDOS_CSV and status_csv != "a validar" else "pendente"

            leads_convertidos = [
                {
                    "nome_empresa": r["nome"],
                    "nicho": r.get("nicho") or "não informado",
                    "cidade": cidade,
                    "bairro": r.get("bairro"),
                    "telefone": None if (r.get("whatsapp") or "").strip().lower() == "a validar" else r.get("whatsapp"),
                    "status": (r.get("status") or "pendente").strip().lower() if (r.get("status") or "").strip().lower() in STATUS_VALIDOS_CSV - {"a validar"} else "pendente",
                }
                for r in linhas
            ]
            salvos = repository.salvar_leads_hunter(db, busca.id, leads_convertidos, origem="csv_import")
            total_importados += len(salvos)
            print(f"{caminho_csv.name}: {len(salvos)} lead(s) novo(s) importado(s) de {len(linhas)} linha(s) real(is).")

        print(f"\nTotal: {total_importados} lead(s) importado(s) pro Postgres.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
