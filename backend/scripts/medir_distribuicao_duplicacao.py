#!/usr/bin/env python3
"""
Mede a DISTRIBUIÇÃO de pares duplicados por config gerado -- 0, 1, 2, 3+
pares -- antes de decidir se vale expandir o Repair Prompt pra corrigir
mais de um par por chamada (decisão do Tech Lead, 2026-08-06: medir a
frequência do problema antes de aumentar a complexidade da solução).

Diferença pra schema_validator._validar_regras_conteudo: aquela função
para no PRIMEIRO par encontrado (correto pra decidir bloquear ou não a
geração). Esta aqui encontra TODOS os pares -- só pra medir, nunca chamada
pelo pipeline de produção.

Gera configs BRUTOS (sem reparo, sem retry -- MAX_TENTATIVAS_GERACAO=1 e
AgenteConstrutor._tentar_reparo_duplicacao neutralizado via monkeypatch só
nesta execução) pra medir a taxa de duplicação nativa do modelo, isolada
de qualquer correção.

Uso:
    python backend/scripts/medir_distribuicao_duplicacao.py [n_nichos]
"""
import itertools
import os
import sys
from collections import Counter
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

from schema_validator import _texto_normalizado, _LIMIAR_SIMILARIDADE_DUPLICATA
import difflib


def _encontrar_todos_pares(config: dict) -> list:
    """
    Mesma lógica de agrupamento de schema_validator._validar_regras_conteudo
    (títulos: sections+services+features; textos: sections.content+
    services.description+features.description; perguntas: faq) -- mas
    retorna TODOS os pares acima do limiar, não só o primeiro.
    """
    sections = config.get("sections") or []
    services = config.get("services") or []
    features = config.get("features") or []
    faq = config.get("faq") or []

    grupos = {
        "titulo": (
            [(f"sections[{s.get('id')}].title", s.get("title")) for s in sections]
            + [(f"services[{s.get('id')}].title", s.get("title")) for s in services]
            + [(f"features[{f.get('id')}].title", f.get("title")) for f in features]
        ),
        "texto": (
            [(f"sections[{s.get('id')}].content", s.get("content")) for s in sections]
            + [(f"services[{s.get('id')}].description", s.get("description")) for s in services]
            + [(f"features[{f.get('id')}].description", f.get("description")) for f in features]
        ),
        "pergunta_faq": [(f"faq[{f.get('id')}].question", f.get("question")) for f in faq],
    }

    pares = []
    for grupo, textos in grupos.items():
        normalizados = [(ident, _texto_normalizado(texto)) for ident, texto in textos if (texto or "").strip()]
        for (ident_a, texto_a), (ident_b, texto_b) in itertools.combinations(normalizados, 2):
            similaridade = difflib.SequenceMatcher(None, texto_a, texto_b).ratio()
            if similaridade >= _LIMIAR_SIMILARIDADE_DUPLICATA:
                pares.append((grupo, ident_a, ident_b, round(similaridade, 2)))
    return pares


NICHOS = [
    ("Auto Elétrica Silva", "Auto Elétrica", "#0066CC"),
    ("Academia Power", "Academia de Ginástica", "#FF006E"),
    ("Consultório Odontológico", "Odontologia", "#0099FF"),
    ("Escritório de Advocacia", "Advocacia Geral", "#1F2937"),
    ("Pet Shop Amigos", "Pet Shop", "#FF85C0"),
    ("Pizzaria do João", "Pizzaria", "#EA580C"),
    ("Restaurante Gourmet", "Restaurante", "#8E7D43"),
    ("Padaria Artesanal", "Padaria", "#D2691E"),
    ("Consultoria Jurídica Silva", "Consultoria Jurídica", "#8B0000"),
    ("Clínica Veterinária", "Veterinária", "#22D3EE"),
]


def main():
    import agent_construtor as ac

    limite = int(sys.argv[1]) if len(sys.argv) > 1 else len(NICHOS)
    nichos = NICHOS[:limite]

    ac.MAX_TENTATIVAS_GERACAO = 1
    ac.AgenteConstrutor._tentar_reparo_duplicacao = lambda self, config, erro, nicho: None  # neutraliza só nesta execução
    # ValidadorSchema.validar_json também é neutralizado -- sem isso,
    # gerar_config_site levanta ValueError e DESCARTA o config bruto nos
    # casos que mais importam pra essa medição (os que têm duplicação).
    # Queremos o config bruto sempre, independente de passar na validação
    # de produção -- _encontrar_todos_pares faz a própria contagem depois.
    ac.ValidadorSchema.validar_json = staticmethod(lambda config: (True, None, None))

    agente = ac.AgenteConstrutor()

    distribuicao = Counter()
    contagem_campo = Counter()
    contagem_indice = Counter()
    total_configs = 0

    for nome, nicho, cor in nichos:
        try:
            config = agente.gerar_config_site(nome_empresa=nome, nicho=nicho, cor_primaria=cor)
        except Exception as e:
            print(f"{nicho}: ERRO na geração ({e}) -- excluído da distribuição")
            continue

        total_configs += 1
        pares = _encontrar_todos_pares(config)
        n_pares = len(pares)
        distribuicao[n_pares if n_pares < 4 else "4+"] += 1

        print(f"{nicho}: {n_pares} par(es)")
        for grupo, ident_a, ident_b, sim in pares:
            print(f"    {grupo}: {ident_a} × {ident_b} ({sim})")
            for ident in (ident_a, ident_b):
                campo = ident.split(".")[-1]
                indice = ident.split("[")[1].split("]")[0]
                tipo = ident.split("[")[0]
                contagem_campo[campo] += 1
                contagem_indice[f"{tipo}[{indice}]"] += 1

    print(f"\n=== DISTRIBUIÇÃO DE PARES POR CONFIG (n={total_configs}) ===")
    for chave in [0, 1, 2, 3, "4+"]:
        qtd = distribuicao.get(chave, 0)
        pct = 100 * qtd / total_configs if total_configs else 0
        print(f"{chave} par(es): {qtd}/{total_configs} ({pct:.0f}%)")

    print("\n=== CAMPOS MAIS RECORRENTES NAS DUPLICATAS ===")
    for campo, qtd in contagem_campo.most_common():
        print(f"{campo}: {qtd}")

    print("\n=== ÍTENS (índice) MAIS RECORRENTES NAS DUPLICATAS ===")
    for indice, qtd in contagem_indice.most_common(10):
        print(f"{indice}: {qtd}")


if __name__ == "__main__":
    main()
