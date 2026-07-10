#!/usr/bin/env python3
"""
Gera o portfólio semente de demos para o Lovable (ROADMAP.md, Fase 0:
"Portfólio semente: 3-5 sites demo do nicho escolhido").

Para cada seed roda o Agente Construtor de verdade (chamada real de IA,
inclusive para derivar a paleta de cores completa a partir de
`cor_primaria` — ver `gerar_paleta_cores()`) e o
AgenteVendedor.conectar_lovable() para produzir um prompt pronto para
colar no chat do Lovable. Salva cada prompt em lovable_prompts/<slug>.txt,
junto com o site-config.json correspondente (lovable_prompts/<slug>.json)
para auditoria/consistência entre a demo e o site de produção.

Nicho definido na Fase 0 do ROADMAP.md: Clínicas Médicas/Saúde (Grande
Vitória-ES) — Odontologia, Fisioterapia e Dermatologia, um por bairro.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_construtor import AgenteConstrutor
from agents.vendedor import AgenteVendedor

SEEDS_PORTFOLIO = [
    {
        "nome_empresa": "Alumi Odontologia Integrada",
        # nicho + regiao curtos de propósito: o siteTitle (H1/SEO) combina os
        # dois e tem limite de 60 caracteres — "Odontologia Estética e
        # Implantes" + "Jardim da Penha, Vitória - ES" originais estouravam
        # esse limite em toda tentativa, não só por azar do retry.
        "nicho": "Odontologia Estética",
        "regiao": "Jardim da Penha, Vitória",
        "cor_primaria": "#0D9488",  # Verde Teal (Saúde e modernidade)
    },
    {
        "nome_empresa": "Studio Vértice Fisioterapia",
        "nicho": "Fisioterapia e Pilates",
        "regiao": "Praia do Canto, Vitória",
        "cor_primaria": "#4F46E5",  # Índigo (Confiança e solidez técnica)
    },
    {
        "nome_empresa": "Clínica Pele & Art",
        "nicho": "Dermatologia Estética",
        "regiao": "Enseada do Suá, Vitória",
        "cor_primaria": "#BE185D",  # Rosa Escuro/Borgonha (Estética premium)
    },
]

PASTA_SAIDA = Path(__file__).resolve().parent.parent.parent / "lovable_prompts"


def main():
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else None
    seeds = SEEDS_PORTFOLIO[:limite] if limite else SEEDS_PORTFOLIO

    construtor = AgenteConstrutor()
    vendedor = AgenteVendedor()
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    print(f"Gerando {len(seeds)} demo(s) para o portfólio do Lovable...\n")

    for i, seed in enumerate(seeds, 1):
        print(f"[{i}/{len(seeds)}] {seed['nome_empresa']} ({seed['nicho']})...")

        site_config = construtor.gerar_config_site(
            nome_empresa=seed["nome_empresa"],
            nicho=seed["nicho"],
            cor_primaria=seed["cor_primaria"],
            localizacao=seed["regiao"],
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
