#!/usr/bin/env python3
"""
Cobre os campos opcionais de tenant que o template lê direto do JSON, em vez
de deixar hardcoded no index.html (diretriz do CLAUDE.md):

- institutional.pillars   -- frentes de atuação da marca (a MGR tira as dela
                             do descritor da própria logo).
- contact.whatsappMessage -- mensagem pré-preenchida dos CTAs de WhatsApp;
                             "agendar um horário" só cabe em negócio de hora
                             marcada, obra/reforma pede orçamento.

Os dois são opcionais de propósito: config antigo, sem os campos, precisa
continuar válido e cair no comportamento histórico.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from pydantic import ValidationError

from schema_validator import Contact, Institutional


CONTATO_MINIMO = {"phone": "+552730266644", "whatsapp": "+5527999413133"}


class TestInstitutionalPillars(unittest.TestCase):
    def test_ausente_fica_none(self):
        self.assertIsNone(Institutional().pillars)

    def test_aceita_lista_de_rotulos(self):
        inst = Institutional(pillars=["Construção", "Reforma", "Gestão", "Planejamento"])
        self.assertEqual(len(inst.pillars), 4)

    def test_rejeita_acima_do_limite(self):
        with self.assertRaises(ValidationError):
            Institutional(pillars=[f"Frente {i}" for i in range(7)])


class TestContactWhatsappMessage(unittest.TestCase):
    def test_ausente_fica_none(self):
        self.assertIsNone(Contact(**CONTATO_MINIMO).whatsappMessage)

    def test_aceita_mensagem_do_tenant(self):
        msg = "Olá! Vim pelo site da MGR Reformas e Projetos e gostaria de solicitar um orçamento."
        self.assertEqual(Contact(**CONTATO_MINIMO, whatsappMessage=msg).whatsappMessage, msg)

    def test_rejeita_mensagem_longa_demais(self):
        with self.assertRaises(ValidationError):
            Contact(**CONTATO_MINIMO, whatsappMessage="x" * 301)


if __name__ == "__main__":
    unittest.main()
