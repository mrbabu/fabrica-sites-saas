#!/usr/bin/env python3
"""
Login por sessão para a ferramenta interna de demo DFY (/demo, /demo/lista,
/demo/preview/*). Separado de auth.py (que protege a API JSON via header
X-API-Key) porque aqui é navegação de navegador — precisa de tela de login
e cookie de sessão, não de header.

Credenciais vêm de variável de ambiente (DEMO_LOGIN_USER/DEMO_LOGIN_PASSWORD),
nunca hardcoded no código — o mesmo motivo pelo qual WEBHOOK_API_KEY também
não é hardcoded (ver auth.py): qualquer coisa hardcoded fica em texto puro
no histórico do Git para sempre, mesmo em repositório privado.
"""

import hmac
import os
import time
from typing import Optional

from fastapi import Request
from fastapi.responses import RedirectResponse

DEMO_LOGIN_USER = os.getenv("DEMO_LOGIN_USER")
DEMO_LOGIN_PASSWORD = os.getenv("DEMO_LOGIN_PASSWORD")
SESSAO_DURACAO_SEGUNDOS = 15 * 60


def credenciais_validas(usuario: str, senha: str) -> bool:
    """Compara em tempo constante (hmac.compare_digest) para não vazar
    timing de quantos caracteres bateram — comparação normal (==) é mais
    rápida quando o início diverge, o que dá pra explorar caractere a
    caractere em ataques de força bruta."""
    if not DEMO_LOGIN_USER or not DEMO_LOGIN_PASSWORD:
        return False
    return hmac.compare_digest(usuario, DEMO_LOGIN_USER) and hmac.compare_digest(senha, DEMO_LOGIN_PASSWORD)


def sessao_valida(request: Request) -> bool:
    login_em = request.session.get("demo_login_em")
    if not request.session.get("demo_autenticado") or login_em is None:
        return False
    return (time.time() - login_em) < SESSAO_DURACAO_SEGUNDOS


def exigir_login_demo(request: Request) -> Optional[RedirectResponse]:
    """Chamar no topo de cada rota protegida. Retorna um redirect pro
    login se a sessão não existir ou tiver passado de 15 minutos, ou None
    se pode prosseguir normalmente."""
    if not sessao_valida(request):
        request.session.clear()
        return RedirectResponse(url=f"/demo/login?next={request.url.path}", status_code=303)
    return None
