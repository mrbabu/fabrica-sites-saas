#!/usr/bin/env python3
"""
Agente Hunter - Fábrica de Sites SaaS
Responsável por capturar e limpar leads recebidos via WhatsApp, transformando
uma mensagem bruta em um payload JSON estruturado ("DadosLead") que alimenta o
restante do pipeline: Agente Construtor -> AgenteVendedor -> AgenteFinanceiro.

A extração de texto livre implementada aqui é deliberadamente simples
(regex), suficiente para validar o contrato de payload entre os agentes.
Substituir por um parser mais robusto (ou um LLM) é trabalho de uma fase
futura, não deste esqueleto inicial.
"""

import re
from typing import Any, Dict, Optional

# Contrato oficial do payload "DadosLead": mesmos nomes de campo consumidos
# por AgenteConstrutor.gerar_config_site() (agent_construtor.py).
CORES_NOMEADAS = {
    "azul": "#0066CC",
    "vermelho": "#DC2626",
    "verde": "#16A34A",
    "amarelo": "#FACC15",
    "roxo": "#7C3AED",
    "laranja": "#EA580C",
    "rosa": "#EC4899",
    "preto": "#111827",
    "cinza": "#6B7280",
    "branco": "#F9FAFB",
}
COR_PADRAO = "#6366f1"

_PADRAO_NICHO_LOCAL = re.compile(
    r"para\s+(?:minha|meu|um|uma)?\s*(?P<nicho>.+?)\s+em\s+(?P<localizacao>[^,]+)",
    re.IGNORECASE,
)
_PADRAO_COR = re.compile(r"cor\s+(?P<cor>[a-zA-ZÀ-ÿ]+)", re.IGNORECASE)
_PADRAO_NOME = re.compile(r"nome\s+(?P<nome>.+)$", re.IGNORECASE)


class AgenteHunter:
    """
    Agente de captura e limpeza de leads.

    Responsabilidade: receber o texto bruto vindo do WhatsApp (via webhook
    n8n), extrair e normalizar os campos mínimos necessários para o
    onboarding (nome da empresa, nicho, localização, cor, contato) e produzir
    o payload JSON "DadosLead" — pronto para ser consumido pelo Agente
    Construtor (geração do site) e, em seguida, pelo AgenteVendedor.
    """

    def capturar_lead(
        self, mensagem_bruta: str, whatsapp_contato: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recebe o texto bruto da mensagem de WhatsApp e extrai os campos
        relevantes do lead via regex (extração simples, não é NLP real).

        Args:
            mensagem_bruta: texto da mensagem recebida via webhook do WhatsApp.
            whatsapp_contato: número do remetente, normalmente vindo separado
                do texto no payload do webhook (não incluído na mensagem).

        Returns:
            Lead com campos ainda "crus" (strings como digitadas pelo usuário),
            antes da normalização feita por limpar_e_validar().
        """
        match_nicho_local = _PADRAO_NICHO_LOCAL.search(mensagem_bruta)
        match_cor = _PADRAO_COR.search(mensagem_bruta)
        match_nome = _PADRAO_NOME.search(mensagem_bruta)

        return {
            "mensagem_original": mensagem_bruta,
            "nicho_raw": match_nicho_local.group("nicho") if match_nicho_local else None,
            "localizacao_raw": match_nicho_local.group("localizacao") if match_nicho_local else None,
            "cor_raw": match_cor.group("cor") if match_cor else None,
            "nome_empresa_raw": match_nome.group("nome") if match_nome else None,
            "whatsapp_contato": whatsapp_contato,
        }

    def limpar_e_validar(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza os campos crus extraídos por capturar_lead() e monta o
        payload "DadosLead" — o contrato de entrada do Agente Construtor.

        Args:
            lead: lead bruto retornado por capturar_lead().

        Returns:
            DadosLead: {nome_empresa, nicho, cor_primaria, localizacao,
            whatsapp_contato}, pronto para AgenteConstrutor.gerar_config_site().
        """
        nome_empresa = (lead.get("nome_empresa_raw") or "Minha Empresa").strip()
        nicho = (lead.get("nicho_raw") or "Negócios").strip()
        localizacao = (lead.get("localizacao_raw") or "").strip() or None

        cor_nome = (lead.get("cor_raw") or "").strip().lower()
        cor_primaria = CORES_NOMEADAS.get(cor_nome, COR_PADRAO)

        return {
            "nome_empresa": nome_empresa,
            "nicho": nicho,
            "cor_primaria": cor_primaria,
            "localizacao": localizacao,
            "whatsapp_contato": lead.get("whatsapp_contato"),
        }
