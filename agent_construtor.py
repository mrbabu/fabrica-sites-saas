#!/usr/bin/env python3
"""
Agente Construtor - Fábrica de Sites SaaS
Gera site-config.json completo a partir de inputs simples usando Claude 3.5 Sonnet
"""

import json
import sys
import os
import time
import requests
from pathlib import Path
from typing import Optional
import re

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env é opcional quando usando Ollama local

from schema_validator import ValidadorSchema
from metrics import obter_metricas


class AgenteConstrutor:
    """Agente que gera configuração de site baseado em dados do cliente - Powered by Ollama Llama3"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """
        Inicializa o agente com Ollama local (Llama 3)
        
        Args:
            ollama_url: URL da API do Ollama (padrão: localhost:11434)
        """
        self.ollama_url = ollama_url
        self.model = "llama3"
        self.api_endpoint = f"{ollama_url}/api/generate"
        
        # Verificar conexão com Ollama
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                print("✅ Conectado ao Ollama local (Llama 3)")
            else:
                raise ConnectionError("Ollama respondeu com erro")
        except Exception as e:
            print(f"⚠️  Aviso: Ollama local não está disponível em {ollama_url}")
            print(f"   Inicie com: ollama run llama3")
            print(f"   Erro: {e}")

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

        response = requests.post(
            self.api_endpoint,
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()

        try:
            texto = response.json()["response"].strip()
            cores = json.loads(texto)
            return cores
        except json.JSONDecodeError:
            print(f"Aviso: Não foi possível gerar paleta de cores. Usando padrão.")
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

    def gerar_config_site(self, nome_empresa: str, nicho: str, cor_primaria: str) -> dict:
        """
        Gera configuração completa de site usando Claude
        
        Args:
            nome_empresa: Nome da empresa
            nicho: Nicho/ramo de atuação
            cor_primaria: Cor primária em hex
            
        Returns:
            Dicionário com configuração completa do site
        """
        # Gerar paleta de cores
        print(f"🎨 Gerando paleta de cores complementares para {cor_primaria}...")
        cores = self.gerar_paleta_cores(cor_primaria)

        # Prompt para Claude gerar o JSON completo
        prompt = f"""Você é um especialista em marketing e copywriting para criar sites profissionais de alto impacto.

Crie um arquivo site-config.json COMPLETO e altamente persuasivo para:
- Empresa: {nome_empresa}
- Nicho: {nicho}
- Cor Primária: {cor_primaria}

IMPORTANTE:
1. Retorne APENAS um JSON válido, sem markdown, sem explicações
2. O JSON deve seguir EXATAMENTE este schema
3. Crie copys persuasivos e impactantes adaptados ao nicho "{nicho}"
4. Use a cor primária {cor_primaria} e a paleta {json.dumps(cores)}
5. Gere 3 serviços principais para o nicho {nicho}
6. Gere 3 depoimentos clientes reais e convincentes
7. Todas as strings devem estar em português (Brasil)

Schema obrigatório (respeite ESTRITAMENTE os limites de caracteres indicados entre parênteses):
{{
  "metadata": {{
    "siteTitle": "string (mínimo 5, MÁXIMO 60 caracteres) - Título SEO do site",
    "siteDescription": "string (mínimo 10, MÁXIMO 160 caracteres) - Meta description",
    "favicon": "emoji"
  }},
  "company": {{
    "name": "string (máximo 100 caracteres)",
    "tagline": "string (mínimo 5, máximo 100 caracteres) - Slogan impactante",
    "description": "string (mínimo 20, máximo 500 caracteres) - Descrição 2-3 frases",
    "logo": "string - URL placeholder"
  }},
  "colors": {json.dumps(cores)},
  "hero": {{
    "title": "string (mínimo 10, máximo 200 caracteres) - Título principal impactante",
    "subtitle": "string (mínimo 10, máximo 300 caracteres) - Subtítulo persuasivo",
    "ctaText": "string (mínimo 3, máximo 50 caracteres) - Texto do botão CTA",
    "ctaLink": "#contato",
    "backgroundImage": "https://via.placeholder.com/1920x600?text=Hero+Background",
    "enabled": true
  }},
  "sections": [
    {{
      "id": "sobre",
      "type": "content",
      "title": "string (mínimo 5, máximo 100 caracteres) - Título seção",
      "subtitle": "string (mínimo 5, máximo 200 caracteres) - Subtítulo",
      "content": "string (mínimo 20, máximo 1000 caracteres) - Conteúdo 3-4 frases",
      "image": "https://via.placeholder.com/500x400?text=About",
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
  "testimonials": [
    {{
      "id": 1,
      "name": "string (mínimo 3, máximo 100 caracteres) - Nome real",
      "role": "string (mínimo 5, máximo 100 caracteres) - Profissão/empresa",
      "content": "string (mínimo 20, máximo 500 caracteres) - Depoimento positivo e específico",
      "avatar": "https://via.placeholder.com/100x100?text=Avatar+1",
      "rating": 5,
      "enabled": true
    }},
    {{
      "id": 2,
      "name": "string (mínimo 3, máximo 100 caracteres)",
      "role": "string (mínimo 5, máximo 100 caracteres)",
      "content": "string (mínimo 20, máximo 500 caracteres)",
      "avatar": "https://via.placeholder.com/100x100?text=Avatar+2",
      "rating": 5,
      "enabled": true
    }},
    {{
      "id": 3,
      "name": "string (mínimo 3, máximo 100 caracteres)",
      "role": "string (mínimo 5, máximo 100 caracteres)",
      "content": "string (mínimo 20, máximo 500 caracteres)",
      "avatar": "https://via.placeholder.com/100x100?text=Avatar+3",
      "rating": 5,
      "enabled": true
    }}
  ],
  "contact": {{
    "email": "contato@{nome_empresa.lower().replace(' ', '')}.com",
    "phone": "+55 11 98765-4321",
    "whatsapp": "+5511987654321",
    "address": "São Paulo, SP - Brasil",
    "social": {{
      "instagram": "https://instagram.com/{nome_empresa.lower().replace(' ', '')}",
      "facebook": "https://facebook.com/{nome_empresa.lower().replace(' ', '')}",
      "linkedin": "https://linkedin.com/company/{nome_empresa.lower().replace(' ', '')}",
      "twitter": "https://twitter.com/{nome_empresa.lower().replace(' ', '')}"
    }}
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
- Depoimentos: Inclua números/resultados específicos
- CTA: Use linguagem ativa e persuasiva
- Todos os textos devem ser concisos mas impactantes

ATENÇÃO:
- Nenhum campo "icon" pode ficar vazio. Cada serviço PRECISA ter um emoji real e visível no campo "icon" (nunca "" ou null).
- Os limites de caracteres MÍNIMO e MÁXIMO indicados em cada campo são REGRAS RÍGIDAS. Nunca ultrapasse o máximo indicado, mesmo que precise encurtar o texto.

Retorne APENAS o JSON, sem nenhum texto adicional ou markdown."""

        print(f"🤖 Gerando configuração com Ollama ({self.model})...")

        response = requests.post(
            self.api_endpoint,
            json={
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()

        try:
            texto = response.json()["response"].strip()
            config = json.loads(texto)
            
            # Validar schema básico
            self._validar_schema(config)
            
            return config
        except json.JSONDecodeError as e:
            print(f"Erro ao fazer parsing do JSON: {e}")
            print(f"Resposta: {texto[:500]}")
            raise
        except ValueError as e:
            print(f"Erro de validação: {e}")
            raise

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
            "sections", "services", "testimonials", "contact", "cta"
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
        
        with open(caminho_abs, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return str(caminho_abs)

    def executar(self, nome_empresa: str, nicho: str, cor_primaria: str, 
                 caminho_saida: str = "site-config.json") -> dict:
        """
        Executa o pipeline completo de geração
        
        Args:
            nome_empresa: Nome da empresa
            nicho: Nicho/ramo de atuação
            cor_primaria: Cor primária em hex
            caminho_saida: Caminho do arquivo de saída
            
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
        print(f"  • Cor Primária: {cor_primaria}")
        print(f"\n{'='*60}\n")

        try:
            config = self.gerar_config_site(nome_empresa, nicho, cor_primaria)
            
            # Validar schema
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
            cor_primaria=cor_primaria
        )
        
        print("✨ Site config.json pronto para uso!")
        print("📌 Próximo passo: Abra index.html no navegador para visualizar")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
