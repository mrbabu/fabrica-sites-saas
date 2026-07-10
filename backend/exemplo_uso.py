#!/usr/bin/env python3
"""
Exemplo de uso do Agente Construtor
Demonstra como usar o agente programaticamente em código
"""

from agent_construtor import AgenteConstrutor
import os


def exemplo_uso_simples():
    """Exemplo básico: usar o agente com dados específicos"""
    
    # Verificar se a API key está configurada
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Erro: Configure a variável de ambiente ANTHROPIC_API_KEY")
        print("   No Windows PowerShell:")
        print("   $env:ANTHROPIC_API_KEY='sua-api-key-aqui'")
        return
    
    # Inicializar agente
    agente = AgenteConstrutor()
    
    # Exemplo 1: Agência de Marketing Digital
    print("\n" + "="*60)
    print("EXEMPLO 1: Agência de Marketing Digital")
    print("="*60)
    
    config = agente.executar(
        nome_empresa="Digital Boost Agency",
        nicho="Agência de Marketing Digital",
        cor_primaria="#FF6B35",
        caminho_saida="site-config.json"
    )


def exemplo_uso_multiplo():
    """Exemplo avançado: gerar múltiplas configurações"""
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Erro: Configure ANTHROPIC_API_KEY")
        return
    
    agente = AgenteConstrutor()
    
    # Lista de clientes para gerar sites
    clientes = [
        {
            "nome": "Tech Solutions",
            "nicho": "Desenvolvimento de Software",
            "cor": "#4F46E5",
            "arquivo": "tech-solutions-config.json"
        },
        {
            "nome": "Beauty&Wellness Spa",
            "nicho": "Spa e Bem-estar",
            "cor": "#EC4899",
            "arquivo": "beauty-wellness-config.json"
        },
        {
            "nome": "EcoFood Market",
            "nicho": "E-commerce Alimentos Orgânicos",
            "cor": "#10B981",
            "arquivo": "ecofood-config.json"
        }
    ]
    
    for cliente in clientes:
        print(f"\n📧 Gerando site para: {cliente['nome']}")
        try:
            config = agente.executar(
                nome_empresa=cliente['nome'],
                nicho=cliente['nicho'],
                cor_primaria=cliente['cor'],
                caminho_saida=cliente['arquivo']
            )
            print(f"✅ Sucesso! Arquivo: {cliente['arquivo']}")
        except Exception as e:
            print(f"❌ Erro: {e}")


def exemplo_uso_interativo():
    """Exemplo: Interface interativa para o usuário"""
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Erro: Configure ANTHROPIC_API_KEY")
        return
    
    agente = AgenteConstrutor()
    
    # Menu principal
    while True:
        print("\n" + "="*60)
        print("🚀 AGENTE CONSTRUTOR - Fábrica de Sites SaaS")
        print("="*60)
        print("\n1. Gerar novo site")
        print("2. Exemplos pré-configurados")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção (1-3): ").strip()
        
        if opcao == "1":
            nome = input("\n📝 Nome da empresa: ").strip() or "Minha Empresa"
            nicho = input("🏢 Nicho (ex: Software, Consultoria): ").strip() or "Negócios"
            cor = input("🎨 Cor primária em HEX (ex: #6366f1): ").strip() or "#6366f1"
            
            arquivo = f"{nome.lower().replace(' ', '-')}-config.json"
            
            try:
                agente.executar(nome, nicho, cor, arquivo)
            except Exception as e:
                print(f"\n❌ Erro: {e}")
        
        elif opcao == "2":
            print("\n📋 Exemplos pré-configurados:")
            print("1. Agência de Marketing")
            print("2. SaaS de Contabilidade")
            print("3. Consultoria em RH")
            print("4. E-commerce Fashion")
            print("5. Consultório Odontológico")
            
            exemplo = input("\nEscolha (1-5): ").strip()
            
            exemplos = {
                "1": ("Digital Marketing Pro", "Agência de Marketing Digital", "#FF6B35"),
                "2": ("ContaControl", "Software Contabilidade", "#2563EB"),
                "3": ("HR Consultoria", "Consultoria em Recursos Humanos", "#8B5CF6"),
                "4": ("FashionHub", "E-commerce Fashion", "#EC4899"),
                "5": ("Sorriso Plus", "Consultório Odontológico", "#06B6D4"),
            }
            
            if exemplo in exemplos:
                nome, nicho, cor = exemplos[exemplo]
                arquivo = f"{nome.lower().replace(' ', '-')}-config.json"
                try:
                    agente.executar(nome, nicho, cor, arquivo)
                except Exception as e:
                    print(f"\n❌ Erro: {e}")
            else:
                print("Opção inválida")
        
        elif opcao == "3":
            print("\n👋 Até logo!")
            break
        else:
            print("Opção inválida")


if __name__ == "__main__":
    import sys
    
    # Verificar argumentos CLI
    if len(sys.argv) > 1:
        if sys.argv[1] == "simples":
            exemplo_uso_simples()
        elif sys.argv[1] == "multiplo":
            exemplo_uso_multiplo()
        elif sys.argv[1] == "interativo":
            exemplo_uso_interativo()
        else:
            print("Uso: python exemplo_uso.py [simples|multiplo|interativo]")
    else:
        # Executar modo interativo por padrão
        exemplo_uso_interativo()
