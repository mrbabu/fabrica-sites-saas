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
"""

from dataclasses import dataclass, field

FORMATOS_IMAGEM_RECUSADOS = (".svg", ".gif")


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
    imagens: list[str] = field(default_factory=list)


def construir_especificacao(config: dict) -> EspecificacaoSite:
    """Único ponto de leitura do site-config — qualquer adapter novo
    reaproveita esta função em vez de reimplementar a extração."""
    company = config.get("company", {})
    contact = config.get("contact", {})
    cores = config.get("colors", {})
    cta = config.get("cta", {})

    candidatas = [config.get("hero", {}).get("backgroundImage", "")]
    candidatas += [s.get("image", "") for s in (config.get("sections") or [])[:2]]
    imagens = [
        url for url in candidatas
        if url and not url.lower().split("?")[0].endswith(FORMATOS_IMAGEM_RECUSADOS)
    ]

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
        imagens=imagens,
    )
