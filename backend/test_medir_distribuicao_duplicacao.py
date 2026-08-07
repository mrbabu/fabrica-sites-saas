#!/usr/bin/env python3
"""
Testa _encontrar_todos_pares() (scripts/medir_distribuicao_duplicacao.py) --
diferente de schema_validator._primeira_duplicata, que para no primeiro
achado (correto pra decidir bloquear geração), esta encontra TODOS os
pares acima do limiar, usada só pra medir distribuição, nunca pelo
pipeline de produção.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from medir_distribuicao_duplicacao import _encontrar_todos_pares


def _config_base():
    return {
        "sections": [],
        "services": [
            {"id": 1, "title": "Instalação elétrica", "description": "Cuidamos de cada detalhe do seu projeto."},
            {"id": 2, "title": "Manutenção preventiva", "description": "Revisão periódica pra evitar falhas."},
            {"id": 3, "title": "Reparo de urgência", "description": "Atendimento rápido em situações críticas."},
        ],
        "features": [],
        "faq": [],
    }


class TestEncontrarTodosPares(unittest.TestCase):
    def test_sem_duplicata_retorna_lista_vazia(self):
        self.assertEqual(_encontrar_todos_pares(_config_base()), [])

    def test_um_par_duplicado_e_encontrado(self):
        config = _config_base()
        config["services"][1]["title"] = "Instalação elétrica"
        pares = _encontrar_todos_pares(config)
        self.assertEqual(len(pares), 1)
        self.assertEqual(pares[0][0], "titulo")

    def test_dois_pares_simultaneos_ancorados_no_mesmo_item(self):
        """services[1] duplicado com services[2] (título) E com services[3] (descrição) --
        exatamente o padrão real observado hoje (Odontologia/Advocacia): mesmo item-âncora,
        dois pares em grupos diferentes."""
        config = _config_base()
        config["services"][1]["title"] = "Instalação elétrica"  # duplica título com services[1]
        config["services"][2]["description"] = "Cuidamos de cada detalhe do seu projeto."  # duplica texto com services[1]
        pares = _encontrar_todos_pares(config)
        self.assertEqual(len(pares), 2)
        grupos = {p[0] for p in pares}
        self.assertEqual(grupos, {"titulo", "texto"})

    def test_triangulo_completo_conta_as_3_combinacoes(self):
        """3 títulos idênticos entre si = C(3,2) = 3 pares, não 2 -- combinação, não item."""
        config = _config_base()
        config["services"][1]["title"] = "Instalação elétrica"
        config["services"][2]["title"] = "Instalação elétrica"
        pares = _encontrar_todos_pares(config)
        self.assertEqual(len(pares), 3)

    def test_similaridade_abaixo_do_limiar_nao_conta(self):
        config = _config_base()
        config["services"][1]["title"] = "Consultoria financeira completa"
        self.assertEqual(_encontrar_todos_pares(config), [])


if __name__ == "__main__":
    unittest.main()
