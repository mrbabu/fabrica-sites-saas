#!/usr/bin/env python3
"""
Testa classificar_reparo() (scripts/analisar_reparo.py) -- classifica o
resultado de uma tentativa de reparo usando a MESMA métrica de similaridade
que já decide TXT-01 (limiar 0.85), não uma métrica nova.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from analisar_reparo import classificar_reparo


class TestClassificarReparo(unittest.TestCase):
    def test_texto_identico_ao_original_e_eco_completo(self):
        r = classificar_reparo(
            texto_original="Cuidamos de cada detalhe do seu projeto elétrico.",
            texto_retornado="Cuidamos de cada detalhe do seu projeto elétrico.",
            texto_conflitante="Outro texto qualquer, bem diferente disso aqui.",
        )
        self.assertEqual(r["categoria"], "ECO_COMPLETO")

    def test_texto_quase_identico_conta_como_eco(self):
        r = classificar_reparo(
            texto_original="Cuidamos de cada detalhe do seu projeto elétrico com atenção.",
            texto_retornado="Cuidamos de cada detalhe do seu projeto elétrico, com atenção.",
            texto_conflitante="Outro texto qualquer, bem diferente disso aqui.",
        )
        self.assertEqual(r["categoria"], "ECO_COMPLETO")

    def test_mudou_mas_ainda_bate_no_conflitante_e_mudanca_insuficiente(self):
        r = classificar_reparo(
            texto_original="Instalação elétrica residencial com equipe qualificada.",
            texto_retornado="Instalação elétrica em residências com time qualificado.",
            texto_conflitante="Instalação elétrica em residências com equipe qualificada.",
        )
        self.assertEqual(r["categoria"], "MUDANCA_INSUFICIENTE")

    def test_texto_genuinamente_diferente_e_sucesso(self):
        r = classificar_reparo(
            texto_original="Cuidamos de cada detalhe do seu projeto elétrico com atenção.",
            texto_retornado="Atendimento rápido e preço justo para toda a região metropolitana.",
            texto_conflitante="Cuidamos de cada detalhe do seu projeto elétrico com atenção.",
        )
        self.assertEqual(r["categoria"], "SUCESSO")

    def test_resposta_sem_texto_e_erro(self):
        r = classificar_reparo(
            texto_original="Original", texto_retornado=None, texto_conflitante="Conflitante",
        )
        self.assertEqual(r["categoria"], "ERRO")

    def test_resposta_vazia_e_erro(self):
        r = classificar_reparo(
            texto_original="Original", texto_retornado="   ", texto_conflitante="Conflitante",
        )
        self.assertEqual(r["categoria"], "ERRO")

    def test_resposta_nao_string_e_erro(self):
        r = classificar_reparo(
            texto_original="Original", texto_retornado=123, texto_conflitante="Conflitante",
        )
        self.assertEqual(r["categoria"], "ERRO")


if __name__ == "__main__":
    unittest.main()
