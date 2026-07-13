#!/usr/bin/env python3
"""
Preview somente-leitura de uma demo DFY já gerada (ver
backend/routers/demo_dfy.py para a geração em si).

Renderiza o template de produção (index.html) com o site-config
correspondente injetado — mesmo método já validado manualmente em sessão
anterior (substituir o fetch('./site-config.json') por um <script> com o
JSON inline), só que servido dinamicamente em vez de copiado à mão.

Sem banco, sem login, sem edição, sem upload — só leitura de
configs/<slug>.json (mesmo arquivo que POST /api/v1/demo-dfy já produz).
"""

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])

PASTA_RAIZ = Path(__file__).resolve().parent.parent.parent
CAMINHO_INDEX_HTML = PASTA_RAIZ / "index.html"
PASTA_CONFIGS = PASTA_RAIZ / "configs"


@router.get("/demo/preview/{slug}", response_class=HTMLResponse)
async def preview_demo(slug: str):
    """Renderiza uma demo já gerada, injetando site-config no template de produção."""
    if not re.match(r"^[a-z0-9-]+$", slug):
        raise HTTPException(status_code=400, detail="Slug inválido")

    caminho_config = PASTA_CONFIGS / f"{slug}.json"
    if not caminho_config.exists():
        raise HTTPException(status_code=404, detail=f"Demo '{slug}' não encontrada")

    config_json = caminho_config.read_text(encoding="utf-8")
    template_html = CAMINHO_INDEX_HTML.read_text(encoding="utf-8")

    injecao = f"<script>window.__SITE_CONFIG__ = {config_json};</script>\n</head>"
    html_final = template_html.replace("</head>", injecao, 1)
    html_final = html_final.replace(
        "const response = await fetch('./site-config.json');\n                config = await response.json();",
        "config = window.__SITE_CONFIG__;",
    )

    return HTMLResponse(content=html_final)
