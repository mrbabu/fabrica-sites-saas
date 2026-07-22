#!/usr/bin/env python3
"""
Revalida os leads com status "pendente" salvos no Postgres (hunter_leads,
fonte de verdade desde 2026-07-22 — ver docs/hunter_online_spec.md) contra
a Google Places API antes do contato manual: confirma que o estabelecimento
ainda existe, não está fechado (businessStatus) e ainda não tem site --
segunda checagem sobre o mesmo critério de buscar_leads_google_maps.py.

Uso: python validar_leads_google_maps.py [cidade]
Sem argumento, revalida todos os pendentes de qualquer cidade.

Não altera nada no banco, só imprime um relatório OK/ATENÇÃO por lead —
mesma postura do script original (decisão fica com quem for contatar).
"""

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import SessionLocal
import repository

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


def buscar_top_resultado(nome: str, local: str, api_key: str) -> dict | None:
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
        json={"textQuery": f"{nome}, {local}", "languageCode": "pt-BR"},
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
    if SessionLocal is None:
        print("Erro: DATABASE_URL não configurada.")
        sys.exit(1)

    cidade = sys.argv[1] if len(sys.argv) > 1 else None

    db = SessionLocal()
    try:
        leads = repository.listar_leads_hunter(db, cidade=cidade, status="pendente")
    finally:
        db.close()

    if not leads:
        print("Nenhum lead pendente pra revalidar" + (f" em '{cidade}'" if cidade else "") + ".")
        return

    print(f"Revalidando {len(leads)} lead(s) pendente(s)...\n")

    ok, atencao = 0, 0
    for lead in leads:
        local = lead.bairro or lead.cidade
        try:
            top = buscar_top_resultado(lead.nome_empresa, local, api_key)
        except requests.HTTPError as e:
            print(f"[ERRO] {lead.nome_empresa} — falha na consulta ({e})")
            atencao += 1
            continue

        if top is None:
            print(f"[ATENÇÃO] {lead.nome_empresa} ({local}) — não encontrado mais no Maps")
            atencao += 1
        elif top.get("websiteUri"):
            print(f"[ATENÇÃO] {lead.nome_empresa} ({local}) — já tem site: {top['websiteUri']}")
            atencao += 1
        elif top.get("businessStatus") not in (None, "OPERATIONAL"):
            print(f"[ATENÇÃO] {lead.nome_empresa} ({local}) — status: {top.get('businessStatus')}")
            atencao += 1
        else:
            print(f"[OK] {lead.nome_empresa} ({local})")
            ok += 1

        time.sleep(0.5)

    print(f"\nResumo: {ok} OK, {atencao} para revisar antes de contatar.")
    print("Nada foi alterado no banco — atualize o status manualmente em /hunter/leads.")


if __name__ == "__main__":
    main()
