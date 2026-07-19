#!/usr/bin/env python3
"""
Utilitários de Imagem - Fábrica de Sites SaaS
Normaliza logos recebidos no onboarding (via URL) para um formato padrão,
pronto para ser injetado no site-config.json do cliente, e mapeia o nicho
(texto livre) para um banco de imagens curado por categoria (Unsplash),
usado como fallback quando o cliente não manda foto própria.
"""

import io
import json
import os
import re
import unicodedata
from pathlib import Path

import requests
from PIL import Image, UnidentifiedImageError

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    _RESAMPLE = Image.LANCZOS

# assets/logos vive na raiz do repo (é servido pelo frontend estático junto
# com o index.html), não dentro de backend/ — por isso sobe um nível a partir
# deste arquivo em vez de usar Path(__file__).parent diretamente.
PASTA_LOGOS = Path(__file__).parent.parent / "assets" / "logos"
TAMANHO_PADRAO = (512, 512)


class ErroNormalizacaoLogo(Exception):
    """Erro ao baixar ou normalizar um logo"""


class ErroBancoImagens(Exception):
    """Erro ao buscar ou cachear imagens curadas por categoria (Unsplash) —
    quem chama decide o fallback, nunca propaga pra quebrar a geração do site."""


# ============================================================================
# BANCO DE IMAGENS CURADO POR NICHO (Unsplash)
# ============================================================================
# Mapeamento determinístico de texto livre de nicho -> categoria controlada.
# Casamento por substring da lista de keywords (sem acento); primeira
# categoria com match vence. Nicho sem match cai em "small_business".
CATEGORIAS_NICHO: dict[str, list[str]] = {
    "bakery": ["padaria", "confeitaria", "doceria", "panificadora"],
    "restaurant": ["restaurante", "lanchonete", "pizzaria", "hamburgueria", "cafeteria"],
    "medical_clinic": [
        "clinica", "consultorio", "odontologia", "dentista",
        "fisioterapia", "dermatologia", "saude",
    ],
    "auto_repair": ["oficina", "mecanica", "auto center", "funilaria"],
    "hotel": ["pousada", "hotel", "hospedagem"],
    "beauty_salon": ["salao", "beleza", "estetica", "barbearia"],
    "law_office": ["advocacia", "advogado", "juridico"],
    "accounting_office": ["contabilidade", "contador"],
    "gym": ["academia", "fitness", "personal trainer", "crossfit"],
    "pet_shop": ["pet shop", "petshop", "veterinaria"],
    "construction": ["construcao", "reforma", "engenharia", "marcenaria"],
}

# Termos de busca em inglês, curados por nós (nunca o texto livre do
# cliente) — é isso que garante relevância no resultado do Unsplash.
QUERY_POR_CATEGORIA: dict[str, str] = {
    "bakery": "bakery interior, artisan bread, pastry shop storefront",
    "restaurant": "restaurant interior, chef cooking, plated food",
    "medical_clinic": (
        "modern medical office reception, dentist office interior, "
        "doctor consultation room"
    ),
    "auto_repair": "auto repair shop, mechanic garage, car workshop",
    "hotel": "hotel room interior, cozy inn, guesthouse",
    "beauty_salon": "hair salon interior, beauty spa, barbershop",
    "law_office": "law office interior, lawyer meeting room",
    "accounting_office": "accounting office interior, financial consultant meeting",
    "gym": "gym interior, fitness training, personal trainer",
    "pet_shop": "pet shop interior, veterinary clinic, dog grooming",
    "construction": "construction site, home renovation, contractor working",
    "small_business": "small business storefront, local shop interior",
}

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
QTD_IMAGENS_POR_CATEGORIA = 10

# backend/cache/ — estado gerado em runtime, não código-fonte (gitignored)
PASTA_CACHE = Path(__file__).parent / "cache"
CAMINHO_CACHE_IMAGENS = PASTA_CACHE / "imagens_categorias.json"


def _normalizar_texto(texto: str) -> str:
    """Remove acentos e pontuação, minúsculo — usado só para o casamento de categoria"""
    texto_normalizado = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", " ", texto_normalizado).strip().lower()


def mapear_categoria(nicho: str) -> str:
    """Mapeia o texto livre de nicho para uma categoria controlada de imagens."""
    texto = _normalizar_texto(nicho)
    for categoria, palavras_chave in CATEGORIAS_NICHO.items():
        if any(palavra in texto for palavra in palavras_chave):
            return categoria
    return "small_business"


def _carregar_cache_imagens() -> dict:
    if not CAMINHO_CACHE_IMAGENS.exists():
        return {}
    try:
        return json.loads(CAMINHO_CACHE_IMAGENS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _salvar_cache_imagens(cache: dict) -> None:
    PASTA_CACHE.mkdir(parents=True, exist_ok=True)
    CAMINHO_CACHE_IMAGENS.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _buscar_imagens_unsplash(query: str) -> list[str]:
    """Busca QTD_IMAGENS_POR_CATEGORIA imagens no Unsplash para a query dada.
    Levanta ErroBancoImagens se a chave não estiver configurada, a chamada
    falhar (rede/rate limit/HTTP erro) ou não vier nenhum resultado."""
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        raise ErroBancoImagens("UNSPLASH_ACCESS_KEY não configurada")

    try:
        resposta = requests.get(
            UNSPLASH_API_URL,
            params={
                "query": query,
                "per_page": QTD_IMAGENS_POR_CATEGORIA,
                "orientation": "landscape",
            },
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=10,
        )
        resposta.raise_for_status()
    except requests.RequestException as e:
        raise ErroBancoImagens(f"Falha ao consultar Unsplash para '{query}': {e}") from e

    resultados = resposta.json().get("results", [])
    urls = [
        item["urls"]["regular"]
        for item in resultados
        if item.get("urls", {}).get("regular")
    ]
    if not urls:
        raise ErroBancoImagens(f"Unsplash não retornou imagens para a query '{query}'")
    return urls


def obter_imagens_categoria(categoria: str) -> list[str]:
    """
    Retorna a lista de URLs de imagem cacheada para a categoria, buscando no
    Unsplash (e cacheando em disco, sem expiração automática) na primeira
    vez que a categoria é necessária. Chamadas seguintes pra mesma categoria
    não geram nova requisição — é isso que mantém o consumo de rate limit
    baixo (1 busca por categoria, não por site gerado).

    Raises:
        ErroBancoImagens: se não houver chave configurada ou a busca
            falhar — quem chama decide o fallback (ver agent_construtor.py).
    """
    cache = _carregar_cache_imagens()
    if cache.get(categoria):
        return cache[categoria]

    query = QUERY_POR_CATEGORIA.get(categoria, QUERY_POR_CATEGORIA["small_business"])
    urls = _buscar_imagens_unsplash(query)

    cache[categoria] = urls
    _salvar_cache_imagens(cache)
    return urls


def _slugify(texto: str) -> str:
    """Converte um nome de empresa em um slug seguro para nome de arquivo"""
    texto_normalizado = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", texto_normalizado).strip("-").lower()
    return slug or "logo"


def normalizar_logo(logo_url: str, nome_empresa: str) -> str:
    """
    Baixa o logo a partir de uma URL e normaliza para um formato padrão:
    PNG quadrado 512x512, fundo transparente, imagem centralizada preservando
    o aspect ratio original. Salva em /assets/logos/{slug-da-empresa}.png

    Args:
        logo_url: URL pública da imagem do logo
        nome_empresa: Nome da empresa, usado para nomear o arquivo salvo

    Returns:
        Caminho relativo do arquivo salvo (ex: "assets/logos/padaria-sabor.png")

    Raises:
        ErroNormalizacaoLogo: Se o download ou o processamento da imagem falhar
    """
    try:
        resposta = requests.get(logo_url, timeout=15)
        resposta.raise_for_status()
    except requests.RequestException as e:
        raise ErroNormalizacaoLogo(f"Falha ao baixar logo de {logo_url}: {e}") from e

    try:
        imagem = Image.open(io.BytesIO(resposta.content))
        imagem.load()
    except UnidentifiedImageError as e:
        raise ErroNormalizacaoLogo(f"Conteúdo em {logo_url} não é uma imagem válida") from e
    except Exception as e:
        raise ErroNormalizacaoLogo(f"Erro ao processar imagem de {logo_url}: {e}") from e

    imagem = imagem.convert("RGBA")

    # Redimensiona preservando o aspect ratio dentro do tamanho padrão
    imagem.thumbnail(TAMANHO_PADRAO, _RESAMPLE)

    # Centraliza em um canvas quadrado transparente
    canvas = Image.new("RGBA", TAMANHO_PADRAO, (0, 0, 0, 0))
    offset = (
        (TAMANHO_PADRAO[0] - imagem.width) // 2,
        (TAMANHO_PADRAO[1] - imagem.height) // 2,
    )
    canvas.paste(imagem, offset, imagem)

    PASTA_LOGOS.mkdir(parents=True, exist_ok=True)
    slug = _slugify(nome_empresa)
    caminho_arquivo = PASTA_LOGOS / f"{slug}.png"
    canvas.save(caminho_arquivo, format="PNG")

    return str(Path("assets") / "logos" / f"{slug}.png").replace("\\", "/")
