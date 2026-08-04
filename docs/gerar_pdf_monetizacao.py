#!/usr/bin/env python3
"""Gera o PDF de 'Monetização da ferramenta de leads (Google Maps)', reaproveitando
o parser/renderer markdown->PDF já existente em gerar_pdf_manual.py."""

from pathlib import Path

from gerar_pdf_manual import parse_markdown, render_pdf


def main():
    script_dir = Path(__file__).parent
    md_path = script_dir / "monetizacao-ferramenta-leads.md"
    output_path = script_dir / "Fabrica-de-Sites-AI-Monetizacao-Leads.pdf"

    md_text = md_path.read_text(encoding="utf-8")
    blocks = parse_markdown(md_text)
    render_pdf(
        blocks,
        output_path,
        titulo_capa="Monetizacao da\nFerramenta de Leads",
        subtitulo_capa="Estrategia de produto | Julho 2026",
        rodape_capa="Busca de leads via Google Maps",
        nota_capa="Documento interno - Estrategia de negocio",
        titulo_cabecalho="Fabrica de Sites AI - Monetizacao da Ferramenta de Leads",
    )
    print(f"PDF gerado: {output_path}")
    print(f"Tamanho: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
