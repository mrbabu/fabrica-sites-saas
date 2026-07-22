#!/usr/bin/env python3
"""
Listagem somente-leitura de todos os sites já gerados (ver
backend/routers/demo_dfy.py para a geração e demo_preview.py para o
preview individual). Funciona como "home" das ferramentas internas —
mostra também contagem real de sites e leads (sem número inventado).
"""

import csv
import html
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from auth_demo import exigir_login_demo
from db import get_db
from ui_common import CSS_BASE, cabecalho
import repository

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])

PASTA_LEADS = Path(__file__).resolve().parent.parent.parent / "leads"
CSVS_LEADS = ["clinicas_grande_vitoria.csv", "prestadores_paraty.csv"]


def _contar_leads_capturados() -> int:
    """Soma linhas dos CSVs de leads reais. Nunca quebra a página — se o
    arquivo não existir (ex.: imagem antiga sem leads/ copiado), conta 0
    pra aquele CSV em vez de derrubar a listagem inteira."""
    total = 0
    for nome in CSVS_LEADS:
        caminho = PASTA_LEADS / nome
        if not caminho.exists():
            continue
        try:
            with caminho.open(encoding="utf-8", newline="") as f:
                total += sum(1 for _ in csv.DictReader(f))
        except OSError:
            continue
    return total


@router.get("/demo/lista", response_class=HTMLResponse)
async def listar_demos(request: Request, db: Session = Depends(get_db)):
    """Lista todos os sites gerados, mais recente primeiro, com link pro preview de cada um."""
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect
    sites = repository.listar_sites(db)
    total_leads = _contar_leads_capturados()

    linhas = "".join(
        f"""<tr>
            <td>{html.escape(site.nome_empresa)}</td>
            <td>{html.escape(site.nicho)}</td>
            <td>{site.created_at.strftime('%d/%m/%Y %H:%M')}</td>
            <td><a href="/demo/preview/{html.escape(site.slug)}" target="_blank">ver site</a></td>
        </tr>"""
        for site in sites
    )

    corpo = (
        '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:24px">Nenhum site gerado ainda.</td></tr>'
        if not sites
        else linhas
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sites gerados — Fábrica de Sites IA</title>
<style>
{CSS_BASE}
  table {{ width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
  th {{ text-align: left; font-size: 0.8rem; color: var(--muted); padding: 10px 14px; border-bottom: 1px solid var(--border); background: #f8fafc; }}
  td {{ padding: 12px 14px; border-bottom: 1px solid #f3f4f6; font-size: 0.92rem; }}
  tr:last-child td {{ border-bottom: none; }}
  a {{ color: var(--accent); font-weight: 600; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .total {{ margin-top: 14px; color: var(--muted); font-size: 0.85rem; }}
</style>
</head>
<body>
{cabecalho("lista")}
<div class="wrap">
  <h1>Sites gerados</h1>
  <p class="subtitle">Histórico de todas as demos DFY já criadas</p>

  <div class="stats">
    <div class="stat-card"><div class="valor">{len(sites)}</div><div class="rotulo">Sites gerados</div></div>
    <div class="stat-card"><div class="valor">{total_leads}</div><div class="rotulo">Leads capturados</div></div>
  </div>

  <table>
    <thead><tr><th>Empresa</th><th>Nicho</th><th>Gerado em</th><th></th></tr></thead>
    <tbody>{corpo}</tbody>
  </table>
  <p class="total">{len(sites)} site(s) no total</p>
</div>
</body>
</html>"""
