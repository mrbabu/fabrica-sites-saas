#!/usr/bin/env python3
"""
Provedor de IA - Fábrica de Sites SaaS
Abstrai a chamada ao modelo de linguagem por trás de uma interface única
(gerar_json), com troca modular de fonte:

  1. NVIDIA NIM (padrão)   - via SDK OpenAI-compatível
  2. Anthropic (fallback)  - via SDK oficial
  3. Ollama local (fallback de dev, opcional) - via requests

A ordem é escolhida por AI_PROVIDER (provedor preferido) e, se ele falhar,
cai automaticamente para o próximo da cadeia.
"""

import json
import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class ErroProvedorIA(Exception):
    """Erro ao inicializar ou chamar um provedor de IA"""


def _extrair_json(texto: str) -> dict:
    """Extrai JSON de uma resposta que pode vir cercada por markdown/texto"""
    texto = texto.strip()

    if texto.startswith("```"):
        partes = texto.split("```")
        texto = partes[1] if len(partes) > 1 else texto
        if texto.lower().startswith("json"):
            texto = texto[4:]
        texto = texto.strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fim = texto.rfind("}")
        if inicio != -1 and fim != -1 and fim > inicio:
            return json.loads(texto[inicio:fim + 1])
        raise


class ProvedorNvidiaNIM:
    """Chama modelos via NVIDIA NIM usando o SDK OpenAI-compatível"""

    nome = "nvidia_nim"

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ErroProvedorIA("Pacote 'openai' não instalado") from e

        self.api_key = os.getenv("NVIDIA_NIM_API_KEY")
        self.base_url = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.model = os.getenv("NVIDIA_NIM_MODEL", "meta/llama3-70b-instruct")

        if not self.api_key:
            raise ErroProvedorIA("NVIDIA_NIM_API_KEY não configurada")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def gerar_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Você retorna exclusivamente JSON válido, sem markdown e sem texto adicional.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        texto = response.choices[0].message.content.strip()
        return _extrair_json(texto)


class ProvedorAnthropic:
    """Chama modelos Claude via SDK oficial da Anthropic (fallback)"""

    nome = "anthropic"

    def __init__(self):
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise ErroProvedorIA("Pacote 'anthropic' não instalado") from e

        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        if not self.api_key:
            raise ErroProvedorIA("ANTHROPIC_API_KEY não configurada")

        self.client = Anthropic(api_key=self.api_key)

    def gerar_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = response.content[0].text.strip()
        return _extrair_json(texto)


class ProvedorOllama:
    """Chama um modelo local via Ollama (fallback de desenvolvimento, opcional)"""

    nome = "ollama"

    def __init__(self):
        import requests

        self._requests = requests
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        self.api_endpoint = f"{self.ollama_url}/api/generate"

        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if resp.status_code != 200:
                raise ErroProvedorIA("Ollama respondeu com erro")
        except ErroProvedorIA:
            raise
        except Exception as e:
            raise ErroProvedorIA(f"Ollama local não disponível em {self.ollama_url}: {e}") from e

    def gerar_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        response = self._requests.post(
            self.api_endpoint,
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        texto = response.json()["response"].strip()
        return _extrair_json(texto)


_PROVEDORES = {
    "nvidia_nim": ProvedorNvidiaNIM,
    "anthropic": ProvedorAnthropic,
    "ollama": ProvedorOllama,
}

_ORDEM_PADRAO = ["nvidia_nim", "anthropic", "ollama"]


class AIProvider:
    """
    Orquestra chamadas a múltiplos provedores de IA com fallback automático.

    Ordem de tentativa: AI_PROVIDER (preferido) primeiro, depois os demais
    da _ORDEM_PADRAO. Pode ser sobrescrita explicitamente via
    AI_PROVIDER_FALLBACK_ORDER="nvidia_nim,anthropic,ollama".
    """

    def __init__(self):
        preferido = os.getenv("AI_PROVIDER", "nvidia_nim").strip().lower()
        ordem_env = os.getenv("AI_PROVIDER_FALLBACK_ORDER")

        if ordem_env:
            ordem = [p.strip().lower() for p in ordem_env.split(",") if p.strip()]
        else:
            ordem = [preferido] + [p for p in _ORDEM_PADRAO if p != preferido]

        self.ordem = [p for p in ordem if p in _PROVEDORES]
        if not self.ordem:
            raise ErroProvedorIA(f"Nenhum provedor válido na ordem configurada: {ordem}")

        self._instancias_cache = {}
        self._ativo_nome: Optional[str] = None

    def _obter_instancia(self, nome: str):
        if nome not in self._instancias_cache:
            self._instancias_cache[nome] = _PROVEDORES[nome]()
        return self._instancias_cache[nome]

    def gerar_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        """
        Gera um JSON a partir do prompt, tentando cada provedor da cadeia
        em ordem até um funcionar.
        """
        erros = []
        for nome in self.ordem:
            try:
                provedor = self._obter_instancia(nome)
                resultado = provedor.gerar_json(prompt, max_tokens=max_tokens)
                self._ativo_nome = nome
                return resultado
            except Exception as e:
                erros.append(f"{nome}: {e}")
                continue

        raise ErroProvedorIA(
            "Nenhum provedor de IA disponível. Tentativas:\n" + "\n".join(erros)
        )

    @property
    def provedor_ativo(self) -> Optional[str]:
        """Nome do último provedor que respondeu com sucesso"""
        return self._ativo_nome


_instancia_global: Optional[AIProvider] = None


def obter_ai_provider() -> AIProvider:
    """Retorna a instância singleton do AIProvider"""
    global _instancia_global
    if _instancia_global is None:
        _instancia_global = AIProvider()
    return _instancia_global
