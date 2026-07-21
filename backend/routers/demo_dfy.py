#!/usr/bin/env python3
"""
Ferramenta interna de demonstração DFY — chama o motor de produção real
(AgenteConstrutor.executar(), o mesmo usado por
backend/scripts/gerar_demo_dfy.py). Nenhuma lógica de geração vive aqui:
tudo é delegado a agent_construtor.py, que continua congelado e intocado.

Escopo desta primeira versão: só o endpoint de geração
(POST /api/v1/demo-dfy). Formulário e preview HTML entram depois, uma vez
que este endpoint estiver confirmado funcionando.
"""

import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from agent_construtor import AgenteConstrutor
from image_utils import _slugify
from auth import verificar_api_key
from db import get_db
import repository

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])

PASTA_RAIZ = Path(__file__).resolve().parent.parent.parent
PASTA_CONFIGS = PASTA_RAIZ / "configs"

_agente: Optional[AgenteConstrutor] = None


def _obter_agente() -> AgenteConstrutor:
    """Instancia o Agente Construtor sob demanda (evita custo na subida do servidor)."""
    global _agente
    if _agente is None:
        _agente = AgenteConstrutor()
    return _agente


class DemoDfyRequest(BaseModel):
    """Dados mínimos pra gerar uma demo DFY — mesmos campos obrigatórios de gerar_demo_dfy.py"""
    nome_empresa: str = Field(..., min_length=2, max_length=100)
    nicho: str = Field(..., min_length=3, max_length=100, description='Rótulo na UI: "Tipo de negócio"')
    localizacao: str = Field(..., min_length=2, max_length=150)
    whatsapp_contato: str = Field(..., min_length=10, max_length=20, description="WhatsApp REAL do negócio, obrigatório")
    cor_primaria: str = Field(default="#0D9488", description="Cor primária em hexadecimal")
    logo_url: Optional[str] = Field(default=None, description="URL pública de imagem já existente — nunca upload")
    descricao_negocio: Optional[str] = Field(default=None, max_length=1000, description="Contexto livre sobre o negócio, informado pelo cliente")
    portfolio_urls: Optional[list[str]] = Field(
        default=None,
        max_length=8,
        description=(
            "Até 8 links diretos de imagem pública (JPG/PNG/WebP) do trabalho "
            "real do cliente — precisam ser o link do próprio arquivo de "
            "imagem, não o link de uma página ou de uma pasta/Drive "
            "compartilhado, pois são usados diretamente em <img>/background "
            "no site gerado. Nunca upload — mesmo padrão de logo_url."
        ),
    )

    @field_validator("cor_primaria")
    @classmethod
    def validar_cor_hex(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Cor deve estar em formato hex válido: #RRGGBB")
        return v.lower()

    @field_validator("portfolio_urls")
    @classmethod
    def validar_portfolio_urls(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if not v:
            return v
        for url in v:
            if not re.match(r"^https?://", url, re.IGNORECASE):
                raise ValueError(
                    f"portfolio_urls deve conter apenas links http(s) diretos de imagem: '{url}' inválido"
                )
            if not re.search(r"\.(jpe?g|png|webp)(\?.*)?$", url, re.IGNORECASE):
                raise ValueError(
                    f"portfolio_urls deve apontar direto pra um arquivo de imagem "
                    f"(.jpg/.jpeg/.png/.webp), não link de página ou pasta/Drive "
                    f"compartilhado: '{url}' não parece ser um link direto de imagem"
                )
        return v


@router.post("/api/v1/demo-dfy", dependencies=[Depends(verificar_api_key)])
async def gerar_demo(payload: DemoDfyRequest, db: Session = Depends(get_db)):
    """
    Gera uma demo DFY chamando o motor real e persiste no Postgres (tabela
    `sites`, mesmo mecanismo de /webhook/whatsapp — ver repository.py).

    A gravação no Postgres é síncrona (não BackgroundTasks): o formulário em
    routers/demo.py navega pro preview_url assim que a resposta chega, então
    o registro precisa existir no banco antes de responder, sem risco de
    corrida com o navegador batendo no preview antes do commit.

    Ainda chama agente.executar(caminho_saida=...) sem alterar
    agent_construtor.py (motor congelado) — o arquivo em configs/ continua
    sendo escrito como efeito colateral inofensivo (é assim que o motor já
    funciona pra todos os chamadores, inclusive scripts de CLI), mas deixou
    de ser a fonte de verdade: só o Postgres é lido por /demo/preview agora.
    """
    agente = _obter_agente()
    slug = _slugify(payload.nome_empresa)
    try:
        config = agente.executar(
            nome_empresa=payload.nome_empresa,
            nicho=payload.nicho,
            cor_primaria=payload.cor_primaria,
            localizacao=payload.localizacao,
            whatsapp_contato=payload.whatsapp_contato,
            logo_url=payload.logo_url,
            descricao_negocio=payload.descricao_negocio,
            portfolio_urls=payload.portfolio_urls,
            caminho_saida=str(PASTA_CONFIGS / f"{slug}.json"),
        )
        repository.upsert_site(db, slug, payload.nome_empresa, payload.nicho, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar demo: {e}")

    return {
        "slug": slug,
        "site_title": config.get("metadata", {}).get("siteTitle", ""),
        "preview_url": f"/demo/preview/{slug}",
    }
