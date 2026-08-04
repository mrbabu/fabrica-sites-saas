#!/usr/bin/env python3
"""
Regressão funcional do pipeline pós-geração: snapshot + invariantes.

O que isto protege: tudo que acontece DEPOIS que o modelo responde —
_autocorrigir(), _preencher_fallbacks(), categorização de imagem por nicho
e a limpeza anti-fabricação. Essa camada concentra o comportamento real do
produto e não tinha nenhuma rede de proteção: dá pra mudar niches.json ou
um fallback e não quebrar teste nenhum, mesmo alterando todo site gerado.

O que isto NÃO protege, e não dá pra fingir que protege: a cor primária
final. `colors` é campo obrigatório de _validar_schema (agent_construtor.py:
623), ou seja, vem do modelo. A cor derivada do nicho entra só no PROMPT
(agent_construtor.py:204) — é instrução, não garantia. Se o modelo devolver
outra cor, nenhum código corrige. A derivação em si (obter_cor_primaria) é
coberta em test_image_utils.py; o que falta é enforcement no config final.

Por que NÃO existe camada de normalização: foi medido, não presumido. Com
o provedor dublado, duas gerações do mesmo nicho saem byte a byte
idênticas — zero campos variáveis, nenhum timestamp, id ou UUID neste
schema. Um normalizador aqui seria código morto que esconderia regressão
no dia em que algum campo começasse a variar de verdade.

A resposta do "modelo" vem de snapshots/_resposta_modelo.json, congelada de
propósito: se viesse do site-config.json da raiz, uma edição de produção
naquele arquivo faria os 12 snapshots quebrarem sem nenhuma mudança de
comportamento.

A fixture é enxuta de propósito: omite backgroundImage, logo, ogImage,
fontPair, icon, whatsapp e address. São exatamente os campos que o pipeline
deriva — com uma fixture completa, os fallbacks nunca rodam e os 12
snapshots saem idênticos, congelando o eco da fixture em vez do
comportamento (foi o primeiro resultado desta suíte, antes da correção).

Os nichos foram escolhidos pra exercitar as áreas mexidas recentemente:
categoria composta (education_school__infantil, ice_cream_shop__acai) e
categoria nova (optical_shop). 12 nichos cobrem 10 categorias distintas.

Atualizar snapshots depois de uma mudança INTENCIONAL:
    ATUALIZAR_SNAPSHOTS=1 pytest backend/test_snapshots.py
    (e revisar o git diff antes de commitar — é o ponto do snapshot)

Uso: pytest backend/test_snapshots.py   (ou via python backend/qa.py)
"""

import contextlib
import io
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

import agent_construtor
from agent_construtor import AgenteConstrutor

PASTA_SNAPSHOTS = Path(__file__).resolve().parent / "snapshots"
CAMINHO_FIXTURE = PASTA_SNAPSHOTS / "_resposta_modelo.json"

ATUALIZANDO = os.getenv("ATUALIZAR_SNAPSHOTS", "").strip().lower() in ("1", "true", "sim")

def imagens_da_categoria(categoria: str) -> list[str]:
    """Dublê do banco de imagens. A categoria vai DENTRO da URL de propósito:
    assim o snapshot registra em que categoria cada nicho caiu, e uma
    regressão em niches.json/mapear_categoria aparece no diff em vez de
    passar despercebida."""
    return [f"https://imagem.test/{categoria}/{i}.jpg" for i in range(6)]

# (slug do arquivo, nome da empresa, nicho). Sem cor: exercita de propósito a
# cor derivada do nicho, que é o caminho de produção desde o commit 4f54580.
NICHOS = [
    ("eletricista", "Eletricista Silva", "Eletricista"),
    ("encanador", "Encanador Express", "Encanador"),
    ("dentista", "Consultório Odontológico", "Odontologia"),
    ("restaurante", "Restaurante Gourmet", "Restaurante"),
    ("pizzaria", "Pizzaria do João", "Pizzaria"),
    ("salao-beleza", "Salão de Beleza Maria", "Salão de Beleza"),
    ("academia", "Academia Power", "Academia de Ginástica"),
    ("advogado", "Escritório de Advocacia", "Advocacia Geral"),
    ("pet-shop", "Pet Shop Amigos", "Pet Shop"),
    ("escola-infantil", "Escola Pequeno Mundo", "Escola Infantil"),
    ("otica", "Ótica Visão Clara", "Ótica"),
    ("acaiteria", "Açaí do Ponto", "Açaiteria"),
]


class ProviderDuble:
    """Mesmo contrato do AIProvider: paleta em 512 tokens, config em 4096.

    A paleta ecoa a cor que veio no prompt, como o modelo real faz (a regra
    "primary: a cor fornecida" está no prompt, agent_construtor.py:97).
    Devolver paleta constante mascararia a cor derivada do nicho.
    """

    def __init__(self, resposta: dict):
        self._resposta = resposta
        self.ordem = ["duble"]
        self.provedor_ativo = "duble"

    def gerar_json(self, prompt, max_tokens=4096):
        if max_tokens == 512:
            achado = re.search(r"#[0-9a-fA-F]{6}", prompt)
            primaria = achado.group(0).lower() if achado else "#000000"
            return {
                "primary": primaria,
                "primaryDark": "#333333",
                "secondary": "#1e88d2",
                "accent": "#d2a91e",
                "background": "#ffffff",
                "text": "#1f2937",
                "textLight": "#6b7280",
                "border": "#e5e7eb",
            }
        return json.loads(json.dumps(self._resposta))


@pytest.fixture(scope="module")
def resposta_modelo() -> dict:
    with CAMINHO_FIXTURE.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def gerar(monkeypatch, resposta_modelo):
    """Devolve uma função que gera o config de um nicho, sem rede."""
    monkeypatch.setattr(agent_construtor, "obter_ai_provider", lambda: ProviderDuble(resposta_modelo))
    monkeypatch.setattr(agent_construtor, "obter_imagens_categoria", imagens_da_categoria)

    def _gerar(nome_empresa: str, nicho: str) -> dict:
        # O agente é verboso; o ruído não ajuda no relatório do pytest.
        with contextlib.redirect_stdout(io.StringIO()):
            agente = AgenteConstrutor()
            return agente.gerar_config_site(
                nome_empresa, nicho, whatsapp_contato="+5527999990000"
            )

    return _gerar


def serializar(config: dict) -> str:
    return json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


# ==========================================================================
# Camada 2 — snapshot canônico
# ==========================================================================

@pytest.mark.parametrize("slug, nome_empresa, nicho", NICHOS, ids=[n[0] for n in NICHOS])
def test_snapshot_do_config_gerado(gerar, slug, nome_empresa, nicho):
    atual = serializar(gerar(nome_empresa, nicho))
    caminho = PASTA_SNAPSHOTS / f"{slug}.json"

    if ATUALIZANDO or not caminho.exists():
        caminho.write_text(atual, encoding="utf-8")
        if not ATUALIZANDO:
            pytest.fail(
                f"Snapshot {caminho.name} não existia e foi criado agora. "
                f"Revise o conteúdo e rode de novo pra confirmar."
            )
        return

    esperado = caminho.read_text(encoding="utf-8")
    assert atual == esperado, (
        f"O config gerado para {nicho!r} mudou.\n"
        f"Se a mudança for intencional: ATUALIZAR_SNAPSHOTS=1 pytest backend/test_snapshots.py\n"
        f"e revise o git diff de {caminho.name} antes de commitar."
    )


def test_nichos_diferentes_geram_configs_diferentes(gerar):
    """Sanidade do próprio snapshot: se o pipeline ignorasse o nicho, os 12
    snapshots seriam idênticos e passariam sem testar nada."""
    a = gerar("Consultório Odontológico", "Odontologia")
    b = gerar("Pizzaria do João", "Pizzaria")
    assert serializar(a) != serializar(b), "o nicho não está influenciando o config gerado"


# ==========================================================================
# Camada 3 — invariantes de negócio (falha nomeada, não diff gigante)
# ==========================================================================

@pytest.mark.parametrize("slug, nome_empresa, nicho", NICHOS, ids=[n[0] for n in NICHOS])
def test_invariantes_de_negocio(gerar, slug, nome_empresa, nicho):
    config = gerar(nome_empresa, nicho)

    # NÃO dá pra assertar company.name == nome_empresa aqui: o pipeline não
    # força esse campo, ele confia no que o modelo devolveu (achado desta
    # suíte). Se o modelo trocar o nome da empresa, nenhum código corrige —
    # a verificação disso pertence ao benchmark com LLM real.
    assert config["company"]["name"], "empresa sem nome"
    assert config["metadata"]["siteTitle"], "site sem título não indexa"
    assert config["metadata"]["siteDescription"], "site sem description não indexa"

    assert config["hero"]["title"], "hero sem título"
    assert config["hero"]["ctaText"], "hero sem chamada pra ação não converte"
    assert config["hero"]["backgroundImage"], "hero sem imagem de fundo"

    assert len(config["services"]) >= 3, "menos de 3 serviços deixa a página vazia"
    assert len(config["features"]) >= 3, "schema exige no mínimo 3 diferenciais"
    assert len(config["faq"]) >= 3, "schema exige no mínimo 3 perguntas"

    assert all(s["icon"] for s in config["services"]), "serviço sem ícone quebra o layout"

    cor = config["colors"]["primary"]
    assert cor.startswith("#") and len(cor) == 7, f"cor primária inválida: {cor!r}"

    assert config["typography"]["fontPair"], "fontPair vazio cai no fallback de fonte no index.html"
    assert config["contact"]["whatsapp"], "sem WhatsApp o lead não tem como fechar"


@pytest.mark.parametrize("slug, nome_empresa, nicho", NICHOS, ids=[n[0] for n in NICHOS])
def test_nao_fabrica_dados_de_contato(gerar, slug, nome_empresa, nicho):
    """Guardrail anti-fabricação: o agente não pode inventar e-mail ou redes
    sociais do cliente (regra explícita no prompt, agent_construtor.py:352)."""
    config = gerar(nome_empresa, nicho)

    assert not config["contact"].get("social"), "redes sociais precisam vir vazias, nunca inventadas"
    assert not config.get("testimonials"), "depoimentos não podem ser fabricados pela IA"
