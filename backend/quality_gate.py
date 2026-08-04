#!/usr/bin/env python3
"""
Quality Gate -- Definition of Professional Site (DoPS)
docs/definition-of-professional-site.md + docs/roadmap-implementacao-dops.md

MODO RELATÓRIO (Lote 1.C, Fase 0/1 do roadmap): lê um site-config.json já
gerado e reporta quais critérios AUTO passam ou falham. Não bloqueia, não
corrige, não altera o config recebido (R1 -- só observa). Ainda não é
chamado de dentro do pipeline de geração (agent_construtor.py) -- ligar
isso como gate bloqueante é Fase 3 do roadmap, e exige primeiro medir a
taxa de reprovação do corpus (Fase 0).

Critérios cobertos aqui: CNF-01, CNF-02, IMG-04, IMG-05.
"""

import re
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import urlparse

import requests


@dataclass
class ResultadoCriterio:
    """Resultado da checagem de um único critério da DoPS."""
    id: str
    passou: bool
    detalhe: str = ""


_REGEX_E164 = re.compile(r"\+?[1-9]\d{7,14}")
_REGEX_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _whatsapp_e164_valido(numero: Optional[str]) -> bool:
    if not numero:
        return False
    limpo = re.sub(r"[\s\-()]", "", numero)
    return bool(_REGEX_E164.fullmatch(limpo))


def _email_valido(email: Optional[str]) -> bool:
    # Campo opcional e nunca fabricado pela IA (ver _preencher_fallbacks em
    # agent_construtor.py) -- None é o estado esperado e válido.
    if email is None:
        return True
    return bool(_REGEX_EMAIL.fullmatch(email))


def validar_cnf01_contato(config: dict) -> ResultadoCriterio:
    """CNF-01: WhatsApp em E.164 válido, e-mail sintaticamente válido (ou ausente)."""
    contact = config.get("contact") or {}
    whatsapp = contact.get("whatsapp")
    email = contact.get("email")

    if not _whatsapp_e164_valido(whatsapp):
        return ResultadoCriterio("CNF-01", False, f"whatsapp inválido: {whatsapp!r}")
    if not _email_valido(email):
        return ResultadoCriterio("CNF-01", False, f"email inválido: {email!r}")
    return ResultadoCriterio("CNF-01", True)


def validar_cnf02_endereco(
    config: dict,
    localizacao_esperada: Optional[str],
    google_maps_url_esperado: Optional[str],
) -> ResultadoCriterio:
    """
    CNF-02: endereço/link de mapa idênticos ao capturado pelo Hunter (o
    parâmetro `localizacao`/`google_maps_url` original passado a
    gerar_config_site) -- nenhum dos dois pode ter sido reescrito ou
    completado pela IA em algum lugar do pipeline.
    """
    contact = config.get("contact") or {}
    address = contact.get("address")
    google_maps_url = contact.get("googleMapsUrl")

    if address != (localizacao_esperada or None):
        return ResultadoCriterio(
            "CNF-02", False,
            f"address diverge do input do Hunter: {address!r} != {(localizacao_esperada or None)!r}",
        )
    if google_maps_url != (google_maps_url_esperado or None):
        return ResultadoCriterio(
            "CNF-02", False,
            f"googleMapsUrl diverge do input do Hunter: {google_maps_url!r} != {(google_maps_url_esperado or None)!r}",
        )
    return ResultadoCriterio("CNF-02", True)


def _url_valida_formato(url: Optional[str]) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _http_head_padrao(url: str):
    return requests.head(url, timeout=5, allow_redirects=True)


def validar_img05_imagens_resolvem(
    config: dict,
    http_head: Optional[Callable[[str], object]] = None,
) -> ResultadoCriterio:
    """
    IMG-05: toda URL de imagem do config (hero + seções) resolve HTTP 200.
    `http_head` é injetável para teste -- por padrão faz um HEAD real.
    """
    http_head = http_head or _http_head_padrao

    urls = []
    hero = config.get("hero") or {}
    if hero.get("backgroundImage"):
        urls.append(hero["backgroundImage"])
    for secao in config.get("sections", []) or []:
        if secao.get("image"):
            urls.append(secao["image"])

    falhas = []
    for url in urls:
        if not _url_valida_formato(url):
            falhas.append(f"{url}: formato de URL inválido")
            continue
        try:
            resposta = http_head(url)
            if resposta.status_code != 200:
                falhas.append(f"{url}: HTTP {resposta.status_code}")
        except Exception as e:
            falhas.append(f"{url}: erro de rede ({e})")

    if falhas:
        return ResultadoCriterio("IMG-05", False, "; ".join(falhas))
    return ResultadoCriterio("IMG-05", True, f"{len(urls)} imagem(ns) verificada(s)")


def _obter_dimensao_imagem_real(url: str) -> tuple:
    """
    Lê só o cabeçalho do arquivo via streaming (não baixa a imagem inteira)
    -- suficiente pra Pillow inferir as dimensões na maioria dos formatos
    (JPEG/PNG/WebP), que é tudo que o Image Engine e o LoremFlickr entregam.
    """
    from PIL import Image
    import io

    resposta = requests.get(url, timeout=10, stream=True)
    resposta.raise_for_status()
    trecho = resposta.raw.read(65536, decode_content=True)
    with Image.open(io.BytesIO(trecho)) as img:
        return img.size


def validar_img04_hero_dimensao(
    config: dict,
    largura_minima: int = 1920,
    razao_minima: float = 16 / 9,
    obter_dimensao: Optional[Callable[[str], tuple]] = None,
) -> ResultadoCriterio:
    """IMG-04: hero.backgroundImage com largura >= 1920px e proporção >= 16:9."""
    hero = config.get("hero") or {}
    url = hero.get("backgroundImage")
    if not url:
        return ResultadoCriterio("IMG-04", False, "hero.backgroundImage ausente")

    obter_dimensao = obter_dimensao or _obter_dimensao_imagem_real

    try:
        largura, altura = obter_dimensao(url)
    except Exception as e:
        return ResultadoCriterio("IMG-04", False, f"não foi possível ler dimensão: {e}")

    if largura < largura_minima:
        return ResultadoCriterio("IMG-04", False, f"largura {largura}px < mínimo {largura_minima}px")

    razao = largura / altura if altura else 0
    if razao < razao_minima:
        return ResultadoCriterio("IMG-04", False, f"proporção {razao:.2f} < mínimo {razao_minima:.2f}")

    return ResultadoCriterio("IMG-04", True, f"{largura}x{altura}")


def rodar_gate_relatorio(
    config: dict,
    localizacao_esperada: Optional[str] = None,
    google_maps_url_esperado: Optional[str] = None,
    http_head: Optional[Callable[[str], object]] = None,
    obter_dimensao: Optional[Callable[[str], tuple]] = None,
) -> list:
    """
    Roda os 4 critérios do Lote 1.C e devolve a lista de ResultadoCriterio.
    Modo relatório: nunca lança exceção por reprovação, nunca altera `config`.
    """
    return [
        validar_cnf01_contato(config),
        validar_cnf02_endereco(config, localizacao_esperada, google_maps_url_esperado),
        validar_img04_hero_dimensao(config, obter_dimensao=obter_dimensao),
        validar_img05_imagens_resolvem(config, http_head=http_head),
    ]
