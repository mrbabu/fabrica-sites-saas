#!/usr/bin/env python3
"""
Testes de backend/routers/demo_upload.py -- chama a função do endpoint
diretamente (sem subir servidor/TestClient), passando um UploadFile
construído em memória. Não testa auth (Depends(verificar_api_key)) --
mesmo padrão de outros testes deste projeto, que verificam a lógica de
negócio isoladamente.
"""

import io
import os
import shutil
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "routers"))

from fastapi import HTTPException, UploadFile
from PIL import Image

import demo_upload


def _jpeg_bytes(largura, altura, cor=(200, 50, 50)):
    buf = io.BytesIO()
    Image.new("RGB", (largura, altura), cor).save(buf, format="JPEG")
    return buf.getvalue()


class TestUploadImagemPortfolio(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._pasta_original = demo_upload.PASTA_UPLOADS_DEMO
        demo_upload.PASTA_UPLOADS_DEMO = demo_upload.PASTA_UPLOADS_DEMO.parent / "demo_test_tmp"

    def tearDown(self):
        shutil.rmtree(demo_upload.PASTA_UPLOADS_DEMO, ignore_errors=True)
        demo_upload.PASTA_UPLOADS_DEMO = self._pasta_original

    async def test_upload_valido_devolve_path_e_salva_arquivo(self):
        arquivo = UploadFile(file=io.BytesIO(_jpeg_bytes(100, 80)), filename="foto.jpg")

        resultado = await demo_upload.upload_imagem_portfolio(arquivo)

        self.assertTrue(resultado["path"].startswith("/assets/uploads/demo/"))
        self.assertTrue(resultado["path"].endswith(".jpg"))
        nome_arquivo = resultado["path"].rsplit("/", 1)[-1]
        self.assertTrue((demo_upload.PASTA_UPLOADS_DEMO / nome_arquivo).is_file())

    async def test_arquivo_nao_e_imagem_e_rejeitado(self):
        arquivo = UploadFile(file=io.BytesIO(b"isso nao e uma imagem de verdade"), filename="foto.jpg")

        with self.assertRaises(HTTPException) as ctx:
            await demo_upload.upload_imagem_portfolio(arquivo)
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_arquivo_grande_demais_e_rejeitado(self):
        conteudo_grande = b"0" * (demo_upload.TAMANHO_MAX_BYTES + 1)
        arquivo = UploadFile(file=io.BytesIO(conteudo_grande), filename="foto.jpg")

        with self.assertRaises(HTTPException) as ctx:
            await demo_upload.upload_imagem_portfolio(arquivo)
        self.assertEqual(ctx.exception.status_code, 413)

    async def test_imagem_maior_que_o_limite_e_redimensionada(self):
        arquivo = UploadFile(
            file=io.BytesIO(_jpeg_bytes(demo_upload.LARGURA_MAX + 800, 1000)),
            filename="foto_grande.jpg",
        )

        resultado = await demo_upload.upload_imagem_portfolio(arquivo)

        nome_arquivo = resultado["path"].rsplit("/", 1)[-1]
        with Image.open(demo_upload.PASTA_UPLOADS_DEMO / nome_arquivo) as salva:
            self.assertEqual(salva.width, demo_upload.LARGURA_MAX)

    async def test_imagem_menor_que_o_limite_nao_e_redimensionada(self):
        arquivo = UploadFile(file=io.BytesIO(_jpeg_bytes(300, 200)), filename="foto_pequena.jpg")

        resultado = await demo_upload.upload_imagem_portfolio(arquivo)

        nome_arquivo = resultado["path"].rsplit("/", 1)[-1]
        with Image.open(demo_upload.PASTA_UPLOADS_DEMO / nome_arquivo) as salva:
            self.assertEqual(salva.width, 300)


if __name__ == "__main__":
    unittest.main()
