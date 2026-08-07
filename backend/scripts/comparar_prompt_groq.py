#!/usr/bin/env python3
"""
Compara o efeito do campo "planejamentoServicos" (commit fd44152) no prompt
de geração, isolando ESSA variável e mantendo tudo o resto (validação,
image engine, fallback) na versão atual do código.

Contexto (ver memória de projeto, sessão 2026-08-04/06 -- "DoPS + Fase 1"):
3 provedores diferentes (Ollama 8B, NVIDIA NIM 8B, Groq 70B) falham por
MODEL_DUPLICATION (services×services) na mesma proporção -- evidência de
que o problema é o prompt, não capacidade do modelo. planejamentoServicos
foi a correção proposta, mas nunca foi validada de verdade: 3 tentativas
na mesma sessão de 2026-08-06 falharam por esgotamento de cota do Groq
(TPD e depois TPM), sempre ANTES de produzir dado da versão nova.

Uso (rodar 1x por dia, NUNCA mais de uma vez no mesmo dia -- ver
[[feedback_orcamento_antes_de_diagnostico]]):

    python backend/scripts/comparar_prompt_groq.py

Pré-requisitos pra não repetir os mesmos erros:
- GROQ_API_KEY configurada em backend/.env, cota diária (100k tokens/dia,
  tier gratuito) preservada -- NÃO rodar nenhum outro teste/diagnóstico
  no Groq no mesmo dia antes disto. Este script já é o "teste de cota".
- AI_PROVIDER_FALLBACK_ORDER é forçado pra "groq" (sem fallback) aqui
  dentro -- se o Groq falhar, o erro aparece explícito no resultado, nunca
  mascarado por uma resposta silenciosa do Ollama (ver
  [[feedback_verificar_mecanismo_real_antes_de_concluir]]).
- Pausa de PAUSA_ENTRE_NICHOS_SEGUNDOS entre cada nicho -- o TPM do tier
  gratuito (12.000 tokens/min) estoura em ~5 chamadas sem pausa.
"""
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
COMMIT_PROMPT_ANTIGO = "0131812"  # imediatamente ANTES de fd44152 (planejamentoServicos)

sys.path.insert(0, str(BACKEND_DIR))
for linha in (BACKEND_DIR / ".env").read_text(encoding="utf-8").splitlines():
    linha = linha.strip()
    if not linha or linha.startswith("#") or "=" not in linha:
        continue
    k, v = linha.split("=", 1)
    os.environ.setdefault(k, v)

os.environ["AI_PROVIDER_FALLBACK_ORDER"] = "groq"
os.environ.setdefault("GROQ_TIMEOUT", "90")

PAUSA_ENTRE_NICHOS_SEGUNDOS = 25
PAUSA_ENTRE_FASES_SEGUNDOS = 50

NICHOS = [
    ("Auto Elétrica Silva", "Auto Elétrica", "#0066CC"),
    ("Academia Power", "Academia de Ginástica", "#FF006E"),
    ("Consultório Odontológico", "Odontologia", "#0099FF"),
    ("Escritório de Advocacia", "Advocacia Geral", "#1F2937"),
    ("Pet Shop Amigos", "Pet Shop", "#FF85C0"),
    ("Pizzaria do João", "Pizzaria", "#EA580C"),
    ("Restaurante Gourmet", "Restaurante", "#8E7D43"),
    ("Confeitaria Doces", "Confeitaria", "#DC143C"),
]


def _carregar_modulo_antigo():
    """Extrai backend/agent_construtor.py do commit anterior a
    planejamentoServicos via `git show` e carrega como módulo Python
    separado -- não deixa arquivo nenhum pra trás no repo."""
    fonte = subprocess.run(
        ["git", "show", f"{COMMIT_PROMPT_ANTIGO}:backend/agent_construtor.py"],
        cwd=BACKEND_DIR.parent, capture_output=True, text=True, check=True, encoding="utf-8",
    ).stdout

    caminho_tmp = BACKEND_DIR / "_tmp_agent_construtor_prompt_antigo.py"
    caminho_tmp.write_text(fonte, encoding="utf-8")
    try:
        spec = importlib.util.spec_from_file_location("agent_construtor_prompt_antigo", caminho_tmp)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    finally:
        caminho_tmp.unlink(missing_ok=True)


def rodar(modulo, nome_versao):
    from test_agentes import _categorizar_erro, _extrair_par_duplicacao

    resultados = []
    agente = modulo.AgenteConstrutor()
    for i, (nome, nicho, cor) in enumerate(NICHOS):
        if i > 0:
            time.sleep(PAUSA_ENTRE_NICHOS_SEGUNDOS)
        t0 = time.time()
        try:
            agente.gerar_config_site(nome_empresa=nome, nicho=nicho, cor_primaria=cor)
            tokens = agente.ai.uso_tokens_ativo if hasattr(agente, "ai") else None
            resultados.append({
                "nicho": nicho, "sucesso": True, "erro": None,
                "categorias": [], "par_duplicacao": None,
                "tempo_segundos": round(time.time() - t0, 1), "tokens": tokens,
            })
        except Exception as e:
            msg = str(e)
            resultados.append({
                "nicho": nicho, "sucesso": False, "erro": msg[:400],
                "categorias": _categorizar_erro(msg), "par_duplicacao": _extrair_par_duplicacao(msg),
                "tempo_segundos": round(time.time() - t0, 1), "tokens": None,
            })
        r = resultados[-1]
        status = "OK" if r["sucesso"] else f"FALHOU {r['categorias']}"
        print(f"[{nome_versao}] {nicho}: {status} ({r['tempo_segundos']}s)")
    return resultados


def resumo(resultados):
    sucesso = sum(1 for r in resultados if r["sucesso"])
    total = len(resultados)
    duplicacao = sum(1 for r in resultados if "MODEL_DUPLICATION" in r.get("categorias", []))
    pares = [r["par_duplicacao"] for r in resultados if r.get("par_duplicacao")]
    return {"total": total, "sucesso": sucesso, "taxa_pct": round(100 * sucesso / total, 1),
            "falhas_duplicacao": duplicacao, "pares": pares}


def main():
    import agent_construtor as ac_novo
    ac_antigo = _carregar_modulo_antigo()
    ac_novo.MAX_TENTATIVAS_GERACAO = 1
    ac_antigo.MAX_TENTATIVAS_GERACAO = 1

    print("=== Rodando versao ANTIGA (sem planejamentoServicos) ===")
    res_antigo = rodar(ac_antigo, "ANTIGO")

    print(f"\n--- pausa de {PAUSA_ENTRE_FASES_SEGUNDOS}s entre as duas fases ---")
    time.sleep(PAUSA_ENTRE_FASES_SEGUNDOS)

    print("\n=== Rodando versao NOVA (com planejamentoServicos) ===")
    res_novo = rodar(ac_novo, "NOVO")

    saida = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "amostra": [n for n, _, _ in NICHOS],
        "antigo": {"resumo": resumo(res_antigo), "resultados": res_antigo},
        "novo": {"resumo": resumo(res_novo), "resultados": res_novo},
    }

    pasta = BACKEND_DIR / "benchmark"
    pasta.mkdir(exist_ok=True)
    caminho = pasta / f"{time.strftime('%Y-%m-%d_%H%M%S')}-comparacao-prompt-antigo-vs-novo.json"
    caminho.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== RESUMO ===")
    print("ANTIGO:", saida["antigo"]["resumo"])
    print("NOVO:  ", saida["novo"]["resumo"])
    print(f"\nSalvo em {caminho}")


if __name__ == "__main__":
    main()
