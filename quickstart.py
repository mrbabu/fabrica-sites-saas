#!/usr/bin/env python3
"""
QUICK START - Agente Construtor
Execute este script para fazer um teste rápido
"""

import sys
import os

print("\n" + "="*70)
print("🚀 QUICK START - Agente Construtor Fábrica de Sites SaaS")
print("="*70 + "\n")

# Step 1: Verificar Python
print("✓ Step 1: Verificar versão Python")
print(f"  Python {sys.version.split()[0]} OK\n")

# Step 2: Verificar variáveis de ambiente
print("✓ Step 2: Verificar variáveis de ambiente")
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    print(f"  ANTHROPIC_API_KEY: configurada ✓\n")
else:
    print(f"  ❌ ANTHROPIC_API_KEY: NÃO CONFIGURADA")
    print(f"\n  Configure no PowerShell (Windows):")
    print(f"  $env:ANTHROPIC_API_KEY='sua-chave-aqui'\n")
    sys.exit(1)

# Step 3: Verificar dependências
print("✓ Step 3: Verificar dependências Python")
try:
    import anthropic
    print(f"  anthropic v{anthropic.__version__}: OK ✓\n")
except ImportError:
    print(f"  ❌ anthropic: NÃO INSTALADA")
    print(f"\n  Instale com:")
    print(f"  pip install -r requirements.txt\n")
    sys.exit(1)

# Step 4: Testar importação do agente
print("✓ Step 4: Testar importação do Agente Construtor")
try:
    from agent_construtor import AgenteConstrutor
    print(f"  AgenteConstrutor: OK ✓\n")
except ImportError as e:
    print(f"  ❌ Erro: {e}\n")
    sys.exit(1)

# Step 5: Executar teste
print("✓ Step 5: Executar teste com dados de exemplo\n")
print("-" * 70)

try:
    agente = AgenteConstrutor()
    
    # Usar dados de teste
    config = agente.executar(
        nome_empresa="Tech Innovators",
        nicho="Desenvolvimento de Software SaaS",
        cor_primaria="#4F46E5",
        caminho_saida="site-config.json"
    )
    
    print("-" * 70)
    print("\n✅ SUCESSO! Agente Construtor está funcionando perfeitamente!\n")
    
    print("📊 Próximas ações:")
    print("  1. Edite o arquivo 'site-config.json' com dados reais")
    print("  2. Abra 'index.html' no navegador para visualizar")
    print("  3. Use 'python agent_construtor.py' para gerar novos sites\n")
    
    print("📚 Documentação:")
    print("  • README.md - Visão geral do projeto")
    print("  • AGENT_CONSTRUTOR.md - Documentação técnica do agente")
    print("  • exemplo_uso.py - Exemplos de uso\n")
    
except Exception as e:
    print("-" * 70)
    print(f"\n❌ ERRO: {e}\n")
    print("💡 Dicas de troubleshooting:")
    print("  • Verifique se a API key está correta")
    print("  • Verifique sua conexão com a internet")
    print("  • Tente novamente em alguns segundos\n")
    sys.exit(1)

print("="*70)
