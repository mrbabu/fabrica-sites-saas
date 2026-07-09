#!/usr/bin/env python3
"""
Simulação da Esteira de Agentes - Fábrica de Sites SaaS
Roda de ponta a ponta a jornada Hunter -> Agente Construtor -> Vendedor,
validando o contrato de payload JSON ("DadosLead") que transita entre eles.

Hunter e Vendedor são mockados (regex simples, sem chamadas HTTP reais).
O Agente Construtor é o real: esta execução chama de fato o AIProvider
configurado (Ollama/NVIDIA NIM/Anthropic), levando ~1min.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.hunter import AgenteHunter
from agents.vendedor import AgenteVendedor, ErroEnvioDemo
from agent_construtor import AgenteConstrutor

MENSAGEM_EXEMPLO = (
    "Quero um site para minha oficina mecânica em Vitória, cor azul, "
    "nome Mecânica do Raphinha"
)
WHATSAPP_EXEMPLO = "+5527999998888"


def main():
    print("=" * 70)
    print("ETAPA 1 — Hunter: captura e limpeza do lead")
    print("=" * 70)

    hunter = AgenteHunter()
    lead_bruto = hunter.capturar_lead(MENSAGEM_EXEMPLO, whatsapp_contato=WHATSAPP_EXEMPLO)
    print(f'Mensagem recebida: "{MENSAGEM_EXEMPLO}"')
    print(f"Lead bruto extraído:\n{json.dumps(lead_bruto, ensure_ascii=False, indent=2)}\n")

    dados_lead = hunter.limpar_e_validar(lead_bruto)
    print(f"DadosLead (payload limpo):\n{json.dumps(dados_lead, ensure_ascii=False, indent=2)}\n")

    print("=" * 70)
    print("ETAPA 2 — Agente Construtor: geração do site-config.json (chamada real de IA)")
    print("=" * 70)

    construtor = AgenteConstrutor()
    site_config = construtor.gerar_config_site(
        nome_empresa=dados_lead["nome_empresa"],
        nicho=dados_lead["nicho"],
        cor_primaria=dados_lead["cor_primaria"],
        localizacao=dados_lead.get("localizacao"),
        whatsapp_contato=dados_lead.get("whatsapp_contato"),
    )
    print(f"site-config.json gerado para \"{site_config['company']['name']}\"\n")

    print("=" * 70)
    print("ETAPA 3 — Vendedor: preparação do payload para o Lovable (mock)")
    print("=" * 70)

    vendedor = AgenteVendedor()
    payload_lovable = vendedor.conectar_lovable(site_config)
    print(f"Payload simulado para o Lovable:\n{json.dumps(payload_lovable, ensure_ascii=False, indent=2)}\n")

    print("=" * 70)
    print("ETAPA 4 — Vendedor: envio do link de demonstração ao lead (mock)")
    print("=" * 70)

    try:
        resultado_envio = vendedor.enviar_link_demonstracao(
            payload_lovable["url_demo_prevista"], dados_lead.get("whatsapp_contato")
        )
        print(f"Resultado do envio (mock Z-API/Evolution API):\n{json.dumps(resultado_envio, ensure_ascii=False, indent=2)}\n")
    except ErroEnvioDemo as e:
        print(f"⚠️  Envio não realizado: {e}\n")

    print("=" * 70)
    print("Esteira simulada concluída: Hunter -> Agente Construtor -> Vendedor")
    print("=" * 70)


if __name__ == "__main__":
    main()
