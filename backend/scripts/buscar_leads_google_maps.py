#!/usr/bin/env python3
"""
Busca leads (estabelecimentos sem site) via Google Places API (Text Search)
e adiciona ao CSV de leads da cidade/mercado escolhido (ROADMAP.md, Fase 2:
"Geração de leads... filtrando quem não tem site").

Uso: python buscar_leads_google_maps.py [cidade]
Cidades disponíveis: vitoria (padrão, nicho Fase 0: clínicas médicas/saúde),
paraty (mercado adicional: pousadas/restaurantes/turismo/prestadores gerais).

Só popula o CSV — não envia nenhuma mensagem. O contato continua manual e
humano (guardrail #1 do ROADMAP.md: nunca outbound automatizado no WhatsApp).

Requer GOOGLE_MAPS_API_KEY no .env (Google Places API, New).
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

PASTA_RAIZ = Path(__file__).resolve().parent.parent.parent
PASTA_LEADS = PASTA_RAIZ / "leads"
CAMPOS_CSV = ["nome", "bairro", "nicho", "whatsapp", "status", "data_contato"]

# Cada cidade é um mercado próprio: CSV separado + lista de buscas (nicho+bairro).
CIDADES = {
    # Fase 0 (ROADMAP.md) e portfólio semente (gerar_portfolio_lovable.py) —
    # Clínicas Médicas/Saúde na Grande Vitória-ES.
    "vitoria": {
        "csv": PASTA_LEADS / "clinicas_grande_vitoria.csv",
        "buscas": [
            {"nicho": "Odontologia", "bairro": "Jardim da Penha, Vitória - ES"},
            {"nicho": "Fisioterapia", "bairro": "Praia do Canto, Vitória - ES"},
            {"nicho": "Odontologia", "bairro": "Centro, Vila Velha - ES"},
            {"nicho": "Fisioterapia", "bairro": "Centro, Vila Velha - ES"},
        ],
    },
    # Mercado adicional (2026-07-11): prestadores de serviço em geral,
    # perfil turístico da cidade — nicho diferente de Vitória por decisão
    # explícita do usuário, não segue o critério de baixa sazonalidade da
    # Fase 0 original.
    "paraty": {
        "csv": PASTA_LEADS / "prestadores_paraty.csv",
        "buscas": [
            {"nicho": "Pousada", "bairro": "Paraty, RJ"},
            {"nicho": "Restaurante", "bairro": "Paraty, RJ"},
            {"nicho": "Agência de Turismo", "bairro": "Paraty, RJ"},
            {"nicho": "Pedreiro", "bairro": "Paraty, RJ"},
            {"nicho": "Estacionamento", "bairro": "Paraty, RJ"},
        ],
    },
}

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


def buscar_estabelecimentos(nicho: str, bairro: str, api_key: str) -> list[dict]:
    """Text Search da Places API (New) para um nicho+bairro."""
    resp = requests.post(
        PLACES_TEXT_SEARCH_URL,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "places.displayName,places.nationalPhoneNumber,"
                "places.websiteUri,places.id,places.googleMapsUri"
            ),
        },
        json={"textQuery": f"{nicho} em {bairro}", "languageCode": "pt-BR"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("places", [])


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
            })
            existentes.add((nome, bairro))

        time.sleep(1)  # respeita rate limit da API entre buscas

    return novos_leads


def salvar_no_csv(leads: list[dict], csv_path: Path) -> None:
    if not leads:
        return
    arquivo_existe = csv_path.exists()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
        if not arquivo_existe:
            writer.writeheader()
        writer.writerows(leads)


def main():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Erro: defina GOOGLE_MAPS_API_KEY no .env (Google Places API).")
        sys.exit(1)

    cidade = sys.argv[1] if len(sys.argv) > 1 else "vitoria"
    if cidade not in CIDADES:
        print(f"Erro: cidade '{cidade}' desconhecida. Opções: {', '.join(CIDADES)}")
        sys.exit(1)

    config = CIDADES[cidade]
    leads = gerar_leads(config["buscas"], api_key, config["csv"])
    salvar_no_csv(leads, config["csv"])

    print(f"\n{len(leads)} lead(s) novo(s) adicionados a {config['csv']}")
    print("Contato continua manual — valide o WhatsApp antes de enviar qualquer mensagem.")


if __name__ == "__main__":
    main()
