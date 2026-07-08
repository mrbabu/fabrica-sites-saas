#!/usr/bin/env python3
"""
Agente Vendedor - Fábrica de Sites SaaS
Responsável por conectar o site-config.json gerado pelo Agente Construtor ao
Lovable e enviar o link de demonstração ao lead capturado pelo AgenteHunter.
"""

from typing import Any, Dict


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
        Publica ou atualiza, no Lovable, a demo correspondente ao site gerado.

        Args:
            site_config: site-config.json validado, gerado pelo Agente
                Construtor (ver `schema_validator.SiteConfig`).

        Returns:
            Payload com os dados da demo publicada (ex: url_demo, id_projeto).
        """
        raise NotImplementedError

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
