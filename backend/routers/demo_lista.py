#!/usr/bin/env python3
"""
Listagem somente-leitura de todos os sites já gerados (ver
backend/routers/demo_dfy.py para a geração e demo_preview.py para o
preview individual).

Mesma postura de segurança já documentada em demo.py/demo_preview.py:
sem login, aceitável nesta etapa (acesso só via link de tunnel
controlado), não pronto pra exposição pública sem autenticação.
"""

import html

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from auth_demo import exigir_login_demo
from db import get_db
import repository

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])


@router.get("/demo/lista", response_class=HTMLResponse)
async def listar_demos(request: Request, db: Session = Depends(get_db)):
    """Lista todos os sites gerados, mais recente primeiro, com link pro preview de cada um."""
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect
    sites = repository.listar_sites(db)

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
        '<tr><td colspan="4" style="text-align:center;color:#6b7280;padding:24px">Nenhum site gerado ainda.</td></tr>'
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
  body {{ font-family: -apple-system, Inter, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1f2937; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
  p.subtitle {{ color: #6b7280; margin-top: 0; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ text-align: left; font-size: 0.85rem; color: #6b7280; padding: 8px 12px; border-bottom: 2px solid #e5e7eb; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #f3f4f6; font-size: 0.95rem; }}
  a {{ color: #0D9488; font-weight: 600; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .total {{ margin-top: 16px; color: #6b7280; font-size: 0.85rem; }}
</style>
</head>
<body>
  <h1>Sites gerados</h1>
  <p class="subtitle">Histórico de todas as demos DFY criadas — <a href="/demo">gerar uma nova</a> · <a href="/demo/logout">sair</a></p>
  <table>
    <thead><tr><th>Empresa</th><th>Nicho</th><th>Gerado em</th><th></th></tr></thead>
    <tbody>{corpo}</tbody>
  </table>
  <p class="total">{len(sites)} site(s) no total</p>
</body>
</html>"""
