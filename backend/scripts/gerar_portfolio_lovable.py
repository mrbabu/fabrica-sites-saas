#!/usr/bin/env python3
"""
Gera o portfólio semente de demos para o Lovable (ROADMAP.md, Fase 0:
"Portfólio semente: 3-5 sites demo do nicho escolhido").

Para cada seed (nome, nicho, cor[, localização]) roda o Agente Construtor de
verdade (chamada real de IA) e o AgenteVendedor.conectar_lovable() para
produzir um prompt pronto para colar no chat do Lovable. Salva cada prompt em
lovable_prompts/<slug>.txt, junto com o site-config.json correspondente
(lovable_prompts/<slug>.json) para auditoria/consistência entre a demo e o
site de produção.

Os SEEDS abaixo são só exemplos de nichos variados para validar o gerador —
troque pelo nicho + região definidos na Fase 0 do ROADMAP.md antes de usar
isto como portfólio de vendas real.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_construtor import AgenteConstrutor
from agents.vendedor import AgenteVendedor

SEEDS = [
    ("Mecânica do Raphinha", "Oficina Mecânica", "#1E3A8A", "Vitória, ES"),
    ("Salão Beleza Rara", "Salão de Beleza", "#BE185D", "Curitiba, PR"),
    ("Padaria Sabor Dourado", "Padaria Artesanal", "#D97706", "Belo Horizonte, MG"),
]

PASTA_SAIDA = Path(__file__).resolve().parent.parent.parent / "lovable_prompts"


def main():
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else None
    seeds = SEEDS[:limite] if limite else SEEDS

    construtor = AgenteConstrutor()
    vendedor = AgenteVendedor()
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    print(f"Gerando {len(seeds)} demo(s) para o portfólio do Lovable...\n")

    for i, (nome, nicho, cor, localizacao) in enumerate(seeds, 1):
        print(f"[{i}/{len(seeds)}] {nome} ({nicho})...")

        site_config = construtor.gerar_config_site(
            nome_empresa=nome,
            nicho=nicho,
            cor_primaria=cor,
            localizacao=localizacao,
        )
        payload = vendedor.conectar_lovable(site_config)
        slug = payload["slug"]

        (PASTA_SAIDA / f"{slug}.txt").write_text(payload["prompt_lovable"], encoding="utf-8")
        (PASTA_SAIDA / f"{slug}.json").write_text(
            json.dumps(site_config, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"    -> lovable_prompts/{slug}.txt (prompt) + {slug}.json (site-config)\n")

    print(f"Portfólio gerado em: {PASTA_SAIDA}")
    print("Cole o conteúdo de cada .txt no chat do Lovable para gerar a demo visual.")


if __name__ == "__main__":
    main()
