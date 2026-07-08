#!/usr/bin/env python3
"""
Agente Financeiro - Fábrica de Sites SaaS
Responsável por monitorar e conciliar pagamentos PIX associados a cada
lead/cliente, fechando o ciclo iniciado pelo AgenteHunter e pelo AgenteVendedor.

Fecha o ciclo: Hunter (referencia_id do lead) -> Construtor -> Vendedor
(entrega da demo) -> Financeiro (libera o site mediante pagamento confirmado).
"""

import json
from typing import Any, Dict

# Único conjunto de status aceitos como "pagamento aprovado". Comparação
# estrita (nunca por prefixo/substring) para não liberar site por engano.
STATUS_APROVADOS = {"approved", "pago", "concluido", "concluído"}

# Tolerância de centavos para lidar com arredondamento de ponto flutuante,
# nunca para aceitar valor pago menor que o esperado.
TOLERANCIA_VALOR = 0.01


class ErroConciliacao(Exception):
    """Payload de webhook de pagamento malformado ou sem os campos mínimos exigidos"""


class AgenteFinanceiro:
    """
    Agente de monitoramento e conciliação financeira (PIX).

    Responsabilidade: receber o webhook de um gateway de pagamento (Mercado
    Pago, EFI, Asaas, etc.), extrair status/valor/referência do lead
    (`referencia_id`, gerado originalmente pelo AgenteHunter) e conciliar
    contra o valor esperado do cliente — liberando o site (status "ativo")
    apenas quando o status for estritamente aprovado E o valor bater.
    """

    def monitorar_pagamento(self, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai os campos relevantes de um webhook de gateway de pagamento.

        Args:
            webhook_payload: payload cru recebido do webhook (formato comum
                a Mercado Pago/EFI/Asaas): {"status": ..., "valor": ...,
                "metadata": {"referencia_id": ...}}.

        Returns:
            Dados normalizados: {status_raw, valor_pago, referencia_id}.

        Raises:
            ErroConciliacao: se campos obrigatórios estiverem ausentes ou em
                formato inválido — nunca falha silenciosamente.
        """
        try:
            status_raw = str(webhook_payload["status"]).strip().lower()
            valor_pago = float(webhook_payload["valor"])
            referencia_id = str(webhook_payload["metadata"]["referencia_id"])
        except (KeyError, TypeError, ValueError) as e:
            raise ErroConciliacao(f"Payload de webhook malformado: {e}") from e

        if not referencia_id:
            raise ErroConciliacao("referencia_id vazio no payload do webhook")

        return {
            "status_raw": status_raw,
            "valor_pago": valor_pago,
            "referencia_id": referencia_id,
        }

    def conciliar(self, pagamento: Dict[str, Any], valor_esperado: float) -> Dict[str, Any]:
        """
        Concilia o pagamento consultado com o valor esperado do cliente e
        decide se o site pode ser liberado.

        Regra de negócio (estrita, por segurança): só libera se o status
        estiver em STATUS_APROVADOS E o valor pago for igual (com tolerância
        de centavos) ao esperado. Valor pago a maior não é tratado como
        aprovação automática — cai em revisão manual.

        Args:
            pagamento: payload retornado por monitorar_pagamento().
            valor_esperado: valor cobrado esperado para este lead/site.

        Returns:
            Payload final: {referencia_id, status, motivo}. `status` é
            "ativo" quando conciliado com sucesso, ou "rejeitado" caso
            contrário — nunca lança exceção aqui, pois recusar é uma decisão
            de negócio válida, não um erro técnico.
        """
        status_aprovado = pagamento["status_raw"] in STATUS_APROVADOS
        valor_bate = abs(pagamento["valor_pago"] - valor_esperado) <= TOLERANCIA_VALOR

        if status_aprovado and valor_bate:
            return {
                "referencia_id": pagamento["referencia_id"],
                "status": "ativo",
                "motivo": "Pagamento aprovado e valor conciliado com sucesso.",
            }

        motivos = []
        if not status_aprovado:
            motivos.append(f"status '{pagamento['status_raw']}' não é um status aprovado")
        if not valor_bate:
            motivos.append(
                f"valor pago ({pagamento['valor_pago']:.2f}) diverge do esperado "
                f"({valor_esperado:.2f})"
            )

        return {
            "referencia_id": pagamento["referencia_id"],
            "status": "rejeitado",
            "motivo": "; ".join(motivos),
        }


if __name__ == "__main__":
    print("💰 Agente Financeiro - Simulação de Conciliação PIX\n")

    agente = AgenteFinanceiro()

    casos = [
        {
            "descricao": "Pagamento aprovado, valor correto",
            "webhook": {
                "status": "approved",
                "valor": 149.90,
                "metadata": {"referencia_id": "lead-001"},
            },
            "valor_esperado": 149.90,
        },
        {
            "descricao": "Pagamento ainda pendente (não aprovado)",
            "webhook": {
                "status": "pending",
                "valor": 149.90,
                "metadata": {"referencia_id": "lead-002"},
            },
            "valor_esperado": 149.90,
        },
        {
            "descricao": "Tentativa fraudulenta: status aprovado mas valor pago abaixo do esperado",
            "webhook": {
                "status": "pago",
                "valor": 10.00,
                "metadata": {"referencia_id": "lead-003"},
            },
            "valor_esperado": 149.90,
        },
        {
            "descricao": "Payload malformado (webhook incompleto/corrompido)",
            "webhook": {"status": "approved"},
            "valor_esperado": 149.90,
        },
    ]

    for caso in casos:
        print(f"🧪 {caso['descricao']}")
        try:
            pagamento = agente.monitorar_pagamento(caso["webhook"])
            resultado = agente.conciliar(pagamento, caso["valor_esperado"])
            emoji = "✅" if resultado["status"] == "ativo" else "❌"
            print(f"   {emoji} {json.dumps(resultado, ensure_ascii=False)}\n")
        except ErroConciliacao as e:
            print(f"   ⚠️  Rejeitado com segurança: {e}\n")
