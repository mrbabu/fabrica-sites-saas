#!/usr/bin/env python3
"""
Gera um site-config.json de demonstração (Fase 2, modelo DFY), reaproveitando
o motor de produção real (AgenteConstrutor.executar()) sem passar pelo
endpoint HTTP protegido (POST /api/v1/generate-site exige X-API-Key) e sem
tocar em Postgres/produção. Saída vai para configs/ (já gitignored), nunca
para o site-config.json da raiz (esse é o arquivo publicado pela Vercel).

Não duplica lógica: reusa gerar_config_site() (retry + validação internos)
e salvar_config() de agent_construtor.py. Não importa agents/vendedor.py
(integração com Lovable, aposentada).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_construtor import AgenteConstrutor
from image_utils import _slugify


def main():
    parser = argparse.ArgumentParser(description="Gera um site-config.json de demonstração DFY")
    parser.add_argument("--nome", required=True, help="Nome do negócio de teste")
    parser.add_argument("--nicho", required=True, help="Nicho/ramo de atuação")
    parser.add_argument("--cor", default="#6366f1", help="Cor primária em hex (ex: #0D9488)")
    parser.add_argument("--localizacao", required=True, help="Cidade/região do negócio (obrigatório — nunca usar fallback genérico)")
    parser.add_argument("--whatsapp", required=True, help="WhatsApp de contato REAL controlado pelo time (obrigatório)")
    parser.add_argument("--saida", default=None, help="Caminho de saída (padrão: configs/<slug>.json)")
    args = parser.parse_args()

    saida = args.saida or f"configs/{_slugify(args.nome)}.json"

    agente = AgenteConstrutor()
    agente.executar(
        nome_empresa=args.nome,
        nicho=args.nicho,
        cor_primaria=args.cor,
        caminho_saida=saida,
        localizacao=args.localizacao,
        whatsapp_contato=args.whatsapp,
    )


if __name__ == "__main__":
    main()
