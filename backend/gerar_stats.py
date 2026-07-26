#!/usr/bin/env python3
"""
Gera backend/cache/stats.json a partir da telemetria acumulada em
backend/cache/telemetria_imagens.jsonl e backend/cache/unknown_categories.jsonl.

Uso: python gerar_stats.py
"""

import json

from image_utils import salvar_estatisticas


def main() -> None:
    stats = salvar_estatisticas()
    print(json.dumps(stats, ensure_ascii=False, indent=2))

    print()
    if stats["dentro_da_meta"]:
        print(f"✅ Taxa de fallback {stats['taxa_fallback']:.2%} dentro da meta (<= {stats['meta_taxa_fallback']:.2%})")
    else:
        print(
            f"⚠️  Taxa de fallback {stats['taxa_fallback']:.2%} ACIMA da meta "
            f"(<= {stats['meta_taxa_fallback']:.2%}) — ver 'categorias_desconhecidas' em stats.json "
            f"para saber quais nichos cadastrar em backend/data/niches.json."
        )


if __name__ == "__main__":
    main()
