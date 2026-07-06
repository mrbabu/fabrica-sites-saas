#!/usr/bin/env python3
"""
Teste da API - Fábrica de Sites SaaS
Script para testar o endpoint FastAPI localmente
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TesteadorAPI:
    """Testa a API do servidor FastAPI"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.resultados = []

    def health_check(self) -> bool:
        """Verifica se a API está online"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API está pronta!")
                print(f"   Status: {data['status']}")
                print(f"   Agente ativo: {data['agente_ativo']}")
                return True
            else:
                print(f"❌ API respondeu com erro: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Não conseguiu conectar em {self.base_url}")
            print(f"   Verifique se o servidor está rodando: python app.py")
            return False
        except Exception as e:
            print(f"❌ Erro ao fazer health check: {e}")
            return False

    def testar_geracao(self, nome_empresa: str, nicho: str, cor: str) -> Dict[str, Any]:
        """Testa geração de um site"""
        print(f"\n📝 Testando: {nome_empresa} ({nicho}) - {cor}")
        
        payload = {
            "nome_empresa": nome_empresa,
            "nicho": nicho,
            "cor_preferida": cor,
            "salvar_arquivo": True
        }

        try:
            tempo_inicio = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/generate-site",
                json=payload,
                timeout=60
            )
            tempo_total = time.time() - tempo_inicio

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Sucesso em {tempo_total:.2f}s")
                print(f"   Empresa: {data['data']['company']['name']}")
                print(f"   Serviços: {len([s for s in data['data']['services'] if s.get('enabled')])}")
                
                resultado = {
                    "nome": nome_empresa,
                    "nicho": nicho,
                    "sucesso": True,
                    "tempo": tempo_total,
                    "status_code": response.status_code
                }
                self.resultados.append(resultado)
                return resultado
            else:
                erro = response.json()
                print(f"   ❌ Erro {response.status_code}")
                print(f"   {erro.get('detail', erro)}")
                
                resultado = {
                    "nome": nome_empresa,
                    "nicho": nicho,
                    "sucesso": False,
                    "tempo": tempo_total,
                    "status_code": response.status_code,
                    "erro": str(erro)
                }
                self.resultados.append(resultado)
                return resultado

        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout (>60s)")
            return {
                "nome": nome_empresa,
                "sucesso": False,
                "erro": "Timeout"
            }
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {
                "nome": nome_empresa,
                "sucesso": False,
                "erro": str(e)
            }

    def testar_multiplos(self, nichos: list) -> None:
        """Testa vários nichos"""
        print("\n" + "="*60)
        print("🧪 TESTE DA API - Fábrica de Sites SaaS")
        print("="*60)

        # Health check
        if not self.health_check():
            return

        print("\n" + "-"*60)
        print("Testando gerações...\n")

        for nome, nicho, cor in nichos:
            self.testar_geracao(nome, nicho, cor)
            time.sleep(1)  # Evitar rate limit

        # Resumo
        self._exibir_resumo()

    def obter_metricas(self) -> None:
        """Obtém métricas da API"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/metrics")
            if response.status_code == 200:
                metricas = response.json()
                print("\n" + "="*60)
                print("📊 MÉTRICAS DA API")
                print("="*60)
                print(json.dumps(metricas, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Erro ao obter métricas: {e}")

    def _exibir_resumo(self) -> None:
        """Exibe resumo dos testes"""
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES")
        print("="*60 + "\n")

        total = len(self.resultados)
        sucessos = sum(1 for r in self.resultados if r.get("sucesso"))
        tempo_total = sum(r.get("tempo", 0) for r in self.resultados)

        print(f"Total de testes: {total}")
        print(f"Sucessos: {sucessos}")
        print(f"Falhas: {total - sucessos}")
        print(f"Taxa de sucesso: {sucessos/total*100:.1f}%")
        print(f"Tempo total: {tempo_total:.2f}s")
        print(f"Tempo médio: {tempo_total/total:.2f}s\n")

        # Detalhe por nicho
        print("Detalhes:")
        for r in self.resultados:
            status = "✅" if r.get("sucesso") else "❌"
            print(f"  {status} {r['nome']:<40} ({r.get('tempo', 0):.2f}s)")


def main():
    """Função principal"""
    import sys

    print("\n🚀 Teste da API - Fábrica de Sites SaaS\n")

    # Nichos para testar
    nichos_teste = [
        ("Tech Solutions", "Software/SaaS", "#4F46E5"),
        ("Digital Boost Agency", "Agência de Marketing", "#FF6B35"),
        ("Spa Wellness", "Spa e Bem-estar", "#D946EF"),
        ("Pet Shop Amigos", "Pet Shop", "#FF85C0"),
        ("Pizzaria do João", "Pizzaria", "#EA580C"),
    ]

    testador = TesteadorAPI()

    if len(sys.argv) > 1:
        if sys.argv[1] == "health":
            testador.health_check()
        elif sys.argv[1] == "metrics":
            testador.obter_metricas()
        elif sys.argv[1] == "single":
            if len(sys.argv) >= 5:
                testador.testar_geracao(sys.argv[2], sys.argv[3], sys.argv[4])
            else:
                print("Uso: python test_api.py single <nome> <nicho> <cor>")
        else:
            print("Opções:")
            print("  health  — Check se API está pronta")
            print("  metrics — Mostrar métricas")
            print("  single  — Testar um nicho")
            print("  (padrão) — Testar 5 nichos")
    else:
        testador.testar_multiplos(nichos_teste)


if __name__ == "__main__":
    main()
