#!/usr/bin/env python3
"""
Repair Prompt localizado (RFC aprovada 2026-08-06, ver memória de projeto):
quando a única falha de validação é TXT-01 (duplicação de título/texto),
tenta reescrever SÓ o campo apontado pelo erro com uma chamada de IA
pequena e barata, em vez de descartar a geração inteira e gastar uma
tentativa completa do laço de retry.

Escopo aprovado: no máximo 1 chamada de reparo por tentativa, sem loop --
se falhar por qualquer motivo, cai pro fluxo normal de retry (regenera
tudo), nunca tenta reparo de novo pra essa mesma falha.

Reusa os dublês de test_agent_construtor_diagnostico.py (mesmo padrão:
self.ai substituído por uma fila de respostas pré-definidas, sem chamada
de IA real).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from agent_construtor import (
    AgenteConstrutor,
    _extrair_identificadores_duplicados,
    _localizar_item,
)
from test_agent_construtor_diagnostico import (
    _config_valido_minimo,
    _config_invalido_faq_curto,
    _agente_com_dublê,
)


def _config_com_titulo_duplicado():
    """2 services com o mesmo title -- dispara TXT-01 (Título duplicado)."""
    config = _config_valido_minimo()
    config["services"] = [
        {"id": 1, "title": "Atendimento especializado", "description": "Cuidamos de cada detalhe do seu caso com atenção.",
         "icon": "⚡", "features": ["Rápido"], "enabled": True},
        {"id": 2, "title": "Atendimento especializado", "description": "Suporte completo do início ao fim do processo.",
         "icon": "🎯", "features": ["Confiável"], "enabled": True},
    ]
    return config


class TestExtrairIdentificadoresDuplicados(unittest.TestCase):
    def test_extrai_os_dois_identificadores_de_titulo_duplicado(self):
        erro = "Título duplicado entre services[1].title e services[2].title (similaridade 1.00)"
        resultado = _extrair_identificadores_duplicados(erro)
        self.assertEqual(resultado, (("services", "1", "title"), ("services", "2", "title")))

    def test_extrai_identificadores_de_tipos_diferentes(self):
        erro = "Texto duplicado entre services[3].description e features[2].description (similaridade 0.86)"
        resultado = _extrair_identificadores_duplicados(erro)
        self.assertEqual(resultado, (("services", "3", "description"), ("features", "2", "description")))

    def test_erro_de_faq_curto_nao_e_reconhecido(self):
        erro = "1 validation error for SiteConfig\nfaq\n  List should have at least 3 items"
        self.assertIsNone(_extrair_identificadores_duplicados(erro))

    def test_erro_de_template_leak_nao_e_reconhecido(self):
        erro = "Texto de template vazou para produção em cta.buttonText: 'Começar'"
        self.assertIsNone(_extrair_identificadores_duplicados(erro))

    def test_secao_com_id_textual_funciona(self):
        erro = "Texto duplicado entre sections[sobre].content e services[1].description (similaridade 1.00)"
        resultado = _extrair_identificadores_duplicados(erro)
        self.assertEqual(resultado, (("sections", "sobre", "content"), ("services", "1", "description")))


class TestLocalizarItem(unittest.TestCase):
    def test_encontra_item_por_id_numerico(self):
        config = _config_com_titulo_duplicado()
        item = _localizar_item(config, "services", "2")
        self.assertEqual(item["title"], "Atendimento especializado")
        self.assertEqual(item["description"], "Suporte completo do início ao fim do processo.")

    def test_id_inexistente_retorna_none(self):
        config = _config_com_titulo_duplicado()
        self.assertIsNone(_localizar_item(config, "services", "99"))


class TestReparoLocalizado(unittest.TestCase):
    def test_reparo_bem_sucedido_nao_gasta_tentativa_extra(self):
        """Duplicação + reparo que funciona de primeira: 1 tentativa no diagnóstico, não 2."""
        agente = _agente_com_dublê([
            _config_com_titulo_duplicado(),
            {"texto": "Suporte técnico especializado para o seu negócio"},
        ])
        diagnostico = []
        resultado = agente.gerar_config_site("Empresa Teste", "nicho", diagnostico_tentativas=diagnostico)

        self.assertEqual(len(diagnostico), 1)
        self.assertTrue(diagnostico[0]["sucesso"])
        self.assertEqual(resultado["services"][1]["title"], "Suporte técnico especializado para o seu negócio")
        # campo não-reparado permanece intacto
        self.assertEqual(resultado["services"][0]["title"], "Atendimento especializado")

    def test_reparo_que_falha_cai_pro_retry_normal(self):
        """Resposta de reparo sem o campo esperado -> não usa, tentativa 1 falha, tentativa 2 regenera tudo."""
        agente = _agente_com_dublê([
            _config_com_titulo_duplicado(),
            {"campo_errado": "não é o que o reparo espera"},
            _config_valido_minimo(),
        ])
        diagnostico = []
        resultado = agente.gerar_config_site("Empresa Teste", "nicho", diagnostico_tentativas=diagnostico)

        self.assertEqual(len(diagnostico), 2)
        self.assertFalse(diagnostico[0]["sucesso"])
        self.assertTrue(diagnostico[1]["sucesso"])
        self.assertEqual(resultado["company"]["name"], "Empresa Teste")

    def test_erro_nao_relacionado_a_duplicacao_nao_aciona_reparo(self):
        """FAQ curto (não é TXT-01) -- vai direto pro retry normal, sem consumir resposta extra de reparo."""
        agente = _agente_com_dublê([_config_invalido_faq_curto(), _config_valido_minimo()])
        diagnostico = []
        agente.gerar_config_site("Empresa Teste", "nicho", diagnostico_tentativas=diagnostico)

        # se o reparo tivesse sido acionado indevidamente, a fila teria sido
        # consumida fora de ordem e a 2ª resposta (config válido) teria sido
        # interpretada como resposta de reparo, quebrando o teste.
        self.assertEqual(len(diagnostico), 2)
        self.assertFalse(diagnostico[0]["sucesso"])
        self.assertTrue(diagnostico[1]["sucesso"])

    def test_reparo_com_excecao_na_chamada_de_ia_nao_propaga(self):
        """Se self.ai.gerar_json do reparo lançar exceção, trata como reparo falho -- não derruba a geração inteira."""

        class _ProvedorComFalhaNoReparo:
            ordem = ["fake"]
            provedor_ativo = "fake"

            def __init__(self):
                self._chamadas = 0

            def gerar_json(self, prompt, max_tokens=4096):
                if "designer de cores" in prompt:
                    return {
                        "primary": "#6366f1", "primaryDark": "#4f46e5", "secondary": "#ec4899",
                        "accent": "#f59e0b", "background": "#ffffff", "text": "#1f2937",
                        "textLight": "#6b7280", "border": "#e5e7eb",
                    }
                self._chamadas += 1
                if self._chamadas == 1:
                    return _config_com_titulo_duplicado()
                if self._chamadas == 2:
                    raise RuntimeError("timeout simulado no reparo")
                return _config_valido_minimo()

        agente = AgenteConstrutor.__new__(AgenteConstrutor)
        agente.ai = _ProvedorComFalhaNoReparo()
        diagnostico = []
        resultado = agente.gerar_config_site("Empresa Teste", "nicho", diagnostico_tentativas=diagnostico)

        self.assertEqual(len(diagnostico), 2)
        self.assertFalse(diagnostico[0]["sucesso"])
        self.assertTrue(diagnostico[1]["sucesso"])
        self.assertEqual(resultado["company"]["name"], "Empresa Teste")


if __name__ == "__main__":
    unittest.main()
