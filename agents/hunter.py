#!/usr/bin/env python3
"""
Agente Hunter - Fábrica de Sites SaaS
Responsável por capturar e limpar leads recebidos via WhatsApp, transformando
uma mensagem bruta em um payload JSON estruturado ("lead") que alimenta o
restante do pipeline: Agente Construtor -> AgenteVendedor -> AgenteFinanceiro.
"""

from typing import Any, Dict


class AgenteHunter:
    """
    Agente de captura e limpeza de leads.

    Responsabilidade: receber o dado bruto vindo do WhatsApp (via webhook n8n),
    extrair e normalizar os campos mínimos necessários para o onboarding
    (nome da empresa, nicho, localização, contato) e produzir um payload JSON
    limpo — o "lead" — pronto para ser consumido pelo Agente Construtor
    (geração do site) e, em seguida, pelo AgenteVendedor.
    """

    def capturar_lead(self, mensagem_bruta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe a mensagem bruta do WhatsApp (via webhook n8n) e extrai os
        campos relevantes do lead.

        Args:
            mensagem_bruta: payload cru recebido do webhook do WhatsApp.

        Returns:
            Lead extraído, ainda não validado/limpo.
        """
        raise NotImplementedError

    def limpar_e_validar(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza e valida os campos do lead (ex: formato do WhatsApp, nome da
        empresa, nicho), preparando-o para ser consumido pelo Agente Construtor.

        Args:
            lead: lead bruto retornado por capturar_lead().

        Returns:
            Payload JSON do lead, limpo e validado — contrato de entrada do
            Agente Construtor (nome_empresa, nicho, localizacao,
            whatsapp_contato, ...).
        """
        raise NotImplementedError
