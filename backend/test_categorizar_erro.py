#!/usr/bin/env python3
"""
Testa a categorização/agregação de falhas de test_agentes.py:
- _categorizar_erro: classifica uma mensagem de erro em categorias que
  distinguem causa de MODELO (o LLM escreveu algo ruim) de causa de
  PIPELINE (constraint estrutural do schema, rede, parsing).
- _agregar_diagnostico: agrega diagnostico_tentativas de todos os nichos
  em métricas por regra / por tentativa / por nicho.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from test_agentes import _categorizar_erro, _agregar_diagnostico, _formatar_tentativas_para_json


class TestCategorizarErro(unittest.TestCase):
    def test_none_ou_vazio_sem_categoria(self):
        self.assertEqual(_categorizar_erro(None), [])
        self.assertEqual(_categorizar_erro(""), [])

    def test_titulo_duplicado_e_model_duplication(self):
        erro = "Título duplicado entre services[1].title e features[2].title (similaridade 1.00)"
        self.assertEqual(_categorizar_erro(erro), ["MODEL_DUPLICATION"])

    def test_texto_duplicado_e_model_duplication(self):
        erro = "Texto duplicado entre services[1].description e features[1].description (similaridade 0.85)"
        self.assertEqual(_categorizar_erro(erro), ["MODEL_DUPLICATION"])

    def test_pergunta_faq_duplicada_e_model_duplication(self):
        erro = "Pergunta de FAQ duplicado entre faq[1].question e faq[3].question (similaridade 0.90)"
        self.assertEqual(_categorizar_erro(erro), ["MODEL_DUPLICATION"])

    def test_template_vazado_e_model_template_leak(self):
        erro = "Texto de template vazou para produção em services[1].title: 'Serviço 1'"
        self.assertEqual(_categorizar_erro(erro), ["MODEL_TEMPLATE_LEAK"])

    def test_faq_curto_e_schema_faq(self):
        erro = (
            "1 validation error for SiteConfig\n"
            "faq\n"
            "  List should have at least 3 items after validation, not 2 [type=too_short, ...]"
        )
        self.assertEqual(_categorizar_erro(erro), ["SCHEMA_FAQ"])

    def test_features_curto_e_schema_features(self):
        erro = (
            "1 validation error for SiteConfig\n"
            "features\n"
            "  List should have at least 3 items after validation, not 2 [type=too_short, ...]"
        )
        self.assertEqual(_categorizar_erro(erro), ["SCHEMA_FEATURES"])

    def test_services_curto_e_schema_services(self):
        erro = (
            "1 validation error for SiteConfig\n"
            "services\n"
            "  List should have at least 1 item after validation, not 0 [type=too_short, ...]"
        )
        self.assertEqual(_categorizar_erro(erro), ["SCHEMA_SERVICES"])

    def test_features_e_faq_curtos_ao_mesmo_tempo_duas_categorias(self):
        erro = (
            "2 validation errors for SiteConfig\n"
            "features\n"
            "  List should have at least 3 items after validation, not 2 [type=too_short, ...]\n"
            "faq\n"
            "  List should have at least 3 items after validation, not 2 [type=too_short, ...]"
        )
        self.assertEqual(set(_categorizar_erro(erro)), {"SCHEMA_FEATURES", "SCHEMA_FAQ"})

    def test_banco_de_imagens_indisponivel_e_image(self):
        erro = "ErroBancoImagens: banco de imagens curado indisponível para 'padaria'"
        self.assertEqual(_categorizar_erro(erro), ["IMAGE"])

    def test_nenhum_provedor_disponivel_e_fallback(self):
        erro = "Nenhum provedor de IA disponível. Tentativas:\ngemini: ...\nollama: ..."
        self.assertEqual(_categorizar_erro(erro), ["FALLBACK"])

    def test_timeout_de_rede_e_timeout(self):
        erro = "HTTPConnectionPool(host='localhost', port=11434): Read timed out."
        self.assertEqual(_categorizar_erro(erro), ["TIMEOUT"])

    def test_json_malformado_e_json_invalid(self):
        erro = "Expecting value: line 1 column 1 (char 0)"
        self.assertEqual(_categorizar_erro(erro), ["JSON_INVALID"])

    def test_erro_pydantic_generico_sem_padrao_conhecido_e_schema_outro(self):
        erro = "1 validation error for SiteConfig\ncolors.primary\n  Invalid hex color"
        self.assertEqual(_categorizar_erro(erro), ["SCHEMA_OUTRO"])

    def test_erro_sem_relacao_com_nada_conhecido_e_outro(self):
        erro = "Algo inesperado e nao mapeado aconteceu"
        self.assertEqual(_categorizar_erro(erro), ["OUTRO"])


def _resultado(tentativas):
    return {"nome": "Nicho Teste", "diagnostico_tentativas": tentativas}


class TestAgregarDiagnostico(unittest.TestCase):
    def test_sucesso_na_primeira_tentativa(self):
        resultados = [_resultado([
            {"tentativa": 1, "sucesso": True, "erro": None, "tempo_segundos": 10.0},
        ])]
        agregado = _agregar_diagnostico(resultados)
        self.assertEqual(agregado["por_tentativa"]["distribuicao_sucesso"], {1: 1})
        self.assertEqual(agregado["por_tentativa"]["nunca_sucesso"], 0)
        self.assertEqual(agregado["por_regra"], {})
        self.assertAlmostEqual(agregado["por_tentativa"]["tempo_medio_por_numero"][1], 10.0)

    def test_falha_duplication_depois_sucesso(self):
        resultados = [_resultado([
            {"tentativa": 1, "sucesso": False, "erro": "Título duplicado entre a e b (similaridade 1.00)", "tempo_segundos": 5.0},
            {"tentativa": 2, "sucesso": True, "erro": None, "tempo_segundos": 7.0},
        ])]
        agregado = _agregar_diagnostico(resultados)
        self.assertEqual(agregado["por_regra"], {"MODEL_DUPLICATION": 1})
        self.assertEqual(agregado["por_nicho"], {"MODEL_DUPLICATION": 1})
        self.assertEqual(agregado["por_tentativa"]["distribuicao_sucesso"], {2: 1})
        self.assertEqual(agregado["por_tentativa"]["nunca_sucesso"], 0)

    def test_esgota_tentativas_sem_sucesso(self):
        erro_faq = "1 validation error for SiteConfig\nfaq\n  List should have at least 3 items"
        resultados = [_resultado([
            {"tentativa": 1, "sucesso": False, "erro": erro_faq, "tempo_segundos": 8.0},
            {"tentativa": 2, "sucesso": False, "erro": erro_faq, "tempo_segundos": 9.0},
            {"tentativa": 3, "sucesso": False, "erro": erro_faq, "tempo_segundos": 10.0},
        ])]
        agregado = _agregar_diagnostico(resultados)
        self.assertEqual(agregado["por_regra"], {"SCHEMA_FAQ": 3})
        self.assertEqual(agregado["por_nicho"], {"SCHEMA_FAQ": 1})
        self.assertEqual(agregado["por_tentativa"]["distribuicao_sucesso"], {})
        self.assertEqual(agregado["por_tentativa"]["nunca_sucesso"], 1)

    def test_percentual_de_sucesso_por_tentativa_relativo_ao_total_de_nichos(self):
        sucesso_1 = [{"tentativa": 1, "sucesso": True, "erro": None, "tempo_segundos": 1.0}]
        sucesso_2 = [
            {"tentativa": 1, "sucesso": False, "erro": "x", "tempo_segundos": 1.0},
            {"tentativa": 2, "sucesso": True, "erro": None, "tempo_segundos": 1.0},
        ]
        nunca = [{"tentativa": 1, "sucesso": False, "erro": "x", "tempo_segundos": 1.0}]
        resultados = [_resultado(sucesso_1), _resultado(sucesso_1), _resultado(sucesso_2), _resultado(nunca)]
        agregado = _agregar_diagnostico(resultados)
        pct = agregado["por_tentativa"]["distribuicao_sucesso_pct"]
        self.assertAlmostEqual(pct[1], 50.0)   # 2 de 4 nichos passaram na 1a
        self.assertAlmostEqual(pct[2], 25.0)   # 1 de 4 passou na 2a
        self.assertAlmostEqual(agregado["por_tentativa"]["nunca_sucesso_pct"], 25.0)

    def test_nicho_sem_diagnostico_nao_quebra_agregacao(self):
        resultados = [{"nome": "X", "diagnostico_tentativas": []}]
        agregado = _agregar_diagnostico(resultados)
        self.assertEqual(agregado["por_tentativa"]["nunca_sucesso"], 0)

    def test_top_n_ordena_por_frequencia_decrescente(self):
        resultados = [
            _resultado([{"tentativa": 1, "sucesso": False, "erro": "Título duplicado entre a e b (similaridade 1.0)", "tempo_segundos": 1.0}]),
            _resultado([{"tentativa": 1, "sucesso": False, "erro": "Título duplicado entre a e b (similaridade 1.0)", "tempo_segundos": 1.0}]),
            _resultado([{"tentativa": 1, "sucesso": False, "erro": "1 validation error for SiteConfig\nfaq\n  List should have at least 3 items", "tempo_segundos": 1.0}]),
        ]
        agregado = _agregar_diagnostico(resultados)
        top = agregado["top_regras"]
        self.assertEqual(top[0], ("MODEL_DUPLICATION", 2))
        self.assertEqual(top[1], ("SCHEMA_FAQ", 1))


class TestFormatarTentativasParaJson(unittest.TestCase):
    def test_sucesso_vira_status_passou_sem_regras(self):
        diagnostico = [{"tentativa": 1, "sucesso": True, "erro": None, "tempo_segundos": 10.5, "provedor": "ollama"}]
        formatado = _formatar_tentativas_para_json(diagnostico)
        self.assertEqual(formatado, [
            {"numero": 1, "status": "passou", "regras": [], "tempo_segundos": 10.5, "provedor": "ollama"}
        ])

    def test_falha_vira_status_falhou_com_regras(self):
        diagnostico = [{
            "tentativa": 1, "sucesso": False,
            "erro": "Título duplicado entre a e b (similaridade 1.0)",
            "tempo_segundos": 5.2, "provedor": "ollama",
        }]
        formatado = _formatar_tentativas_para_json(diagnostico)
        self.assertEqual(formatado, [
            {"numero": 1, "status": "falhou", "regras": ["MODEL_DUPLICATION"], "tempo_segundos": 5.2, "provedor": "ollama"}
        ])

    def test_lista_vazia_retorna_lista_vazia(self):
        self.assertEqual(_formatar_tentativas_para_json([]), [])


if __name__ == "__main__":
    unittest.main()
