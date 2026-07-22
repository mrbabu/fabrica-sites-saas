#!/usr/bin/env python3
"""
Busca Leads (MVP interno) — ver docs/hunter_online_spec.md.

Ferramenta interna de prospecção, protegida pelo mesmo login de /demo.
Reaproveita buscar_estabelecimentos() do script de linha de comando
existente (backend/scripts/buscar_leads_google_maps.py), só que com
parâmetros dinâmicos (nicho/local/quantidade) em vez da lista fixa de
buscas por cidade — o script original continua funcionando do jeito que
está, esta rota só chama a mesma função de busca.

Escopo fechado (spec, seção 11/12): sem disparo automático de WhatsApp,
sem CRM, sem score avançado, sem coleta automática de Instagram/Facebook,
sem agente de IA novo — a "mensagem sugerida" é um template estático
preenchido com os dados do lead, não uma chamada de LLM.
"""

import io
import os
from html import escape as esc

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from openpyxl import Workbook

from auth_demo import exigir_login_demo
from scripts.buscar_leads_google_maps import buscar_estabelecimentos
from ui_common import CSS_BASE, cabecalho as cabecalho_nav

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])

TEMPLATE_ABORDAGEM = (
    "Oi! Vi a {nome} aqui em {local} e reparei que vocês não têm site — só "
    "o Google/Instagram. Sou da área de tecnologia, trabalho criando sites "
    "pra {nicho_lower} da região. Não é nada empurrado, só queria entender: "
    "hoje como é que um cliente novo acha vocês, além de indicação?"
)


class ErroBuscaLeads(Exception):
    pass


def _buscar(nicho: str, local: str, quantidade: int) -> list[dict]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ErroBuscaLeads("GOOGLE_MAPS_API_KEY não configurada no ambiente do servidor")

    try:
        estabelecimentos = buscar_estabelecimentos(nicho, local, api_key)
    except Exception as e:
        raise ErroBuscaLeads(f"Erro ao consultar a Google Places API: {e}") from e

    leads = []
    for lugar in estabelecimentos:
        if lugar.get("websiteUri"):
            continue  # já tem site — fora do critério de lead
        nome = (lugar.get("displayName", {}) or {}).get("text", "").strip()
        if not nome:
            continue
        telefone = (lugar.get("nationalPhoneNumber") or "").strip() or "a validar"
        leads.append({
            "nome": nome,
            "nicho": nicho,
            "local": local,
            "telefone": telefone,
            "mapa_url": lugar.get("googleMapsUri") or "",
            "mensagem": TEMPLATE_ABORDAGEM.format(nome=nome, local=local, nicho_lower=nicho.lower()),
        })
        if len(leads) >= quantidade:
            break
    return leads


def _pagina(nicho: str, local: str, quantidade: int, leads: list[dict] | None, erro: str) -> str:
    if erro:
        resultado_html = f'<p class="erro">Erro: {esc(erro)}</p>'
    elif leads is None:
        resultado_html = ""
    elif not leads:
        resultado_html = '<p class="vazio">Nenhuma empresa sem site encontrada pra esses critérios.</p>'
    else:
        linhas = "".join(
            f"""<tr>
                <td>{esc(l['nome'])}</td>
                <td>{esc(l['telefone'])}</td>
                <td>{f'<a class="mapa" href="{esc(l["mapa_url"])}" target="_blank" rel="noopener">Ver no mapa</a>' if l['mapa_url'] else '—'}</td>
                <td>
                  <button type="button" class="copiar" data-msg="{esc(l['mensagem'])}">Copiar mensagem</button>
                </td>
            </tr>"""
            for l in leads
        )
        export_url = f"/hunter/exportar?nicho={esc(nicho)}&local={esc(local)}&quantidade={quantidade}"
        resultado_html = f"""
          <p class="total">{len(leads)} empresa(s) sem site encontrada(s) — telefone vindo da Google Places, validar WhatsApp manualmente antes de contatar.</p>
          <table>
            <thead><tr><th>Empresa</th><th>Telefone</th><th>Mapa</th><th>Abordagem</th></tr></thead>
            <tbody>{linhas}</tbody>
          </table>
          <a class="exportar" href="{export_url}">Exportar XLS</a>
        """

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Busca Leads — Fábrica de Sites IA</title>
<style>
{CSS_BASE}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 24px 26px; margin-bottom: 24px; }}
  form {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: end; margin: 0; }}
  label {{ display: block; font-weight: 600; font-size: 0.82rem; margin-bottom: 6px; }}
  input {{ padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.95rem; }}
  input[name=quantidade] {{ width: 90px; }}
  button[type=submit] {{ padding: 11px 20px; background: var(--accent); color: white; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: background .15s; }}
  button[type=submit]:hover {{ background: var(--accent-dark); }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
  th {{ text-align: left; font-size: 0.8rem; color: var(--muted); padding: 10px 14px; border-bottom: 1px solid var(--border); background: #f8fafc; }}
  td {{ padding: 12px 14px; border-bottom: 1px solid #f3f4f6; font-size: 0.92rem; }}
  tr:last-child td {{ border-bottom: none; }}
  .copiar {{ background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; padding: 6px 10px; font-size: 0.85rem; cursor: pointer; }}
  .copiar.copiado {{ background: var(--accent); color: white; border-color: var(--accent); }}
  a.mapa {{ color: var(--accent); font-weight: 600; text-decoration: none; font-size: 0.88rem; }}
  a.mapa:hover {{ text-decoration: underline; }}
  .erro {{ color: #b91c1c; }}
  .vazio {{ color: var(--muted); }}
  .total {{ color: var(--muted); font-size: 0.85rem; margin: 0 0 10px; }}
  .exportar {{ display: inline-block; margin-top: 16px; color: var(--accent); font-weight: 600; text-decoration: none; }}
  .exportar:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
{cabecalho_nav("hunter")}
<div class="wrap">
  <h1>Busca Leads</h1>
  <p class="subtitle">Prospecção interna (Google Places) — sem disparo automático, você copia e manda manualmente</p>
  <div class="card">
  <form method="get" action="/hunter">
    <div>
      <label>Nicho</label>
      <input name="nicho" value="{esc(nicho)}" placeholder="Ex.: Odontologia" required>
    </div>
    <div>
      <label>Cidade / bairro</label>
      <input name="local" value="{esc(local)}" placeholder="Ex.: Jardim da Penha, Vitória - ES" required>
    </div>
    <div>
      <label>Quantidade</label>
      <input name="quantidade" type="number" min="1" max="20" value="{quantidade}">
    </div>
    <button type="submit">Buscar oportunidades</button>
  </form>
  </div>
  {resultado_html}
</div>

<script>
document.querySelectorAll('.copiar').forEach(btn => {{
  btn.addEventListener('click', async () => {{
    await navigator.clipboard.writeText(btn.dataset.msg);
    btn.textContent = 'Copiado!';
    btn.classList.add('copiado');
    setTimeout(() => {{ btn.textContent = 'Copiar mensagem'; btn.classList.remove('copiado'); }}, 2000);
  }});
}});
</script>
</body>
</html>"""


@router.get("/hunter", response_class=HTMLResponse)
async def busca_leads(request: Request, nicho: str = "", local: str = "", quantidade: int = 20):
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect

    quantidade = max(1, min(quantidade, 20))
    leads, erro = None, ""
    if nicho and local:
        try:
            leads = _buscar(nicho, local, quantidade)
        except ErroBuscaLeads as e:
            erro = str(e)

    return _pagina(nicho, local, quantidade, leads, erro)


@router.get("/hunter/exportar")
async def exportar_leads(request: Request, nicho: str = "", local: str = "", quantidade: int = 20):
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect
    if not nicho or not local:
        return HTMLResponse("Informe nicho e local pra exportar", status_code=400)

    quantidade = max(1, min(quantidade, 20))
    try:
        leads = _buscar(nicho, local, quantidade)
    except ErroBuscaLeads as e:
        return HTMLResponse(f"Erro: {esc(str(e))}", status_code=502)

    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"
    cabecalho = ["Empresa", "Nicho", "Local", "Telefone", "Google Maps", "Mensagem sugerida"]
    ws.append(cabecalho)
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)
    for lead in leads:
        ws.append([lead["nome"], lead["nicho"], lead["local"], lead["telefone"], lead["mapa_url"], lead["mensagem"]])
    for col in ws.columns:
        largura = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(largura + 2, 60)
    ws.freeze_panes = "A2"

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nome_arquivo = f"leads_{nicho}_{local}.xlsx".replace(" ", "_").replace(",", "").lower()
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
