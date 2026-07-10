#!/usr/bin/env python3
"""
Suite de Testes - Validação do Agente Construtor
Testa o agent_construtor.py com 50+ nichos diferentes
Gera relatório de qualidade
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from agent_construtor import AgenteConstrutor
from schema_validator import ValidadorSchema

# Lista de nichos para testar (Fase 1)
NICHOS_TESTE = [
    # Automóvel
    ("Auto Elétrica Silva", "Auto Elétrica", "#0066CC"),
    ("Mecânica Premium", "Mecânica Geral", "#333333"),
    ("Lavajato Express", "Lavagem de Veículos", "#FF6B35"),
    
    # Saúde & Bem-estar
    ("Academia Power", "Academia de Ginástica", "#FF006E"),
    ("Clínica Médica Central", "Clínica Médica", "#06A77D"),
    ("Consultório Odontológico", "Odontologia", "#0099FF"),
    ("Spa Wellness", "Spa e Bem-estar", "#D946EF"),
    ("Fisioterapia Motriz", "Fisioterapia", "#00B4D8"),
    
    # Advocacia
    ("Consultoria Jurídica Silva", "Consultoria Jurídica", "#8B0000"),
    ("Escritório de Advocacia", "Advocacia Geral", "#1F2937"),
    
    # Animais
    ("Pet Shop Amigos", "Pet Shop", "#FF85C0"),
    ("Clínica Veterinária", "Veterinária", "#22D3EE"),
    ("Banho e Tosa Paw", "Banho e Tosa", "#F0B030"),
    
    # Alimentação
    ("Pizzaria do João", "Pizzaria", "#EA580C"),
    ("Restaurante Gourmet", "Restaurante", "#8E7D43"),
    ("Padaria Artesanal", "Padaria", "#D2691E"),
    ("Sorveteria Gelato", "Sorveteria", "#FF69B4"),
    ("Confeitaria Doces", "Confeitaria", "#DC143C"),
    ("Lanchonete Express", "Lanchonete", "#FF8C00"),
    
    # Moda
    ("Loja Fashion Plus", "Loja de Roupas", "#FF1493"),
    ("Sapatos Premium", "Sapetaria", "#8B4513"),
    ("Brechó Criativo", "Brechó", "#A020F0"),
    
    # Beleza
    ("Salão de Beleza Maria", "Salão de Beleza", "#FF69B4"),
    ("Barbearia Clássica", "Barbearia", "#2F4F4F"),
    ("Manicure e Pedicure", "Manicure", "#FFB6C1"),
    
    # Imóveis
    ("Imobiliária Casagrande", "Imobiliária", "#4169E1"),
    ("Aluguel Fácil", "Aluguel de Imóveis", "#1E90FF"),
    
    # Educação
    ("Academia de Idiomas", "Escola de Idiomas", "#007AFF"),
    ("Curso de Culinária", "Curso Online", "#DC143C"),
    ("Escola de Artes", "Escola de Artes", "#FF8C00"),
    
    # Tecnologia
    ("Tech Innovations", "Software/SaaS", "#4F46E5"),
    ("Web Design Studio", "Web Design", "#0891B2"),
    ("Consultoria TI", "Consultoria Tecnológica", "#1D4ED8"),
    
    # Marketing & Publicidade
    ("Digital Boost Agency", "Agência de Marketing", "#FF6B35"),
    ("Estúdio Criativo", "Estúdio de Design", "#A855F7"),
    ("Social Media Expert", "Social Media", "#F97316"),
    
    # Serviços
    ("Encanador Express", "Encanador", "#4B5563"),
    ("Eletricista Profissional", "Eletricista", "#FFD700"),
    ("Serralharia Premium", "Serralharia", "#696969"),
    ("Construção & Reforma", "Construção Civil", "#8B4513"),
    ("Limpeza Profissional", "Limpeza de Ambientes", "#87CEEB"),
    
    # Turismo & Hospedagem
    ("Hotel Praia Dourada", "Hotel", "#00CED1"),
    ("Pousada Aconchego", "Pousada", "#228B22"),
    ("Agência de Viagens", "Agência de Viagens", "#FF4500"),
    
    # Outros
    ("Floricultura Flores", "Floricultura", "#FF1493"),
    ("Fotógrafo Profissional", "Fotografia", "#000000"),
    ("DJ Para Festas", "DJ Services", "#FF00FF"),
    ("Buffet de Festas", "Buffet", "#FFD700"),
]


class TestadorAgente:
    """Executa suite de testes com múltiplos nichos"""

    def __init__(self):
        self.resultados: List[Dict] = []
        self.tempo_inicio = None
        self.agente = None

    def inicializar(self) -> bool:
        """Inicializa o agente"""
        try:
            print("🤖 Inicializando Agente Construtor...")
            self.agente = AgenteConstrutor()
            print("✅ Agente inicializado\n")
            return True
        except Exception as e:
            print(f"❌ Erro ao inicializar agente: {e}")
            return False

    def testar_nicho(self, nome: str, nicho: str, cor: str, indice: int, total: int) -> Dict:
        """
        Testa o agente com um nicho específico
        
        Returns:
            Dict com resultado do teste
        """
        print(f"[{indice}/{total}] Testando: {nome} ({nicho}) - {cor}")
        
        resultado = {
            "indice": indice,
            "nome": nome,
            "nicho": nicho,
            "cor": cor,
            "timestamp": datetime.now().isoformat(),
            "sucesso": False,
            "tempo_segundos": 0,
            "erro": None,
            "validacao_schema": False,
            "campos_faltantes": [],
            "campos_vazios": [],
            "info": {}
        }

        tempo_inicio = time.time()

        try:
            # Gerar config
            config = self.agente.gerar_config_site(nome, nicho, cor)
            resultado["tempo_segundos"] = time.time() - tempo_inicio

            # Validar schema
            valido, erro, config_obj = ValidadorSchema.validar_json(config)

            if not valido:
                resultado["erro"] = erro
                print(f"   ❌ Schema inválido: {erro}\n")
                return resultado

            resultado["validacao_schema"] = True

            # Coletar info
            resultado["info"] = {
                "empresa": config_obj.company.name,
                "serviços": len([s for s in config_obj.services if s.enabled]),
                "depoimentos": len([t for t in config_obj.testimonials if t.enabled]),
                "cores": len(config_obj.colors.model_dump()),
                "hero_enabled": config_obj.hero.enabled,
                "cta_enabled": config_obj.cta.enabled
            }

            resultado["sucesso"] = True
            print(f"   ✅ Sucesso em {resultado['tempo_segundos']:.2f}s\n")

        except Exception as e:
            resultado["erro"] = str(e)
            resultado["tempo_segundos"] = time.time() - tempo_inicio
            print(f"   ❌ Erro: {e}\n")

        return resultado

    def executar_testes(self, limite: int = None) -> None:
        """Executa a suite completa de testes"""
        if not self.inicializar():
            return

        print("="*70)
        print("🧪 SUITE DE TESTES - Agente Construtor")
        print("="*70)
        print(f"Total de nichos a testar: {len(NICHOS_TESTE)}\n")

        self.tempo_inicio = time.time()

        # Executar testes
        nichos_para_testar = NICHOS_TESTE[:limite] if limite else NICHOS_TESTE

        for i, (nome, nicho, cor) in enumerate(nichos_para_testar, 1):
            resultado = self.testar_nicho(nome, nicho, cor, i, len(nichos_para_testar))
            self.resultados.append(resultado)

        tempo_total = time.time() - self.tempo_inicio

        # Gerar relatório
        self.gerar_relatorio(tempo_total)

    def gerar_relatorio(self, tempo_total: float) -> None:
        """Gera relatório de qualidade"""
        print("\n" + "="*70)
        print("📊 RELATÓRIO DE QUALIDADE")
        print("="*70 + "\n")

        total = len(self.resultados)
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        schema_ok = sum(1 for r in self.resultados if r["validacao_schema"])

        # Taxa de sucesso
        taxa_sucesso = (sucessos / total * 100) if total > 0 else 0
        taxa_schema = (schema_ok / total * 100) if total > 0 else 0

        print(f"📈 Estatísticas Gerais:")
        print(f"   Total de testes: {total}")
        print(f"   Sucessos: {sucessos}")
        print(f"   Falhas: {total - sucessos}")
        print(f"   Taxa de sucesso: {taxa_sucesso:.1f}%")
        print(f"   Schema válido: {schema_ok}/{total} ({taxa_schema:.1f}%)")
        print(f"   Tempo total: {tempo_total:.2f}s")
        print(f"   Tempo médio/nicho: {tempo_total/total:.2f}s\n")

        # Resumo por nicho
        print(f"📋 Resumo por Nicho:")
        for r in self.resultados:
            status = "✅" if r["sucesso"] else "❌"
            print(f"   {status} {r['nome']:<40} ({r['tempo_segundos']:.1f}s)")

        # Erros
        erros = [r for r in self.resultados if not r["sucesso"]]
        if erros:
            print(f"\n❌ Erros Encontrados ({len(erros)}):")
            for r in erros:
                print(f"   • {r['nome']}: {r['erro']}")

        # Salvar relatório JSON
        self.salvar_relatorio_json()

        # Avisos
        print(f"\n⚠️  Status:")
        if taxa_sucesso >= 95:
            print(f"   ✅ PRONTO PARA PRODUÇÃO (Taxa > 95%)")
        elif taxa_sucesso >= 85:
            print(f"   🟡 REQUER MELHORIAS (Taxa entre 85-95%)")
        else:
            print(f"   ❌ CRÍTICO (Taxa < 85%)")

        print("\n" + "="*70 + "\n")

    def salvar_relatorio_json(self) -> None:
        """Salva relatório em JSON"""
        caminho = "relatorio_testes.json"
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(self.resultados, f, ensure_ascii=False, indent=2)
        print(f"💾 Relatório salvo em: {caminho}")


def main():
    """Função principal"""
    print("\n")

    # Verificar API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Erro: ANTHROPIC_API_KEY não configurada")
        sys.exit(1)

    # Argumentos CLI
    limite = None
    if len(sys.argv) > 1:
        try:
            limite = int(sys.argv[1])
        except ValueError:
            print(f"Uso: python test_agentes.py [limite_nichos]")
            sys.exit(1)

    # Executar testes
    testador = TestadorAgente()
    testador.executar_testes(limite=limite)


if __name__ == "__main__":
    main()
