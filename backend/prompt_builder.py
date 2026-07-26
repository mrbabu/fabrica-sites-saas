#!/usr/bin/env python3
"""
PromptBuilder: extrai do site-config JÁ GERADO (agent_construtor.py +
Image Engine, nenhum dos dois alterado aqui) uma estrutura intermediária
independente de qualquer plataforma de IA específica. Cada adapter de
plataforma (ver lovable_adapter.py) consome essa mesma EspecificacaoSite
pra montar o prompt/URL no formato próprio dele — permite reaproveitar
este módulo pra futuras integrações (Bolt, v0, Figma AI etc.) sem
duplicar a extração de dados do site-config.

Não cria categoria/conhecimento novo: só lê os campos que o gerador já
produziu.

Guardrail de imagens (pedido explícito do usuário): nenhuma imagem
produzida pelo nosso Image Engine (Unsplash) ou pelos fallbacks
determinísticos (LoremFlickr, ui-avatars) é enviada como referência
visual pra plataforma nenhuma — são stock photo/avatar genérico, não a
identidade real do cliente, e mandar isso como "referência de marca"
confundiria a IA da plataforma de destino. Só company.logo e as imagens
de hero/seção são candidatas a "brand asset", e só entram se NÃO vierem
de um domínio conhecido do Image Engine/fallback (ou seja, só quando são
uma URL real fornecida pela equipe via logo_url/portfolio_urls).
"""

from dataclasses import dataclass, field
from urllib.parse import urlparse

FORMATOS_IMAGEM_RECUSADOS = (".svg", ".gif")

# Domínios do próprio Image Engine/fallbacks determinísticos — nunca são
# identidade visual real do cliente, nunca viram brand asset.
DOMINIOS_IMAGEM_GERADA = (
    "images.unsplash.com",
    "loremflickr.com",
    "ui-avatars.com",
    "i.pravatar.cc",
)


def _e_imagem_gerada(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == d or host.endswith(f".{d}") for d in DOMINIOS_IMAGEM_GERADA)


@dataclass
class EspecificacaoSite:
    """Estrutura intermediária, agnóstica de plataforma."""
    nome: str
    tagline: str | None = None
    descricao: str | None = None
    cor_primaria: str | None = None
    cor_destaque: str | None = None
    servicos: list[tuple[str, str]] = field(default_factory=list)       # (titulo, descricao)
    diferenciais: list[tuple[str, str]] = field(default_factory=list)   # (titulo, descricao)
    cta_titulo: str | None = None
    cta_descricao: str | None = None
    whatsapp: str | None = None
    endereco: str | None = None
    google_maps_url: str | None = None
    brand_assets: list[str] = field(default_factory=list)  # logo/fachada/equipe/produtos REAIS do cliente — nunca Image Engine
    instrucao_identidade_visual: str | None = None


def construir_especificacao(config: dict) -> EspecificacaoSite:
    """Único ponto de leitura do site-config — qualquer adapter novo
    reaproveita esta função em vez de reimplementar a extração."""
    company = config.get("company", {})
    contact = config.get("contact", {})
    cores = config.get("colors", {})
    cta = config.get("cta", {})

    candidatas = [company.get("logo", "")]
    candidatas.append(config.get("hero", {}).get("backgroundImage", ""))
    candidatas += [s.get("image", "") for s in (config.get("sections") or [])]
    brand_assets = [
        url for url in candidatas
        if url
        and not url.lower().split("?")[0].endswith(FORMATOS_IMAGEM_RECUSADOS)
        and not _e_imagem_gerada(url)
    ]

    instrucao_identidade_visual = (
        "Utilize estas imagens como referência principal da identidade "
        "visual deste negócio e gere o restante do site mantendo "
        "consistência com elas."
    ) if brand_assets else None

    return EspecificacaoSite(
        nome=company.get("name", ""),
        tagline=company.get("tagline"),
        descricao=company.get("description"),
        cor_primaria=cores.get("primary"),
        cor_destaque=cores.get("accent"),
        servicos=[(s.get("title", ""), s.get("description", "")) for s in (config.get("services") or [])],
        diferenciais=[(f.get("title", ""), f.get("description", "")) for f in (config.get("features") or [])],
        cta_titulo=cta.get("title"),
        cta_descricao=cta.get("description"),
        whatsapp=contact.get("whatsapp"),
        endereco=contact.get("address"),
        google_maps_url=contact.get("googleMapsUrl"),
        brand_assets=brand_assets,
        instrucao_identidade_visual=instrucao_identidade_visual,
    )
