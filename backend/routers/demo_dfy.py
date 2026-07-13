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

from agent_construtor import AgenteConstrutor
from image_utils import _slugify
from auth import verificar_api_key

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

    @field_validator("cor_primaria")
    @classmethod
    def validar_cor_hex(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Cor deve estar em formato hex válido: #RRGGBB")
        return v.lower()


@router.post("/api/v1/demo-dfy", dependencies=[Depends(verificar_api_key)])
async def gerar_demo(payload: DemoDfyRequest):
    """Gera uma demo DFY chamando o motor real e salva em configs/<slug>.json."""
    agente = _obter_agente()
    try:
        config = agente.executar(
            nome_empresa=payload.nome_empresa,
            nicho=payload.nicho,
            cor_primaria=payload.cor_primaria,
            localizacao=payload.localizacao,
            whatsapp_contato=payload.whatsapp_contato,
            logo_url=payload.logo_url,
            caminho_saida=str(PASTA_CONFIGS / f"{_slugify(payload.nome_empresa)}.json"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar demo: {e}")

    slug = _slugify(payload.nome_empresa)
    return {
        "slug": slug,
        "site_title": config.get("metadata", {}).get("siteTitle", ""),
        "preview_url": f"/demo/preview/{slug}",
    }
