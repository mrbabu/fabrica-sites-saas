#!/usr/bin/env python3
"""
Validador de Schema - Fábrica de Sites SaaS
Define e valida o contrato que site-config.json deve seguir
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator
import re
import json


# ============================================================================
# SCHEMA MODELS - Definem o contrato que todo JSON deve seguir
# ============================================================================

class Metadata(BaseModel):
    """Informações de metadata do site"""
    siteTitle: str = Field(..., min_length=5, max_length=60, description="Título SEO")
    siteDescription: str = Field(..., min_length=10, max_length=160, description="Meta description")
    favicon: str = Field(default="🚀", description="Emoji ou URL")
    keywords: List[str] = Field(default_factory=list, max_items=10, description="Palavras-chave de SEO")
    ogTitle: str = Field(default="", description="Título Open Graph (derivado de siteTitle)")
    ogDescription: str = Field(default="", description="Descrição Open Graph (derivada de siteDescription)")
    ogImage: str = Field(default="", description="Imagem Open Graph (derivada de hero.backgroundImage)")

    class Config:
        examples = [{
            "siteTitle": "Meu Negócio Profissional",
            "siteDescription": "Descrição breve do seu negócio",
            "favicon": "🚀",
            "keywords": ["negócio", "profissional"],
            "ogTitle": "Meu Negócio Profissional",
            "ogDescription": "Descrição breve do seu negócio",
            "ogImage": "https://loremflickr.com/1920/600/negocio"
        }]


class Company(BaseModel):
    """Informações da empresa"""
    name: str = Field(..., min_length=2, max_length=100, description="Nome da empresa")
    tagline: str = Field(..., min_length=5, max_length=100, description="Slogan/proposta de valor")
    description: str = Field(..., min_length=20, max_length=500, description="Descrição completa")
    logo: str = Field(default="https://loremflickr.com/180/50/logo", description="URL do logo")

    class Config:
        examples = [{
            "name": "Minha Empresa",
            "tagline": "Transformando negócios",
            "description": "Somos especializados em inovação...",
            "logo": "https://loremflickr.com/180/50/logo"
        }]


class Colors(BaseModel):
    """Paleta de cores em hexadecimal"""
    primary: str = Field(..., description="Cor primária")
    primaryDark: str = Field(..., description="Cor primária escura")
    secondary: str = Field(..., description="Cor secundária")
    accent: str = Field(..., description="Cor de destaque")
    background: str = Field(default="#ffffff", description="Cor de fundo")
    text: str = Field(default="#1f2937", description="Cor de texto principal")
    textLight: str = Field(default="#6b7280", description="Cor de texto secundário")
    border: str = Field(default="#e5e7eb", description="Cor de bordas")

    @validator('primary', 'primaryDark', 'secondary', 'accent', 'background', 'text', 'textLight', 'border')
    def validate_hex_color(cls, v):
        """Valida se a cor está em formato hexadecimal válido"""
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError(f'Cor deve estar em formato hex válido: {v}')
        return v.lower()

    class Config:
        examples = [{
            "primary": "#6366f1",
            "primaryDark": "#4f46e5",
            "secondary": "#ec4899",
            "accent": "#f59e0b",
            "background": "#ffffff",
            "text": "#1f2937",
            "textLight": "#6b7280",
            "border": "#e5e7eb"
        }]


class Hero(BaseModel):
    """Seção hero do site"""
    title: str = Field(..., min_length=10, max_length=200, description="Título principal")
    subtitle: str = Field(..., min_length=10, max_length=300, description="Subtítulo")
    ctaText: str = Field(..., min_length=3, max_length=50, description="Texto do botão")
    ctaLink: str = Field(default="#contato", description="Link do botão")
    backgroundImage: str = Field(default="https://loremflickr.com/1920/600/negocio", description="URL background")
    enabled: bool = Field(default=True, description="Ativar/desativar seção")

    class Config:
        examples = [{
            "title": "Bem-vindo ao Futuro",
            "subtitle": "Soluções inovadoras",
            "ctaText": "Começar Agora",
            "ctaLink": "#contato",
            "backgroundImage": "https://loremflickr.com/1920/600/negocio",
            "enabled": True
        }]


class Section(BaseModel):
    """Seção de conteúdo genérica"""
    id: str = Field(..., min_length=3, max_length=50, description="ID único da seção")
    type: str = Field(default="content", description="Tipo de seção")
    title: str = Field(..., min_length=5, max_length=100, description="Título")
    subtitle: str = Field(..., min_length=5, max_length=200, description="Subtítulo")
    content: str = Field(..., min_length=20, max_length=1000, description="Conteúdo")
    image: str = Field(default="https://loremflickr.com/500/400/negocio", description="URL imagem")
    enabled: bool = Field(default=True, description="Ativar/desativar")

    class Config:
        examples = [{
            "id": "sobre",
            "type": "content",
            "title": "Sobre Nós",
            "subtitle": "Nossa história",
            "content": "Somos uma empresa...",
            "image": "https://loremflickr.com/500/400/negocio",
            "enabled": True
        }]


class Service(BaseModel):
    """Serviço oferecido"""
    id: int = Field(..., description="ID único do serviço")
    title: str = Field(..., min_length=5, max_length=100, description="Nome do serviço")
    description: str = Field(..., min_length=20, max_length=300, description="Descrição")
    icon: str = Field(..., min_length=1, max_length=2, description="Emoji do serviço")
    features: List[str] = Field(default_factory=list, min_items=1, max_items=10, description="Features")
    enabled: bool = Field(default=True, description="Ativar/desativar")

    @validator('features')
    def validate_features(cls, v):
        """Valida features"""
        if not v or len(v) < 1:
            raise ValueError('Deve ter pelo menos 1 feature')
        return v

    class Config:
        examples = [{
            "id": 1,
            "title": "Serviço 1",
            "description": "Descrição breve",
            "icon": "⚡",
            "features": ["Feature 1", "Feature 2"],
            "enabled": True
        }]


class Testimonial(BaseModel):
    """Depoimento de cliente"""
    id: int = Field(..., description="ID único")
    name: str = Field(..., min_length=3, max_length=100, description="Nome do cliente")
    role: str = Field(..., min_length=5, max_length=100, description="Profissão/empresa")
    content: str = Field(..., min_length=20, max_length=500, description="Conteúdo do depoimento")
    avatar: str = Field(default="https://i.pravatar.cc/100", description="URL avatar")
    rating: int = Field(default=5, ge=1, le=5, description="Avaliação 1-5")
    enabled: bool = Field(default=True, description="Ativar/desativar")

    class Config:
        examples = [{
            "id": 1,
            "name": "João Silva",
            "role": "CEO - Tech",
            "content": "Excelente serviço!",
            "avatar": "https://i.pravatar.cc/100",
            "rating": 5,
            "enabled": True
        }]


class Feature(BaseModel):
    """Diferencial competitivo"""
    id: int = Field(..., description="ID único")
    title: str = Field(..., min_length=5, max_length=80, description="Nome do diferencial")
    description: str = Field(..., min_length=20, max_length=200, description="Descrição breve")
    icon: str = Field(..., min_length=1, max_length=2, description="Emoji do diferencial")
    enabled: bool = Field(default=True, description="Ativar/desativar")

    class Config:
        examples = [{
            "id": 1,
            "title": "Atendimento Rápido",
            "description": "Respondemos em menos de 1 hora",
            "icon": "⚡",
            "enabled": True
        }]


class FAQItem(BaseModel):
    """Pergunta frequente"""
    id: int = Field(..., description="ID único")
    question: str = Field(..., min_length=10, max_length=150, description="Pergunta")
    answer: str = Field(..., min_length=10, max_length=400, description="Resposta")
    enabled: bool = Field(default=True, description="Ativar/desativar")

    class Config:
        examples = [{
            "id": 1,
            "question": "Como funciona o atendimento?",
            "answer": "Atendemos via WhatsApp em horário comercial.",
            "enabled": True
        }]


class FooterLink(BaseModel):
    """Link do rodapé"""
    label: str = Field(..., min_length=2, max_length=40, description="Texto do link")
    url: str = Field(..., description="URL/âncora do link")


class Footer(BaseModel):
    """Rodapé dinâmico do site"""
    description: str = Field(..., min_length=20, max_length=500, description="Descrição curta da empresa")
    links: List[FooterLink] = Field(default_factory=list, description="Links de navegação")
    copyrightText: str = Field(..., min_length=5, max_length=150, description="Texto de copyright")

    class Config:
        examples = [{
            "description": "Somos especializados em inovação...",
            "links": [{"label": "Sobre", "url": "#sobre"}, {"label": "Contato", "url": "#contato"}],
            "copyrightText": "© 2026 Minha Empresa. Todos os direitos reservados."
        }]


class Social(BaseModel):
    """Redes sociais"""
    instagram: Optional[str] = Field(default=None, description="URL Instagram")
    facebook: Optional[str] = Field(default=None, description="URL Facebook")
    linkedin: Optional[str] = Field(default=None, description="URL LinkedIn")
    twitter: Optional[str] = Field(default=None, description="URL Twitter")


class Contact(BaseModel):
    """Informações de contato"""
    email: Optional[str] = Field(default=None, description="Email principal (opcional — só se fornecido, nunca inventado)")
    phone: str = Field(..., min_length=10, description="Telefone")
    whatsapp: str = Field(..., min_length=10, description="WhatsApp")
    address: Optional[str] = Field(default=None, description="Endereço/cidade do negócio (opcional — só se fornecido, nunca um endereço genérico)")
    googleMapsUrl: Optional[str] = Field(default=None, description="Link direto do Google Maps do negócio (opcional — mais preciso que endereço em texto)")
    social: Social = Field(default_factory=Social, description="Redes sociais")

    @validator('email')
    def validate_email(cls, v):
        """Valida formato de email, se informado"""
        if v and ('@' not in v or '.' not in v):
            raise ValueError('Email deve ser válido')
        return v

    class Config:
        examples = [{
            "email": "contato@empresa.com",
            "phone": "+55 11 99999-9999",
            "whatsapp": "+5511999999999",
            "address": "Rua Principal, 123",
            "social": {
                "instagram": "https://instagram.com/empresa",
                "facebook": "https://facebook.com/empresa",
                "linkedin": "https://linkedin.com/company/empresa",
                "twitter": "https://twitter.com/empresa"
            }
        }]


class CTA(BaseModel):
    """Call-to-action final"""
    title: str = Field(..., min_length=10, max_length=200, description="Título")
    description: str = Field(..., min_length=10, max_length=300, description="Descrição")
    buttonText: str = Field(..., min_length=3, max_length=50, description="Texto do botão")
    buttonLink: str = Field(..., description="Link do botão")
    enabled: bool = Field(default=True, description="Ativar/desativar")

    class Config:
        examples = [{
            "title": "Pronto para Começar?",
            "description": "Não perca tempo!",
            "buttonText": "Fale Conosco",
            "buttonLink": "mailto:contato@empresa.com",
            "enabled": True
        }]


class SiteConfig(BaseModel):
    """Schema completo de site-config.json"""
    metadata: Metadata
    company: Company
    colors: Colors
    hero: Hero
    sections: List[Section] = Field(default_factory=list, max_items=10, description="Seções de conteúdo")
    services: List[Service] = Field(..., min_items=1, max_items=10, description="Serviços")
    features: List[Feature] = Field(..., min_items=3, max_items=6, description="Diferenciais competitivos")
    testimonials: List[Testimonial] = Field(default_factory=list, max_items=20, description="Depoimentos (opcional — só depoimentos reais fornecidos pelo cliente, nunca fabricados pela IA)")
    faq: List[FAQItem] = Field(..., min_items=3, max_items=8, description="Perguntas frequentes")
    contact: Contact
    cta: CTA
    footer: Footer

    @validator('services')
    def validate_services(cls, v):
        """Valida que há pelo menos 1 serviço ativo"""
        if not any(s.enabled for s in v):
            raise ValueError('Deve haver pelo menos 1 serviço ativo')
        return v

    class Config:
        examples = [{
            "metadata": {"siteTitle": "Empresa", "siteDescription": "Descrição", "favicon": "🚀", "keywords": ["empresa"], "ogTitle": "Empresa", "ogDescription": "Descrição", "ogImage": "url"},
            "company": {"name": "Empresa", "tagline": "Slogan", "description": "Descrição", "logo": "url"},
            "colors": {"primary": "#6366f1", "primaryDark": "#4f46e5", "secondary": "#ec4899", "accent": "#f59e0b", "background": "#ffffff", "text": "#1f2937", "textLight": "#6b7280", "border": "#e5e7eb"},
            "hero": {"title": "Título", "subtitle": "Subtítulo", "ctaText": "CTA", "ctaLink": "#", "backgroundImage": "url", "enabled": True},
            "sections": [],
            "services": [{"id": 1, "title": "Serviço", "description": "Desc", "icon": "⚡", "features": ["F1"], "enabled": True}],
            "features": [{"id": 1, "title": "Diferencial", "description": "Desc", "icon": "⚡", "enabled": True}],
            "testimonials": [{"id": 1, "name": "Nome", "role": "Profissão", "content": "Depoimento", "avatar": "url", "rating": 5, "enabled": True}],
            "faq": [{"id": 1, "question": "Pergunta?", "answer": "Resposta.", "enabled": True}],
            "contact": {"email": "email@test.com", "phone": "+55", "whatsapp": "+55", "address": "Endereço", "social": {}},
            "cta": {"title": "Título", "description": "Descrição", "buttonText": "Botão", "buttonLink": "url", "enabled": True},
            "footer": {"description": "Descrição", "links": [{"label": "Contato", "url": "#contato"}], "copyrightText": "© 2026 Empresa"}
        }]


# ============================================================================
# VALIDADOR PÚBLICO
# ============================================================================

class ValidadorSchema:
    """Classe para validar site-config.json"""

    @staticmethod
    def validar_json(dados: Dict[str, Any]) -> tuple[bool, Optional[str], Optional[SiteConfig]]:
        """
        Valida se o JSON segue o schema correto
        
        Args:
            dados: Dicionário com dados do site
            
        Returns:
            (sucesso: bool, erro: str ou None, config: SiteConfig ou None)
        """
        try:
            config = SiteConfig(**dados)
            return True, None, config
        except Exception as e:
            erro = str(e)
            return False, erro, None

    @staticmethod
    def validar_arquivo(caminho: str) -> tuple[bool, Optional[str], Optional[SiteConfig]]:
        """
        Carrega e valida um arquivo site-config.json
        
        Args:
            caminho: Caminho do arquivo JSON
            
        Returns:
            (sucesso: bool, erro: str ou None, config: SiteConfig ou None)
        """
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            return ValidadorSchema.validar_json(dados)
        except json.JSONDecodeError as e:
            return False, f"JSON inválido: {e}", None
        except FileNotFoundError:
            return False, f"Arquivo não encontrado: {caminho}", None
        except Exception as e:
            return False, f"Erro ao ler arquivo: {e}", None

    @staticmethod
    def gerar_template() -> dict:
        """
        Gera um template vazio com valores padrão
        
        Returns:
            Dicionário com template do schema
        """
        return {
            "metadata": {
                "siteTitle": "Título do Site",
                "siteDescription": "Descrição meta",
                "favicon": "🚀",
                "keywords": ["negócio", "serviço"],
                "ogTitle": "Título do Site",
                "ogDescription": "Descrição meta",
                "ogImage": "https://loremflickr.com/1920/600/negocio"
            },
            "company": {
                "name": "Nome Empresa",
                "tagline": "Tagline/Slogan",
                "description": "Descrição da empresa",
                "logo": "https://loremflickr.com/180/50/logo"
            },
            "colors": {
                "primary": "#6366f1",
                "primaryDark": "#4f46e5",
                "secondary": "#ec4899",
                "accent": "#f59e0b",
                "background": "#ffffff",
                "text": "#1f2937",
                "textLight": "#6b7280",
                "border": "#e5e7eb"
            },
            "hero": {
                "title": "Título Principal",
                "subtitle": "Subtítulo do Hero",
                "ctaText": "Começar",
                "ctaLink": "#contato",
                "backgroundImage": "https://loremflickr.com/1920/600/negocio",
                "enabled": True
            },
            "sections": [
                {
                    "id": "sobre",
                    "type": "content",
                    "title": "Sobre",
                    "subtitle": "Conheça nossa história",
                    "content": "Descrição completa da empresa e sua história",
                    "image": "https://loremflickr.com/500/400/negocio",
                    "enabled": True
                }
            ],
            "services": [
                {
                    "id": 1,
                    "title": "Serviço 1",
                    "description": "Descrição breve e objetiva do serviço",
                    "icon": "⚡",
                    "features": ["Feature 1", "Feature 2", "Feature 3"],
                    "enabled": True
                }
            ],
            "features": [
                {
                    "id": 1,
                    "title": "Diferencial 1",
                    "description": "Descrição breve do diferencial",
                    "icon": "⭐",
                    "enabled": True
                },
                {
                    "id": 2,
                    "title": "Diferencial 2",
                    "description": "Descrição breve do diferencial",
                    "icon": "✅",
                    "enabled": True
                },
                {
                    "id": 3,
                    "title": "Diferencial 3",
                    "description": "Descrição breve do diferencial",
                    "icon": "🎯",
                    "enabled": True
                }
            ],
            "testimonials": [
                {
                    "id": 1,
                    "name": "Cliente",
                    "role": "Profissão",
                    "content": "Depoimento positivo e muito satisfeito com o resultado",
                    "avatar": "https://i.pravatar.cc/150?u=cliente-1",
                    "rating": 5,
                    "enabled": True
                }
            ],
            "faq": [
                {
                    "id": 1,
                    "question": "Como funciona o atendimento?",
                    "answer": "Atendemos via WhatsApp em horário comercial.",
                    "enabled": True
                },
                {
                    "id": 2,
                    "question": "Quais formas de pagamento vocês aceitam?",
                    "answer": "Aceitamos PIX, cartão e boleto.",
                    "enabled": True
                },
                {
                    "id": 3,
                    "question": "Qual o prazo de entrega/atendimento?",
                    "answer": "O prazo varia conforme a demanda, entre em contato para detalhes.",
                    "enabled": True
                }
            ],
            "contact": {
                "email": "contato@empresa.com",
                "phone": "+55 11 99999-9999",
                "whatsapp": "+5511999999999",
                "address": "Endereço da empresa",
                "social": {
                    "instagram": "https://instagram.com/empresa",
                    "facebook": "https://facebook.com/empresa",
                    "linkedin": "https://linkedin.com/company/empresa",
                    "twitter": "https://twitter.com/empresa"
                }
            },
            "cta": {
                "title": "Chamada Final",
                "description": "Descrição do benefício",
                "buttonText": "Agir Agora",
                "buttonLink": "mailto:contato@empresa.com",
                "enabled": True
            },
            "footer": {
                "description": "Descrição da empresa",
                "links": [
                    {"label": "Sobre", "url": "#sobre"},
                    {"label": "Contato", "url": "#contato"}
                ],
                "copyrightText": "© 2026 Nome Empresa. Todos os direitos reservados."
            }
        }


if __name__ == "__main__":
    # Teste rápido
    print("🔍 Validador de Schema - Teste Rápido\n")
    
    template = ValidadorSchema.gerar_template()
    print("✓ Template gerado\n")
    
    # Testar validação
    valido, erro, config = ValidadorSchema.validar_json(template)
    
    if valido:
        print("✅ Template é válido!")
        print(f"   Empresa: {config.company.name}")
        print(f"   Serviços: {len([s for s in config.services if s.enabled])}")
        print(f"   Depoimentos: {len([t for t in config.testimonials if t.enabled])}")
    else:
        print(f"❌ Erro: {erro}")
