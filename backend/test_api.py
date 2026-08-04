#!/usr/bin/env python3
"""
Testes da API — FastAPI TestClient, sem servidor externo e sem IA real.

Substitui a versão anterior, que era um script manual apontando pra
http://localhost:8000 e exigia `python app.py` rodando em outro terminal.
Além de não rodar em CI, aquela versão estava quebrada: nunca enviava o
header `X-API-Key`, que passou a ser obrigatório em /api/v1/generate-site
(app.py -> Depends(verificar_api_key)) — ou seja, falharia 100% das vezes
mesmo com o servidor de pé.

Determinismo: nada aqui toca rede, disco de produção ou banco.
  - WEBHOOK_API_KEY é fixada ANTES do import de `app`, porque auth.py lê a
    variável no import (auth.py:19) — definir depois não teria efeito.
  - DATABASE_URL é removida: db.py deixa `engine = None` e nada conecta.
  - O agente de IA é substituído por um dublê que devolve um config real
    (o site-config.json versionado na raiz, que passa no ValidadorSchema).
  - `salvar_arquivo=False` nos payloads, pra não disparar a background task
    que escreve arquivo.
  - TestClient é usado SEM context manager de propósito: assim o lifespan
    não roda e o shutdown não chama metricas.salvar_metricas(), que
    escreveria em disco.

Uso: pytest backend/test_api.py   (ou via python backend/qa.py)
"""

import json
import os
import sys
from pathlib import Path

CHAVE_TESTE = "chave-de-teste-nao-usada-em-producao"

# Ordem importa: estas duas linhas precisam vir antes de importar `app`.
os.environ["WEBHOOK_API_KEY"] = CHAVE_TESTE
os.environ.pop("DATABASE_URL", None)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app

CAMINHO_CONFIG_REAL = Path(__file__).resolve().parent.parent / "site-config.json"


class AgenteDuble:
    """Dublê do AgenteConstrutor: mesma assinatura, zero chamada de IA.

    Devolve uma cópia de um site-config.json real (versionado no repo), com
    o nome da empresa trocado — assim o teste exercita o caminho de
    validação de schema de verdade, sem inventar um config sintético que
    poderia divergir do schema quando ele mudar.
    """

    def __init__(self, config_base: dict):
        self._config_base = config_base
        self.chamadas: list[tuple] = []

    def gerar_config_site(self, nome_empresa: str, nicho: str, cor_preferida=None) -> dict:
        self.chamadas.append((nome_empresa, nicho, cor_preferida))
        config = json.loads(json.dumps(self._config_base))
        config["company"]["name"] = nome_empresa
        return config


@pytest.fixture(scope="session")
def config_real() -> dict:
    with CAMINHO_CONFIG_REAL.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def agente(monkeypatch, config_real) -> AgenteDuble:
    """Instala o dublê no lugar do agente global de app.py."""
    duble = AgenteDuble(config_real)
    monkeypatch.setattr(app_module, "agente", duble)
    return duble


@pytest.fixture
def sem_agente(monkeypatch) -> None:
    """Simula a API subindo sem conseguir inicializar o agente."""
    monkeypatch.setattr(app_module, "agente", None)


def payload(**overrides) -> dict:
    base = {
        "nome_empresa": "Tech Solutions",
        "nicho": "Desenvolvimento de Software",
        "cor_preferida": "#4F46E5",
        "salvar_arquivo": False,
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------
# Rotas informativas
# --------------------------------------------------------------------------

def test_root_responde_com_indice_de_endpoints(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"].startswith("Fábrica de Sites")
    assert "endpoints" in corpo


def test_health_saudavel_quando_agente_ativo(client, agente):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "healthy"
    assert corpo["agente_ativo"] is True


def test_health_degradado_quando_agente_ausente(client, sem_agente):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "degraded"
    assert corpo["agente_ativo"] is False


def test_metrics_responde(client):
    resposta = client.get("/api/v1/metrics")
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), dict)


# --------------------------------------------------------------------------
# Proteção por API key — o buraco que a versão anterior deste arquivo não via
# --------------------------------------------------------------------------

def test_generate_sem_api_key_recusa(client, agente):
    resposta = client.post("/api/v1/generate-site", json=payload())
    assert resposta.status_code == 401
    assert not agente.chamadas, "não pode chamar a IA antes de autenticar"


def test_generate_com_api_key_errada_recusa(client, agente):
    resposta = client.post(
        "/api/v1/generate-site",
        json=payload(),
        headers={"X-API-Key": "chave-errada"},
    )
    assert resposta.status_code == 401
    assert not agente.chamadas


# --------------------------------------------------------------------------
# Geração
# --------------------------------------------------------------------------

def test_generate_com_api_key_valida_gera_config(client, agente):
    resposta = client.post(
        "/api/v1/generate-site",
        json=payload(nome_empresa="Padaria Sabor Dourado"),
        headers={"X-API-Key": CHAVE_TESTE},
    )
    assert resposta.status_code == 200, resposta.text

    corpo = resposta.json()
    assert corpo["status"] == "success"
    assert corpo["data"]["company"]["name"] == "Padaria Sabor Dourado"
    assert corpo["tempo_geracao_segundos"] >= 0

    # O endpoint precisa repassar exatamente o que recebeu, sem reescrever.
    assert agente.chamadas == [("Padaria Sabor Dourado", "Desenvolvimento de Software", "#4f46e5")]


def test_generate_sem_agente_responde_indisponivel(client, sem_agente):
    resposta = client.post(
        "/api/v1/generate-site",
        json=payload(),
        headers={"X-API-Key": CHAVE_TESTE},
    )
    assert resposta.status_code == 503


def test_generate_propaga_erro_do_agente_como_500(client, agente, monkeypatch):
    def explodir(*_args, **_kwargs):
        raise RuntimeError("provedor de IA fora do ar")

    monkeypatch.setattr(agente, "gerar_config_site", explodir)
    resposta = client.post(
        "/api/v1/generate-site",
        json=payload(),
        headers={"X-API-Key": CHAVE_TESTE},
    )
    assert resposta.status_code == 500


# --------------------------------------------------------------------------
# Validação de payload (Pydantic) — não deve nem chegar no agente
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "invalido, motivo",
    [
        ({"nome_empresa": "X"}, "nome com menos de 2 caracteres"),
        ({"nicho": "ab"}, "nicho com menos de 3 caracteres"),
        ({"cor_preferida": "azul"}, "cor fora do formato #RRGGBB"),
        ({"cor_preferida": "#GGGGGG"}, "hex com caracteres inválidos"),
        ({"nome_empresa": "N" * 101}, "nome acima de 100 caracteres"),
    ],
)
def test_generate_rejeita_payload_invalido(client, agente, invalido, motivo):
    resposta = client.post(
        "/api/v1/generate-site",
        json=payload(**invalido),
        headers={"X-API-Key": CHAVE_TESTE},
    )
    assert resposta.status_code == 422, f"deveria rejeitar: {motivo}"
    assert not agente.chamadas, f"payload inválido chegou no agente: {motivo}"


def test_generate_normaliza_cor_para_minusculo(client, agente):
    resposta = client.post(
        "/api/v1/generate-site",
        json=payload(cor_preferida="#4F46E5"),
        headers={"X-API-Key": CHAVE_TESTE},
    )
    assert resposta.status_code == 200
    _, _, cor = agente.chamadas[0]
    assert cor == "#4f46e5"
