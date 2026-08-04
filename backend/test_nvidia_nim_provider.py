#!/usr/bin/env python3
"""
Testes do ProvedorNvidiaNIM -- cobertura mínima, focada na captura de uso
de tokens (compartilha _extrair_uso_openai com ProvedorGroq, já coberto
em test_groq_provider.py; aqui só confirma que NIM de fato liga esse
extrator). Nenhum teste faz chamada de rede real.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(__file__))

from ai_provider import ErroProvedorIA, ProvedorNvidiaNIM


class TestProvedorNvidiaNIM(unittest.TestCase):
    def setUp(self):
        os.environ["NVIDIA_NIM_API_KEY"] = "nvapi-teste"

    def tearDown(self):
        os.environ.pop("NVIDIA_NIM_API_KEY", None)

    def test_sem_api_key_levanta_erro(self):
        os.environ.pop("NVIDIA_NIM_API_KEY", None)
        with self.assertRaises(ErroProvedorIA):
            ProvedorNvidiaNIM()

    def test_gerar_json_captura_uso_de_tokens_quando_a_api_informa(self):
        provedor = ProvedorNvidiaNIM()
        resposta_fake = MagicMock()
        resposta_fake.choices = [MagicMock()]
        resposta_fake.choices[0].message.content = '{"ok": true}'
        resposta_fake.usage.prompt_tokens = 80
        resposta_fake.usage.completion_tokens = 120
        resposta_fake.usage.total_tokens = 200
        provedor.client = MagicMock()
        provedor.client.chat.completions.create.return_value = resposta_fake

        resultado = provedor.gerar_json("prompt de teste")

        self.assertEqual(resultado, {"ok": True})
        self.assertEqual(provedor.ultimo_uso_tokens, {"prompt": 80, "completion": 120, "total": 200})

    def test_gerar_json_sem_usage_marca_tokens_none(self):
        provedor = ProvedorNvidiaNIM()
        resposta_fake = MagicMock(spec=["choices"])
        resposta_fake.choices = [MagicMock()]
        resposta_fake.choices[0].message.content = '{"ok": true}'
        provedor.client = MagicMock()
        provedor.client.chat.completions.create.return_value = resposta_fake

        provedor.gerar_json("prompt de teste")

        self.assertIsNone(provedor.ultimo_uso_tokens)


if __name__ == "__main__":
    unittest.main()
