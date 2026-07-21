#!/usr/bin/env python3
"""
Login/logout por sessão da ferramenta interna de demo DFY. Ver
backend/auth_demo.py para a validação de credenciais e expiração de sessão
(15 minutos).
"""

import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth_demo import credenciais_validas

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])


def _pagina_login(next_url: str, erro: bool = False) -> str:
    aviso = (
        '<p class="erro">Usuário ou senha inválidos.</p>' if erro else ""
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login — Fábrica de Sites IA</title>
<style>
  body {{ font-family: -apple-system, Inter, sans-serif; max-width: 360px; margin: 100px auto; padding: 0 20px; color: #1f2937; }}
  h1 {{ font-size: 1.3rem; margin-bottom: 24px; }}
  label {{ display: block; font-weight: 600; font-size: 0.9rem; margin: 14px 0 6px; }}
  input {{ width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; box-sizing: border-box; }}
  button {{ margin-top: 20px; width: 100%; padding: 12px; background: #0D9488; color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }}
  .erro {{ color: #b91c1c; font-size: 0.9rem; margin-top: 12px; }}
</style>
</head>
<body>
  <h1>Acesso à ferramenta de demo</h1>
  <form method="post" action="/demo/login">
    <input type="hidden" name="next" value="{next_url}">
    <label>Usuário</label>
    <input name="usuario" required autofocus>
    <label>Senha</label>
    <input name="senha" type="password" required>
    <button type="submit">Entrar</button>
    {aviso}
  </form>
</body>
</html>"""


@router.get("/demo/login", response_class=HTMLResponse)
async def login_form(next: str = "/demo", erro: int = 0):
    return _pagina_login(next, erro=bool(erro))


@router.post("/demo/login", response_class=HTMLResponse)
async def login_submit(request: Request):
    form = await request.form()
    usuario = str(form.get("usuario", ""))
    senha = str(form.get("senha", ""))
    next_url = str(form.get("next", "/demo")) or "/demo"

    if not credenciais_validas(usuario, senha):
        return RedirectResponse(url=f"/demo/login?next={next_url}&erro=1", status_code=303)

    request.session["demo_autenticado"] = True
    request.session["demo_login_em"] = time.time()
    return RedirectResponse(url=next_url, status_code=303)


@router.get("/demo/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/demo/login", status_code=303)
