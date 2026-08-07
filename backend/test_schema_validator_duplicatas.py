#!/usr/bin/env python3
"""
Testa _primeira_duplicata() (agora wrapper de _todas_duplicatas()) e
listar_todas_duplicatas() (schema_validator.py) -- RFC "Repair Engine v2"
aprovada 2026-08-06: uma única implementação da lógica de detecção de
duplicação (normalização + limiar de similaridade), reusada tanto pela
validação bloqueante (para no primeiro achado) quanto pelo Repair Engine
(precisa de TODOS os pares pra agrupar em clusters).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from schema_validator import _primeira_duplicata, _todas_duplicatas, listar_todas_duplicatas


class TestPrimeiraDuplicataContinuaIgual(unittest.TestCase):
    """Comportamento externo de _primeira_duplicata não pode mudar --
    quality_gate.py e o pipeline de validação bloqueante dependem dele."""

    def test_sem_duplicata_retorna_none(self):
        textos = [("a", "Texto um qualquer"), ("b", "Texto completamente diferente")]
        self.assertIsNone(_primeira_duplicata("Título", textos))

    def test_duplicata_retorna_mensagem_no_formato_original(self):
        textos = [("services[1].title", "Instalação elétrica"), ("services[2].title", "Instalação elétrica")]
        erro = _primeira_duplicata("Título", textos)
        self.assertEqual(erro, "Título duplicado entre services[1].title e services[2].title (similaridade 1.00)")

    def test_retorna_so_a_primeira_mesmo_com_multiplas_duplicatas(self):
        textos = [
            ("a", "Instalação elétrica residencial"),
            ("b", "Instalação elétrica residencial"),
            ("c", "Instalação elétrica residencial"),
        ]
        erro = _primeira_duplicata("Título", textos)
        self.assertIn("entre a e b", erro)  # primeira dupla na ordem de combinations, não a segunda (a×c) nem terceira (b×c)


class TestTodasDuplicatas(unittest.TestCase):
    def test_sem_duplicata_lista_vazia(self):
        textos = [("a", "Texto um"), ("b", "Texto dois, bem diferente")]
        self.assertEqual(_todas_duplicatas("Título", textos), [])

    def test_encontra_todas_as_duplicatas_nao_so_a_primeira(self):
        textos = [
            ("a", "Instalação elétrica residencial"),
            ("b", "Instalação elétrica residencial"),
            ("c", "Instalação elétrica residencial"),
        ]
        pares = _todas_duplicatas("Título", textos)
        self.assertEqual(len(pares), 3)  # a×b, a×c, b×c

    def test_formato_do_dict_retornado(self):
        textos = [("services[1].title", "Instalação elétrica"), ("services[2].title", "Instalação elétrica")]
        pares = _todas_duplicatas("Título", textos)
        self.assertEqual(pares[0]["rotulo"], "Título")
        self.assertEqual(pares[0]["campo_a"], "services[1].title")
        self.assertEqual(pares[0]["campo_b"], "services[2].title")
        self.assertEqual(pares[0]["similaridade"], 1.0)


class TestListarTodasDuplicatas(unittest.TestCase):
    def _config_base(self):
        return {
            "sections": [],
            "services": [
                {"id": 1, "title": "Instalação elétrica", "description": "Cuidamos de cada detalhe do seu projeto."},
                {"id": 2, "title": "Manutenção preventiva", "description": "Revisão periódica pra evitar falhas."},
            ],
            "features": [],
            "faq": [],
        }

    def test_config_sem_duplicata_retorna_lista_vazia(self):
        self.assertEqual(listar_todas_duplicatas(self._config_base()), [])

    def test_encontra_duplicatas_de_grupos_diferentes(self):
        config = self._config_base()
        config["services"].append(
            {"id": 3, "title": "Instalação elétrica", "description": "Texto totalmente diferente aqui."}
        )
        pares = listar_todas_duplicatas(config)
        self.assertEqual(len(pares), 1)
        self.assertEqual(pares[0]["rotulo"], "Título")

    def test_ordem_e_deterministica_titulo_antes_de_texto_antes_de_faq(self):
        """Mesma ordem que _validar_regras_conteudo já checava."""
        config = self._config_base()
        config["services"][1]["title"] = "Instalação elétrica"  # duplica título
        config["services"][1]["description"] = "Cuidamos de cada detalhe do seu projeto."  # duplica texto
        config["faq"] = [
            {"id": 1, "question": "Vocês atendem fim de semana?"},
            {"id": 2, "question": "Vocês atendem fim de semana?"},
        ]
        pares = listar_todas_duplicatas(config)
        rotulos = [p["rotulo"] for p in pares]
        self.assertEqual(rotulos, ["Título", "Texto", "Pergunta de FAQ"])


if __name__ == "__main__":
    unittest.main()
