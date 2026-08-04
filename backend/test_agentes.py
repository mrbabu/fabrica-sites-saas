#!/usr/bin/env python3
"""
Testes determinísticos do Agente Construtor e da cadeia de provedores de IA.

Substitui a versão anterior deste arquivo, que rodava 50 nichos contra um
LLM real e reportava taxa de sucesso. Aquilo é um *benchmark de qualidade
do modelo*, não um teste de regressão: lento, caro, dependente de rede e
não reprodutível. Foi preservado, sem perda de capacidade, em
`test_agentes_llm.py` (suíte lenta, opt-in) — este arquivo testa a lógica
que o projeto controla, e por isso pode rodar no gate de commit.

O que é dublado, e por quê:
  - Provedores de IA: `_PROVEDORES` de ai_provider.py é substituído por
    classes falsas. Nenhuma chamada de rede, nenhum SDK real.
  - `obter_imagens_categoria`: gerar_config_site() -> _preencher_fallbacks()
    consulta o Unsplash. Sem dublar isso, a suíte dependeria de rede e de
    rate limit (conta Demo, 50 req/hora).
  - AI_PROVIDER / AI_PROVIDER_FALLBACK_ORDER são limpas do ambiente em cada
    teste: ai_provider.py e agent_construtor.py chamam load_dotenv() no
    import, então um .env da máquina mudaria o resultado silenciosamente.

Uso: pytest backend/test_agentes.py   (ou via python backend/qa.py)
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

import agent_construtor
import ai_provider
from agent_construtor import MAX_TENTATIVAS_GERACAO, AgenteConstrutor
from ai_provider import _ORDEM_PADRAO, AIProvider, ErroProvedorIA

CAMINHO_CONFIG_REAL = Path(__file__).resolve().parent.parent / "site-config.json"

IMAGENS_FALSAS = [f"https://exemplo.test/foto-{i}.jpg" for i in range(1, 7)]


# ==========================================================================
# Infraestrutura de dublês
# ==========================================================================

def fabricar_provedor(resposta=None, erro=None, registro=None, nome=""):
    """Cria uma classe de provedor falsa compatível com _PROVEDORES.

    _PROVEDORES[nome]() é chamado sem argumentos, então a configuração
    precisa ser capturada por closure, não por parâmetro de __init__.
    """

    class ProvedorFalso:
        def __init__(self):
            if isinstance(erro, type) and issubclass(erro, Exception):
                # Falha já na construção (ex.: chave ausente) — o AIProvider
                # precisa tratar isso igual a falha de geração.
                raise erro(f"{nome}: indisponível")

        def gerar_json(self, prompt, max_tokens=4096):
            if registro is not None:
                registro.append(nome)
            if isinstance(erro, Exception):
                raise erro
            return resposta

    return ProvedorFalso


@pytest.fixture(autouse=True)
def ambiente_limpo(monkeypatch):
    """Neutraliza configuração de provedor vinda do ambiente/.env."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_PROVIDER_FALLBACK_ORDER", raising=False)


@pytest.fixture
def config_real() -> dict:
    with CAMINHO_CONFIG_REAL.open(encoding="utf-8") as f:
        return json.load(f)


# ==========================================================================
# Cadeia de provedores — a ordem e o fallback que a aplicação usa de fato
# ==========================================================================

def test_ordem_padrao_e_gemini_nim_anthropic_ollama():
    assert AIProvider().ordem == ["gemini", "nvidia_nim", "anthropic", "ollama"]
    assert _ORDEM_PADRAO == ["gemini", "nvidia_nim", "anthropic", "ollama"]


def test_ai_provider_preferido_vai_para_o_topo_sem_duplicar(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    ordem = AIProvider().ordem
    assert ordem[0] == "ollama"
    assert sorted(ordem) == sorted(_ORDEM_PADRAO), "nenhum provedor pode sumir ou duplicar"


def test_ordem_explicita_sobrescreve_o_padrao(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_FALLBACK_ORDER", "anthropic, ollama")
    assert AIProvider().ordem == ["anthropic", "ollama"]


def test_nomes_desconhecidos_sao_descartados(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_FALLBACK_ORDER", "provedor_que_nao_existe,ollama")
    assert AIProvider().ordem == ["ollama"]


def test_ordem_toda_invalida_levanta_erro(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_FALLBACK_ORDER", "inexistente_a,inexistente_b")
    with pytest.raises(ErroProvedorIA):
        AIProvider()


def test_fallback_pula_provedores_que_falham(monkeypatch):
    chamados: list[str] = []
    monkeypatch.setattr(ai_provider, "_PROVEDORES", {
        "gemini": fabricar_provedor(erro=RuntimeError("cota estourada"), registro=chamados, nome="gemini"),
        "nvidia_nim": fabricar_provedor(erro=ErroProvedorIA, nome="nvidia_nim"),  # falha no __init__
        "anthropic": fabricar_provedor(resposta={"ok": True}, registro=chamados, nome="anthropic"),
        "ollama": fabricar_provedor(resposta={"nao": "deveria chegar aqui"}, registro=chamados, nome="ollama"),
    })

    provedor = AIProvider()
    assert provedor.provedor_ativo is None, "ninguém respondeu ainda"

    assert provedor.gerar_json("prompt") == {"ok": True}
    assert provedor.provedor_ativo == "anthropic"
    assert chamados == ["gemini", "anthropic"], "ollama não podia ser chamado após sucesso"


def test_todos_os_provedores_falhando_levanta_erro_com_diagnostico(monkeypatch):
    monkeypatch.setattr(ai_provider, "_PROVEDORES", {
        nome: fabricar_provedor(erro=RuntimeError(f"falha de {nome}"), nome=nome)
        for nome in _ORDEM_PADRAO
    })

    with pytest.raises(ErroProvedorIA) as ctx:
        AIProvider().gerar_json("prompt")

    mensagem = str(ctx.value)
    for nome in _ORDEM_PADRAO:
        assert nome in mensagem, f"o diagnóstico precisa dizer que {nome} foi tentado"


# ==========================================================================
# Agente Construtor — pipeline de geração, sem IA e sem rede
# ==========================================================================

# Paleta que o dublê devolve no lugar da chamada de IA de cores.
PALETA_FALSA = {
    "primary": "#d2691e",
    "primaryDark": "#a85417",
    "secondary": "#1e88d2",
    "accent": "#d2a91e",
    "background": "#ffffff",
    "text": "#1f2937",
    "textLight": "#6b7280",
    "border": "#e5e7eb",
}


class ProviderDuble:
    """Dublê do AIProvider, na interface que agent_construtor consome.

    Atenção ao contrato real: gerar_config_site() faz DUAS chamadas de IA
    distintas quando recebe cor — primeiro a paleta complementar
    (max_tokens=512, agent_construtor.py:109) e depois o config do site
    (max_tokens=4096). Contar as duas juntas mediria a coisa errada nos
    testes de retry, então o dublê separa por max_tokens.
    """

    def __init__(self, respostas: list[dict]):
        self._respostas = list(respostas)
        self._ultima: dict = {}
        self.ordem = ["duble"]
        self.provedor_ativo = "duble"
        self.chamadas_config = 0
        self.chamadas_paleta = 0

    def gerar_json(self, prompt, max_tokens=4096):
        if max_tokens == 512:
            self.chamadas_paleta += 1
            return dict(PALETA_FALSA)

        self.chamadas_config += 1
        if self._respostas:
            self._ultima = self._respostas.pop(0)
        return json.loads(json.dumps(self._ultima))


@pytest.fixture
def montar_agente(monkeypatch):
    """Devolve uma factory que instala o dublê e entrega o agente pronto."""

    def _montar(respostas: list[dict]) -> tuple[AgenteConstrutor, ProviderDuble]:
        duble = ProviderDuble(respostas)
        monkeypatch.setattr(agent_construtor, "obter_ai_provider", lambda: duble)
        # Sem isto, _preencher_fallbacks consulta o Unsplash de verdade.
        monkeypatch.setattr(
            agent_construtor, "obter_imagens_categoria", lambda categoria: list(IMAGENS_FALSAS)
        )
        return AgenteConstrutor(), duble

    return _montar


def test_gera_config_valido_na_primeira_tentativa(montar_agente, config_real):
    agente, duble = montar_agente([config_real])

    config = agente.gerar_config_site("Padaria Sabor Dourado", "Padaria Artesanal", "#d2691e")

    assert config["company"]["name"]
    assert duble.chamadas_config == 1, "config válido não pode gastar tentativa extra"


def test_retry_reaproveita_tentativas_ate_config_valido(montar_agente, config_real):
    invalido = json.loads(json.dumps(config_real))
    # Precisa ser um campo que NENHUMA etapa determinística reconstrói:
    # _autocorrigir() conserta siteTitle/icon/fontPair e _preencher_fallbacks()
    # reescreve metadata inteiro, então quebrar esses nunca chega no validador.
    # faq exige min_items=3 (schema_validator.py:317) e passa intacto.
    invalido["faq"] = invalido["faq"][:1]

    agente, duble = montar_agente([invalido, invalido, config_real])

    config = agente.gerar_config_site("Clínica Central", "Clínica Médica", "#06a77d")

    assert config["company"]["name"]
    assert duble.chamadas_config == 3, "deveria ter tentado de novo até o config válido"


def test_retry_desiste_apos_o_maximo_de_tentativas(montar_agente, config_real):
    invalido = json.loads(json.dumps(config_real))
    invalido["faq"] = invalido["faq"][:1]

    agente, duble = montar_agente([invalido])

    with pytest.raises(ValueError, match="Schema inválido"):
        agente.gerar_config_site("Loja Teste", "Loja de Roupas", "#ff1493")

    assert duble.chamadas_config == MAX_TENTATIVAS_GERACAO


def test_autocorrige_icon_invalido_sem_gastar_tentativa(montar_agente, config_real):
    quebrado = json.loads(json.dumps(config_real))
    for servico in quebrado.get("services", []):
        servico["icon"] = ""

    agente, duble = montar_agente([quebrado])

    config = agente.gerar_config_site("Pet Shop Amigos", "Pet Shop", "#ff85c0")

    assert all(s["icon"] for s in config["services"]), "icon vazio deveria ter sido autocorrigido"
    assert duble.chamadas_config == 1, "autocorreção é determinística, não pode custar nova chamada"


def test_cor_ausente_e_derivada_do_nicho(montar_agente, config_real):
    """Regressão do commit 4f54580: cor_primaria virou opcional e é resolvida
    a partir da categoria do nicho quando não vem no payload."""
    agente, _ = montar_agente([config_real])

    config = agente.gerar_config_site("Clínica Central", "Clínica Médica")

    assert config["colors"]["primary"].startswith("#")
    assert len(config["colors"]["primary"]) == 7


def test_nao_toca_a_rede_de_imagens(montar_agente, config_real, monkeypatch):
    """Garante que o dublê de imagens está mesmo interceptando: se o código
    passar a chamar a função real, este teste quebra em vez de fazer HTTP."""
    def explodir(*_a, **_kw):
        raise AssertionError("gerar_config_site tentou buscar imagem de verdade")

    agente, _ = montar_agente([config_real])
    monkeypatch.setattr(agent_construtor, "obter_imagens_categoria", explodir)

    with pytest.raises(AssertionError):
        agente.gerar_config_site("Pizzaria do João", "Pizzaria", "#ea580c")
