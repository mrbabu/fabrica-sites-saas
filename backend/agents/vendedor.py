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
# Endpoint mockado no padrão de disparo usado por Z-API/Evolution API
# (POST {instancia}/message/sendText — corpo {"number", "text"}).
WHATSAPP_DISPATCH_API_URL_MOCK = "https://api.z-api.io/mock/instances/instance/token/token/send-text"


def _slugificar(texto: str) -> str:
    """Gera um slug simples (minúsculo, hífens) a partir do nome da empresa"""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", texto.strip().lower()).strip("-")
    return slug or "site"


def _formatar_numero_whatsapp(numero: str) -> str:
    """Normaliza o contato para o formato somente-dígitos (DDI+DDD+número)
    exigido pelo corpo de requisição de Z-API/Evolution API — remove
    símbolos como '+', espaços, parênteses e hífens."""
    return re.sub(r"\D", "", numero or "")


class ErroEnvioDemo(Exception):
    """Lead sem contato de WhatsApp válido para o envio do link de demonstração"""


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
        self, link_demonstracao: str, whatsapp_contato: str
    ) -> Dict[str, Any]:
        """
        Monta (mock) o payload de disparo que seria enviado a uma API de
        WhatsApp (Z-API/Evolution API) para entregar o link de demonstração
        ao lead — ainda não é uma chamada HTTP real, mesmo padrão de
        conectar_lovable(). Contrato estrito: recebe só o link gerado pelo
        Lovable e o contato extraído pelo AgenteHunter, não os dicts inteiros
        de onde vêm.

        Args:
            link_demonstracao: URL da demo (ex: `conectar_lovable()`'s
                `url_demo_prevista`).
            whatsapp_contato: número de contato do lead, extraído pelo
                AgenteHunter (`DadosLead["whatsapp_contato"]`).

        Returns:
            {"sucesso": bool, "numero_formatado": str,
            "payload_envio": {"number", "text"}, "endpoint": str} — o
            payload final pronto para ser enviado à API de disparo real.

        Raises:
            ErroEnvioDemo: se o número de contato estiver vazio — nunca
                falha silenciosamente, dado que dados de contato são
                sensíveis.
        """
        numero_formatado = _formatar_numero_whatsapp(whatsapp_contato)
        if not numero_formatado:
            raise ErroEnvioDemo("Contato de WhatsApp vazio: impossível enviar link de demonstração")

        mensagem = (
            "🚀 *Seu site profissional já está pronto!*\n\n"
            f"Preparamos uma demonstração exclusiva para o seu negócio: {link_demonstracao}\n\n"
            "Esse layout foi pensado para transformar visitantes em clientes já na primeira "
            "impressão. Estamos com poucas vagas de ativação esta semana — responda agora "
            "e coloque seu site oficial no ar ainda hoje! 💼✨"
        )

        payload_envio = {
            "number": numero_formatado,
            "text": mensagem,
        }

        return {
            "sucesso": True,
            "numero_formatado": numero_formatado,
            "payload_envio": payload_envio,
            "endpoint": WHATSAPP_DISPATCH_API_URL_MOCK,
        }
