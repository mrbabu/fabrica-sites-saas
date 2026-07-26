#!/usr/bin/env python3
"""
Busca leads (estabelecimentos sem site) via Google Places API (Text Search)
e adiciona ao CSV de leads da cidade/mercado escolhido (ROADMAP.md, Fase 2:
"Geração de leads... filtrando quem não tem site").

Uso:
  python buscar_leads_google_maps.py [cidade]
  python buscar_leads_google_maps.py [cidade] --nicho "X" --bairro "Y"

Sem --nicho/--bairro, roda a lista inteira de buscas configurada pra cidade
em backend/data/buscas_leads.json. Com ambos, roda só essa busca pontual
(não precisa editar o JSON pra testar um nicho/bairro novo) — ainda salva
no CSV/Postgres da cidade informada.

Cidades disponíveis: vitoria (padrão, nicho Fase 0: clínicas médicas/saúde),
paraty (mercado adicional: pousadas/restaurantes/turismo/prestadores gerais).

Só popula o CSV — não envia nenhuma mensagem. O contato continua manual e
humano (guardrail #1 do ROADMAP.md: nunca outbound automatizado no WhatsApp).

Requer GOOGLE_MAPS_API_KEY no .env (Google Places API, New).
"""

import argparse
import csv
import json
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

PASTA_RAIZ = Path(__file__).resolve().parent.parent.parent
PASTA_LEADS = PASTA_RAIZ / "leads"
ARQUIVO_BUSCAS = PASTA_RAIZ / "backend" / "data" / "buscas_leads.json"
CAMPOS_CSV = ["nome", "bairro", "nicho", "whatsapp", "status", "data_contato"]

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = (
    "places.displayName,places.nationalPhoneNumber,places.websiteUri,"
    "places.id,places.googleMapsUri,places.businessStatus,nextPageToken"
)
MAX_PAGINAS = 3  # Places API (New) pagina até 60 resultados (3x20) por busca.
STATUS_FECHADO = {"CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"}


def carregar_cidades() -> dict:
    """Cada cidade é um mercado próprio: CSV separado + lista de buscas
    (nicho+bairro), configurados em backend/data/buscas_leads.json — editável
    sem tocar em código pra testar um bairro/nicho novo."""
    with ARQUIVO_BUSCAS.open(encoding="utf-8") as f:
        cidades = json.load(f)
    for dados in cidades.values():
        dados["csv"] = PASTA_LEADS / dados["csv"]
    return cidades


def buscar_estabelecimentos(nicho: str, bairro: str, api_key: str) -> list[dict]:
    """Text Search da Places API (New) para um nicho+bairro, paginando até
    MAX_PAGINAS (a API exige um pequeno intervalo antes do pageToken virar
    válido, daí o sleep antes de reusar)."""
    todos = []
    page_token = None
    for pagina in range(MAX_PAGINAS):
        body = {"textQuery": f"{nicho} em {bairro}", "languageCode": "pt-BR"}
        if page_token:
            body["pageToken"] = page_token

        resp = requests.post(
            PLACES_TEXT_SEARCH_URL,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": FIELD_MASK,
            },
            json=body,
            timeout=15,
        )
        resp.raise_for_status()
        dados = resp.json()
        todos.extend(dados.get("places", []))

        page_token = dados.get("nextPageToken")
        if not page_token:
            break
        time.sleep(2)  # pageToken só fica válido após um pequeno intervalo

    return todos


def carregar_slugs_existentes(csv_path: Path) -> set[tuple[str, str]]:
    """(nome, bairro) já presentes no CSV, para não duplicar entre execuções."""
    if not csv_path.exists():
        return set()
    with csv_path.open(encoding="utf-8", newline="") as f:
        return {(linha["nome"], linha["bairro"]) for linha in csv.DictReader(f)}


def gerar_leads(buscas: list[dict], api_key: str, csv_path: Path) -> list[dict]:
    existentes = carregar_slugs_existentes(csv_path)
    novos_leads = []

    for busca in buscas:
        nicho, bairro = busca["nicho"], busca["bairro"]
        print(f"Buscando '{nicho}' em '{bairro}'...")

        try:
            estabelecimentos = buscar_estabelecimentos(nicho, bairro, api_key)
        except requests.HTTPError as e:
            print(f"  ! Erro na busca ({e}), pulando.")
            continue

        for lugar in estabelecimentos:
            if lugar.get("websiteUri"):
                continue  # já tem site — fora do critério de lead
            if lugar.get("businessStatus") in STATUS_FECHADO:
                continue  # fechado (permanente ou temporário) — não vale contato

            nome = lugar.get("displayName", {}).get("text", "").strip()
            if not nome or (nome, bairro) in existentes:
                continue

            novos_leads.append({
                "nome": nome,
                "bairro": bairro,
                "nicho": nicho,
                # Places API retorna telefone comercial, não confirma WhatsApp —
                # validar manualmente antes de contatar (mesma prática já usada
                # nas linhas "Exemplo..." pré-existentes do CSV).
                "whatsapp": lugar.get("nationalPhoneNumber", "a validar"),
                "status": "pendente",
                "data_contato": "",
                "place_id": lugar.get("id"),
                "google_maps_url": lugar.get("googleMapsUri"),
            })
            existentes.add((nome, bairro))

        time.sleep(1)  # respeita rate limit da API entre buscas

    return novos_leads


def salvar_no_csv(leads: list[dict], csv_path: Path) -> None:
    """CSV agora é só export/backup — a fonte de verdade é o Postgres (ver
    persistir_no_banco). extrasaction='ignore' porque os leads carregam
    place_id/google_maps_url, que não fazem parte das colunas do CSV."""
    if not leads:
        return
    arquivo_existe = csv_path.exists()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_CSV, extrasaction="ignore")
        if not arquivo_existe:
            writer.writeheader()
        writer.writerows(leads)


def persistir_no_banco(leads: list[dict], cidade: str) -> int:
    """Persiste os leads encontrados no Postgres (hunter_leads/hunter_buscas
    — fonte de verdade, decisão de produto 2026-07-22). Se DATABASE_URL não
    estiver configurada (ex.: rodando localmente sem banco), avisa e segue
    sem quebrar o script — o CSV continua sendo escrito de qualquer jeito."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from db import SessionLocal
    import repository

    if SessionLocal is None:
        print("  ! DATABASE_URL não configurada — leads salvos só no CSV, não no banco.")
        return 0

    db = SessionLocal()
    try:
        nichos_unicos = ", ".join(sorted({l["nicho"] for l in leads})) or "vários"
        busca = repository.criar_busca_hunter(
            db, nicho=nichos_unicos, cidade=cidade, bairro=None, raio_km=None,
            quantidade_solicitada=len(leads), origem="cli_script",
        )
        leads_convertidos = [
            {
                "place_id": l.get("place_id"),
                "nome_empresa": l["nome"],
                "nicho": l["nicho"],
                "cidade": cidade,
                "bairro": l.get("bairro"),
                "telefone": None if l.get("whatsapp") == "a validar" else l.get("whatsapp"),
                "google_maps_url": l.get("google_maps_url"),
            }
            for l in leads
        ]
        salvos = repository.salvar_leads_hunter(db, busca.id, leads_convertidos, origem="cli_script")
        return len(salvos)
    finally:
        db.close()


def main():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Erro: defina GOOGLE_MAPS_API_KEY no .env (Google Places API).")
        sys.exit(1)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cidade", nargs="?", default="vitoria")
    parser.add_argument("--nicho", help="roda só essa busca pontual, junto com --bairro")
    parser.add_argument("--bairro", help="roda só essa busca pontual, junto com --nicho")
    args = parser.parse_args()

    cidades = carregar_cidades()
    if args.cidade not in cidades:
        print(f"Erro: cidade '{args.cidade}' desconhecida. Opções: {', '.join(cidades)}")
        sys.exit(1)
    if bool(args.nicho) != bool(args.bairro):
        print("Erro: --nicho e --bairro precisam ser usados juntos.")
        sys.exit(1)

    config = cidades[args.cidade]
    buscas = [{"nicho": args.nicho, "bairro": args.bairro}] if args.nicho else config["buscas"]
    leads = gerar_leads(buscas, api_key, config["csv"])
    salvar_no_csv(leads, config["csv"])

    salvos_no_banco = 0
    if leads:
        try:
            salvos_no_banco = persistir_no_banco(leads, args.cidade)
        except Exception as e:
            print(f"  ! Erro ao salvar no Postgres ({e}) — leads já estão salvos no CSV.")

    print(f"\n{len(leads)} lead(s) novo(s) adicionados a {config['csv']}")
    if leads:
        print(f"{salvos_no_banco} lead(s) salvo(s) no Postgres (fonte de verdade).")
    print("Contato continua manual — valide o WhatsApp antes de enviar qualquer mensagem.")


if __name__ == "__main__":
    main()
