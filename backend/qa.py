#!/usr/bin/env python3
"""
Runner único de QA — ponto de entrada para todos os testes do projeto.

Substitui o "lembre-se de rodar 4 scripts diferentes na mão" por um único
comando com código de saída confiável (0 = tudo passou, 1 = algo quebrou).

As suítes são classificadas em dois grupos:

  RÁPIDA  — determinística, sem rede, sem servidor, sem LLM real.
            É o gate de commit (.githooks/pre-commit). Orçamento: < 30s.
  LENTA   — depende de infra externa (LLM real, servidor HTTP de pé).
            Fica FORA do gate de commit porque não é reprodutível: uma
            falha aqui pode ser culpa da rede, não do código.

Uso:
    python backend/qa.py              # só as rápidas (é o que o hook roda)
    python backend/qa.py --todas      # rápidas + lentas
    python backend/qa.py --lentas     # só as lentas
    python backend/qa.py --lista      # mostra as suítes e sai
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

# Orçamento de tempo do gate de commit. Não falha o build — só avisa, pra
# a lentidão aparecer antes de virar motivo pra desativar o hook.
ORCAMENTO_RAPIDO_S = 30.0

# Teto por suíte, pra um teste travado não pendurar o commit pra sempre.
TIMEOUT_SUITE_S = 300


@dataclass(frozen=True)
class Suite:
    """Uma suíte de testes, executada como script próprio ou via pytest."""

    nome: str
    arquivo: str
    rapida: bool
    descricao: str
    # Só para as lentas: o que precisa estar de pé pra ela rodar.
    requisito: str = ""
    # Suítes migradas pra pytest; as antigas ainda são scripts com main().
    pytest: bool = False

    def comando(self) -> list[str]:
        if self.pytest:
            # -p no:cacheprovider: não cria backend/.pytest_cache no repo.
            return [sys.executable, "-m", "pytest", self.arquivo, "-q", "-p", "no:cacheprovider"]
        return [sys.executable, self.arquivo]


SUITES: list[Suite] = [
    Suite(
        nome="image_utils",
        arquivo="test_image_utils.py",
        rapida=True,
        descricao="Categorização de nichos, dedup de query, cor por categoria",
    ),
    Suite(
        nome="ollama_provider",
        arquivo="test_ollama_provider.py",
        rapida=True,
        descricao="Validação de modelo local do ProvedorOllama (requests mockado)",
    ),
    Suite(
        nome="agentes",
        arquivo="test_agentes.py",
        rapida=True,
        descricao="Cadeia de provedores + pipeline do Agente Construtor (dublado)",
        pytest=True,
    ),
    Suite(
        nome="agentes_llm",
        arquivo="test_agentes_llm.py",
        rapida=False,
        descricao="Benchmark de qualidade em 50 nichos contra LLM real",
        requisito="LLM real (Ollama local ou chave de API) — gera custo/latência",
    ),
    Suite(
        nome="api",
        arquivo="test_api.py",
        rapida=True,
        descricao="Endpoints da API via TestClient (sem servidor, sem IA, sem banco)",
        pytest=True,
    ),
]


@dataclass
class Resultado:
    suite: Suite
    passou: bool
    segundos: float
    saida: str


def executar_suite(suite: Suite) -> Resultado:
    """Roda uma suíte como subprocesso e traduz o exit code em passou/falhou."""
    inicio = time.time()
    try:
        proc = subprocess.run(
            suite.comando(),
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SUITE_S,
        )
        saida = (proc.stdout or "") + (proc.stderr or "")
        passou = proc.returncode == 0
    except subprocess.TimeoutExpired:
        saida = f"Suíte excedeu o limite de {TIMEOUT_SUITE_S}s e foi interrompida."
        passou = False

    return Resultado(suite, passou, time.time() - inicio, saida)


def selecionar(rapidas: bool, lentas: bool) -> list[Suite]:
    return [s for s in SUITES if (s.rapida and rapidas) or (not s.rapida and lentas)]


def imprimir_lista() -> None:
    print("\nSuítes registradas:\n")
    for grupo, rapida in (("RÁPIDA (gate de commit)", True), ("LENTA (fora do gate)", False)):
        print(f"  {grupo}")
        for s in (x for x in SUITES if x.rapida is rapida):
            print(f"    • {s.nome:<18} {s.arquivo}")
            print(f"      {s.descricao}")
            if s.requisito:
                print(f"      requer: {s.requisito}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Runner único de QA da Fábrica de Sites.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--todas", action="store_true", help="roda rápidas + lentas")
    parser.add_argument("--lentas", action="store_true", help="roda só as lentas")
    parser.add_argument("--lista", action="store_true", help="lista as suítes e sai")
    args = parser.parse_args()

    if args.lista:
        imprimir_lista()
        return 0

    rapidas = not args.lentas
    lentas = args.todas or args.lentas
    alvo = selecionar(rapidas, lentas)

    rotulo = "rápidas + lentas" if (rapidas and lentas) else ("lentas" if lentas else "rápidas")
    print(f"\n🧪 QA — rodando {len(alvo)} suíte(s) [{rotulo}]\n")

    resultados: list[Resultado] = []
    for suite in alvo:
        print(f"  ▸ {suite.nome} ... ", end="", flush=True)
        r = executar_suite(suite)
        resultados.append(r)
        print(f"{'✅' if r.passou else '❌'} {r.segundos:.1f}s")

    falhas = [r for r in resultados if not r.passou]
    total_s = sum(r.segundos for r in resultados)

    # Só o log das que falharam — sucesso não precisa de 300 linhas de ruído.
    for r in falhas:
        print(f"\n{'=' * 70}")
        print(f"❌ {r.suite.nome} ({r.suite.arquivo})")
        print("=" * 70)
        print(r.saida.rstrip())

    print(f"\n{'=' * 70}")
    print(f"{len(resultados) - len(falhas)}/{len(resultados)} suíte(s) passaram em {total_s:.1f}s")

    if rapidas and not lentas and total_s > ORCAMENTO_RAPIDO_S:
        print(f"⚠️  Acima do orçamento de {ORCAMENTO_RAPIDO_S:.0f}s do gate de commit.")

    if falhas:
        print(f"❌ FALHOU: {', '.join(r.suite.nome for r in falhas)}")
        return 1

    print("✅ Tudo passou.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
