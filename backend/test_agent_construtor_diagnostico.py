#!/usr/bin/env python3
"""
Testa o parâmetro opcional diagnostico_tentativas de
AgenteConstrutor.gerar_config_site() -- instrumentação pedida pra medir,
por tentativa, se a geração passou/falhou e por qual motivo, sem mudar
nenhum comportamento existente (backward-compatible: omitir o parâmetro
preserva 100% do comportamento atual).

Não faz chamada de IA real: self.ai é substituído por um dublê que devolve
uma sequência pré-definida de respostas, uma por chamada.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from agent_construtor import AgenteConstrutor


def _config_valido_minimo(nome_empresa="Empresa Teste"):
    """Config que passa ValidadorSchema.validar_json sem qualquer autocorreção."""
    return {
        "metadata": {
            "siteTitle": "Empresa Teste - Serviços de qualidade",
            "siteDescription": "A melhor empresa da região, com anos de experiência no mercado local.",
            "favicon": "🚀",
            "keywords": ["empresa", "teste", "servico"],
        },
        "company": {
            "name": nome_empresa,
            "tagline": "Excelência em tudo que fazemos",
            "description": "Somos uma empresa dedicada a oferecer o melhor serviço possível pros nossos clientes.",
            "logo": "",
        },
        "colors": {
            "primary": "#6366f1", "primaryDark": "#4f46e5", "secondary": "#ec4899",
            "accent": "#f59e0b", "background": "#ffffff", "text": "#1f2937",
            "textLight": "#6b7280", "border": "#e5e7eb",
        },
        "typography": {"fontPair": "modern"},
        "hero": {
            "title": "Bem-vindo à Empresa Teste, referência no setor",
            "subtitle": "Oferecemos soluções completas e personalizadas para você",
            "ctaText": "Fale conosco agora",
            "ctaLink": "#contato",
            "backgroundImage": "",
            "enabled": True,
        },
        "sections": [
            {"id": "sobre", "type": "content", "title": "Sobre nós", "subtitle": "Nossa história",
             "content": "Fundada com o objetivo de atender bem cada cliente, crescemos com dedicação.",
             "image": "", "enabled": True},
        ],
        "services": [
            {"id": 1, "title": "Serviço especializado A", "description": "Atendimento completo e personalizado pro seu caso.",
             "icon": "⚡", "features": ["Rápido", "Confiável", "Acessível"], "enabled": True},
        ],
        "features": [
            {"id": 1, "title": "Equipe qualificada", "description": "Profissionais com anos de experiência prática.", "icon": "⭐", "enabled": True},
            {"id": 2, "title": "Atendimento ágil", "description": "Resposta rápida pra todas as suas demandas.", "icon": "✅", "enabled": True},
            {"id": 3, "title": "Preço justo", "description": "Valores competitivos sem abrir mão da qualidade.", "icon": "🎯", "enabled": True},
        ],
        "testimonials": [],
        "faq": [
            {"id": 1, "question": "Como faço pra agendar um horário?", "answer": "Basta entrar em contato pelo WhatsApp e escolher o melhor horário.", "enabled": True},
            {"id": 2, "question": "Quais formas de pagamento são aceitas?", "answer": "Aceitamos PIX, cartão e dinheiro.", "enabled": True},
            {"id": 3, "question": "Vocês atendem fora do horário comercial?", "answer": "Sim, temos horários estendidos mediante agendamento prévio.", "enabled": True},
        ],
        "contact": {"email": None, "phone": "+5511987654321", "whatsapp": "+5511987654321", "address": None, "social": {}},
        "cta": {"title": "Pronto pra começar?", "description": "Entre em contato e peça seu orçamento sem compromisso.",
                "buttonText": "Solicitar orçamento", "buttonLink": "mailto:contato@empresateste.com", "enabled": True},
    }


def _config_invalido_faq_curto():
    """Config com FAQ abaixo do mínimo (2 ao invés de 3) -- falha estrutural pura, sem relação com TXT-01/04."""
    config = _config_valido_minimo()
    config["faq"] = config["faq"][:2]
    return config


class _ProvedorFake:
    """
    Dublê de AIProvider: devolve uma resposta pré-definida por chamada, na
    ordem dada -- mas só para a geração do site-config. gerar_config_site()
    também chama self.ai.gerar_json() por baixo via gerar_paleta_cores()
    (uma chamada extra, por tentativa, ANTES da chamada principal) -- sem
    distinguir isso, a fila de respostas esvaziava cedo demais (a
    respostas.pop(0) da paleta consumia o item destinado ao site-config).
    Detecta a chamada de paleta pelo prompt (só ela menciona "designer de
    cores") e devolve uma paleta fixa válida, sem consumir a fila.
    """

    ordem = ["fake"]

    def __init__(self, respostas):
        self._respostas = list(respostas)
        self.provedor_ativo = "fake"

    def gerar_json(self, prompt, max_tokens=4096):
        if "designer de cores" in prompt:
            return {
                "primary": "#6366f1", "primaryDark": "#4f46e5", "secondary": "#ec4899",
                "accent": "#f59e0b", "background": "#ffffff", "text": "#1f2937",
                "textLight": "#6b7280", "border": "#e5e7eb",
            }
        return self._respostas.pop(0)


def _agente_com_dublê(respostas) -> AgenteConstrutor:
    """Cria um AgenteConstrutor sem passar pelo __init__ real (evita precisar de credencial de IA)."""
    agente = AgenteConstrutor.__new__(AgenteConstrutor)
    agente.ai = _ProvedorFake(respostas)
    return agente


class TestDiagnosticoTentativas(unittest.TestCase):
    def test_parametro_omitido_nao_muda_comportamento_existente(self):
        """Backward-compat: sem diagnostico_tentativas, comportamento é idêntico ao anterior."""
        agente = _agente_com_dublê([_config_valido_minimo()])
        resultado = agente.gerar_config_site("Empresa Teste", "nicho de teste")
        self.assertEqual(resultado["company"]["name"], "Empresa Teste")

    def test_sucesso_na_primeira_tentativa_registra_uma_entrada(self):
        agente = _agente_com_dublê([_config_valido_minimo()])
        diagnostico = []
        agente.gerar_config_site("Empresa Teste", "nicho", diagnostico_tentativas=diagnostico)

        self.assertEqual(len(diagnostico), 1)
        self.assertEqual(diagnostico[0]["tentativa"], 1)
        self.assertTrue(diagnostico[0]["sucesso"])
        self.assertIsNone(diagnostico[0]["erro"])
        self.assertIn("tempo_segundos", diagnostico[0])
        self.assertGreaterEqual(diagnostico[0]["tempo_segundos"], 0)

    def test_falha_depois_sucesso_registra_duas_entradas_na_ordem(self):
        agente = _agente_com_dublê([_config_invalido_faq_curto(), _config_valido_minimo()])
        diagnostico = []
        agente.gerar_config_site("Empresa Teste", "nicho", diagnostico_tentativas=diagnostico)

        self.assertEqual(len(diagnostico), 2)
        self.assertEqual(diagnostico[0]["tentativa"], 1)
        self.assertFalse(diagnostico[0]["sucesso"])
        self.assertIn("faq", diagnostico[0]["erro"].lower())
        self.assertEqual(diagnostico[1]["tentativa"], 2)
        self.assertTrue(diagnostico[1]["sucesso"])

    def test_todas_as_tentativas_falham_registra_todas_e_propaga_excecao(self):
        agente = _agente_com_dublê([_config_invalido_faq_curto()] * 3)
        diagnostico = []
        with self.assertRaises(ValueError):
            agente.gerar_config_site("Empresa Teste", "nicho", diagnostico_tentativas=diagnostico)

        self.assertEqual(len(diagnostico), 3)
        self.assertTrue(all(not d["sucesso"] for d in diagnostico))
        self.assertEqual([d["tentativa"] for d in diagnostico], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
