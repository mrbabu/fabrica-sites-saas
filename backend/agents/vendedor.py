#!/usr/bin/env python3
"""
Agente Vendedor - Fábrica de Sites SaaS
Responsável por conectar o site-config.json gerado pelo Agente Construtor ao
Lovable e enviar o link de demonstração ao lead capturado pelo AgenteHunter.

conectar_lovable() gera de verdade o prompt em linguagem natural (a partir do
site-config.json) que alimenta o Lovable — essa é a integração real, já que
o Lovable não expõe uma API de import de JSON. O que ainda é mockado em
ambas as funções é só a chamada HTTP (webhook do Lovable / API de disparo do
WhatsApp): elas montam o payload exatamente como seria enviado, para validar
o contrato de dados antes de existir uma integração HTTP real.
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


def _montar_prompt_lovable(site_config: Dict[str, Any]) -> str:
    """
    Traduz o site-config.json (contrato JSON do Agente Construtor) em um
    prompt de texto pronto para colar no chat do Lovable.

    O Lovable não tem uma API pública de import de JSON schema — ele é
    guiado por prompt em linguagem natural — então esta função É a
    integração real (determinística, sem chamada de IA) entre o nosso
    contrato e o Lovable: o texto que ela devolve é o que efetivamente
    gera a demo visual, usada só para mockups de venda. O motor de
    produção que entrega o site de verdade ao cliente continua sendo
    agent_construtor.py + index.html — não é substituído por isto.

    Mantém a mesma ordem de seções do template de produção (Hero →
    Serviços → Diferenciais → Depoimentos → FAQ → Chamada final → Contato/
    Rodapé) para que a demo pareça o mais fiel possível ao que o cliente
    vai efetivamente receber depois de fechar.
    """
    company = site_config.get("company", {})
    colors = site_config.get("colors", {})
    hero = site_config.get("hero", {})
    services = [s for s in site_config.get("services", []) if s.get("enabled", True)]
    features = [f for f in site_config.get("features", []) if f.get("enabled", True)]
    testimonials = [t for t in site_config.get("testimonials", []) if t.get("enabled", True)]
    faq = [f for f in site_config.get("faq", []) if f.get("enabled", True)]
    contact = site_config.get("contact", {})
    cta = site_config.get("cta", {})
    footer = site_config.get("footer", {})

    linhas = [
        f'Crie uma landing page de uma página só para "{company.get("name", "Empresa")}", '
        "em React + Tailwind, mobile-first e totalmente responsiva.",
        "",
        f"SLOGAN: {company.get('tagline', '')}",
        f"SOBRE A EMPRESA: {company.get('description', '')}",
        "",
        "PALETA DE CORES (usar exatamente estes hex, sem inventar novas cores):",
        f"- Primária: {colors.get('primary', '')}",
        f"- Primária escura (hover / estados ativos): {colors.get('primaryDark', '')}",
        f"- Secundária: {colors.get('secondary', '')}",
        f"- Destaque / CTA: {colors.get('accent', '')}",
        f"- Fundo: {colors.get('background', '#ffffff')}",
        f"- Texto principal: {colors.get('text', '#1f2937')}",
        "",
        "SEÇÃO HERO (topo, full-width, imagem de fundo com overlay em gradiente "
        "das cores primária/secundária acima):",
        f'- Título: "{hero.get("title", "")}"',
        f'- Subtítulo: "{hero.get("subtitle", "")}"',
        f'- Botão (CTA): "{hero.get("ctaText", "")}"',
        "",
    ]

    if services:
        linhas.append("SEÇÃO DE SERVIÇOS (grid de cards, um por serviço):")
        for s in services:
            linhas.append(f"- {s.get('icon', '')} {s.get('title', '')}: {s.get('description', '')}")
        linhas.append("")

    if features:
        linhas.append('SEÇÃO DE DIFERENCIAIS ("por que escolher a gente", ícone + texto curto):')
        for f in features:
            linhas.append(f"- {f.get('icon', '')} {f.get('title', '')}: {f.get('description', '')}")
        linhas.append("")

    if testimonials:
        linhas.append("SEÇÃO DE DEPOIMENTOS (cards lado a lado, com estrelas de avaliação):")
        for t in testimonials:
            estrelas = "⭐" * int(t.get("rating", 5))
            linhas.append(f'- "{t.get("content", "")}" — {t.get("name", "")}, {t.get("role", "")} {estrelas}')
        linhas.append("")

    if faq:
        linhas.append("SEÇÃO DE PERGUNTAS FREQUENTES (accordion):")
        for item in faq:
            linhas.append(f"- P: {item.get('question', '')}")
            linhas.append(f"  R: {item.get('answer', '')}")
        linhas.append("")

    if cta:
        linhas.append("SEÇÃO DE CHAMADA FINAL (banner de destaque antes do rodapé):")
        linhas.append(f'- Título: "{cta.get("title", "")}"')
        linhas.append(f'- Texto: "{cta.get("description", "")}"')
        linhas.append(f'- Botão: "{cta.get("buttonText", "")}"')
        linhas.append("")

    linhas.extend([
        "CONTATO (seção de contato e/ou rodapé):",
        f"- WhatsApp: {contact.get('whatsapp', '')}",
        f"- Telefone: {contact.get('phone', '')}",
        f"- E-mail: {contact.get('email', '')}",
        f"- Endereço: {contact.get('address', '')}",
        "",
        f"RODAPÉ: {footer.get('description', '')}",
        f"Copyright: {footer.get('copyrightText', '')}",
        "",
        "IMPORTANTE: manter a ordem das seções acima (Hero → Serviços → "
        "Diferenciais → Depoimentos → FAQ → Chamada final → Contato/Rodapé) — "
        "essa é a mesma estrutura do site que será entregue de verdade ao "
        "cliente. Este mockup é só para demonstração de vendas.",
    ])

    return "\n".join(linhas)


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
        Traduz o site-config.json em um prompt pronto para o Lovable e monta
        o restante do payload de entrega da demo.

        `prompt_lovable` é a parte real desta função — geração de texto
        determinística, sem chamada de IA, pronta para colar no chat do
        Lovable. `webhook_url` e `url_demo_prevista` continuam mockados: só
        viram chamada HTTP real quando/se o Lovable expuser uma API de
        criação de projeto que possamos automatizar.

        Args:
            site_config: site-config.json validado, gerado pelo Agente
                Construtor (ver `schema_validator.SiteConfig`).

        Returns:
            Payload de entrega da demo: `slug`, `prompt_lovable` (texto
            pronto pra colar no Lovable), `url_demo_prevista`, `webhook_url`
            (mock) e `corpo_requisicao` (site_config bruto, para auditoria).
        """
        nome_empresa = site_config.get("company", {}).get("name", "Site")
        slug = _slugificar(nome_empresa)

        return {
            "status": "mock_preparado",
            "slug": slug,
            "webhook_url": LOVABLE_WEBHOOK_URL_MOCK,
            "url_demo_prevista": f"https://preview.lovable.dev/{slug}",
            "prompt_lovable": _montar_prompt_lovable(site_config),
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
