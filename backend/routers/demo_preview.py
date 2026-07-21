#!/usr/bin/env python3
"""
Preview somente-leitura de uma demo DFY já gerada (ver
backend/routers/demo_dfy.py para a geração em si).

Renderiza o template de produção (index.html) com o site-config
correspondente injetado — mesmo método já validado manualmente em sessão
anterior (substituir o fetch('./site-config.json') por um <script> com o
JSON inline), só que servido dinamicamente em vez de copiado à mão.

Lê do Postgres (tabela `sites`, mesmo mecanismo de /webhook/whatsapp — ver
repository.py), não mais de configs/<slug>.json: um arquivo dentro do
container do backend não sobrevive a um rebuild (não é volume Docker), o
que apagava toda demo gerada sempre que o backend era reconstruído. Sem
login, sem edição, sem upload — só leitura.
"""

import json
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from auth_demo import exigir_login_demo
from db import get_db
import repository

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])

PASTA_RAIZ = Path(__file__).resolve().parent.parent.parent
CAMINHO_INDEX_HTML = PASTA_RAIZ / "index.html"


@router.get("/demo/preview/{slug}", response_class=HTMLResponse)
async def preview_demo(slug: str, request: Request, db: Session = Depends(get_db)):
    """Renderiza uma demo já gerada, injetando site-config no template de produção."""
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect
    if not re.match(r"^[a-z0-9-]+$", slug):
        raise HTTPException(status_code=400, detail="Slug inválido")

    site = repository.obter_site(db, slug)
    if site is None:
        raise HTTPException(status_code=404, detail=f"Demo '{slug}' não encontrada")

    config_json = json.dumps(site.config, ensure_ascii=False)
    template_html = CAMINHO_INDEX_HTML.read_text(encoding="utf-8")

    injecao = f"<script>window.__SITE_CONFIG__ = {config_json};</script>\n</head>"
    html_final = template_html.replace("</head>", injecao, 1)
    html_final = html_final.replace(
        "const response = await fetch('./site-config.json');\n                config = await response.json();",
        "config = window.__SITE_CONFIG__;",
    )

    return HTMLResponse(content=html_final)
