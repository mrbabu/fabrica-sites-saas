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
    validar_img02_hero_nao_repete,
    validar_vis03_icones_repetidos,
    validar_txt01_duplicacao,
    validar_txt04_template,
    rodar_gate_relatorio,
    rodar_gate_completo,
    _gerar_relatorio,
    _relatorio_para_markdown,
    _carregar_configs,
    ResultadoCriterio,
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

    def test_caminho_relativo_de_asset_existente_passa_sem_rede(self):
        """assets/... é padrão válido já usado pra logo/portfólio (caminho relativo servido
        pelo mesmo host do site) -- IMG-05 deve checar existência do arquivo, não fazer HTTP."""
        config = _config_base()
        config["hero"]["backgroundImage"] = "assets/logos/existe.png"
        config["sections"] = []

        def http_head_nunca_deveria_ser_chamado(url):
            raise AssertionError("não deveria fazer HEAD pra caminho relativo")

        resultado = validar_img05_imagens_resolvem(
            config, http_head=http_head_nunca_deveria_ser_chamado,
            arquivo_existe=lambda caminho: True,
        )
        self.assertTrue(resultado.passou)

    def test_caminho_relativo_de_asset_inexistente_falha(self):
        config = _config_base()
        config["hero"]["backgroundImage"] = "assets/logos/nao-existe.png"
        config["sections"] = []

        resultado = validar_img05_imagens_resolvem(
            config, arquivo_existe=lambda caminho: False,
        )
        self.assertFalse(resultado.passou)
        self.assertIn("nao-existe.png", resultado.detalhe)

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


class TestIMG02HeroNaoRepete(unittest.TestCase):
    def test_hero_diferente_das_secoes_passa(self):
        resultado = validar_img02_hero_nao_repete(_config_base())
        self.assertTrue(resultado.passou)

    def test_hero_repetida_em_secao_falha(self):
        config = _config_base()
        config["sections"][0]["image"] = config["hero"]["backgroundImage"]
        resultado = validar_img02_hero_nao_repete(config)
        self.assertFalse(resultado.passou)
        self.assertIn("sobre", resultado.detalhe)

    def test_hero_ausente_passa_nada_a_comparar(self):
        config = _config_base()
        config["hero"]["backgroundImage"] = ""
        resultado = validar_img02_hero_nao_repete(config)
        self.assertTrue(resultado.passou)


class TestVIS03IconesRepetidos(unittest.TestCase):
    def test_icones_unicos_por_grupo_passa(self):
        config = _config_base()
        config["services"] = [{"id": 1, "icon": "🔧"}, {"id": 2, "icon": "⚡"}]
        config["features"] = [{"id": 1, "icon": "✅"}, {"id": 2, "icon": "🚀"}]
        resultado = validar_vis03_icones_repetidos(config)
        self.assertTrue(resultado.passou)

    def test_icone_repetido_dentro_de_services_falha(self):
        config = _config_base()
        config["services"] = [{"id": 1, "icon": "🔧"}, {"id": 2, "icon": "🔧"}]
        config["features"] = []
        resultado = validar_vis03_icones_repetidos(config)
        self.assertFalse(resultado.passou)

    def test_mesmo_icone_em_services_e_features_nao_conflita(self):
        """Grupos são deduplicados separadamente (mesma regra de agent_construtor._autocorrigir)."""
        config = _config_base()
        config["services"] = [{"id": 1, "icon": "🔧"}]
        config["features"] = [{"id": 1, "icon": "🔧"}]
        resultado = validar_vis03_icones_repetidos(config)
        self.assertTrue(resultado.passou)


class TestTXT01Duplicacao(unittest.TestCase):
    def test_titulos_e_textos_unicos_passa(self):
        config = _config_base()
        config["services"] = [
            {"id": 1, "title": "Instalação elétrica", "description": "Fazemos instalação completa em residências."},
            {"id": 2, "title": "Manutenção preventiva", "description": "Revisão periódica pra evitar falhas graves."},
        ]
        resultado = validar_txt01_duplicacao(config)
        self.assertTrue(resultado.passou)

    def test_titulo_duplicado_entre_services_falha(self):
        config = _config_base()
        config["services"] = [
            {"id": 1, "title": "Instalação elétrica", "description": "Texto A distinto o suficiente."},
            {"id": 2, "title": "Instalação elétrica", "description": "Texto B também distinto."},
        ]
        resultado = validar_txt01_duplicacao(config)
        self.assertFalse(resultado.passou)
        self.assertIn("Título duplicado", resultado.detalhe)

    def test_faq_com_perguntas_repetidas_falha(self):
        config = _config_base()
        config["faq"] = [
            {"id": 1, "question": "Vocês atendem aos finais de semana?"},
            {"id": 2, "question": "Vocês atendem aos finais de semana?"},
        ]
        resultado = validar_txt01_duplicacao(config)
        self.assertFalse(resultado.passou)


class TestTXT04Template(unittest.TestCase):
    def test_sem_placeholder_passa(self):
        config = _config_base()
        config["company"] = {"name": "Auto Elétrica Silva"}
        resultado = validar_txt04_template(config)
        self.assertTrue(resultado.passou)

    def test_placeholder_de_template_vazado_falha(self):
        config = _config_base()
        config["company"] = {"name": "Nome Empresa"}
        resultado = validar_txt04_template(config)
        self.assertFalse(resultado.passou)
        self.assertIn("company.name", resultado.detalhe)


def _http_head_fake_200(url):
    return type("R", (), {"status_code": 200})()


def _obter_dimensao_fake_1920x600(url):
    return (1920, 600)


class TestRodarGateCompleto(unittest.TestCase):
    """Agregador usado pelo modo CLI -- não inclui CNF-02 (exige dado externo
    ao site-config.json, não disponível num corpus solto)."""

    def test_nao_inclui_cnf02(self):
        relatorio = rodar_gate_completo(
            _config_base(), http_head=_http_head_fake_200, obter_dimensao=_obter_dimensao_fake_1920x600
        )
        ids = {r.id for r in relatorio}
        self.assertNotIn("CNF-02", ids)

    def test_inclui_todos_os_outros_sete_criterios(self):
        relatorio = rodar_gate_completo(
            _config_base(), http_head=_http_head_fake_200, obter_dimensao=_obter_dimensao_fake_1920x600
        )
        ids = {r.id for r in relatorio}
        self.assertEqual(ids, {"CNF-01", "IMG-02", "IMG-04", "IMG-05", "TXT-01", "TXT-04", "VIS-03"})

    def test_nao_altera_o_config_recebido(self):
        import copy
        config = _config_base()
        config_original = copy.deepcopy(config)
        rodar_gate_completo(config, http_head=_http_head_fake_200, obter_dimensao=_obter_dimensao_fake_1920x600)
        self.assertEqual(config, config_original)


class TestGerarRelatorio(unittest.TestCase):
    def test_agrega_severidade_e_contagem_por_criterio(self):
        resultados_por_arquivo = {
            "site_a.json": [
                ResultadoCriterio("TXT-01", False, "duplicado"),
                ResultadoCriterio("IMG-04", True),
            ],
            "site_b.json": [
                ResultadoCriterio("TXT-01", False, "duplicado de novo"),
                ResultadoCriterio("IMG-04", False, "muito pequena"),
            ],
        }
        relatorio = _gerar_relatorio(resultados_por_arquivo)
        self.assertEqual(relatorio["resumo"]["total_sites"], 2)
        self.assertEqual(relatorio["resumo"]["total_falhas"], 3)
        self.assertEqual(relatorio["resumo"]["por_severidade"]["P0"], 2)  # TXT-01 x2
        self.assertEqual(relatorio["resumo"]["por_severidade"]["P2"], 1)  # IMG-04
        self.assertEqual(relatorio["quantidade_por_criterio"]["TXT-01"], 2)
        self.assertEqual(relatorio["quantidade_por_site"]["site_a.json"], 1)
        self.assertEqual(relatorio["quantidade_por_site"]["site_b.json"], 2)

    def test_top10_ordenado_por_ocorrencia(self):
        resultados_por_arquivo = {
            "a.json": [ResultadoCriterio("TXT-01", False), ResultadoCriterio("IMG-02", False)],
            "b.json": [ResultadoCriterio("TXT-01", False)],
        }
        relatorio = _gerar_relatorio(resultados_por_arquivo)
        self.assertEqual(relatorio["top10_problemas"][0]["criterio"], "TXT-01")
        self.assertEqual(relatorio["top10_problemas"][0]["ocorrencias"], 2)

    def test_relatorio_vazio_nao_lanca_excecao(self):
        relatorio = _gerar_relatorio({})
        self.assertEqual(relatorio["resumo"]["total_sites"], 0)
        self.assertEqual(relatorio["resumo"]["total_falhas"], 0)


class TestRelatorioParaMarkdown(unittest.TestCase):
    def test_gera_markdown_com_secoes_esperadas(self):
        resultados_por_arquivo = {"site_a.json": [ResultadoCriterio("TXT-01", False, "duplicado")]}
        relatorio = _gerar_relatorio(resultados_por_arquivo)
        md = _relatorio_para_markdown(relatorio)
        self.assertIn("Top 10 problemas", md)
        self.assertIn("TXT-01", md)
        self.assertIn("site_a.json", md)


class TestCarregarConfigs(unittest.TestCase):
    def test_carrega_todos_os_json_do_diretorio(self):
        import tempfile
        import json as json_mod
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "site1.json").write_text(json_mod.dumps({"a": 1}), encoding="utf-8")
            Path(tmp, "site2.json").write_text(json_mod.dumps({"b": 2}), encoding="utf-8")
            Path(tmp, "nao_e_json.txt").write_text("ignorar", encoding="utf-8")

            resultado = _carregar_configs(Path(tmp))
            nomes = {nome for nome, _ in resultado}
            self.assertEqual(nomes, {"site1.json", "site2.json"})

    def test_json_invalido_marca_dados_none_em_vez_de_lancar(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "quebrado.json").write_text("{ isso não é json", encoding="utf-8")
            resultado = _carregar_configs(Path(tmp))
            self.assertEqual(resultado, [("quebrado.json", None)])


if __name__ == "__main__":
    unittest.main()
