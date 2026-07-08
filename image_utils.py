#!/usr/bin/env python3
"""
Utilitários de Imagem - Fábrica de Sites SaaS
Normaliza logos recebidos no onboarding (via URL) para um formato padrão,
pronto para ser injetado no site-config.json do cliente.
"""

import io
import re
import unicodedata
from pathlib import Path

import requests
from PIL import Image, UnidentifiedImageError

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    _RESAMPLE = Image.LANCZOS

PASTA_LOGOS = Path(__file__).parent / "assets" / "logos"
TAMANHO_PADRAO = (512, 512)


class ErroNormalizacaoLogo(Exception):
    """Erro ao baixar ou normalizar um logo"""


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
