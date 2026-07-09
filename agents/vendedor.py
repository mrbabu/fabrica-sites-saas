#!/usr/bin/env python3
"""
Agente Vendedor - Fábrica de Sites SaaS
Responsável por conectar o site-config.json gerado pelo Agente Construtor ao
Lovable e enviar o link de demonstração ao lead capturado pelo AgenteHunter.

conectar_lovable() e enviar_link_demonstracao() ainda são mockados (não fazem
chamada HTTP real): montam o payload exatamente como seria enviado à
API/webhook do Lovable/WhatsApp, para validar o contrato de dados antes de
existir uma integração real.
"""

import re
from typing import Any, Dict

LOVABLE_WEBHOOK_URL_MOCK = "https://api.lovable.dev/mock/webhook"
WHATSAPP_API_URL_MOCK = "https://api.whatsapp.com/mock/send"


def _slugificar(texto: str) -> str:
    """Gera um slug simples (minúsculo, hífens) a partir do nome da empresa"""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", texto.strip().lower()).strip("-")
    return slug or "site"


class ErroEnvioDemo(Exception):
    """Lead sem contato de WhatsApp válido, ou payload de demo incompleto,
    para o envio do link de demonstração"""


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
        Monta (mock) o payload que seria enviado à API do WhatsApp para
        entregar o link de demonstração ao lead — ainda não é uma chamada
        HTTP real, mesmo padrão de conectar_lovable().

        Args:
            lead: payload do lead ("DadosLead"), já limpo/validado pelo
                AgenteHunter (deve conter `whatsapp_contato`).
            demo: payload retornado por conectar_lovable() (deve conter
                `url_demo_prevista`).

        Returns:
            Payload do lead atualizado com o status de envio e o link
            enviado — contrato de entrada do AgenteFinanceiro após a venda.

        Raises:
            ErroEnvioDemo: se o lead não tiver `whatsapp_contato` ou o
                payload de demo não tiver `url_demo_prevista` — nunca falha
                silenciosamente, dado que dados de contato são sensíveis.
        """
        whatsapp_contato = str(lead.get("whatsapp_contato") or "").strip()
        if not whatsapp_contato:
            raise ErroEnvioDemo("Lead sem whatsapp_contato: impossível enviar link de demonstração")

        url_demo = demo.get("url_demo_prevista")
        if not url_demo:
            raise ErroEnvioDemo(
                "Payload de demo sem url_demo_prevista: conectar_lovable() não foi executado corretamente"
            )

        mensagem = (
            f"Olá! Seu site de demonstração já está pronto: {url_demo}\n"
            "Responda esta mensagem para ativarmos o pagamento e publicarmos o site oficial."
        )

        return {
            **lead,
            "status_envio": "mock_enviado",
            "url_demo_enviada": url_demo,
            "corpo_requisicao_whatsapp": {
                "webhook_url": WHATSAPP_API_URL_MOCK,
                "to": whatsapp_contato,
                "mensagem": mensagem,
            },
        }
