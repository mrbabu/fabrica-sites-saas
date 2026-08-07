#!/usr/bin/env python3
"""
Testa as peças puras do Repair Engine v2 (RFC aprovada 2026-08-06):
agrupamento de campos duplicados em componentes conectados e escolha de
âncora por prioridade semântica fixa (services > features > faq >
sections), determinística -- não depende de qual campo tem mais conexões
no grafo.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from agent_construtor import _agrupar_campos_conectados, _escolher_ancora


class TestAgruparCamposConectados(unittest.TestCase):
    def test_um_par_isolado_forma_um_cluster_de_2(self):
        duplicatas = [{"campo_a": "services[1].title", "campo_b": "services[2].title"}]
        clusters = _agrupar_campos_conectados(duplicatas)
        self.assertEqual(clusters, [["services[1].title", "services[2].title"]])

    def test_dois_pares_disjuntos_formam_dois_clusters(self):
        duplicatas = [
            {"campo_a": "services[1].title", "campo_b": "services[2].title"},
            {"campo_a": "features[1].description", "campo_b": "features[2].description"},
        ]
        clusters = _agrupar_campos_conectados(duplicatas)
        self.assertEqual(len(clusters), 2)

    def test_cadeia_transitiva_forma_um_cluster_so(self):
        """A×B, B×C, A×D -- mesmo padrão real observado (Odontologia): tudo conectado por um hub."""
        duplicatas = [
            {"campo_a": "services[2].description", "campo_b": "features[2].description"},
            {"campo_a": "features[1].description", "campo_b": "features[2].description"},
            {"campo_a": "features[1].description", "campo_b": "features[3].description"},
            {"campo_a": "services[3].description", "campo_b": "features[1].description"},
        ]
        clusters = _agrupar_campos_conectados(duplicatas)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(
            clusters[0],
            sorted(["services[2].description", "features[2].description", "features[1].description",
                    "features[3].description", "services[3].description"]),
        )

    def test_resultado_e_deterministico_independente_da_ordem_de_entrada(self):
        duplicatas_ordem_a = [
            {"campo_a": "services[2].description", "campo_b": "features[2].description"},
            {"campo_a": "features[1].description", "campo_b": "features[2].description"},
        ]
        duplicatas_ordem_b = list(reversed(duplicatas_ordem_a))
        self.assertEqual(
            _agrupar_campos_conectados(duplicatas_ordem_a),
            _agrupar_campos_conectados(duplicatas_ordem_b),
        )

    def test_clusters_ordenados_deterministicamente(self):
        duplicatas = [
            {"campo_a": "services[3].title", "campo_b": "services[4].title"},
            {"campo_a": "features[1].title", "campo_b": "features[2].title"},
        ]
        clusters = _agrupar_campos_conectados(duplicatas)
        # ordenado pelo primeiro identificador de cada cluster
        self.assertEqual(clusters[0][0], "features[1].title")
        self.assertEqual(clusters[1][0], "services[3].title")


class TestEscolherAncora(unittest.TestCase):
    def test_services_tem_prioridade_sobre_features(self):
        cluster = ["features[1].description", "services[2].description"]
        self.assertEqual(_escolher_ancora(cluster), "services[2].description")

    def test_features_tem_prioridade_sobre_faq(self):
        cluster = ["faq[1].question", "features[3].description"]
        self.assertEqual(_escolher_ancora(cluster), "features[3].description")

    def test_faq_tem_prioridade_sobre_sections(self):
        cluster = ["sections[sobre].content", "faq[1].question"]
        self.assertEqual(_escolher_ancora(cluster), "faq[1].question")

    def test_empate_de_tipo_desempata_por_identificador_menor_deterministico(self):
        cluster = ["services[3].description", "services[1].description", "services[2].description"]
        self.assertEqual(_escolher_ancora(cluster), "services[1].description")

    def test_nao_depende_do_hub_do_grafo_so_do_tipo(self):
        """Mesmo se features[1] aparece em mais pares (seria o 'hub'), services sempre vence."""
        cluster = ["features[1].description", "features[2].description", "features[3].description", "services[3].description"]
        self.assertEqual(_escolher_ancora(cluster), "services[3].description")


if __name__ == "__main__":
    unittest.main()
