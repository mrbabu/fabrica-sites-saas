#!/usr/bin/env python3
"""
Testes do ProvedorGroq (LPU, tier gratuito, SDK OpenAI-compativel).
Nenhum teste faz chamada de rede real -- o client OpenAI e' mockado.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(__file__))

from ai_provider import ErroProvedorIA, ProvedorGroq


class TestProvedorGroqInicializacao(unittest.TestCase):
    def setUp(self):
        for var in ["GROQ_API_KEY", "GROQ_BASE_URL", "GROQ_MODEL", "GROQ_TIMEOUT"]:
            os.environ.pop(var, None)

    def tearDown(self):
        for var in ["GROQ_API_KEY", "GROQ_BASE_URL", "GROQ_MODEL", "GROQ_TIMEOUT"]:
            os.environ.pop(var, None)

    def test_sem_api_key_levanta_erro(self):
        with self.assertRaises(ErroProvedorIA) as ctx:
            ProvedorGroq()
        self.assertIn("GROQ_API_KEY", str(ctx.exception))

    def test_com_api_key_usa_defaults_corretos(self):
        os.environ["GROQ_API_KEY"] = "gsk_teste"
        provedor = ProvedorGroq()
        self.assertEqual(provedor.model, "llama-3.3-70b-versatile")
        self.assertEqual(provedor.base_url, "https://api.groq.com/openai/v1")
        self.assertEqual(provedor.client.timeout, 60.0)

    def test_permite_sobrescrever_modelo_base_url_timeout(self):
        os.environ["GROQ_API_KEY"] = "gsk_teste"
        os.environ["GROQ_MODEL"] = "llama-3.1-8b-instant"
        os.environ["GROQ_BASE_URL"] = "https://exemplo.com/v1"
        os.environ["GROQ_TIMEOUT"] = "30"
        provedor = ProvedorGroq()
        self.assertEqual(provedor.model, "llama-3.1-8b-instant")
        self.assertEqual(provedor.base_url, "https://exemplo.com/v1")
        self.assertEqual(provedor.client.timeout, 30.0)

    def test_nome_do_provedor(self):
        self.assertEqual(ProvedorGroq.nome, "groq")


class TestProvedorGroqGerarJson(unittest.TestCase):
    def setUp(self):
        os.environ["GROQ_API_KEY"] = "gsk_teste"

    def tearDown(self):
        os.environ.pop("GROQ_API_KEY", None)

    def test_gerar_json_extrai_resposta_do_client(self):
        provedor = ProvedorGroq()

        resposta_fake = MagicMock()
        resposta_fake.choices = [MagicMock()]
        resposta_fake.choices[0].message.content = '{"ok": true}'
        provedor.client = MagicMock()
        provedor.client.chat.completions.create.return_value = resposta_fake

        resultado = provedor.gerar_json("prompt de teste", max_tokens=100)

        self.assertEqual(resultado, {"ok": True})
        provedor.client.chat.completions.create.assert_called_once()
        chamada = provedor.client.chat.completions.create.call_args.kwargs
        self.assertEqual(chamada["model"], "llama-3.3-70b-versatile")
        self.assertEqual(chamada["max_tokens"], 100)

    def test_gerar_json_lida_com_markdown_ao_redor_do_json(self):
        provedor = ProvedorGroq()
        resposta_fake = MagicMock()
        resposta_fake.choices = [MagicMock()]
        resposta_fake.choices[0].message.content = '```json\n{"ok": true}\n```'
        provedor.client = MagicMock()
        provedor.client.chat.completions.create.return_value = resposta_fake

        resultado = provedor.gerar_json("prompt de teste")
        self.assertEqual(resultado, {"ok": True})

    def test_gerar_json_captura_uso_de_tokens_quando_a_api_informa(self):
        provedor = ProvedorGroq()
        resposta_fake = MagicMock()
        resposta_fake.choices = [MagicMock()]
        resposta_fake.choices[0].message.content = '{"ok": true}'
        resposta_fake.usage.prompt_tokens = 150
        resposta_fake.usage.completion_tokens = 300
        resposta_fake.usage.total_tokens = 450
        provedor.client = MagicMock()
        provedor.client.chat.completions.create.return_value = resposta_fake

        provedor.gerar_json("prompt de teste")

        self.assertEqual(provedor.ultimo_uso_tokens, {"prompt": 150, "completion": 300, "total": 450})

    def test_gerar_json_sem_usage_no_retorno_marca_none_com_motivo(self):
        provedor = ProvedorGroq()
        resposta_fake = MagicMock(spec=["choices"])
        resposta_fake.choices = [MagicMock()]
        resposta_fake.choices[0].message.content = '{"ok": true}'
        provedor.client = MagicMock()
        provedor.client.chat.completions.create.return_value = resposta_fake

        provedor.gerar_json("prompt de teste")

        self.assertIsNone(provedor.ultimo_uso_tokens)


if __name__ == "__main__":
    unittest.main()
