#!/usr/bin/env python3
"""
Upload de fotos reais de portfólio para a ferramenta interna de demo DFY
(/demo, protegida por login em auth_demo.py). Alternativa ao campo de URL
colada que já existe (portfolio_urls_raw, ver demo.py) -- este endpoint só
recebe o arquivo, valida/reprocessa e devolve um caminho servível; quem
decide o que entra em portfolio_urls continua sendo o frontend, e quem
valida portfolio_urls continua sendo DemoDfyRequest (demo_dfy.py). Nenhuma
mudança no motor de geração.

Mesmo padrão de segurança de normalizar_logo() (image_utils.py): nunca
confia em extensão/content-type do arquivo recebido, decodifica de
verdade com Pillow e sempre RESSALVA em formato controlado -- os bytes
originais enviados pelo navegador nunca chegam a tocar o disco.
"""

import io
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from auth import verificar_api_key

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    _RESAMPLE = Image.LANCZOS

# assets/uploads/demo vive na raiz do repo (mesma pasta assets/ que
# PASTA_LOGOS em image_utils.py), servida em /assets por StaticFiles
# (app.py) -- salvar aqui já deixa o arquivo acessível sem mudança de infra.
PASTA_UPLOADS_DEMO = Path(__file__).resolve().parent.parent.parent / "assets" / "uploads" / "demo"
TAMANHO_MAX_BYTES = 8 * 1024 * 1024
LARGURA_MAX = 2400


@router.post("/api/v1/demo-upload/imagem", dependencies=[Depends(verificar_api_key)])
async def upload_imagem_portfolio(arquivo: UploadFile = File(...)):
    """
    Recebe 1 imagem, valida que é uma imagem de verdade (não confia em
    Content-Type/extensão), redimensiona só se ultrapassar LARGURA_MAX
    (nunca upscale) e salva com nome aleatório. Devolve o caminho relativo
    pronto pra virar URL absoluta no frontend (window.location.origin + path).
    """
    conteudo = await arquivo.read()
    if len(conteudo) > TAMANHO_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo maior que {TAMANHO_MAX_BYTES // (1024 * 1024)} MB",
        )

    try:
        imagem = Image.open(io.BytesIO(conteudo))
        imagem.load()
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Arquivo não é uma imagem válida")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar imagem: {e}")

    if imagem.mode != "RGB":
        imagem = imagem.convert("RGB")
    if imagem.width > LARGURA_MAX:
        altura = round(imagem.height * LARGURA_MAX / imagem.width)
        imagem = imagem.resize((LARGURA_MAX, altura), _RESAMPLE)

    PASTA_UPLOADS_DEMO.mkdir(parents=True, exist_ok=True)
    nome_arquivo = f"{uuid.uuid4().hex}.jpg"
    imagem.save(PASTA_UPLOADS_DEMO / nome_arquivo, format="JPEG", quality=90)

    return {"path": f"/assets/uploads/demo/{nome_arquivo}"}
