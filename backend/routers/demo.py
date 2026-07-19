#!/usr/bin/env python3
"""
Página de entrada da ferramenta interna de demo DFY (ver
backend/routers/demo_dfy.py para a geração e demo_preview.py para o
resultado renderizado).

Só o formulário — nenhuma lógica de negócio aqui. Servida dinamicamente
(não é um arquivo estático commitado) pra injetar a API key a partir do
ambiente do servidor no momento da resposta: nunca fica em texto plano no
repositório, nunca precisa ser digitada/colada durante uma apresentação.

Nota de segurança (aceita para esta etapa de MVP local, não pro produto
público): a chave injetada aqui fica visível no HTML/JS enviado ao
navegador. Antes de expor isso como produto real, trocar por um POST /demo
que chama /api/v1/demo-dfy no próprio backend (a chave nunca sai do
servidor) em vez do fetch() client-side atual.
"""

import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])


@router.get("/demo", response_class=HTMLResponse)
async def formulario_demo():
    """Formulário de geração de demo DFY — nome, nicho, localização e WhatsApp obrigatórios."""
    api_key = os.getenv("WEBHOOK_API_KEY", "")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fábrica de Sites IA — Gerador de Demo DFY</title>
<style>
  body {{ font-family: -apple-system, Inter, sans-serif; max-width: 480px; margin: 60px auto; padding: 0 20px; color: #1f2937; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
  p.subtitle {{ color: #6b7280; margin-top: 0; margin-bottom: 28px; }}
  label {{ display: block; font-weight: 600; font-size: 0.9rem; margin: 16px 0 6px; }}
  input, textarea {{ width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; box-sizing: border-box; font-family: inherit; }}
  input[type=color] {{ padding: 4px; height: 42px; }}
  textarea {{ resize: vertical; min-height: 70px; }}
  button {{ margin-top: 24px; width: 100%; padding: 12px; background: #0D9488; color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; }}
  button:disabled {{ background: #9ca3af; cursor: wait; }}
  #resultado {{ margin-top: 20px; padding: 14px; border-radius: 8px; display: none; }}
  #resultado.erro {{ background: #fef2f2; border: 1px solid #fca5a5; display: block; }}
</style>
</head>
<body>
  <h1>Gerador de Demo DFY</h1>
  <p class="subtitle">Ferramenta interna — não é o produto final do cliente.</p>
  <form id="form-demo">
    <label>Nome da empresa</label>
    <input name="nome_empresa" required>

    <label>Tipo de negócio</label>
    <input name="nicho" required placeholder="Ex.: Odontologia, Restaurante, Pousada">

    <label>Cidade</label>
    <input name="localizacao" required placeholder="Ex.: Vitória - ES">

    <label>WhatsApp (obrigatório, número real)</label>
    <input name="whatsapp_contato" required placeholder="+55 27 99999-9999">

    <label>Cor principal</label>
    <input name="cor_primaria" type="color" value="#0D9488">

    <label>Me conte sobre seu negócio (opcional)</label>
    <textarea name="descricao_negocio" placeholder="O que torna esse negócio especial? Diferenciais, história, público-alvo..."></textarea>

    <label>Fotos reais do trabalho (portfólio, opcional, até 8)</label>
    <textarea name="portfolio_urls_raw" placeholder="Uma URL por linha — link direto de imagem (.jpg/.png/.webp), não link de página ou pasta compartilhada&#10;https://...&#10;https://..."></textarea>

    <button type="submit" id="btn-gerar">Gerar Demo</button>
  </form>
  <div id="resultado"></div>

<script>
const API_KEY = {api_key!r};

// FastAPI/Pydantic devolve "detail" como string (erros HTTPException, ex.:
// falha ao chamar a IA) ou como lista de objetos {{msg, loc, type}} (erros de
// validação 422, ex.: portfolio_urls inválido) — sem isso, new Error(array)
// vira literalmente "[object Object]" na tela.
function formatarErroDetail(detail) {{
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {{
    return detail.map(item => (item && item.msg) ? item.msg : JSON.stringify(item)).join('; ');
  }}
  return detail ? JSON.stringify(detail) : 'Erro ao gerar demo';
}}

document.getElementById('form-demo').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const btn = document.getElementById('btn-gerar');
  const resultado = document.getElementById('resultado');
  const dados = Object.fromEntries(new FormData(e.target).entries());
  const portfolioUrls = (dados.portfolio_urls_raw || '').split(/\\r?\\n/).map(s => s.trim()).filter(Boolean);
  delete dados.portfolio_urls_raw;
  if (portfolioUrls.length > 0) dados.portfolio_urls = portfolioUrls;

  btn.disabled = true;
  btn.textContent = 'Gerando... (~30-60s)';
  resultado.style.display = 'none';

  try {{
    const resp = await fetch('/api/v1/demo-dfy', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json', 'X-API-Key': API_KEY }},
      body: JSON.stringify(dados),
    }});
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.detail || 'Erro ao gerar demo');

    window.location.href = json.preview_url;
  }} catch (err) {{
    resultado.className = 'erro';
    resultado.textContent = 'Erro: ' + err.message;
    resultado.style.display = 'block';
    btn.disabled = false;
    btn.textContent = 'Gerar Demo';
  }}
}});
</script>
</body>
</html>"""
