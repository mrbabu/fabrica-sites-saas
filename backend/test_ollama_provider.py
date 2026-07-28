#!/usr/bin/env python3
"""
Smoke tests para ProvedorOllama - validação de modelo local.

Cenários testados:
1. Modelo existente -> __init__ OK
2. Modelo inexistente -> ErroProvedorIA sem chamar pull
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(__file__))

from ai_provider import ErroProvedorIA, ProvedorOllama


def _mock_requests(modelos):
    """Cria um mock do módulo requests com a lista de modelos fornecida."""
    mock = MagicMock()

    tags_resp = MagicMock()
    tags_resp.status_code = 200
    tags_resp.json.return_value = {"models": [{"name": m, "size": 0} for m in modelos]}
    tags_resp.raise_for_status = MagicMock()

    mock.get.return_value = tags_resp
    return mock


class TestProvedorOllamaValidacaoModelo(unittest.TestCase):
    """Testa a validação de modelo local no __init__ do ProvedorOllama."""

    def setUp(self):
        self.modelos = ["llama3", "llama3:8b", "mistral"]

    def test_modelo_existe_init_ok(self):
        """Cenário 1: Modelo existe -> __init__ completa sem erro."""
        mock = _mock_requests(self.modelos)
        provedor = ProvedorOllama(_requests_module=mock)
        self.assertEqual(provedor.model, "llama3")

    def test_modelo_com_tag_existe_init_ok(self):
        """Cenário 1b: Modelo com tag (:8b) existe -> OK."""
        os.environ["OLLAMA_MODEL"] = "llama3:8b"
        try:
            mock = _mock_requests(self.modelos)
            provedor = ProvedorOllama(_requests_module=mock)
            self.assertEqual(provedor.model, "llama3:8b")
        finally:
            del os.environ["OLLAMA_MODEL"]

    def test_modelo_inexistente_levanta_erro(self):
        """Cenário 2: Modelo inexistente -> ErroProvedorIA com instrução de pull."""
        os.environ["OLLAMA_MODEL"] = "llama3.1:8b"
        try:
            mock = _mock_requests(self.modelos)
            with self.assertRaises(ErroProvedorIA) as ctx:
                ProvedorOllama(_requests_module=mock)

            erro_msg = str(ctx.exception)
            self.assertIn("llama3.1:8b", erro_msg)
            self.assertIn("ollama pull llama3.1:8b", erro_msg)
        finally:
            del os.environ["OLLAMA_MODEL"]

    def test_modelo_inexistente_mostra_modelos_disponiveis(self):
        """Cenário 2b: Erro lista modelos disponíveis."""
        os.environ["OLLAMA_MODEL"] = "nao-existe"
        try:
            mock = _mock_requests(self.modelos)
            with self.assertRaises(ErroProvedorIA) as ctx:
                ProvedorOllama(_requests_module=mock)

            erro_msg = str(ctx.exception)
            self.assertIn("llama3", erro_msg)
            self.assertIn("mistral", erro_msg)
        finally:
            del os.environ["OLLAMA_MODEL"]

    def test_modelo_inexistente_nao_chama_generate(self):
        """Cenário 3: Modelo inexistente -> /api/generate NUNCA é chamado."""
        os.environ["OLLAMA_MODEL"] = "inexistente"
        try:
            mock = _mock_requests(self.modelos)
            with self.assertRaises(ErroProvedorIA):
                ProvedorOllama(_requests_module=mock)

            mock.post.assert_not_called()
        finally:
            del os.environ["OLLAMA_MODEL"]

    def test_modelo_existe_gerar_json_ok(self):
        """Cenário 4: Modelo existe -> gerar_json funciona."""
        mock = _mock_requests(self.modelos)
        gen_resp = MagicMock()
        gen_resp.status_code = 200
        gen_resp.json.return_value = {"response": '{"key": "value"}'}
        gen_resp.raise_for_status = MagicMock()
        mock.post.return_value = gen_resp

        provedor = ProvedorOllama(_requests_module=mock)
        resultado = provedor.gerar_json("test prompt")
        self.assertEqual(resultado, {"key": "value"})

    def test_modelo_custom_com_tag_existe(self):
        """Cenário 5: Modelo custom com :latest existe -> OK."""
        os.environ["OLLAMA_MODEL"] = "custom-model:latest"
        try:
            mock = _mock_requests(["custom-model:latest"])
            provedor = ProvedorOllama(_requests_module=mock)
            self.assertEqual(provedor.model, "custom-model:latest")
        finally:
            del os.environ["OLLAMA_MODEL"]

    def test_modelo_sem_tag_mas_tag_disponivel_sugere_versoes(self):
        """Cenário 6: Modelo 'custom-model' mas só existe 'custom-model:latest' -> erro com sugestão."""
        os.environ["OLLAMA_MODEL"] = "custom-model"
        try:
            mock = _mock_requests(["custom-model:latest"])
            with self.assertRaises(ErroProvedorIA) as ctx:
                ProvedorOllama(_requests_module=mock)

            erro_msg = str(ctx.exception)
            self.assertIn("custom-model", erro_msg)
            self.assertIn("custom-model:latest", erro_msg)
        finally:
            del os.environ["OLLAMA_MODEL"]


if __name__ == "__main__":
    unittest.main()
