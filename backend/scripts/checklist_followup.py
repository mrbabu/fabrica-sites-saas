#!/usr/bin/env python3
"""
Checklist de Prospecção Manual — cruza leads/*.csv e sinaliza quem retomar
hoje: leads nunca contatados, e leads contatados há mais de 48h sem
resposta registrada. Só leitura — não manda mensagem nenhuma, não altera
nenhum arquivo, não chama API de WhatsApp nenhuma.

O envio continua manual e humano (guardrail #1 do ROADMAP.md: nunca
outbound automatizado). Os ganchos sugeridos reaproveitam os scripts reais
de docs/fase2_scripts_whatsapp.md — adapte antes de mandar, não copie e
cole o mesmo texto pra todo mundo.

Uso: python checklist_followup.py
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buscar_leads_google_maps import carregar_cidades

HORAS_LIMITE_FOLLOWUP = 48

NOME_CIDADE = {"vitoria": "Vitória", "paraty": "Paraty"}

FORMATOS_DATA = ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M")


def parse_data_contato(valor: str):
    """Retorna datetime se `valor` tiver uma data reconhecível, senão None."""
    if not valor or not valor.strip():
        return None
    for fmt in FORMATOS_DATA:
        try:
            return datetime.strptime(valor.strip(), fmt)
        except ValueError:
            continue
    return None


def gancho_abertura(nome: str, bairro: str, regiao: str) -> str:
    """Script 1 de docs/fase2_scripts_whatsapp.md — primeiro contato."""
    return (
        f'"Oi! Tudo bem? Vi a {nome} aqui em {bairro} e reparei que vocês '
        f'não têm site próprio — só o que aparece no Google/Instagram. '
        f'Sou da área de tecnologia aqui de {regiao}, trabalho criando '
        f'sites pra negócios locais. Não é nada empurrado, só queria '
        f'entender: hoje como um cliente novo acha vocês, além de indicação?"'
    )


def gancho_followup(nome: str) -> str:
    """Script 3 de docs/fase2_scripts_whatsapp.md — retomada sem resposta."""
    return (
        f'"Oi! Só um retorno rápido sobre a {nome} — sei que a rotina é '
        f'corrida. Fico à disposição se quiser bater um papo sobre o site, '
        f'sem pressa nenhuma. Abraço!"'
    )


def carregar_leads(cidade_key: str, cidades: dict) -> list[dict]:
    csv_path = cidades[cidade_key]["csv"]
    if not csv_path.exists():
        return []
    with csv_path.open(encoding="utf-8", newline="") as f:
        return [
            row for row in csv.DictReader(f)
            if not row["nome"].startswith("Exemplo")
        ]


def montar_checklist() -> tuple[list[dict], list[dict]]:
    """Retorna (nunca_contatados, parados_48h) prontos pra exibição."""
    agora = datetime.now()
    nunca_contatados = []
    parados = []
    cidades = carregar_cidades()

    for cidade_key in cidades:
        regiao = NOME_CIDADE.get(cidade_key, cidade_key)
        for lead in carregar_leads(cidade_key, cidades):
            base = {
                "nome": lead["nome"],
                "cidade": regiao,
                "bairro": lead["bairro"],
                "nicho": lead["nicho"],
                "whatsapp": lead["whatsapp"],
            }
            data_contato = parse_data_contato(lead.get("data_contato", ""))

            if data_contato is None:
                base["gancho"] = gancho_abertura(lead["nome"], lead["bairro"], regiao)
                nunca_contatados.append(base)
            else:
                horas = (agora - data_contato).total_seconds() / 3600
                if horas < HORAS_LIMITE_FOLLOWUP:
                    continue  # ainda dentro da janela, não precisa retomar hoje
                base["dias_parado"] = int(horas // 24)
                base["gancho"] = gancho_followup(lead["nome"])
                parados.append(base)

    parados.sort(key=lambda i: -i["dias_parado"])
    return nunca_contatados, parados


def imprimir_bloco(titulo: str, itens: list[dict], mostrar_tempo: bool) -> None:
    print(f"\n{titulo} ({len(itens)})")
    print("-" * len(f"{titulo} ({len(itens)})"))
    if not itens:
        print("  (nenhum)")
        return
    for i, item in enumerate(itens, 1):
        tempo = f"  ·  parado há {item['dias_parado']}d" if mostrar_tempo else ""
        print(f"\n[{i}] {item['nome']}")
        print(f"    Cidade/Bairro: {item['cidade']} — {item['bairro']}")
        print(f"    Segmento: {item['nicho']}{tempo}")
        print(f"    WhatsApp: {item['whatsapp']}")
        print(f"    Gancho sugerido: {item['gancho']}")


def main():
    nunca_contatados, parados = montar_checklist()
    total = len(nunca_contatados) + len(parados)

    print("=" * 70)
    print("CHECKLIST DE PROSPECÇÃO MANUAL")
    print("=" * 70)
    print(f"{total} lead(s) pra retomar hoje. Envio é manual — adapte cada")
    print("gancho, nunca copie e cole o mesmo texto pra todo mundo.")

    imprimir_bloco("NUNCA CONTATADOS", nunca_contatados, mostrar_tempo=False)
    imprimir_bloco(f"SEM RESPOSTA HÁ MAIS DE {HORAS_LIMITE_FOLLOWUP}H", parados, mostrar_tempo=True)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
