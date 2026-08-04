#!/usr/bin/env python3
"""
Testes do Quality Gate em modo relatório (Lote 1.C do roadmap DoPS --
docs/roadmap-implementacao-dops.md). Cobre CNF-01, CNF-02, IMG-04, IMG-05.

Nenhum teste faz rede real: HTTP e leitura de dimensão de imagem são
injetados via parâmetro (mesmo padrão de _requests_module em
test_ollama_provider.py), pra não depender de conectividade nem de URLs
externas ainda no ar.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from quality_gate import (
    validar_cnf01_contato,
    validar_cnf02_endereco,
    validar_img04_hero_dimensao,
    validar_img05_imagens_resolvem,
    rodar_gate_relatorio,
)


def _config_base() -> dict:
    return {
        "hero": {"backgroundImage": "https://exemplo.com/hero.jpg"},
        "sections": [
            {"id": "sobre", "image": "https://exemplo.com/secao1.jpg"},
            {"id": "servicos", "image": "https://exemplo.com/secao2.jpg"},
        ],
        "contact": {
            "whatsapp": "+5527999998888",
            "email": None,
            "address": "Rua das Flores, 100 - Vitória ES",
            "googleMapsUrl": "https://maps.google.com/?q=exemplo",
        },
    }


class TestCNF01Contato(unittest.TestCase):
    def test_whatsapp_e164_valido_passa(self):
        resultado = validar_cnf01_contato(_config_base())
        self.assertTrue(resultado.passou)

    def test_whatsapp_ausente_falha(self):
        config = _config_base()
        config["contact"]["whatsapp"] = None
        resultado = validar_cnf01_contato(config)
        self.assertFalse(resultado.passou)

    def test_whatsapp_com_letras_falha(self):
        config = _config_base()
        config["contact"]["whatsapp"] = "não é um número"
        resultado = validar_cnf01_contato(config)
        self.assertFalse(resultado.passou)

    def test_email_none_passa_campo_opcional_nunca_inventado(self):
        config = _config_base()
        config["contact"]["email"] = None
        resultado = validar_cnf01_contato(config)
        self.assertTrue(resultado.passou)

    def test_email_malformado_falha(self):
        config = _config_base()
        config["contact"]["email"] = "nao-e-email"
        resultado = validar_cnf01_contato(config)
        self.assertFalse(resultado.passou)

    def test_email_valido_passa(self):
        config = _config_base()
        config["contact"]["email"] = "contato@exemplo.com"
        resultado = validar_cnf01_contato(config)
        self.assertTrue(resultado.passou)


class TestCNF02Endereco(unittest.TestCase):
    def test_endereco_identico_ao_input_passa(self):
        config = _config_base()
        resultado = validar_cnf02_endereco(
            config,
            localizacao_esperada="Rua das Flores, 100 - Vitória ES",
            google_maps_url_esperado="https://maps.google.com/?q=exemplo",
        )
        self.assertTrue(resultado.passou)

    def test_endereco_divergente_do_input_falha(self):
        config = _config_base()
        config["contact"]["address"] = "Endereço inventado pela IA"
        resultado = validar_cnf02_endereco(
            config,
            localizacao_esperada="Rua das Flores, 100 - Vitória ES",
            google_maps_url_esperado="https://maps.google.com/?q=exemplo",
        )
        self.assertFalse(resultado.passou)

    def test_ambos_ausentes_passa_nunca_fabricado(self):
        config = _config_base()
        config["contact"]["address"] = None
        config["contact"]["googleMapsUrl"] = None
        resultado = validar_cnf02_endereco(config, localizacao_esperada=None, google_maps_url_esperado=None)
        self.assertTrue(resultado.passou)


class TestIMG05ImagensResolvem(unittest.TestCase):
    def test_todas_as_imagens_200_passa(self):
        def http_head_fake(url):
            class _Resp:
                status_code = 200
            return _Resp()

        resultado = validar_img05_imagens_resolvem(_config_base(), http_head=http_head_fake)
        self.assertTrue(resultado.passou)

    def test_uma_imagem_404_falha(self):
        def http_head_fake(url):
            class _Resp:
                status_code = 404 if "secao2" in url else 200
            return _Resp()

        resultado = validar_img05_imagens_resolvem(_config_base(), http_head=http_head_fake)
        self.assertFalse(resultado.passou)
        self.assertIn("secao2", resultado.detalhe)

    def test_url_com_formato_invalido_falha_sem_tentar_rede(self):
        config = _config_base()
        config["hero"]["backgroundImage"] = "não-é-uma-url"
        chamadas = []

        def http_head_fake(url):
            chamadas.append(url)
            class _Resp:
                status_code = 200
            return _Resp()

        resultado = validar_img05_imagens_resolvem(config, http_head=http_head_fake)
        self.assertFalse(resultado.passou)
        self.assertNotIn("não-é-uma-url", chamadas)


class TestIMG04HeroDimensao(unittest.TestCase):
    def test_hero_1920x600_passa_largura_e_proporcao(self):
        resultado = validar_img04_hero_dimensao(
            _config_base(), obter_dimensao=lambda url: (1920, 600)
        )
        self.assertTrue(resultado.passou)

    def test_hero_estreito_demais_falha_largura(self):
        resultado = validar_img04_hero_dimensao(
            _config_base(), obter_dimensao=lambda url: (800, 600)
        )
        self.assertFalse(resultado.passou)

    def test_hero_proporcao_quadrada_falha_razao(self):
        resultado = validar_img04_hero_dimensao(
            _config_base(), obter_dimensao=lambda url: (2000, 2000)
        )
        self.assertFalse(resultado.passou)

    def test_hero_ausente_falha_sem_chamar_obter_dimensao(self):
        config = _config_base()
        config["hero"]["backgroundImage"] = ""
        chamado = []
        resultado = validar_img04_hero_dimensao(
            config, obter_dimensao=lambda url: chamado.append(url) or (9999, 1)
        )
        self.assertFalse(resultado.passou)
        self.assertEqual(chamado, [])


class TestRodarGateRelatorio(unittest.TestCase):
    """Testa o agregador que roda os 4 critérios e devolve um relatório único."""

    def test_relatorio_agrega_todos_os_criterios_sem_lancar_excecao(self):
        relatorio = rodar_gate_relatorio(
            _config_base(),
            localizacao_esperada="Rua das Flores, 100 - Vitória ES",
            google_maps_url_esperado="https://maps.google.com/?q=exemplo",
            http_head=lambda url: type("R", (), {"status_code": 200})(),
            obter_dimensao=lambda url: (1920, 600),
        )
        ids = {r.id for r in relatorio}
        self.assertEqual(ids, {"CNF-01", "CNF-02", "IMG-04", "IMG-05"})
        self.assertTrue(all(r.passou for r in relatorio))

    def test_relatorio_nao_bloqueia_nem_altera_o_config(self):
        """R1: modo relatório não pode mutar o config recebido."""
        config = _config_base()
        import copy
        config_original = copy.deepcopy(config)
        rodar_gate_relatorio(
            config,
            localizacao_esperada="Rua das Flores, 100 - Vitória ES",
            google_maps_url_esperado="https://maps.google.com/?q=exemplo",
            http_head=lambda url: type("R", (), {"status_code": 200})(),
            obter_dimensao=lambda url: (1920, 600),
        )
        self.assertEqual(config, config_original)


if __name__ == "__main__":
    unittest.main()
