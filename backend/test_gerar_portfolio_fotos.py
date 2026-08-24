#!/usr/bin/env python3
"""
Testes de gerar_portfolio_fotos.py -- lógica pura de classificação/merge,
sem chamada de API real e sem gravar fora de diretório temporário.

AIProvider é substituído por um dublê de classe inteira (mesmo padrão de
test_ai_provider_fallback.py) para testar só a validação de contagem/nomes
de classificar_fotos(), não o fallback entre provedores (isso já é coberto
em test_ai_provider_fallback.py).
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from PIL import Image

import gerar_portfolio_fotos as gpf
from ai_provider import ErroProvedorIA


def _criar_foto(caminho: Path) -> None:
    Image.new("RGB", (20, 20), color=(120, 40, 40)).save(caminho, format="JPEG")


class _AIProviderSucesso:
    """Dublê que devolve uma classificação válida para todas as fotos."""

    def __init__(self, respostas):
        self._respostas = respostas

    def gerar_json_com_imagens(self, prompt, imagens, max_tokens=4096):
        return {"fotos": self._respostas}


class TestMontarSections(unittest.TestCase):
    def test_monta_sections_a_partir_das_classificacoes(self):
        caminhos = [Path("estrutura.jpg"), Path("finalizado.jpg")]
        classificacoes = {
            "estrutura.jpg": {"titulo": "Portfólio: Piscina — Estrutura", "subtitulo": "Execução", "conteudo": "Primeira etapa."},
            "finalizado.jpg": {"titulo": "Portfólio: Piscina — Finalizada", "subtitulo": "Entrega", "conteudo": "Obra concluída."},
        }

        sections = gpf.montar_sections(classificacoes, caminhos, "cliente-teste")

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0]["image"], "assets/portfolio/cliente-teste/estrutura.jpg")
        self.assertEqual(sections[0]["title"], "Portfólio: Piscina — Estrutura")
        self.assertEqual(sections[0]["type"], "content")
        self.assertTrue(sections[0]["enabled"])
        self.assertEqual(sections[1]["image"], "assets/portfolio/cliente-teste/finalizado.jpg")


class TestClassificarFotos(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.pasta = Path(self._tmpdir.name)
        self.caminhos = [self.pasta / "a.jpg", self.pasta / "b.jpg"]
        for c in self.caminhos:
            _criar_foto(c)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_sucesso_devolve_dict_por_arquivo(self):
        respostas = [
            {"arquivo": "a.jpg", "titulo": "T1", "subtitulo": "S1", "conteudo": "C1"},
            {"arquivo": "b.jpg", "titulo": "T2", "subtitulo": "S2", "conteudo": "C2"},
        ]
        with patch.object(gpf, "AIProvider", lambda: _AIProviderSucesso(respostas)):
            resultado = gpf.classificar_fotos("reformas", "Empresa Teste", self.caminhos)

        self.assertEqual(resultado["a.jpg"]["titulo"], "T1")
        self.assertEqual(resultado["b.jpg"]["titulo"], "T2")

    def test_erro_quando_contagem_nao_bate(self):
        respostas = [{"arquivo": "a.jpg", "titulo": "T1", "subtitulo": "S1", "conteudo": "C1"}]
        with patch.object(gpf, "AIProvider", lambda: _AIProviderSucesso(respostas)):
            with self.assertRaises(gpf.ErroGerarPortfolio):
                gpf.classificar_fotos("reformas", "Empresa Teste", self.caminhos)

    def test_erro_quando_arquivo_nao_enviado_e_classificado(self):
        respostas = [
            {"arquivo": "a.jpg", "titulo": "T1", "subtitulo": "S1", "conteudo": "C1"},
            {"arquivo": "arquivo-inexistente.jpg", "titulo": "T2", "subtitulo": "S2", "conteudo": "C2"},
        ]
        with patch.object(gpf, "AIProvider", lambda: _AIProviderSucesso(respostas)):
            with self.assertRaises(gpf.ErroGerarPortfolio):
                gpf.classificar_fotos("reformas", "Empresa Teste", self.caminhos)

    def test_propaga_erro_do_provedor_de_ia(self):
        class _AIProviderFalha:
            def gerar_json_com_imagens(self, *a, **kw):
                raise ErroProvedorIA("nenhum provedor com visão disponível")

        with patch.object(gpf, "AIProvider", _AIProviderFalha):
            with self.assertRaises(ErroProvedorIA):
                gpf.classificar_fotos("reformas", "Empresa Teste", self.caminhos)


class TestMesclarNoConfig(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmpdir.name)
        (self.raiz / "configs").mkdir()
        self._patch_raiz = patch.object(gpf, "RAIZ", self.raiz)
        self._patch_raiz.start()

    def tearDown(self):
        self._patch_raiz.stop()
        self._tmpdir.cleanup()

    def _escrever_config(self, slug, config):
        caminho = self.raiz / "configs" / f"{slug}.json"
        caminho.write_text(json.dumps(config), encoding="utf-8")
        return caminho

    def test_acrescenta_sections_sem_mexer_no_resto(self):
        config_original = {
            "company": {"name": "Empresa Teste"},
            "hero": {"backgroundImage": "https://banco-de-imagens/foto.jpg"},
            "sections": [{"id": "sobre", "title": "Sobre", "content": "..."}],
        }
        self._escrever_config("cliente-teste", config_original)

        sections_novas = [{"id": "portfolio-a", "title": "Novo", "content": "..."}]
        caminho_salvo = gpf.mesclar_no_config("cliente-teste", sections_novas)

        resultado = json.loads(caminho_salvo.read_text(encoding="utf-8"))
        self.assertEqual(len(resultado["sections"]), 2)
        self.assertEqual(resultado["sections"][0]["id"], "sobre")
        self.assertEqual(resultado["sections"][1]["id"], "portfolio-a")
        self.assertEqual(resultado["company"]["name"], "Empresa Teste")
        self.assertEqual(resultado["hero"]["backgroundImage"], "https://banco-de-imagens/foto.jpg")

    def test_hero_so_muda_quando_explicitamente_passado(self):
        self._escrever_config("cliente-teste", {"hero": {"backgroundImage": "antigo.jpg"}, "sections": []})

        gpf.mesclar_no_config("cliente-teste", [], hero_arquivo="nova-foto.jpg")

        resultado = json.loads((self.raiz / "configs" / "cliente-teste.json").read_text(encoding="utf-8"))
        self.assertEqual(resultado["hero"]["backgroundImage"], "assets/portfolio/cliente-teste/nova-foto.jpg")

    def test_erro_quando_config_nao_existe(self):
        with self.assertRaises(gpf.ErroGerarPortfolio):
            gpf.mesclar_no_config("slug-inexistente", [])


if __name__ == "__main__":
    unittest.main()
