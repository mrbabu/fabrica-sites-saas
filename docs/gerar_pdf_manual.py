#!/usr/bin/env python3
"""Gera o PDF do Manual do Operador de Vendas."""

import re
from pathlib import Path
from fpdf import FPDF


class ManualPDF(FPDF):
    """PDF customizado com cabeçalho e rodapé da Fábrica de Sites AI."""

    def __init__(self, titulo_cabecalho: str = "Fabrica de Sites AI - Manual do Operador de Vendas"):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)
        self.titulo_cabecalho = titulo_cabecalho
        self._setup_fonts()

    def _setup_fonts(self):
        """Configura fontes Unicode."""
        font_dir = Path(__file__).parent.parent / "assets" / "fonts"
        # Usa Helvetica como fallback (fonte padrão do fpdf2 com suporte Latin-1)
        # Para Unicode completo, seria necessário adicionar fontes TTF

    def header(self):
        if self.page_no() == 1:
            return  # Capa não tem cabeçalho
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, self.titulo_cabecalho, align="L")
        self.cell(0, 8, f"Pagina {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-20)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "Fabrica de Sites AI | fabrica-de-sites.ai | Julho 2026", align="C")


def parse_markdown(md_text: str) -> list[dict]:
    """Parse simples de markdown para estrutura de blocos."""
    blocks = []
    lines = md_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Pular linhas vazias
        if not line.strip():
            i += 1
            continue

        # Code block
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append({"type": "code", "lang": lang, "content": "\n".join(code_lines)})
            i += 1
            continue

        # Tabela
        if "|" in line and line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip().startswith("|"):
                # Pular linha de separador (|---|---|)
                if re.match(r"^\|[\s\-:|]+\|$", lines[i].strip()):
                    i += 1
                    continue
                cells = [c.strip() for c in lines[i].strip().split("|")[1:-1]]
                table_lines.append(cells)
                i += 1
            blocks.append({"type": "table", "rows": table_lines})
            continue

        # Heading
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            blocks.append({"type": "heading", "level": level, "content": m.group(2).strip()})
            i += 1
            continue

        # Blockquote
        if line.strip().startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append({"type": "quote", "content": " ".join(quote_lines)})
            continue

        # Horizontal rule
        if re.match(r"^---+\s*$", line.strip()):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Lista com marcadores
        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                item_text = re.sub(r"^\s*[-*]\s+", "", lines[i])
                items.append(item_text)
                i += 1
            blocks.append({"type": "list", "items": items})
            continue

        # Lista numerada
        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                item_text = re.sub(r"^\s*\d+\.\s+", "", lines[i])
                items.append(item_text)
                i += 1
            blocks.append({"type": "ordered_list", "items": items})
            continue

        # Parágrafo
        para_lines = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#") \
                and not lines[i].strip().startswith("```") and not lines[i].strip().startswith("|") \
                and not lines[i].strip().startswith(">") and not re.match(r"^---+\s*$", lines[i].strip()) \
                and not re.match(r"^\s*[-*]\s+", lines[i]) and not re.match(r"^\s*\d+\.\s+", lines[i]):
            para_lines.append(lines[i])
            i += 1
        if para_lines:
            blocks.append({"type": "paragraph", "content": " ".join(para_lines)})
        else:
            i += 1

    return blocks


def clean_md_inline(text: str) -> str:
    """Remove formatação inline markdown e normaliza Unicode para Latin-1."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    # Substituir caracteres Unicode problemáticos para Latin-1
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u2026": "...", # ellipsis
        "\u2022": "*",   # bullet
        "\u2717": "X",   # cross
        "\u2714": "OK",  # checkmark
        "\u2705": "OK",  # check mark
        "\u274c": "NO",  # cross mark
        "\u26a0": "!",   # warning
        "\u2192": "->",  # right arrow
        "\u2190": "<-",  # left arrow
        "\u2714": "OK",  # check
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    # Fallback: remover qualquer caractere não-Latin-1
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text.strip()


def render_pdf(
    blocks: list[dict],
    output_path: Path,
    titulo_capa: str = "Manual do Operador\nde Vendas",
    subtitulo_capa: str = "Versao 2.0 | Julho 2026",
    rodape_capa: str = "Baseado 100% no codigo implementado",
    nota_capa: str = "Documento interno - Uso da equipe de vendas",
    titulo_cabecalho: str = "Fabrica de Sites AI - Manual do Operador de Vendas",
):
    """Renderiza os blocos parseados em PDF."""
    pdf = ManualPDF(titulo_cabecalho=titulo_cabecalho)
    pdf.set_margins(15, 15, 15)

    # --- CAPA ---
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(31, 87, 69)  # Verde escuro da marca
    pdf.multi_cell(0, 12, titulo_capa, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Fabrica de Sites AI", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(31, 87, 69)
    pdf.set_line_width(0.8)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, subtitulo_capa, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, rodape_capa, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, nota_capa, align="C", new_x="LMARGIN", new_y="NEXT")

    # --- CONTEUDO ---
    for block in blocks:
        btype = block["type"]

        if btype == "heading":
            level = block["level"]
            content = clean_md_inline(block["content"])

            if level == 1:
                pdf.add_page()
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 22)
                pdf.set_text_color(31, 87, 69)
                pdf.multi_cell(0, 10, content)
                pdf.set_draw_color(31, 87, 69)
                pdf.set_line_width(0.6)
                pdf.line(15, pdf.get_y() + 2, 195, pdf.get_y() + 2)
                pdf.ln(6)
            elif level == 2:
                if pdf.get_y() > 240:
                    pdf.add_page()
                pdf.ln(4)
                pdf.set_font("Helvetica", "B", 15)
                pdf.set_text_color(31, 87, 69)
                pdf.multi_cell(0, 8, content)
                pdf.ln(2)
            elif level == 3:
                if pdf.get_y() > 250:
                    pdf.add_page()
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 7, content)
                pdf.ln(1)
            elif level == 4:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 6, content)
                pdf.ln(1)

        elif btype == "paragraph":
            content = clean_md_inline(block["content"])
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 5.5, content)
            pdf.ln(2)

        elif btype == "list":
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            for item in block["items"]:
                content = clean_md_inline(item)
                x = pdf.get_x()
                pdf.cell(5, 5.5, "-")  # bullet
                pdf.multi_cell(0, 5.5, content)
                pdf.set_x(x)
            pdf.ln(2)

        elif btype == "ordered_list":
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            for idx, item in enumerate(block["items"], 1):
                content = clean_md_inline(item)
                x = pdf.get_x()
                pdf.cell(8, 5.5, f"{idx}.")
                pdf.multi_cell(0, 5.5, content)
                pdf.set_x(x)
            pdf.ln(2)

        elif btype == "code":
            code = block["content"]
            if pdf.get_y() > 240:
                pdf.add_page()
            pdf.ln(2)
            pdf.set_fill_color(245, 245, 245)
            pdf.set_draw_color(220, 220, 220)
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(50, 50, 50)

            # Sanitizar caracteres Unicode no código
            def sanitize_code(text):
                replacements = {
                    "\u250c": "+", "\u2510": "+", "\u2514": "+", "\u2518": "+",
                    "\u2500": "-", "\u2502": "|", "\u251c": "+", "\u2524": "+",
                    "\u253c": "+", "\u2192": "->", "\u2190": "<-",
                    "\u2191": "^", "\u2193": "v", "\u25cf": "*",
                    "\u25cb": "o", "\u25a0": "[ ]", "\u25a1": "[ ]",
                    "\u2714": "[OK]", "\u2717": "[X]", "\u2705": "[OK]",
                    "\u274c": "[NO]", "\u26a0": "[!]", "\u2022": "-",
                    "\u2014": "-", "\u2013": "-",
                }
                for orig, repl in replacements.items():
                    text = text.replace(orig, repl)
                return text.encode("latin-1", errors="replace").decode("latin-1")

            code_lines = [sanitize_code(cl) for cl in code.split("\n")]
            line_h = 4.5
            block_h = len(code_lines) * line_h + 6

            if pdf.get_y() + block_h > 270:
                pdf.add_page()

            y_start = pdf.get_y()
            pdf.rect(15, y_start, 180, block_h, style="DF")
            pdf.set_xy(18, y_start + 3)
            for cl in code_lines:
                pdf.cell(0, line_h, cl[:90])  # Truncar linhas muito longas
                pdf.ln(line_h)
                pdf.set_x(18)
            pdf.set_y(y_start + block_h + 2)
            pdf.ln(2)

        elif btype == "table":
            rows = block["rows"]
            if not rows:
                continue

            if pdf.get_y() > 230:
                pdf.add_page()

            col_count = max(len(r) for r in rows)
            available_w = 180
            col_w = available_w / col_count

            pdf.ln(2)
            for row_idx, row in enumerate(rows):
                if pdf.get_y() > 265:
                    pdf.add_page()

                if row_idx == 0:
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_fill_color(31, 87, 69)
                    pdf.set_text_color(255, 255, 255)
                else:
                    pdf.set_font("Helvetica", "", 8)
                    if row_idx % 2 == 0:
                        pdf.set_fill_color(245, 248, 246)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                    pdf.set_text_color(50, 50, 50)

                for ci in range(col_count):
                    cell_text = clean_md_inline(row[ci]) if ci < len(row) else ""
                    pdf.cell(col_w, 6, cell_text[:40], border=1, fill=True, align="L")
                pdf.ln()

            pdf.ln(3)

        elif btype == "quote":
            content = clean_md_inline(block["content"])
            pdf.ln(2)
            pdf.set_fill_color(240, 248, 240)
            y_start = pdf.get_y()
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(60, 100, 60)
            pdf.set_x(20)
            pdf.multi_cell(165, 5.5, content, fill=True)
            pdf.ln(3)

        elif btype == "hr":
            pdf.ln(3)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.3)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(5)

    # Salvar
    pdf.output(str(output_path))
    return output_path


def main():
    script_dir = Path(__file__).parent
    md_path = script_dir / "manual-operador-vendas.md"
    output_path = script_dir / "Fabrica-de-Sites-AI-Manual-Operador-Vendas.pdf"

    md_text = md_path.read_text(encoding="utf-8")
    blocks = parse_markdown(md_text)
    render_pdf(blocks, output_path)
    print(f"PDF gerado: {output_path}")
    print(f"Tamanho: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
