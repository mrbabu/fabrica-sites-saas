#!/usr/bin/env python3
"""
Quick Start - API Server
Setup rápido e validação da API
"""

import os
import sys
import subprocess
import time

def separator(char="=", length=60):
    """Imprime separador"""
    print(f"\n{char * length}\n")

def check_api_key():
    """Verifica se API key está configurada"""
    if os.getenv("ANTHROPIC_API_KEY"):
        print("✅ ANTHROPIC_API_KEY configurada")
        return True
    else:
        print("❌ ANTHROPIC_API_KEY não configurada")
        print("\nConfigure com:")
        print("  $env:ANTHROPIC_API_KEY='sk-ant-api03-xxxxxxxxxxxxxxxx'")
        print("\nOu execute:")
        print("  [System.Environment]::SetEnvironmentVariable(")
        print('    "ANTHROPIC_API_KEY",')
        print('    "sk-ant-api03-xxxxxxxxxxxxxxxx",')
        print('    "User"')
        print("  )")
        return False

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    deps = ["fastapi", "uvicorn", "pydantic", "anthropic", "requests"]
    missing = []
    
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"❌ Faltam dependências: {', '.join(missing)}")
        print("\nInstale com:")
        print("  pip install -r requirements.txt")
        return False
    else:
        print("✅ Todas as dependências instaladas")
        return True

def check_files():
    """Verifica se arquivos necessários existem"""
    files = ["app.py", "agent_construtor.py", "schema_validator.py", "metrics.py"]
    missing = []
    
    for f in files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        print(f"❌ Faltam arquivos: {', '.join(missing)}")
        return False
    else:
        print("✅ Todos os arquivos necessários existem")
        return True

def main():
    print("\n")
    print(" " * 15 + "🚀 QUICK START - API Server")
    print(" " * 10 + "Fábrica de Sites SaaS - FastAPI")
    
    separator("=")
    
    print("📋 VERIFICAÇÃO DE SETUP\n")
    
    # Checks
    print("1️⃣  Arquivos do projeto...")
    files_ok = check_files()
    
    print("\n2️⃣  Dependências Python...")
    deps_ok = check_dependencies()
    
    print("\n3️⃣  API Key...")
    key_ok = check_api_key()
    
    separator("=")
    
    if not (files_ok and deps_ok and key_ok):
        print("❌ Setup incompleto. Corrija os problemas acima e tente novamente.\n")
        sys.exit(1)
    
    print("✅ Setup validado com sucesso!\n")
    
    separator("=")
    print("🎯 PRÓXIMOS PASSOS\n")
    
    print("Opção 1️⃣ — Rodar servidor (recomendado):")
    print("  python app.py")
    print("  Depois acesse: http://localhost:8000/docs\n")
    
    print("Opção 2️⃣ — Testar a API (em outro terminal):")
    print("  python test_api.py\n")
    
    print("Opção 3️⃣ — Testar um nicho específico:")
    print("  python test_api.py single 'Minha Empresa' 'Software' '#4F46E5'\n")
    
    separator("=")
    print("📚 DOCUMENTAÇÃO\n")
    print("Guia completo: README.md ou API_DOCS.md\n")

if __name__ == "__main__":
    main()
