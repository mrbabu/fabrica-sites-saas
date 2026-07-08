#!/usr/bin/env python3
"""
Agente Vendedor - Fábrica de Sites SaaS
Responsável por conectar o site-config.json gerado pelo Agente Construtor ao
Lovable e enviar o link de demonstração ao lead capturado pelo AgenteHunter.

conectar_lovable() ainda é mockado (não faz chamada HTTP real): monta o
payload exatamente como seria enviado à API/webhook do Lovable, para validar
o contrato de dados antes de existir uma integração real.
"""

import re
from typing import Any, Dict

LOVABLE_WEBHOOK_URL_MOCK = "https://api.lovable.dev/mock/webhook"


def _slugificar(texto: str) -> str:
    """Gera um slug simples (minúsculo, hífens) a partir do nome da empresa"""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", texto.strip().lower()).strip("-")
    return slug or "site"


class AgenteVendedor:
    """
    Agente de vendas e demonstração.

    Responsabilidade: receber o payload do lead (produzido pelo AgenteHunter)
    junto com o site-config.json gerado pelo Agente Construtor, publicar/
    conectar a demo correspondente no Lovable e enviar o link de demonstração
    ao lead via WhatsApp. Repassa o payload atualizado (com status de venda)
    ao AgenteFinanceiro.
    """

    def conectar_lovable(self, site_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monta (mock) o payload que seria enviado à API/webhook do Lovable
        para gerar o preview do site, a partir do site-config.json.

        Args:
            site_config: site-config.json validado, gerado pelo Agente
                Construtor (ver `schema_validator.SiteConfig`).

        Returns:
            Payload simulado de entrega ao Lovable (ex: url_demo,
            webhook_url, corpo da requisição) — ainda não é uma chamada
            HTTP real.
        """
        nome_empresa = site_config.get("company", {}).get("name", "Site")
        slug = _slugificar(nome_empresa)

        return {
            "status": "mock_preparado",
            "webhook_url": LOVABLE_WEBHOOK_URL_MOCK,
            "url_demo_prevista": f"https://preview.lovable.dev/{slug}",
            "corpo_requisicao": {
                "project_name": nome_empresa,
                "site_config": site_config,
            },
        }

    def enviar_link_demonstracao(
        self, lead: Dict[str, Any], demo: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envia o link de demonstração gerado pelo Lovable ao lead via WhatsApp.

        Args:
            lead: payload do lead, já limpo/validado pelo AgenteHunter.
            demo: payload retornado por conectar_lovable().

        Returns:
            Payload do lead atualizado com o status de envio e o link
            enviado — contrato de entrada do AgenteFinanceiro após a venda.
        """
        raise NotImplementedError
