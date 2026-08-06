#!/usr/bin/env python3
"""
IMG-04 (definition-of-professional-site.md): hero.backgroundImage precisa ter
largura >= 1920px e proporção >= 16:9.

Bug real encontrado em produção (demo Odontologia, benchmark 2026-08-04):
obter_imagens_categoria() usava item["urls"]["regular"] -- variante que a
própria Unsplash sempre serve capada em 1080px de largura, independente da
resolução da foto original. Por isso IMG-04 reprovava sempre, não importa
quão bom fosse o ranking (_rankear_imagens já pontua resolução, mas o campo
usado pra montar a URL final descartava esse ganho).

Este teste cobre a função pura extraída pra corrigir isso: _url_hero_otimizada()
deve montar a URL a partir de urls.raw pedindo explicitamente w=1920&h=1080,
nunca usar urls.regular.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("IMAGE_ENGINE_LLM_FALLBACK", "0")

from image_utils import _url_hero_otimizada


class TestUrlHeroOtimizada(unittest.TestCase):
    def setUp(self):
        self.item = {
            "urls": {
                "raw": "https://images.unsplash.com/photo-123",
                "full": "https://images.unsplash.com/photo-123?fm=jpg",
                "regular": "https://images.unsplash.com/photo-123?w=1080",
                "small": "https://images.unsplash.com/photo-123?w=400",
            },
            "width": 5000,
            "height": 3333,
        }

    def test_usa_raw_nao_regular(self):
        url = _url_hero_otimizada(self.item)
        self.assertIn("photo-123", url)
        self.assertNotIn("w=1080", url)

    def test_pede_largura_minima_1920(self):
        url = _url_hero_otimizada(self.item)
        self.assertIn("w=1920", url)

    def test_pede_altura_para_forcar_proporcao_16_9(self):
        url = _url_hero_otimizada(self.item)
        self.assertIn("h=1080", url)

    def test_raw_ja_com_query_string_usa_e_comercial(self):
        item = dict(self.item)
        item["urls"] = dict(self.item["urls"])
        item["urls"]["raw"] = "https://images.unsplash.com/photo-123?ixid=abc123"
        url = _url_hero_otimizada(item)
        self.assertIn("ixid=abc123", url)
        self.assertIn("&w=1920", url)

    def test_sem_raw_cai_pra_regular_sem_quebrar(self):
        item = {"urls": {"regular": "https://images.unsplash.com/photo-999?w=1080"}}
        url = _url_hero_otimizada(item)
        self.assertIn("photo-999", url)


if __name__ == "__main__":
    unittest.main()
