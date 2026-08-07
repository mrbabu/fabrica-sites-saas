#!/usr/bin/env python3
"""
Repair Prompt Analysis (não "Improvement") -- decisão explícita do usuário
(Tech Lead), 2026-08-06: antes de mexer no texto do prompt de reparo,
isolar POR QUE ele às vezes não resolve a duplicação. Causas possíveis,
nenhuma escolhida a priori: redação do prompt, capacidade do modelo 8B,
parâmetros de geração (temperature/top_p/max_tokens), ou o próprio
mecanismo de detecção -- não dá pra saber sem medir.

Isola o mecanismo de reparo (AgenteConstrutor._tentar_reparo_duplicacao)
da geração completa do site -- roda repetidamente contra pares de texto
duplicado FIXOS (reais, capturados nos benchmarks de hoje), removendo a
variância de "será que a geração principal duplicou desta vez" que
confundia as medições anteriores (2/6, 3/6 misturavam geração+retry+reparo).

Classificação de cada tentativa, baseada na MESMA métrica de similaridade
que já decide TXT-01 (difflib.SequenceMatcher, limiar 0.85 -- ver
schema_validator._LIMIAR_SIMILARIDADE_DUPLICATA), não uma métrica nova
inventada:

- ECO_COMPLETO: texto devolvido é >=95% igual ao original (não reescreveu).
- MUDANCA_INSUFICIENTE: mudou em relação ao original, mas ainda >=85%
  parecido com o texto conflitante (continua sendo duplicata pro TXT-01).
- SUCESSO: <85% parecido com o conflitante -- deixa de ser duplicata.
- ERRO: exceção, resposta sem o campo "texto", ou não-string.

Uso:
    python backend/scripts/analisar_reparo.py [tentativas_por_cenario]
"""
import difflib
import os
import re
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
for linha in (BACKEND_DIR / ".env").read_text(encoding="utf-8").splitlines():
    linha = linha.strip()
    if not linha or linha.startswith("#") or "=" not in linha:
        continue
    k, v = linha.split("=", 1)
    os.environ.setdefault(k, v)

os.environ["AI_PROVIDER_FALLBACK_ORDER"] = "nvidia_nim"

LIMIAR_DUPLICATA = 0.85
LIMIAR_ECO = 0.95


def _normalizado(texto: str) -> str:
    return re.sub(r"\s+", " ", (texto or "").strip().lower())


def _similaridade(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _normalizado(a), _normalizado(b)).ratio()


def classificar_reparo(texto_original: str, texto_retornado, texto_conflitante: str) -> dict:
    """
    Classifica o resultado de UMA tentativa de reparo. Puro, sem I/O --
    testável isoladamente (ver test_analisar_reparo.py).
    """
    if not isinstance(texto_retornado, str) or not texto_retornado.strip():
        return {"categoria": "ERRO", "sim_original": None, "sim_conflitante": None}

    sim_original = _similaridade(texto_original, texto_retornado)
    sim_conflitante = _similaridade(texto_conflitante, texto_retornado)

    if sim_original >= LIMIAR_ECO:
        categoria = "ECO_COMPLETO"
    elif sim_conflitante >= LIMIAR_DUPLICATA:
        categoria = "MUDANCA_INSUFICIENTE"
    else:
        categoria = "SUCESSO"

    return {"categoria": categoria, "sim_original": round(sim_original, 3), "sim_conflitante": round(sim_conflitante, 3)}


# Cenários reais, capturados nos benchmarks desta sessão (não inventados) --
# cada um é um par (texto_a, texto_b) que já disparou TXT-01 de verdade.
CENARIOS = [
    {
        "nicho": "Auto Elétrica",
        "campo": "description",
        "texto_conflitante": "Cuidamos de cada detalhe do seu projeto elétrico com atenção.",
        "texto_a_reparar": "Cuidamos de cada detalhe do seu projeto elétrico com atenção.",
    },
    {
        "nicho": "Academia de Ginástica",
        "campo": "title",
        "texto_conflitante": "Atendimento especializado",
        "texto_a_reparar": "Atendimento especializado",
    },
    {
        "nicho": "Advocacia Geral",
        "campo": "description",
        "texto_conflitante": "Oferecemos consultoria jurídica completa para proteger seus interesses.",
        "texto_a_reparar": "Prestamos consultoria jurídica completa para proteger seus interesses.",
    },
]


def main():
    from agent_construtor import AgenteConstrutor, _montar_prompt_reparo

    tentativas_por_cenario = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    agente = AgenteConstrutor()

    resultados = []
    for cenario in CENARIOS:
        for i in range(tentativas_por_cenario):
            prompt = _montar_prompt_reparo(
                cenario["campo"], cenario["texto_a_reparar"], cenario["texto_conflitante"], cenario["nicho"]
            )
            t0 = time.time()
            try:
                resposta = agente.ai.gerar_json(prompt, max_tokens=300)
                texto_retornado = (resposta or {}).get("texto")
                erro = None
            except Exception as e:
                texto_retornado = None
                erro = str(e)[:200]
            tempo = time.time() - t0

            classificacao = classificar_reparo(cenario["texto_a_reparar"], texto_retornado, cenario["texto_conflitante"])
            resultado = {
                "nicho": cenario["nicho"],
                "tentativa": i + 1,
                "texto_retornado": texto_retornado,
                "erro": erro,
                "tempo_segundos": round(tempo, 1),
                "tokens": getattr(agente.ai, "uso_tokens_ativo", None),
                **classificacao,
            }
            resultados.append(resultado)
            print(f"[{cenario['nicho']} #{i+1}] {classificacao['categoria']} "
                  f"(sim_original={classificacao['sim_original']}, sim_conflitante={classificacao['sim_conflitante']}) "
                  f"({tempo:.1f}s)")
            if texto_retornado:
                print(f"    -> {texto_retornado!r}")

    print("\n=== DISTRIBUIÇÃO ===")
    contagem = {}
    for r in resultados:
        contagem[r["categoria"]] = contagem.get(r["categoria"], 0) + 1
    total = len(resultados)
    for categoria, qtd in sorted(contagem.items(), key=lambda p: -p[1]):
        print(f"{categoria}: {qtd}/{total} ({100*qtd/total:.0f}%)")


if __name__ == "__main__":
    main()
