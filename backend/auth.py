#!/usr/bin/env python3
"""
Autenticação compartilhada dos endpoints protegidos da API (geração de
site, webhook do WhatsApp/onboarding, ferramenta interna de demo DFY).

Extraído de app.py para evitar import circular: routers/*.py precisam
desta dependência e são importados por app.py, então ela não pode viver
dentro de app.py.
"""

import logging
import os
from typing import Optional

from fastapi import Header, HTTPException

logger = logging.getLogger("FabricaSitesAPI.auth")

WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY")


def verificar_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    """
    Protege endpoints sensíveis contra acesso público.
    Exige o header `X-API-Key` batendo com WEBHOOK_API_KEY do ambiente.
    """
    if not WEBHOOK_API_KEY:
        logger.error("❌ WEBHOOK_API_KEY não configurada — endpoint protegido está bloqueado até configurar")
        raise HTTPException(
            status_code=503,
            detail="Endpoint não configurado: defina WEBHOOK_API_KEY no ambiente do servidor"
        )
    if not x_api_key or x_api_key != WEBHOOK_API_KEY:
        raise HTTPException(status_code=401, detail="API key ausente ou inválida")
