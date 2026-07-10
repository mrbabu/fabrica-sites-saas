#!/usr/bin/env python3
"""
Módulo de Métricas - Logging e Tracking
Registra performance, erros e qualidade do sistema
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TipoEvento(str, Enum):
    """Tipos de eventos que podem ser registrados"""
    TESTE_INICIADO = "teste_iniciado"
    TESTE_CONCLUIDO = "teste_concluido"
    TESTE_FALHOU = "teste_falhou"
    GERACAO_INICIADA = "geracao_iniciada"
    GERACAO_CONCLUIDA = "geracao_concluida"
    GERACAO_FALHOU = "geracao_falhou"
    VALIDACAO_OK = "validacao_ok"
    VALIDACAO_FALHOU = "validacao_falhou"
    ERRO_API = "erro_api"
    ERRO_SCHEMA = "erro_schema"


class Metricas:
    """Gerenciador de métricas e logging"""

    def __init__(self, arquivo_log: str = "metrics.log", arquivo_json: str = "metrics.json"):
        """
        Inicializa o gerenciador de métricas
        
        Args:
            arquivo_log: Arquivo para logs em texto
            arquivo_json: Arquivo para métricas em JSON
        """
        self.arquivo_log = arquivo_log
        self.arquivo_json = arquivo_json
        self.eventos: list = []

        # Configurar logging
        self.logger = logging.getLogger("FabricaSites")
        self.logger.setLevel(logging.INFO)

        # Handler para arquivo
        handler_arquivo = logging.FileHandler(arquivo_log, encoding='utf-8')
        handler_arquivo.setLevel(logging.INFO)

        # Handler para console
        handler_console = logging.StreamHandler()
        handler_console.setLevel(logging.WARNING)

        # Formato
        formato = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler_arquivo.setFormatter(formato)
        handler_console.setFormatter(formato)

        self.logger.addHandler(handler_arquivo)
        self.logger.addHandler(handler_console)

    def registrar(self, tipo_evento: TipoEvento, dados: Dict[str, Any]) -> None:
        """
        Registra um evento
        
        Args:
            tipo_evento: Tipo do evento
            dados: Dados do evento
        """
        evento = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo_evento.value,
            "dados": dados
        }

        self.eventos.append(evento)

        # Log também em arquivo de texto
        mensagem = f"[{tipo_evento.value}] {json.dumps(dados)}"
        self.logger.info(mensagem)

    def registrar_teste(self, nome: str, nicho: str, sucesso: bool, 
                       tempo: float, erro: Optional[str] = None) -> None:
        """Registra resultado de um teste"""
        dados = {
            "nome": nome,
            "nicho": nicho,
            "sucesso": sucesso,
            "tempo_segundos": round(tempo, 3),
            "erro": erro
        }

        tipo = TipoEvento.TESTE_CONCLUIDO if sucesso else TipoEvento.TESTE_FALHOU
        self.registrar(tipo, dados)

    def registrar_geracao(self, empresa: str, nicho: str, sucesso: bool,
                         tempo: float, tokens_usados: int = 0, 
                         custo_usd: float = 0, erro: Optional[str] = None) -> None:
        """Registra resultado de uma geração"""
        dados = {
            "empresa": empresa,
            "nicho": nicho,
            "sucesso": sucesso,
            "tempo_segundos": round(tempo, 3),
            "tokens_usados": tokens_usados,
            "custo_usd": round(custo_usd, 4),
            "erro": erro
        }

        tipo = TipoEvento.GERACAO_CONCLUIDA if sucesso else TipoEvento.GERACAO_FALHOU
        self.registrar(tipo, dados)

    def registrar_validacao(self, arquivo: str, valido: bool,
                           erro: Optional[str] = None) -> None:
        """Registra resultado de validação"""
        dados = {
            "arquivo": arquivo,
            "valido": valido,
            "erro": erro
        }

        tipo = TipoEvento.VALIDACAO_OK if valido else TipoEvento.VALIDACAO_FALHOU
        self.registrar(tipo, dados)

    def registrar_erro_api(self, endpoint: str, codigo_erro: int,
                          mensagem: str) -> None:
        """Registra erro de API"""
        dados = {
            "endpoint": endpoint,
            "codigo_erro": codigo_erro,
            "mensagem": mensagem
        }
        self.registrar(TipoEvento.ERRO_API, dados)

    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Calcula estatísticas dos eventos registrados
        
        Returns:
            Dicionário com estatísticas
        """
        if not self.eventos:
            return {}

        testes = [e for e in self.eventos if "teste" in e["tipo"]]
        geracoes = [e for e in self.eventos if "geracao" in e["tipo"]]
        validacoes = [e for e in self.eventos if "validacao" in e["tipo"]]

        # Testes
        testes_ok = [t for t in testes if t["dados"].get("sucesso")]
        tempo_teste_medio = sum(t["dados"]["tempo_segundos"] for t in testes) / len(testes) if testes else 0

        # Gerações
        geracoes_ok = [g for g in geracoes if g["dados"].get("sucesso")]
        tempo_geracao_medio = sum(g["dados"]["tempo_segundos"] for g in geracoes) / len(geracoes) if geracoes else 0
        tokens_total = sum(g["dados"].get("tokens_usados", 0) for g in geracoes)
        custo_total = sum(g["dados"].get("custo_usd", 0) for g in geracoes)

        # Validações
        validacoes_ok = [v for v in validacoes if v["dados"].get("valido")]

        return {
            "total_eventos": len(self.eventos),
            "testes": {
                "total": len(testes),
                "sucesso": len(testes_ok),
                "falhas": len(testes) - len(testes_ok),
                "taxa_sucesso": round(len(testes_ok) / len(testes) * 100, 1) if testes else 0,
                "tempo_medio_segundos": round(tempo_teste_medio, 3)
            },
            "geracoes": {
                "total": len(geracoes),
                "sucesso": len(geracoes_ok),
                "falhas": len(geracoes) - len(geracoes_ok),
                "taxa_sucesso": round(len(geracoes_ok) / len(geracoes) * 100, 1) if geracoes else 0,
                "tempo_medio_segundos": round(tempo_geracao_medio, 3),
                "tokens_total": tokens_total,
                "custo_total_usd": round(custo_total, 4)
            },
            "validacoes": {
                "total": len(validacoes),
                "sucesso": len(validacoes_ok),
                "falhas": len(validacoes) - len(validacoes_ok),
                "taxa_sucesso": round(len(validacoes_ok) / len(validacoes) * 100, 1) if validacoes else 0
            }
        }

    def salvar_metricas(self) -> None:
        """Salva métricas em JSON"""
        dados = {
            "data_inicio": self.eventos[0]["timestamp"] if self.eventos else None,
            "data_fim": self.eventos[-1]["timestamp"] if self.eventos else None,
            "eventos": self.eventos,
            "estatisticas": self.obter_estatisticas()
        }

        with open(self.arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

        print(f"💾 Métricas salvas em: {self.arquivo_json}")

    def exibir_resumo(self) -> None:
        """Exibe resumo das estatísticas"""
        stats = self.obter_estatisticas()

        if not stats:
            print("Nenhuma métrica disponível")
            return

        print("\n" + "="*60)
        print("📊 RESUMO DE MÉTRICAS")
        print("="*60 + "\n")

        # Testes
        if "testes" in stats:
            t = stats["testes"]
            print(f"🧪 Testes:")
            print(f"   Total: {t['total']}")
            print(f"   Sucesso: {t['sucesso']} ({t['taxa_sucesso']}%)")
            print(f"   Tempo médio: {t['tempo_medio_segundos']:.3f}s\n")

        # Gerações
        if "geracoes" in stats:
            g = stats["geracoes"]
            print(f"🤖 Gerações:")
            print(f"   Total: {g['total']}")
            print(f"   Sucesso: {g['sucesso']} ({g['taxa_sucesso']}%)")
            print(f"   Tempo médio: {g['tempo_medio_segundos']:.3f}s")
            print(f"   Tokens: {g['tokens_total']}")
            print(f"   Custo: ${g['custo_total_usd']:.4f}\n")

        # Validações
        if "validacoes" in stats:
            v = stats["validacoes"]
            print(f"✔️  Validações:")
            print(f"   Total: {v['total']}")
            print(f"   Válido: {v['sucesso']} ({v['taxa_sucesso']}%)\n")

        print("="*60 + "\n")


# Instância global de métricas
_metricas_global: Optional[Metricas] = None


def obter_metricas() -> Metricas:
    """Obtém a instância global de métricas"""
    global _metricas_global
    if _metricas_global is None:
        _metricas_global = Metricas()
    return _metricas_global


if __name__ == "__main__":
    # Teste
    print("📊 Módulo de Métricas - Teste\n")

    metricas = Metricas()

    # Simular alguns eventos
    metricas.registrar_teste("Empresa 1", "Software", True, 5.23)
    metricas.registrar_teste("Empresa 2", "Consultoria", True, 4.87)
    metricas.registrar_teste("Empresa 3", "E-commerce", False, 3.21, "Timeout API")

    metricas.registrar_geracao("Tech Corp", "Software", True, 8.5, 1500, 0.025)
    metricas.registrar_geracao("Marketing Plus", "Marketing", True, 7.2, 1400, 0.023)

    metricas.registrar_validacao("config1.json", True)
    metricas.registrar_validacao("config2.json", False, "Cor hexadecimal inválida")

    metricas.exibir_resumo()
    metricas.salvar_metricas()
