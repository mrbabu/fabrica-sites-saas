#!/usr/bin/env python3
"""
Testes de integração da cadeia de fallback do AIProvider
(gemini -> nvidia_nim -> anthropic -> ollama).

Não fazem chamada de rede real: cada provedor é substituído por um dublê
via patch.dict em ai_provider._PROVEDORES, o mesmo dicionário que
AIProvider._obter_instancia usa pra resolver cada nome -- garante que o
teste exercita a política real de ordem/fallback/erro consolidado, não uma
reimplementação paralela dela.
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))

import ai_provider
from ai_provider import AIProvider, ErroProvedorIA


class _ProvedorFalhaSempre:
    """Dublê que simula um provedor indisponível (sem credencial/rede)."""

    def __init__(self, *args, **kwargs):
        raise ErroProvedorIA("indisponível (dublê de teste)")


class _ProvedorSucessoSempre:
    """Dublê que simula um provedor disponível e funcional."""

    def __init__(self, *args, **kwargs):
        self.ultimo_uso_tokens = None

    def gerar_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        self.ultimo_uso_tokens = {"prompt": 10, "completion": 20, "total": 30}
        return {"ok": True, "prompt_recebido": prompt}


class _ProvedorSucessoSemTokens:
    """Dublê que simula um provedor que nunca informa uso de tokens (sem o atributo)."""

    def __init__(self, *args, **kwargs):
        pass

    def gerar_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        return {"ok": True}


class TestCadeiaDeFallback(unittest.TestCase):
    """Testa AIProvider.gerar_json() com a ordem real gemini->nim->anthropic->ollama."""

    def setUp(self):
        os.environ["AI_PROVIDER_FALLBACK_ORDER"] = "gemini,nvidia_nim,anthropic,ollama"

    def tearDown(self):
        os.environ.pop("AI_PROVIDER_FALLBACK_ORDER", None)

    def test_cai_ate_ollama_quando_os_tres_primeiros_falham(self):
        """Gemini indisponível -> NIM indisponível -> Anthropic indisponível -> Ollama responde."""
        dubles = {
            "gemini": _ProvedorFalhaSempre,
            "nvidia_nim": _ProvedorFalhaSempre,
            "anthropic": _ProvedorFalhaSempre,
            "ollama": _ProvedorSucessoSempre,
        }
        with patch.dict(ai_provider._PROVEDORES, dubles):
            provider = AIProvider()
            resultado = provider.gerar_json("prompt de teste")

            self.assertEqual(resultado["ok"], True)
            self.assertEqual(provider.provedor_ativo, "ollama")

    def test_usa_primeiro_provedor_disponivel_sem_tentar_os_seguintes(self):
        """Se Gemini responde, NIM/Anthropic/Ollama nem devem ser instanciados."""
        chamadas = {"nim": 0, "anthropic": 0, "ollama": 0}

        class _NimNuncaDeveSerChamado:
            def __init__(self, *a, **kw):
                chamadas["nim"] += 1
                raise ErroProvedorIA("não deveria ter sido chamado")

        class _AnthropicNuncaDeveSerChamado:
            def __init__(self, *a, **kw):
                chamadas["anthropic"] += 1
                raise ErroProvedorIA("não deveria ter sido chamado")

        class _OllamaNuncaDeveSerChamado:
            def __init__(self, *a, **kw):
                chamadas["ollama"] += 1
                raise ErroProvedorIA("não deveria ter sido chamado")

        dubles = {
            "gemini": _ProvedorSucessoSempre,
            "nvidia_nim": _NimNuncaDeveSerChamado,
            "anthropic": _AnthropicNuncaDeveSerChamado,
            "ollama": _OllamaNuncaDeveSerChamado,
        }
        with patch.dict(ai_provider._PROVEDORES, dubles):
            provider = AIProvider()
            provider.gerar_json("prompt de teste")

            self.assertEqual(provider.provedor_ativo, "gemini")
            self.assertEqual(chamadas, {"nim": 0, "anthropic": 0, "ollama": 0})

    def test_erro_consolidado_quando_todos_os_provedores_falham(self):
        """Gemini indisponível -> NIM indisponível -> Anthropic indisponível -> Ollama indisponível -> erro consolidado."""
        dubles = {
            "gemini": _ProvedorFalhaSempre,
            "nvidia_nim": _ProvedorFalhaSempre,
            "anthropic": _ProvedorFalhaSempre,
            "ollama": _ProvedorFalhaSempre,
        }
        with patch.dict(ai_provider._PROVEDORES, dubles):
            provider = AIProvider()
            with self.assertRaises(ErroProvedorIA) as ctx:
                provider.gerar_json("prompt de teste")

            mensagem_erro = str(ctx.exception)
            for nome in ("gemini", "nvidia_nim", "anthropic", "ollama"):
                self.assertIn(nome, mensagem_erro)


class TestUsoTokensAtivo(unittest.TestCase):
    def setUp(self):
        os.environ["AI_PROVIDER_FALLBACK_ORDER"] = "gemini,ollama"

    def tearDown(self):
        os.environ.pop("AI_PROVIDER_FALLBACK_ORDER", None)

    def test_expoe_tokens_do_provedor_que_respondeu(self):
        dubles = {"gemini": _ProvedorSucessoSempre, "ollama": _ProvedorFalhaSempre}
        with patch.dict(ai_provider._PROVEDORES, dubles):
            provider = AIProvider()
            provider.gerar_json("prompt de teste")
            self.assertEqual(provider.uso_tokens_ativo, {"prompt": 10, "completion": 20, "total": 30})

    def test_none_quando_provedor_ativo_nao_expoe_tokens(self):
        dubles = {"gemini": _ProvedorSucessoSemTokens, "ollama": _ProvedorFalhaSempre}
        with patch.dict(ai_provider._PROVEDORES, dubles):
            provider = AIProvider()
            provider.gerar_json("prompt de teste")
            self.assertIsNone(provider.uso_tokens_ativo)

    def test_none_antes_de_qualquer_chamada(self):
        dubles = {"gemini": _ProvedorSucessoSempre, "ollama": _ProvedorFalhaSempre}
        with patch.dict(ai_provider._PROVEDORES, dubles):
            provider = AIProvider()
            self.assertIsNone(provider.uso_tokens_ativo)


if __name__ == "__main__":
    unittest.main()
