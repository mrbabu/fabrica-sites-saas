#!/usr/bin/env python3
"""
Provedor de IA - Fábrica de Sites SaaS
Abstrai a chamada ao modelo de linguagem por trás de uma interface única
(gerar_json), com troca modular de fonte:

  1. Gemini (padrão)       - via SDK google-generativeai (Google AI Studio)
  2. NVIDIA NIM (fallback) - via SDK OpenAI-compatível
  3. Groq (fallback)       - via SDK OpenAI-compatível (infra LPU própria,
                             tier gratuito sem os timeouts do NIM gratuito)
  4. Anthropic (fallback)  - via SDK oficial
  5. Ollama local (fallback de dev, opcional) - via requests

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


def _extrair_uso_openai(response) -> Optional[dict]:
    """
    Extrai uso de tokens de uma resposta do SDK OpenAI-compatível
    (NVIDIA NIM/Groq -- mesmo formato de `response.usage`). None se a API
    não informar -- nunca estimado por aproximação.
    """
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    return {
        "prompt": usage.prompt_tokens,
        "completion": usage.completion_tokens,
        "total": usage.total_tokens,
    }


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
        self.model = os.getenv("NVIDIA_NIM_MODEL", "meta/llama-3.1-8b-instruct")
        self.ultimo_uso_tokens: Optional[dict] = None

        if not self.api_key:
            raise ErroProvedorIA("NVIDIA_NIM_API_KEY não configurada")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            # NVIDIA NIM gera o JSON completo do site (SEO, seções, serviços,
            # depoimentos, FAQ) em uma única resposta - 30s+max_retries=1 do
            # SDK estourava constantemente (~60-70s até desistir, sempre pelo
            # mesmo motivo: timeout, não erro real). max_retries=0 porque o
            # retry de verdade já é feito um nível acima, no fallback entre
            # provedores (gemini -> nvidia_nim -> anthropic -> ollama).
            timeout=float(os.getenv("NVIDIA_NIM_TIMEOUT", "60")),
            max_retries=0,
        )

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
        self.ultimo_uso_tokens = _extrair_uso_openai(response)
        texto = response.choices[0].message.content.strip()
        return _extrair_json(texto)


class ProvedorGroq:
    """
    Chama modelos via Groq usando o SDK OpenAI-compativel. Infra propria
    (LPU) com latencia muito baixa mesmo pra modelos grandes -- pensada
    como alternativa ao NVIDIA NIM quando o tier gratuito do NIM nao
    aguenta o prompt completo (ver relatorio_testes.json e memoria de
    2026-08-04: meta/llama-3.3-70b-instruct no NIM gratuito estourava com
    504 do proprio gateway deles, mesmo com timeout de 600s no client).
    """

    nome = "groq"

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ErroProvedorIA("Pacote 'openai' não instalado") from e

        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.ultimo_uso_tokens: Optional[dict] = None

        if not self.api_key:
            raise ErroProvedorIA("GROQ_API_KEY não configurada")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=float(os.getenv("GROQ_TIMEOUT", "60")),
            max_retries=0,
        )

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
        self.ultimo_uso_tokens = _extrair_uso_openai(response)
        texto = response.choices[0].message.content.strip()
        return _extrair_json(texto)


class ProvedorGemini:
    """Chama modelos Gemini via Google AI Studio (SDK google-generativeai)"""

    nome = "gemini"

    def __init__(self):
        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ErroProvedorIA("Pacote 'google-generativeai' não instalado") from e

        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        if not self.api_key:
            raise ErroProvedorIA("GEMINI_API_KEY não configurada")

        genai.configure(api_key=self.api_key)
        self._genai = genai
        self.client = genai.GenerativeModel(
            self.model_name,
            system_instruction="Você retorna exclusivamente JSON válido, sem markdown e sem texto adicional.",
        )

    def gerar_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        response = self.client.generate_content(
            prompt,
            generation_config=self._genai.GenerationConfig(
                response_mime_type="application/json",
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
            request_options={"timeout": 30},
        )
        texto = response.text.strip()
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
    """Chama um modelo local via Ollama (fallback de desenvolvimento, opcional).

    NÃO baixa modelos automaticamente. Se o modelo configurado não existir
    localmente, levanta ErroProvedorIA com instruções de instalação manual.
    """

    nome = "ollama"

    def __init__(self, _requests_module=None):
        if _requests_module is None:
            import requests as _requests_module
        self._requests = _requests_module

        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        self.api_endpoint = f"{self.ollama_url}/api/generate"
        self.ultimo_uso_tokens: Optional[dict] = None

        try:
            resp = self._requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if resp.status_code != 200:
                raise ErroProvedorIA("Ollama respondeu com erro")
        except ErroProvedorIA:
            raise
        except Exception as e:
            raise ErroProvedorIA(
                f"Ollama local não disponível em {self.ollama_url}: {e}"
            ) from e

        self._validar_modelo_local()

    def _validar_modelo_local(self) -> None:
        """Verifica se o modelo existe localmente antes de tentar usá-lo.

        O servidor Ollama baixa automaticamente modelos ausentes ao receber
        requisições em /api/generate. Para evitar downloads acidentais de
        vários GB, esta validação é feita explicitamente antes.
        """
        try:
            resp = self._requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            resp.raise_for_status()
            modelos = [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            # Se não conseguir listar, deixa o erro explodir na chamada real
            return

        if self.model in modelos:
            return

        # Normalizar nomes para comparação (llama3 vs llama3:latest)
        modelos_normalizados = {}
        for m in modelos:
            # "llama3:latest" -> "llama3", "llama3:8b" -> "llama3:8b"
            base = m.split(":")[0] if ":" in m else m
            modelos_normalizados.setdefault(base, []).append(m)

        modelo_base = self.model.split(":")[0] if ":" in self.model else self.model

        if modelo_base in modelos_normalizados:
            # Match por nome-base (ex.: configurado "llama3", instalado
            # "llama3:latest") é o mesmo modelo — resolve pra tag exata em
            # vez de barrar. Bug anterior: essa normalização era calculada
            # só pra compor a mensagem de erro, e o código levantava
            # ErroProvedorIA nos dois ramos (match ou não), inutilizando o
            # próprio propósito da normalização.
            self.model = modelos_normalizados[modelo_base][0]
            return

        disponiveis = ", ".join(modelos[:10]) if modelos else "(nenhum modelo instalado)"
        sugestao = (
            f"Modelo '{self.model}' não encontrado localmente.\n"
            f"Modelos disponíveis: {disponiveis}\n"
            f"Para instalar, execute manualmente: ollama pull {self.model}"
        )
        raise ErroProvedorIA(sugestao)

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
        resposta_json = response.json()

        # Ollama não usa a chave "usage" (formato OpenAI) -- devolve
        # prompt_eval_count/eval_count soltos no corpo, só quando
        # stream=False (nosso caso). Ausentes -> None, sem estimar.
        if "prompt_eval_count" in resposta_json and "eval_count" in resposta_json:
            prompt_tokens = resposta_json["prompt_eval_count"]
            completion_tokens = resposta_json["eval_count"]
            self.ultimo_uso_tokens = {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": prompt_tokens + completion_tokens,
            }
        else:
            self.ultimo_uso_tokens = None

        texto = resposta_json["response"].strip()
        return _extrair_json(texto)


_PROVEDORES = {
    "gemini": ProvedorGemini,
    "nvidia_nim": ProvedorNvidiaNIM,
    "groq": ProvedorGroq,
    "anthropic": ProvedorAnthropic,
    "ollama": ProvedorOllama,
}

_ORDEM_PADRAO = ["gemini", "nvidia_nim", "groq", "anthropic", "ollama"]


class AIProvider:
    """
    Orquestra chamadas a múltiplos provedores de IA com fallback automático.

    Ordem de tentativa: AI_PROVIDER (preferido) primeiro, depois os demais
    da _ORDEM_PADRAO. Pode ser sobrescrita explicitamente via
    AI_PROVIDER_FALLBACK_ORDER="nvidia_nim,anthropic,ollama".
    """

    def __init__(self):
        preferido = os.getenv("AI_PROVIDER", "gemini").strip().lower()
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

    @property
    def uso_tokens_ativo(self) -> Optional[dict]:
        """
        {"prompt", "completion", "total"} da última chamada bem-sucedida,
        ou None se o provedor ativo não informa uso de tokens (nunca
        estimado por aproximação -- ver _extrair_uso_openai).
        """
        if self._ativo_nome is None:
            return None
        instancia = self._instancias_cache.get(self._ativo_nome)
        return getattr(instancia, "ultimo_uso_tokens", None) if instancia else None


_instancia_global: Optional[AIProvider] = None


def obter_ai_provider() -> AIProvider:
    """Retorna a instância singleton do AIProvider"""
    global _instancia_global
    if _instancia_global is None:
        _instancia_global = AIProvider()
    return _instancia_global
