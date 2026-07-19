#!/usr/bin/env python3
"""
Agente Construtor - Fábrica de Sites SaaS
Gera site-config.json completo a partir de dados de onboarding do cliente,
usando o AIProvider modular (NVIDIA NIM -> Anthropic -> Ollama)
"""

import json
import sys
import os
import time
import zlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote
import re

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from schema_validator import ValidadorSchema
from metrics import obter_metricas
from ai_provider import obter_ai_provider, ErroProvedorIA
from image_utils import _slugify, mapear_categoria, obter_imagens_categoria, ErroBancoImagens


MAX_TENTATIVAS_GERACAO = 3
ICONES_FALLBACK = ["⭐", "✅", "🔧", "📦", "🎯", "💡", "🛠️", "📋"]


def _lock_estavel(texto: str) -> int:
    """
    Deriva um inteiro estável a partir de uma string, para usar como
    ?lock= do LoremFlickr — sem isso, o serviço sorteia uma foto nova a
    cada requisição (ver hero.backgroundImage/company.logo em
    _preencher_fallbacks). CRC32 é suficiente aqui: só precisa ser estável
    e determinístico, não criptográfico.
    """
    return zlib.crc32(texto.encode("utf-8"))


def _truncar_para_limite(texto: str, limite: int) -> str:
    """
    Corta um texto que excede um limite de caracteres, preferindo quebrar
    no último espaço (sem partir palavra no meio) e removendo pontuação
    solta que sobrar na borda do corte.
    """
    texto = texto.strip()
    if len(texto) <= limite:
        return texto
    cortado = texto[:limite]
    ultimo_espaco = cortado.rfind(" ")
    if ultimo_espaco > 0:
        cortado = cortado[:ultimo_espaco]
    return cortado.rstrip(" ,.-–—")


class AgenteConstrutor:
    """Agente que gera configuração de site baseado em dados de onboarding do cliente"""

    def __init__(self):
        """Inicializa o agente com o provedor de IA modular (NIM/Anthropic/Ollama)"""
        self.ai = obter_ai_provider()
        print(f"✅ Agente Construtor pronto (cadeia de provedores: {' -> '.join(self.ai.ordem)})")

    def gerar_paleta_cores(self, cor_primaria: str) -> dict:
        """
        Gera paleta de 8 cores hexadecimais complementares baseada em cor primária

        Args:
            cor_primaria: Cor em formato hex (ex: #6366f1)

        Returns:
            Dicionário com 8 variações de cores
        """
        prompt = f"""Você é um designer de cores especialista. Dada a cor primária {cor_primaria},
gere uma paleta harmônica de 8 cores hexadecimais complementares.

Retorne APENAS um JSON válido no seguinte formato (sem explicações):
{{
    "primary": "{cor_primaria}",
    "primaryDark": "#...",
    "secondary": "#...",
    "accent": "#...",
    "background": "#ffffff",
    "text": "#...",
    "textLight": "#...",
    "border": "#..."
}}

Regras:
- primary: a cor fornecida
- primaryDark: versão mais escura (aprox -20% de luminosidade)
- secondary: cor complementar harmônica
- accent: cor que contrasta bem
- background: deve ser clara (#ffffff ou similar)
- text: cor escura para texto (#1f2937 ou similar)
- textLight: cor cinza para texto secundário (#6b7280 ou similar)
- border: cor muito clara (#e5e7eb ou similar)

Todas as cores devem ser hexadecimais válidas. Sem markdown, sem explicações."""

        try:
            return self.ai.gerar_json(prompt, max_tokens=512)
        except (ErroProvedorIA, json.JSONDecodeError) as e:
            print(f"Aviso: Não foi possível gerar paleta de cores ({e}). Usando padrão.")
            return {
                "primary": cor_primaria,
                "primaryDark": "#4f46e5",
                "secondary": "#ec4899",
                "accent": "#f59e0b",
                "background": "#ffffff",
                "text": "#1f2937",
                "textLight": "#6b7280",
                "border": "#e5e7eb"
            }

    def gerar_config_site(
        self,
        nome_empresa: str,
        nicho: str,
        cor_primaria: str,
        localizacao: Optional[str] = None,
        whatsapp_contato: Optional[str] = None,
        logo_url: Optional[str] = None,
        descricao_negocio: Optional[str] = None,
        portfolio_urls: list[str] | None = None,
    ) -> dict:
        """
        Gera configuração completa de site usando o AIProvider, com SEO by design

        Args:
            nome_empresa: Nome da empresa
            nicho: Nicho/ramo de atuação (ex: ramo_atividade do onboarding)
            cor_primaria: Cor primária em hex
            localizacao: Cidade/região do negócio, usada para SEO local (opcional)
            whatsapp_contato: Número de WhatsApp do cliente (opcional)
            logo_url: URL/caminho do logo já normalizado (opcional)
            descricao_negocio: Contexto livre sobre o negócio, informado pelo
                próprio cliente (opcional) — usado só para enriquecer a copy,
                nunca para inventar dados factuais (contato/redes/depoimentos)
            portfolio_urls: links diretos de imagem (JPG/PNG/WebP) do
                trabalho real do cliente, já validados pelo chamador
                (opcional). Mesmo padrão de logo_url — nunca upload, só
                link já pronto e já hospedado publicamente; a validação de
                formato/esquema/quantidade é responsabilidade da camada de
                entrada (ver DemoDfyRequest em routers/demo_dfy.py), este
                método assume que a lista já chegou válida. Quando
                fornecida, substitui o fallback de stock photo (LoremFlickr)
                em hero.backgroundImage e sections[].image; não afeta
                company.logo (ver logo_url para isso)

        Returns:
            Dicionário com configuração completa do site
        """
        # Gerar paleta de cores
        print(f"🎨 Gerando paleta de cores complementares para {cor_primaria}...")
        cores = self.gerar_paleta_cores(cor_primaria)

        bloco_seo = self._montar_instrucoes_seo(nicho, localizacao)

        # Bloco de contato: com whatsapp_contato informado, o prompt já recebe o
        # número real em phone/whatsapp (nunca um valor fictício pra corrigir
        # depois). Sem whatsapp_contato, preserva o comportamento legado — só
        # para compatibilidade com chamadores que ainda não passam esse parâmetro
        # (ex.: gerar_portfolio_lovable.py). _preencher_fallbacks() continua
        # sendo a segunda camada de segurança, não a única.
        if whatsapp_contato:
            contato_phone_prompt = whatsapp_contato
            contato_whatsapp_prompt = whatsapp_contato
        else:
            contato_phone_prompt = "+55 11 98765-4321"
            contato_whatsapp_prompt = "+5511987654321"

        # Prompt para o modelo gerar o JSON completo
        prompt = f"""Você é um especialista em marketing, copywriting e SEO para criar sites profissionais de alto impacto.

Crie um arquivo site-config.json COMPLETO e altamente persuasivo para:
- Empresa: {nome_empresa}
- Nicho/Ramo de atividade: {nicho}
- Localização: {localizacao or "não informada"}
- Cor Primária: {cor_primaria}
{f'- Contexto sobre o negócio, informado pelo próprio cliente (use para tornar a copy mais específica e realista, mas sem inventar dados factuais como contato, redes sociais ou depoimentos): {descricao_negocio}' if descricao_negocio else ''}

IMPORTANTE:
1. Retorne APENAS um JSON válido, sem markdown, sem explicações
2. O JSON deve seguir EXATAMENTE este schema
3. Crie copys persuasivos e impactantes adaptados ao nicho "{nicho}"
4. Use a cor primária {cor_primaria} e a paleta {json.dumps(cores)}
5. Gere 3 serviços principais para o nicho {nicho}
6. NÃO gere depoimentos de clientes — retorne "testimonials": [] (a plataforma só publica depoimentos reais fornecidos pelo próprio cliente, nunca fabricados pela IA)
7. Todas as strings devem estar em português (Brasil)

{bloco_seo}

Schema obrigatório (respeite ESTRITAMENTE os limites de caracteres indicados entre parênteses):
{{
  "metadata": {{
    "siteTitle": "string (mínimo 5, MÁXIMO 60 caracteres) - Título SEO do site, com palavra-chave do nicho{' e localização' if localizacao else ''}",
    "siteDescription": "string (mínimo 10, MÁXIMO 160 caracteres) - Meta description focada em conversão",
    "favicon": "emoji",
    "keywords": ["5 a 8 palavras-chave de SEO relacionadas ao nicho, cada uma uma string curta"]
  }},
  "company": {{
    "name": "string (máximo 100 caracteres)",
    "tagline": "string (mínimo 5, máximo 100 caracteres) - Slogan impactante",
    "description": "string (mínimo 20, máximo 500 caracteres) - Descrição 2-3 frases",
    "logo": "string - URL placeholder"
  }},
  "colors": {json.dumps(cores)},
  "hero": {{
    "title": "string (mínimo 10, máximo 200 caracteres) - Título principal impactante (funciona como H1: inclua a palavra-chave do nicho{' e a localização' if localizacao else ''})",
    "subtitle": "string (mínimo 10, máximo 300 caracteres) - Subtítulo persuasivo",
    "ctaText": "string (mínimo 3, máximo 50 caracteres) - Texto do botão CTA",
    "ctaLink": "#contato",
    "backgroundImage": "",
    "enabled": true
  }},
  "sections": [
    {{
      "id": "sobre",
      "type": "content",
      "title": "string (mínimo 5, máximo 100 caracteres) - Título seção",
      "subtitle": "string (mínimo 5, máximo 200 caracteres) - Subtítulo",
      "content": "string (mínimo 20, máximo 1000 caracteres) - Conteúdo 3-4 frases, rico em palavras-chave do ramo de atividade",
      "image": "",
      "enabled": true
    }}
  ],
  "services": [
    {{
      "id": 1,
      "title": "string (mínimo 5, máximo 100 caracteres) - Nome do serviço",
      "description": "string (mínimo 20, máximo 300 caracteres) - Descrição curta e impactante",
      "icon": "string OBRIGATÓRIO (exatamente 1 caractere, 1-2 de tamanho) - um único emoji relacionado ao serviço, ex: \"🍞\"",
      "features": ["feature1", "feature2", "feature3"],
      "enabled": true
    }},
    {{
      "id": 2,
      "title": "string (mínimo 5, máximo 100 caracteres)",
      "description": "string (mínimo 20, máximo 300 caracteres)",
      "icon": "string OBRIGATÓRIO (exatamente 1 caractere, 1-2 de tamanho) - um único emoji relacionado ao serviço, ex: \"🎂\"",
      "features": ["feature1", "feature2", "feature3"],
      "enabled": true
    }},
    {{
      "id": 3,
      "title": "string (mínimo 5, máximo 100 caracteres)",
      "description": "string (mínimo 20, máximo 300 caracteres)",
      "icon": "string OBRIGATÓRIO (exatamente 1 caractere, 1-2 de tamanho) - um único emoji relacionado ao serviço, ex: \"🚚\"",
      "features": ["feature1", "feature2", "feature3"],
      "enabled": true
    }}
  ],
  "features": [
    {{
      "id": 1,
      "title": "string (mínimo 5, máximo 80 caracteres) - Nome do diferencial competitivo",
      "description": "string (mínimo 20, máximo 200 caracteres) - Por que isso é um diferencial",
      "icon": "string OBRIGATÓRIO (1-2 de tamanho) - um único emoji relacionado, ex: \"⚡\"",
      "enabled": true
    }},
    {{
      "id": 2,
      "title": "string (mínimo 5, máximo 80 caracteres)",
      "description": "string (mínimo 20, máximo 200 caracteres)",
      "icon": "string OBRIGATÓRIO (1-2 de tamanho) - emoji, ex: \"✅\"",
      "enabled": true
    }},
    {{
      "id": 3,
      "title": "string (mínimo 5, máximo 80 caracteres)",
      "description": "string (mínimo 20, máximo 200 caracteres)",
      "icon": "string OBRIGATÓRIO (1-2 de tamanho) - emoji, ex: \"🎯\"",
      "enabled": true
    }}
  ],
  "testimonials": [],
  "faq": [
    {{
      "id": 1,
      "question": "string (mínimo 10, máximo 150 caracteres) - Pergunta frequente realista do nicho \"{nicho}\"",
      "answer": "string (mínimo 10, máximo 400 caracteres) - Resposta persuasiva e curta",
      "enabled": true
    }},
    {{
      "id": 2,
      "question": "string (mínimo 10, máximo 150 caracteres)",
      "answer": "string (mínimo 10, máximo 400 caracteres)",
      "enabled": true
    }},
    {{
      "id": 3,
      "question": "string (mínimo 10, máximo 150 caracteres)",
      "answer": "string (mínimo 10, máximo 400 caracteres)",
      "enabled": true
    }},
    {{
      "id": 4,
      "question": "string (mínimo 10, máximo 150 caracteres)",
      "answer": "string (mínimo 10, máximo 400 caracteres)",
      "enabled": true
    }}
  ],
  "contact": {{
    "email": null,
    "phone": "{contato_phone_prompt}",
    "whatsapp": "{contato_whatsapp_prompt}",
    "address": "{localizacao or 'São Paulo, SP - Brasil'}",
    "social": {{}}
  }},
  "cta": {{
    "title": "string (mínimo 10, máximo 200 caracteres) - Chamada final impactante",
    "description": "string (mínimo 10, máximo 300 caracteres) - Descrição curta do benefício",
    "buttonText": "string (mínimo 3, máximo 50 caracteres) - Texto botão",
    "buttonLink": "mailto:contato@{nome_empresa.lower().replace(' ', '')}.com",
    "enabled": true
  }}
}}

Instruções de copywriting para o nicho "{nicho}":
- Hero: Crie urgência e prometa resultados mensuráveis
- Serviços: Descreva benefícios, não apenas features
- Diferenciais (features): Destaque o que torna o negócio diferente da concorrência
- FAQ: Antecipe as dúvidas mais comuns de quem procura "{nicho}" antes de comprar/contratar
- CTA: Use linguagem ativa e persuasiva
- Todos os textos devem ser concisos mas impactantes

ATENÇÃO:
- Nenhum campo "icon" pode ficar vazio. Cada serviço PRECISA ter um emoji real e visível no campo "icon" (nunca "" ou null).
- Os limites de caracteres MÍNIMO e MÁXIMO indicados em cada campo são REGRAS RÍGIDAS. Nunca ultrapasse o máximo indicado, mesmo que precise encurtar o texto.
- NUNCA use "via.placeholder.com" ou qualquer outro serviço de placeholder para os campos de imagem (hero.backgroundImage, sections[].image, testimonials[].avatar, company.logo). Se não souber uma URL de imagem real, deixe o campo como string vazia "" — o sistema preenche automaticamente com uma imagem real depois.
- NUNCA invente contact.email ou contact.social (instagram/facebook/linkedin/twitter). Retorne sempre "email": null e "social": {{}}.
- NÃO gere depoimentos (testimonials) — retorne sempre "testimonials": [].

Retorne APENAS o JSON, sem nenhum texto adicional ou markdown."""

        print(f"🤖 Gerando configuração (SEO by design) via {' -> '.join(self.ai.ordem)}...")

        ultimo_erro = None
        for tentativa in range(1, MAX_TENTATIVAS_GERACAO + 1):
            config = self.ai.gerar_json(prompt, max_tokens=4096)
            print(f"   ↳ Provedor utilizado: {self.ai.provedor_ativo}")

            if logo_url:
                config.setdefault("company", {})["logo"] = logo_url

            config = self._autocorrigir(config)
            config = self._preencher_fallbacks(
                config,
                nicho,
                nome_empresa,
                tem_logo_explicito=bool(logo_url),
                whatsapp_contato=whatsapp_contato,
                portfolio_urls=portfolio_urls,
            )

            # Validar schema básico (campos obrigatórios presentes)
            self._validar_schema(config)

            # Validação completa (tipos, tamanhos, regras de negócio)
            valido, erro, _ = ValidadorSchema.validar_json(config)
            if valido:
                return config

            ultimo_erro = erro
            print(f"⚠️  Validação de conteúdo falhou na tentativa {tentativa}/{MAX_TENTATIVAS_GERACAO}: {erro}")

        raise ValueError(f"Schema inválido após {MAX_TENTATIVAS_GERACAO} tentativas: {ultimo_erro}")

    def _autocorrigir(self, config: dict) -> dict:
        """
        Corrige determinísticamente problemas comuns e recorrentes que o modelo
        às vezes deixa passar apesar das instruções do prompt (ex: icon vazio).
        Falhas que exigem regenerar conteúdo (campos curtos/longos demais) não
        são adivinhadas aqui — o laço de retry em gerar_config_site tenta de novo.

        Exceção: metadata.siteTitle. Com nicho + localização longos (ex.:
        "Igreja Católica Apostólica Romana" + "Vitória ES - Mata da Praia"),
        só as duas palavras-chave já somam mais que os 60 caracteres do
        limite — a instrução do prompt (combinar nicho+localização no
        siteTitle) e o limite de tamanho ficam matematicamente incompatíveis,
        e o retry sozinho não resolve (resorteia o texto, não encurta a
        combinação de entrada, tende a estourar de novo). Por isso, ao
        contrário dos outros campos de tamanho, aqui aplicamos corte
        determinístico em vez de só confiar no retry.
        """
        metadata = config.get("metadata") or {}
        site_title = (metadata.get("siteTitle") or "").strip()
        if len(site_title) > 60:
            metadata["siteTitle"] = _truncar_para_limite(site_title, 60)

        for i, servico in enumerate(config.get("services", []) or []):
            icon = (servico.get("icon") or "").strip()
            if not (1 <= len(icon) <= 2):
                servico["icon"] = ICONES_FALLBACK[i % len(ICONES_FALLBACK)]

        for i, diferencial in enumerate(config.get("features", []) or []):
            icon = (diferencial.get("icon") or "").strip()
            if not (1 <= len(icon) <= 2):
                diferencial["icon"] = ICONES_FALLBACK[i % len(ICONES_FALLBACK)]

        return config

    def _preencher_fallbacks(
        self,
        config: dict,
        nicho: str,
        nome_empresa: str,
        tem_logo_explicito: bool = False,
        whatsapp_contato: Optional[str] = None,
        portfolio_urls: list[str] | None = None,
    ) -> dict:
        """
        Garante que nenhum campo de imagem/SEO derivado fique vazio ou quebrado
        no JSON final. A IA às vezes retorna "" para favicon/logo/backgroundImage/
        image/avatar, ou copia URLs de serviços de placeholder (via.placeholder.com
        e similares) que não carregam de verdade; aqui aplicamos fallbacks
        determinísticos (sem custo de API), usando LoremFlickr (fotos reais por
        palavra-chave, sem API key) e pravatar.cc (avatares de pessoa para
        depoimentos). Os campos ogTitle/ogDescription/ogImage e o objeto footer
        são sempre derivados aqui, nunca pedidos à IA.

        portfolio_urls (opcional, já validado pelo chamador): quando presente,
        tem prioridade sobre o banco de imagens curado (Unsplash, por
        categoria de nicho) em hero.backgroundImage e sections[].image —
        fotos reais do cliente sempre substituem stock photo. Não afeta
        company.logo. Lista vazia/None preserva exatamente o comportamento
        atual (zero mudança de comportamento sem portfólio).

        Sem portfolio_urls, a imagem vem do banco curado por categoria
        (mapear_categoria() + obter_imagens_categoria(), ver image_utils.py);
        se o Unsplash não estiver configurado ou a busca falhar, cai pro
        LoremFlickr com ?lock= estável (rede de segurança, nunca quebra a
        geração do site).
        """
        nicho_slug = _slugify(nicho) or "negocio"
        empresa_slug = _slugify(nome_empresa) or "empresa"

        def _url_invalida(url: Optional[str]) -> bool:
            url = (url or "").strip().lower()
            return not url or "placeholder" in url

        categoria_imagem = mapear_categoria(nicho)
        try:
            imagens_categoria = obter_imagens_categoria(categoria_imagem)
        except ErroBancoImagens as e:
            print(
                f"Aviso: banco de imagens curado indisponível para "
                f"'{categoria_imagem}' ({e}). Usando fallback LoremFlickr."
            )
            imagens_categoria = None

        def _imagem_curada(chave_lock: str) -> Optional[str]:
            if not imagens_categoria:
                return None
            indice = _lock_estavel(chave_lock) % len(imagens_categoria)
            return imagens_categoria[indice]

        metadata = config.setdefault("metadata", {})
        if not (metadata.get("favicon") or "").strip():
            metadata["favicon"] = "🚀"
        if not metadata.get("keywords"):
            metadata["keywords"] = [
                palavra for palavra in re.split(r"\s+", nicho.strip().lower()) if palavra
            ]

        hero = config.setdefault("hero", {})
        if portfolio_urls:
            hero["backgroundImage"] = portfolio_urls[0]
        elif _url_invalida(hero.get("backgroundImage")):
            imagem_curada = _imagem_curada(f"{empresa_slug}-hero")
            if imagem_curada:
                hero["backgroundImage"] = imagem_curada
            else:
                lock_hero = _lock_estavel(f"{empresa_slug}-hero")
                hero["backgroundImage"] = f"https://loremflickr.com/1920/600/{nicho_slug}?lock={lock_hero}"

        # Foto de banco (mesmo curada) não faz sentido como "logo" — trocado
        # por um avatar de iniciais (determinístico: mesmo nome = mesmo
        # resultado), usando a cor primária já gerada pra paleta do site.
        company = config.setdefault("company", {})
        if not tem_logo_explicito and _url_invalida(company.get("logo")):
            cor_fundo = (config.get("colors", {}).get("primary") or "#6366f1").lstrip("#")
            company["logo"] = (
                f"https://ui-avatars.com/api/?name={quote(nome_empresa)}"
                f"&background={cor_fundo}&color=fff&size=400&bold=true"
            )

        for i, secao in enumerate(config.get("sections", []) or []):
            if portfolio_urls:
                secao["image"] = portfolio_urls[(i + 1) % len(portfolio_urls)]
            elif _url_invalida(secao.get("image")):
                imagem_curada = _imagem_curada(f"{empresa_slug}-secao-{i}")
                if imagem_curada:
                    secao["image"] = imagem_curada
                else:
                    secao["image"] = f"https://loremflickr.com/500/400/{nicho_slug}?lock={i}"

        for i, depoimento in enumerate(config.get("testimonials", []) or []):
            if _url_invalida(depoimento.get("avatar")):
                depoimento["avatar"] = f"https://i.pravatar.cc/150?u={empresa_slug}-{i}"

        # Guardrail: email/social/depoimentos nunca são fatos inventados — sempre
        # zerados aqui, independente do que a IA tenha retornado. phone/whatsapp
        # já chegam corretos do próprio prompt quando whatsapp_contato é informado
        # (ver bloco "contact" em gerar_config_site); esta sobrescrita é a segunda
        # camada de segurança, não a única. Quando whatsapp_contato NÃO é informado
        # (chamador legado, ex.: gerar_portfolio_lovable.py), phone/whatsapp/address
        # mantêm o comportamento antigo (podem conter números/localização
        # genéricos) — isso NÃO é a garantia do fluxo DFY, só compatibilidade
        # preservada.
        contact = config.setdefault("contact", {})
        contact["email"] = None
        contact["social"] = {}
        if whatsapp_contato:
            contact["whatsapp"] = whatsapp_contato
            contact["phone"] = whatsapp_contato
        config["testimonials"] = []

        # SEO/OG derivados sempre de metadata/hero já preenchidos acima
        metadata["ogTitle"] = metadata.get("siteTitle", "")
        metadata["ogDescription"] = metadata.get("siteDescription", "")
        metadata["ogImage"] = hero.get("backgroundImage", "")

        # Rodapé é 100% derivado (nunca pedido à IA) para evitar mais uma
        # superfície de falha/retry no modelo
        links_footer = [
            {"label": secao.get("title", ""), "url": f"#{secao.get('id', '')}"}
            for secao in (config.get("sections", []) or [])
            if secao.get("enabled", True) and secao.get("title") and secao.get("id")
        ]
        links_footer.append({"label": "Contato", "url": "#contato"})

        config["footer"] = {
            "description": company.get("description", "") or f"{nome_empresa} - {nicho}",
            "links": links_footer,
            "copyrightText": f"© {datetime.now().year} {nome_empresa}. Todos os direitos reservados.",
        }

        return config

    def _montar_instrucoes_seo(self, nicho: str, localizacao: Optional[str]) -> str:
        """Monta o bloco de instruções de SEO 'by design' injetado no prompt"""
        if localizacao:
            local_instrucao = (
                f'- Combine a palavra-chave do nicho "{nicho}" com a localização "{localizacao}" '
                f'no título principal (H1) e no siteTitle, no formato natural '
                f'"{nicho} em {localizacao}" ou equivalente.'
            )
        else:
            local_instrucao = (
                f'- Nenhuma localização foi informada: foque a otimização apenas na palavra-chave '
                f'do nicho "{nicho}", sem inventar uma cidade/região.'
            )

        return f"""BLOCO DE SEO "BY DESIGN" (obrigatório seguir):
{local_instrucao}
- O campo metadata.siteDescription deve funcionar como meta description: resumir a proposta de
  valor e terminar com uma chamada para ação que incentive o clique/conversão.
- O campo hero.title atua como H1 da página: deve conter a palavra-chave principal do nicho de
  forma natural (não robotizada).
- Os campos sections[].content e services[].description devem ser ricos em palavras-chave e
  termos relacionados ao ramo de atividade "{nicho}", mantendo a leitura natural (sem keyword
  stuffing)."""

    def _validar_schema(self, config: dict) -> None:
        """
        Valida se o JSON segue o schema esperado

        Args:
            config: Dicionário de configuração

        Raises:
            ValueError: Se o schema não estiver correto
        """
        campos_obrigatorios = [
            "metadata", "company", "colors", "hero",
            "sections", "services", "features", "testimonials", "faq",
            "contact", "cta", "footer"
        ]

        for campo in campos_obrigatorios:
            if campo not in config:
                raise ValueError(f"Campo obrigatório ausente: {campo}")

        # Validar cores
        cores_obrigatorias = [
            "primary", "primaryDark", "secondary", "accent",
            "background", "text", "textLight", "border"
        ]
        for cor in cores_obrigatorias:
            if cor not in config["colors"]:
                raise ValueError(f"Cor obrigatória ausente: {cor}")

    def salvar_config(self, config: dict, caminho: str = "site-config.json") -> str:
        """
        Salva configuração em arquivo JSON

        Args:
            config: Dicionário de configuração
            caminho: Caminho do arquivo

        Returns:
            Caminho do arquivo salvo
        """
        caminho_abs = Path(caminho).absolute()
        caminho_abs.parent.mkdir(parents=True, exist_ok=True)

        with open(caminho_abs, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return str(caminho_abs)

    def executar(
        self,
        nome_empresa: str,
        nicho: str,
        cor_primaria: str,
        caminho_saida: str = "site-config.json",
        localizacao: Optional[str] = None,
        whatsapp_contato: Optional[str] = None,
        logo_url: Optional[str] = None,
        descricao_negocio: Optional[str] = None,
        portfolio_urls: list[str] | None = None,
    ) -> dict:
        """
        Executa o pipeline completo de geração

        Args:
            nome_empresa: Nome da empresa
            nicho: Nicho/ramo de atuação
            cor_primaria: Cor primária em hex
            caminho_saida: Caminho do arquivo de saída
            localizacao: Cidade/região do negócio (opcional, para SEO local)
            whatsapp_contato: WhatsApp do cliente (opcional)
            logo_url: URL/caminho do logo já normalizado (opcional)
            descricao_negocio: Contexto livre sobre o negócio, informado pelo
                cliente (opcional)
            portfolio_urls: links diretos de imagem do trabalho real do
                cliente, já validados pelo chamador (opcional) — ver
                gerar_config_site() para o comportamento exato

        Returns:
            Configuração gerada
        """
        metricas = obter_metricas()
        tempo_inicio = time.time()

        print(f"\n{'='*60}")
        print(f"🚀 AGENTE CONSTRUTOR - Fábrica de Sites SaaS")
        print(f"{'='*60}")
        print(f"\n📋 Dados fornecidos:")
        print(f"  • Empresa: {nome_empresa}")
        print(f"  • Nicho: {nicho}")
        print(f"  • Localização: {localizacao or 'não informada'}")
        print(f"  • Cor Primária: {cor_primaria}")
        print(f"\n{'='*60}\n")

        try:
            # gerar_config_site já tenta até MAX_TENTATIVAS_GERACAO vezes
            # internamente (com autocorreção) antes de desistir.
            config = self.gerar_config_site(
                nome_empresa, nicho, cor_primaria,
                localizacao=localizacao,
                whatsapp_contato=whatsapp_contato,
                logo_url=logo_url,
                descricao_negocio=descricao_negocio,
                portfolio_urls=portfolio_urls,
            )

            # Validação final (config já passou por isso dentro de gerar_config_site,
            # mas repetimos aqui, sem custo de API, para obter o objeto Pydantic)
            print("🔍 Validando schema...")
            valido, erro, config_obj = ValidadorSchema.validar_json(config)

            if not valido:
                print(f"❌ Validação falhou: {erro}\n")
                metricas.registrar_geracao(
                    nome_empresa, nicho, False,
                    time.time() - tempo_inicio, erro=erro
                )
                raise ValueError(f"Schema inválido: {erro}")

            print("✅ Schema válido!\n")
            metricas.registrar_validacao(caminho_saida, True)

            caminho_salvo = self.salvar_config(config, caminho_saida)
            tempo_total = time.time() - tempo_inicio

            print(f"💾 Arquivo salvo em: {caminho_salvo}\n")

            # Exibir resumo
            print(f"📊 Resumo da configuração:")
            print(f"  • Título do site: {config_obj.metadata.siteTitle}")
            print(f"  • Tagline: {config_obj.company.tagline}")
            print(f"  • Serviços: {len([s for s in config_obj.services if s.enabled])}")
            print(f"  • Depoimentos: {len([t for t in config_obj.testimonials if t.enabled])}")
            print(f"  • Paleta de cores: {len(config_obj.colors.model_dump())} cores")
            print(f"\n{'='*60}\n")

            # Registrar sucesso
            metricas.registrar_geracao(
                nome_empresa, nicho, True, tempo_total
            )

            return config

        except Exception as e:
            tempo_total = time.time() - tempo_inicio
            print(f"\n❌ Erro ao gerar configuração: {e}")
            metricas.registrar_geracao(
                nome_empresa, nicho, False, tempo_total, erro=str(e)
            )
            raise


def main():
    """Função principal para uso via CLI"""
    print("\n🎯 Agente Construtor - Fábrica de Sites SaaS\n")

    # Coletar inputs
    nome_empresa = input("📝 Nome da Empresa: ").strip()
    if not nome_empresa:
        nome_empresa = "Minha Empresa"

    nicho = input("🏢 Nicho/Ramo de Atuação (ex: Software, Consultoria, E-commerce): ").strip()
    if not nicho:
        nicho = "Negócios"

    localizacao = input("📍 Localização (cidade/região, opcional): ").strip() or None

    cor_primaria = input("🎨 Cor de Preferência em HEX (ex: #6366f1): ").strip()
    if not cor_primaria:
        cor_primaria = "#6366f1"

    # Validar cor
    if not re.match(r'^#[0-9a-fA-F]{6}$', cor_primaria):
        print(f"⚠️  Cor inválida. Usando padrão #6366f1")
        cor_primaria = "#6366f1"

    try:
        agente = AgenteConstrutor()
        config = agente.executar(
            nome_empresa=nome_empresa,
            nicho=nicho,
            cor_primaria=cor_primaria,
            localizacao=localizacao,
        )

        print("✨ Site config.json pronto para uso!")
        print("📌 Próximo passo: Abra index.html no navegador para visualizar")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
