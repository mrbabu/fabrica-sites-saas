#!/usr/bin/env python3
"""
Agente Financeiro - Fábrica de Sites SaaS
Responsável por monitorar e conciliar pagamentos via PIX associados a cada
lead/cliente, fechando o ciclo iniciado pelo AgenteHunter e pelo AgenteVendedor.
"""

from typing import Any, Dict


class AgenteFinanceiro:
    """
    Agente de monitoramento e conciliação financeira (PIX).

    Responsabilidade: acompanhar pagamentos PIX referentes aos leads
    convertidos pelo AgenteVendedor, conciliar com o registro do cliente e
    atualizar o payload com o status financeiro final (pago, pendente,
    atrasado).
    """

    def monitorar_pagamento(self, cliente: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consulta o status de pagamento PIX referente ao cliente/lead.

        Args:
            cliente: payload do cliente, produzido pelo AgenteVendedor após
                o envio do link de demonstração.

        Returns:
            Payload com o status de pagamento consultado (ex: status_pix,
            valor, data_pagamento).
        """
        raise NotImplementedError

    def conciliar(
        self, cliente: Dict[str, Any], pagamento: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Concilia o pagamento consultado com o registro do cliente,
        atualizando seu status final.

        Args:
            cliente: payload do cliente.
            pagamento: payload retornado por monitorar_pagamento().

        Returns:
            Payload final do cliente, com status financeiro consolidado
            (ex: ativo, inadimplente).
        """
        raise NotImplementedError
