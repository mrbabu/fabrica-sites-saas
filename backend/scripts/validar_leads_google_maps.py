#!/usr/bin/env python3
"""
Revalida os leads reais de um CSV de leads (ignora as linhas "Exemplo..."
pré-existentes, que são placeholders sintéticos) contra a Google Places API
antes do contato manual: confirma que o estabelecimento ainda existe, não
está fechado (businessStatus) e ainda não tem site -- segunda checagem sobre
o mesmo critério de buscar_leads_google_maps.py.

Uso: python validar_leads_google_maps.py [cidade]
Cidades disponíveis: vitoria (padrão), paraty.

Não envia nenhuma mensagem, só imprime um relatório OK/ATENÇÃO por lead.
"""

import csv
import os
import sys
import time
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PASTA_LEADS = Path(__file__).resolve().parent.parent.parent / "leads"
CSVS_POR_CIDADE = {
    "vitoria": PASTA_LEADS / "clinicas_grande_vitoria.csv",
    "paraty": PASTA_LEADS / "prestadores_paraty.csv",
}

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


def buscar_top_resultado(nome: str, bairro: str, api_key: str) -> dict | None:
    resp = requests.post(
        PLACES_TEXT_SEARCH_URL,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "places.displayName,places.websiteUri,"
                "places.businessStatus,places.formattedAddress"
            ),
        },
        json={"textQuery": f"{nome}, {bairro}", "languageCode": "pt-BR"},
        timeout=15,
    )
    resp.raise_for_status()
    resultados = resp.json().get("places", [])
    return resultados[0] if resultados else None


def main():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Erro: defina GOOGLE_MAPS_API_KEY no .env (Google Places API).")
        sys.exit(1)

    cidade = sys.argv[1] if len(sys.argv) > 1 else "vitoria"
    if cidade not in CSVS_POR_CIDADE:
        print(f"Erro: cidade '{cidade}' desconhecida. Opções: {', '.join(CSVS_POR_CIDADE)}")
        sys.exit(1)

    with CSVS_POR_CIDADE[cidade].open(encoding="utf-8", newline="") as f:
        leads = [r for r in csv.DictReader(f) if not r["nome"].startswith("Exemplo")]

    print(f"Revalidando {len(leads)} lead(s) real(is)...\n")

    ok, atencao = 0, 0
    for lead in leads:
        nome, bairro = lead["nome"], lead["bairro"]
        try:
            top = buscar_top_resultado(nome, bairro, api_key)
        except requests.HTTPError as e:
            print(f"[ERRO] {nome} — falha na consulta ({e})")
            atencao += 1
            continue

        if top is None:
            print(f"[ATENÇÃO] {nome} ({bairro}) — não encontrado mais no Maps")
            atencao += 1
        elif top.get("websiteUri"):
            print(f"[ATENÇÃO] {nome} ({bairro}) — já tem site: {top['websiteUri']}")
            atencao += 1
        elif top.get("businessStatus") not in (None, "OPERATIONAL"):
            print(f"[ATENÇÃO] {nome} ({bairro}) — status: {top.get('businessStatus')}")
            atencao += 1
        else:
            print(f"[OK] {nome} ({bairro})")
            ok += 1

        time.sleep(0.5)

    print(f"\nResumo: {ok} OK, {atencao} para revisar antes de contatar.")


if __name__ == "__main__":
    main()
