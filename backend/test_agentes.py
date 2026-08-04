#!/usr/bin/env python3
"""
Suite de Testes - Validação do Agente Construtor
Testa o agent_construtor.py com 50+ nichos diferentes
Gera relatório de qualidade
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from agent_construtor import AgenteConstrutor, MAX_TENTATIVAS_GERACAO
from schema_validator import ValidadorSchema


# Categorização de erro de validação -- distingue causa de MODELO (o LLM
# escreveu algo ruim: duplicou texto, vazou placeholder) de causa de
# PIPELINE (constraint estrutural do schema, rede, parsing) -- "70% porque
# o modelo repete texto" e "70% porque o schema rejeita FAQ curto" são
# diagnósticos diferentes e pedem correções diferentes. Uma mensagem pode
# disparar mais de uma categoria (ex.: pydantic reporta features E faq
# curtos na mesma exceção) -- por isso retorna lista, não categoria única.
# Ordem importa: categorias mais específicas primeiro.
_PADROES_CATEGORIA_ERRO = [
    ("MODEL_DUPLICATION", re.compile(r"(Título|Texto|Pergunta de FAQ) duplicado", re.IGNORECASE)),
    ("MODEL_TEMPLATE_LEAK", re.compile(r"Texto de template vazou para produção", re.IGNORECASE)),
    ("SCHEMA_FAQ", re.compile(r"\bfaq\b\s*\n\s*List should have at least", re.IGNORECASE)),
    ("SCHEMA_FEATURES", re.compile(r"\bfeatures\b\s*\n\s*List should have at least", re.IGNORECASE)),
    ("SCHEMA_SERVICES", re.compile(r"\bservices\b\s*\n\s*List should have at least", re.IGNORECASE)),
    ("IMAGE", re.compile(r"ErroBancoImagens|banco de imagens", re.IGNORECASE)),
    ("FALLBACK", re.compile(r"Nenhum provedor de IA dispon[íi]vel", re.IGNORECASE)),
    ("TIMEOUT", re.compile(r"\btimed?[\s_-]?out\b|\btimeout\b", re.IGNORECASE)),
    ("JSON_INVALID", re.compile(r"Expecting value|JSONDecodeError|json inv[áa]lido", re.IGNORECASE)),
]


def _categorizar_erro(mensagem: Optional[str]) -> List[str]:
    """Classifica uma mensagem de erro em 0+ categorias conhecidas (MODEL_*/SCHEMA_*/IMAGE/FALLBACK/TIMEOUT/JSON_INVALID)."""
    if not mensagem:
        return []
    categorias = [nome for nome, padrao in _PADROES_CATEGORIA_ERRO if padrao.search(mensagem)]
    if categorias:
        return categorias
    if "validation error" in mensagem.lower():
        return ["SCHEMA_OUTRO"]
    return ["OUTRO"]


def _agregar_diagnostico(resultados: List[Dict]) -> Dict:
    """
    Agrega diagnostico_tentativas de todos os nichos testados em:
    - por_regra: quantas TENTATIVAS (não nichos) falharam por cada
      categoria (uma tentativa pode contar em mais de uma categoria)
    - por_nicho: quantos NICHOS DISTINTOS tiveram essa categoria em pelo
      menos uma tentativa
    - por_tentativa: distribuição (conta e %) de em qual tentativa cada
      nicho teve sucesso, quantos nunca tiveram, e tempo médio por número
      de tentativa (ex.: "a 3ª tentativa demora mais que a 1ª?")
    - top_regras: por_regra ordenado do mais pro menos frequente
    Não faz rede nem I/O -- só lê a estrutura já coletada por testar_nicho.
    """
    por_regra: Dict[str, int] = {}
    por_nicho: Dict[str, int] = {}
    distribuicao_sucesso: Dict[int, int] = {}
    soma_tempo_por_numero: Dict[int, float] = {}
    contagem_tempo_por_numero: Dict[int, int] = {}
    nunca_sucesso = 0
    total_nichos_com_diagnostico = 0

    for resultado in resultados:
        diagnostico = resultado.get("diagnostico_tentativas") or []
        if not diagnostico:
            continue
        total_nichos_com_diagnostico += 1
        categorias_neste_nicho = set()

        tentativa_de_sucesso = None
        for entrada in diagnostico:
            numero = entrada["tentativa"]
            soma_tempo_por_numero[numero] = soma_tempo_por_numero.get(numero, 0.0) + entrada.get("tempo_segundos", 0.0)
            contagem_tempo_por_numero[numero] = contagem_tempo_por_numero.get(numero, 0) + 1

            if entrada["sucesso"]:
                tentativa_de_sucesso = numero
                continue
            for categoria in _categorizar_erro(entrada["erro"]):
                por_regra[categoria] = por_regra.get(categoria, 0) + 1
                categorias_neste_nicho.add(categoria)

        for categoria in categorias_neste_nicho:
            por_nicho[categoria] = por_nicho.get(categoria, 0) + 1

        if tentativa_de_sucesso is not None:
            distribuicao_sucesso[tentativa_de_sucesso] = distribuicao_sucesso.get(tentativa_de_sucesso, 0) + 1
        else:
            nunca_sucesso += 1

    tempo_medio_por_numero = {
        numero: soma_tempo_por_numero[numero] / contagem_tempo_por_numero[numero]
        for numero in soma_tempo_por_numero
    }

    base_pct = total_nichos_com_diagnostico or 1
    distribuicao_sucesso_pct = {
        numero: (contagem / base_pct * 100) for numero, contagem in distribuicao_sucesso.items()
    }
    nunca_sucesso_pct = nunca_sucesso / base_pct * 100

    top_regras = sorted(por_regra.items(), key=lambda kv: -kv[1])

    return {
        "por_regra": por_regra,
        "por_nicho": por_nicho,
        "por_tentativa": {
            "distribuicao_sucesso": distribuicao_sucesso,
            "distribuicao_sucesso_pct": distribuicao_sucesso_pct,
            "nunca_sucesso": nunca_sucesso,
            "nunca_sucesso_pct": nunca_sucesso_pct,
            "tempo_medio_por_numero": tempo_medio_por_numero,
        },
        "top_regras": top_regras,
    }


def _formatar_tentativas_para_json(diagnostico: List[Dict]) -> List[Dict]:
    """Converte diagnostico_tentativas (formato interno) pro formato de exportação em relatorio_testes.json."""
    formatado = []
    for entrada in diagnostico:
        formatado.append({
            "numero": entrada["tentativa"],
            "status": "passou" if entrada["sucesso"] else "falhou",
            "regras": [] if entrada["sucesso"] else _categorizar_erro(entrada["erro"]),
            "tempo_segundos": entrada.get("tempo_segundos"),
            "provedor": entrada.get("provedor"),
        })
    return formatado


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
            "info": {},
            "diagnostico_tentativas": [],
        }

        tempo_inicio = time.time()
        diagnostico_tentativas: List[Dict] = []

        try:
            # Gerar config
            config = self.agente.gerar_config_site(
                nome, nicho, cor, diagnostico_tentativas=diagnostico_tentativas
            )
            resultado["tempo_segundos"] = time.time() - tempo_inicio
            resultado["diagnostico_tentativas"] = diagnostico_tentativas

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
            resultado["diagnostico_tentativas"] = diagnostico_tentativas
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

        # Diagnóstico por regra e por tentativa -- pra decidir com dado
        # (não com percepção) se o problema é o modelo/provedor ou a regra
        # de validação em si (ver docs/roadmap-implementacao-dops.md)
        agregado = _agregar_diagnostico(self.resultados)
        if agregado["top_regras"]:
            print(f"\n📐 Top problemas (tentativas que falharam por regra):")
            top5 = agregado["top_regras"][:5]
            maior_nome = max(len(nome) for nome, _ in top5)
            for categoria, n_tentativas in top5:
                n_nichos = agregado["por_nicho"].get(categoria, 0)
                pontos = "." * (maior_nome - len(categoria) + 3)
                print(f"   {categoria} {pontos} {n_tentativas:>3}  ({n_nichos} nicho(s) distinto(s))")
            restantes = agregado["top_regras"][5:]
            if restantes:
                print(f"   + {len(restantes)} categoria(s) menor(es): {', '.join(nome for nome, _ in restantes)}")

        pt = agregado["por_tentativa"]
        if pt["distribuicao_sucesso"] or pt["nunca_sucesso"]:
            print(f"\n🔁 Distribuição de sucesso por tentativa (% dos nichos testados):")
            for numero in sorted(pt["distribuicao_sucesso"]):
                contagem = pt["distribuicao_sucesso"][numero]
                pct = pt["distribuicao_sucesso_pct"][numero]
                tempo_medio = pt["tempo_medio_por_numero"].get(numero)
                tempo_str = f", tempo médio {tempo_medio:.1f}s" if tempo_medio is not None else ""
                print(f"   Passou na {numero}ª tentativa: {contagem} ({pct:.1f}%{tempo_str})")
            if pt["nunca_sucesso"]:
                print(f"   Nunca (esgotou {MAX_TENTATIVAS_GERACAO} tentativas): {pt['nunca_sucesso']} ({pt['nunca_sucesso_pct']:.1f}%)")

        # Salvar relatório JSON (formato: resumo / resultados / metricas --
        # ver docs internos; "resultados" preserva os campos originais mais
        # o detalhe por tentativa em cada nicho)
        self.salvar_relatorio_json(tempo_total, agregado)

        # Avisos
        print(f"\n⚠️  Status:")
        if taxa_sucesso >= 95:
            print(f"   ✅ PRONTO PARA PRODUÇÃO (Taxa > 95%)")
        elif taxa_sucesso >= 85:
            print(f"   🟡 REQUER MELHORIAS (Taxa entre 85-95%)")
        else:
            print(f"   ❌ CRÍTICO (Taxa < 85%)")

        print("\n" + "="*70 + "\n")

    def salvar_relatorio_json(self, tempo_total: float = 0.0, agregado: Optional[Dict] = None) -> None:
        """
        Salva relatório em JSON no formato {resumo, resultados, metricas}.
        - resumo: contagens/taxas agregadas do run inteiro
        - resultados: um item por nicho, com "tentativas" (todas, não só a
          final) já formatado (numero/status/regras/tempo_segundos/provedor)
        - metricas: por_regra / por_tentativa / por_nicho, vindos de
          _agregar_diagnostico -- serve pra responder "o gargalo é o modelo,
          o schema, a rede ou a política de retry?" com dado, não percepção.
        """
        agregado = agregado or {}
        total = len(self.resultados)
        sucessos = sum(1 for r in self.resultados if r["sucesso"])

        resumo = {
            "total": total,
            "sucessos": sucessos,
            "falhas": total - sucessos,
            "taxa_sucesso_pct": (sucessos / total * 100) if total else 0.0,
            "tempo_total_segundos": tempo_total,
            "tempo_medio_por_nicho_segundos": (tempo_total / total) if total else 0.0,
        }

        resultados_exportados = []
        for r in self.resultados:
            r_exportado = {k: v for k, v in r.items() if k != "diagnostico_tentativas"}
            r_exportado["tentativas"] = _formatar_tentativas_para_json(r.get("diagnostico_tentativas") or [])
            resultados_exportados.append(r_exportado)

        payload = {
            "resumo": resumo,
            "resultados": resultados_exportados,
            "metricas": {
                "por_regra": agregado.get("por_regra", {}),
                "por_tentativa": agregado.get("por_tentativa", {}),
                "por_nicho": agregado.get("por_nicho", {}),
                "top_regras": agregado.get("top_regras", []),
            },
        }

        caminho = "relatorio_testes.json"
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"💾 Relatório salvo em: {caminho}")


def main():
    """Função principal"""
    print("\n")

    # Nenhuma checagem de credencial aqui: AIProvider (ai_provider.py) já
    # resolve isso sozinho, tentando toda a cadeia de fallback (Gemini ->
    # NVIDIA NIM -> Anthropic -> Ollama local) e só falha se NENHUM provedor
    # estiver disponível. Checar uma env var específica aqui duplicava essa
    # lógica de forma desatualizada — travava a suite inteira por falta de
    # ANTHROPIC_API_KEY mesmo quando outro provedor da cadeia funcionaria.
    # TestadorAgente.inicializar() já captura e reporta esse erro se ocorrer.

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
