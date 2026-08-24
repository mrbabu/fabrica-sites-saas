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
from html import escape as esc

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from auth_demo import exigir_login_demo
from ui_common import CSS_BASE, cabecalho

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])


@router.get("/demo", response_class=HTMLResponse)
async def formulario_demo(request: Request, nome_empresa: str = "", nicho: str = "", localizacao: str = "", lead_id: str = "", google_maps_url: str = ""):
    """
    Formulário de geração de demo DFY — nome, nicho, localização e WhatsApp
    obrigatórios. Aceita pré-preenchimento vindo de um lead do Hunter
    (?nome_empresa=&nicho=&localizacao=&lead_id=&google_maps_url=) — WhatsApp
    nunca é pré-preenchido: o telefone que o Hunter traz é comercial, não
    confirmado como WhatsApp, precisa ser validado manualmente antes.
    google_maps_url vem do próprio Hunter (link real do Places) — nunca
    digitado à mão, garante que o mapa do site aponte pro lugar certo.
    """
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect
    api_key = os.getenv("WEBHOOK_API_KEY", "")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fábrica de Sites IA — Gerador de Demo DFY</title>
<style>
{CSS_BASE}
  .wrap {{ max-width: 520px; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 28px 30px; }}
  label {{ display: block; font-weight: 600; font-size: 0.85rem; margin: 16px 0 6px; }}
  label:first-of-type {{ margin-top: 0; }}
  input, textarea {{ width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.95rem; box-sizing: border-box; font-family: inherit; }}
  input[type=color] {{ padding: 4px; height: 42px; }}
  textarea {{ resize: vertical; min-height: 70px; }}
  button {{ margin-top: 24px; width: 100%; padding: 12px; background: var(--accent); color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background .15s; }}
  button:hover {{ background: var(--accent-dark); }}
  button:disabled {{ background: #9ca3af; cursor: wait; }}
  #resultado {{ margin-top: 20px; padding: 14px; border-radius: 8px; display: none; }}
  #resultado.erro {{ background: #fef2f2; border: 1px solid #fca5a5; display: block; }}
  #drop-zone {{ border: 2px dashed #d1d5db; border-radius: 8px; padding: 18px; text-align: center; font-size: 0.85rem; color: var(--muted); cursor: pointer; transition: border-color .15s, background .15s; }}
  #drop-zone.arrastando {{ border-color: var(--accent); background: #f0fdfa; }}
  #galeria-uploads {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
  .chip-imagem {{ position: relative; width: 64px; height: 64px; border-radius: 6px; overflow: hidden; border: 1px solid var(--border); }}
  .chip-imagem img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .chip-imagem button {{ position: absolute; top: 0; right: 0; margin: 0; width: 20px; height: 20px; padding: 0; line-height: 1; font-size: 0.9rem; background: rgba(0,0,0,.6); border-radius: 0 0 0 6px; }}
  .chip-imagem.erro {{ border-color: #fca5a5; }}
  .chip-imagem .legenda-erro {{ position: absolute; inset: 0; background: rgba(254,242,242,.95); color: #b91c1c; font-size: 0.55rem; display: flex; align-items: center; justify-content: center; text-align: center; padding: 2px; }}
  .chip-imagem .enviando {{ position: absolute; inset: 0; background: rgba(15,23,42,.55); color: #fff; font-size: 0.6rem; display: flex; align-items: center; justify-content: center; text-align: center; }}
</style>
</head>
<body>
{cabecalho("demo")}
<div class="wrap">
  <h1>Gerador de Demo DFY</h1>
  <p class="subtitle">Ferramenta interna — não é o produto final do cliente</p>
  <div class="card">
  <form id="form-demo">
    <input type="hidden" name="lead_id" value="{esc(lead_id)}">
    <input type="hidden" name="google_maps_url" value="{esc(google_maps_url)}">
    <label>Nome da empresa</label>
    <input name="nome_empresa" value="{esc(nome_empresa)}" required>

    <label>Tipo de negócio</label>
    <input name="nicho" value="{esc(nicho)}" required placeholder="Ex.: Odontologia, Restaurante, Pousada">

    <label>Cidade</label>
    <input name="localizacao" value="{esc(localizacao)}" required placeholder="Ex.: Vitória - ES">

    <label>WhatsApp (obrigatório, número real)</label>
    <input name="whatsapp_contato" required placeholder="+55 27 99999-9999">

    <label>Me conte sobre seu negócio (opcional)</label>
    <textarea name="descricao_negocio" placeholder="O que torna esse negócio especial? Diferenciais, história, público-alvo..."></textarea>

    <label>Fotos reais do trabalho (portfólio, opcional, até 8 no total)</label>
    <textarea name="portfolio_urls_raw" placeholder="Uma URL por linha — link direto de imagem (.jpg/.png/.webp), não link de página ou pasta compartilhada&#10;https://...&#10;https://..."></textarea>
    <div id="drop-zone">Ou arraste as fotos aqui, ou clique pra escolher do computador</div>
    <input type="file" id="input-arquivos" accept="image/jpeg,image/png,image/webp" multiple hidden>
    <div id="galeria-uploads"></div>

    <button type="submit" id="btn-gerar">Gerar Demo</button>
  </form>
  <div id="resultado"></div>
  </div>
</div>

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

// Upload de portfólio: alternativa ao textarea de URL — cada arquivo vira
// uma chamada pro endpoint novo (backend/routers/demo_upload.py), que
// devolve um caminho relativo. A URL absoluta só é montada aqui (o backend
// não sabe seu próprio hostname público, que varia entre túnel/Tailscale/
// local) e entra no MESMO portfolio_urls que o textarea já preenche.
const MAX_PORTFOLIO_TOTAL = 8;
const imagensEnviadas = []; // cada item: path (relativo) + url (absoluta)

function contarPortfolioAtual() {{
  const urlsTexto = (document.querySelector('[name=portfolio_urls_raw]').value || '')
    .split(/\\r?\\n/).map(s => s.trim()).filter(Boolean);
  return urlsTexto.length + imagensEnviadas.length;
}}

function renderizarGaleria() {{
  document.getElementById('galeria-uploads').innerHTML = imagensEnviadas.map((img, i) => `
    <div class="chip-imagem">
      <img src="${{img.url}}" alt="">
      <button type="button" data-i="${{i}}" title="Remover">×</button>
    </div>
  `).join('');
}}

document.getElementById('galeria-uploads').addEventListener('click', (e) => {{
  const btn = e.target.closest('button[data-i]');
  if (!btn) return;
  imagensEnviadas.splice(Number(btn.dataset.i), 1);
  renderizarGaleria();
}});

async function enviarArquivo(arquivo) {{
  const galeria = document.getElementById('galeria-uploads');
  const chip = document.createElement('div');
  chip.className = 'chip-imagem';
  chip.innerHTML = `<img src="${{URL.createObjectURL(arquivo)}}" alt=""><div class="enviando">Enviando…</div>`;
  galeria.appendChild(chip);

  try {{
    const formData = new FormData();
    formData.append('arquivo', arquivo);
    const resp = await fetch('/api/v1/demo-upload/imagem', {{
      method: 'POST',
      headers: {{ 'X-API-Key': API_KEY }},
      body: formData,
    }});
    const json = await resp.json();
    if (!resp.ok) throw new Error(formatarErroDetail(json.detail));

    imagensEnviadas.push({{ path: json.path, url: window.location.origin + json.path }});
    renderizarGaleria();
  }} catch (err) {{
    chip.classList.add('erro');
    chip.querySelector('.enviando')?.remove();
    chip.innerHTML += `<div class="legenda-erro">${{err.message}}</div>`;
  }}
}}

function processarArquivos(arquivos) {{
  const restantes = MAX_PORTFOLIO_TOTAL - contarPortfolioAtual();
  if (restantes <= 0) {{
    alert(`Máximo de ${{MAX_PORTFOLIO_TOTAL}} fotos no total (URLs + upload).`);
    return;
  }}
  [...arquivos].slice(0, restantes).forEach(enviarArquivo);
}}

const dropZone = document.getElementById('drop-zone');
const inputArquivos = document.getElementById('input-arquivos');
dropZone.addEventListener('click', () => inputArquivos.click());
inputArquivos.addEventListener('change', (e) => {{
  processarArquivos(e.target.files);
  e.target.value = '';
}});
['dragover', 'dragleave', 'drop'].forEach(evento => {{
  dropZone.addEventListener(evento, (e) => {{
    e.preventDefault();
    dropZone.classList.toggle('arrastando', evento === 'dragover');
  }});
}});
dropZone.addEventListener('drop', (e) => processarArquivos(e.dataTransfer.files));

document.getElementById('form-demo').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const btn = document.getElementById('btn-gerar');
  const resultado = document.getElementById('resultado');
  const dados = Object.fromEntries(new FormData(e.target).entries());
  const urlsColadas = (dados.portfolio_urls_raw || '').split(/\\r?\\n/).map(s => s.trim()).filter(Boolean);
  delete dados.portfolio_urls_raw;
  const portfolioUrls = [...urlsColadas, ...imagensEnviadas.map(img => img.url)].slice(0, MAX_PORTFOLIO_TOTAL);
  if (portfolioUrls.length > 0) dados.portfolio_urls = portfolioUrls;
  const leadId = dados.lead_id;
  delete dados.lead_id;

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
    if (!resp.ok) throw new Error(formatarErroDetail(json.detail));

    if (leadId) {{
      try {{
        await fetch(`/hunter/leads/${{leadId}}/vincular-demo`, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ slug: json.slug }}),
        }});
      }} catch (e) {{ /* não bloqueia o fluxo se isso falhar */ }}
    }}

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
