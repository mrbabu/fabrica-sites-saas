#!/usr/bin/env python3
"""
Busca Leads — ver docs/hunter_online_spec.md. Módulo central da plataforma
(decisão de produto 2026-07-22): Postgres é a fonte de verdade dos leads
encontrados (tabelas hunter_buscas/hunter_leads, ver models_db.py); CSV
deixou de ser a base do sistema e virou só mecanismo de import/export
(backend/scripts/importar_leads_csv.py).

Reaproveita buscar_estabelecimentos() do script de linha de comando
existente (backend/scripts/buscar_leads_google_maps.py) — a busca em si
não mudou, só o que acontece com o resultado depois.

Escopo fechado, mesmo de antes: sem disparo automático de WhatsApp, sem
score avançado, sem coleta automática de Instagram/Facebook, sem agente
de IA novo — a "mensagem sugerida" é template estático, não LLM.
"""

import io
import json
import os
from functools import lru_cache
from html import escape as esc
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from auth_demo import exigir_login_demo
from db import get_db
from scripts.buscar_leads_google_maps import buscar_estabelecimentos
from ui_common import CSS_BASE, cabecalho as cabecalho_nav
import repository

router = APIRouter(tags=["Demo DFY (ferramenta interna)"])

# vendas-config.json é a única fonte de verdade pro preço público (é o que
# vendas.html mostra) — o Hunter lê o mesmo arquivo em vez de duplicar o
# valor, pra nunca ficar dessincronizado.
_VENDAS_CONFIG_PATH = Path(__file__).resolve().parents[2] / "vendas-config.json"


@lru_cache(maxsize=1)
def _vendas_config() -> dict:
    with open(_VENDAS_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _preco_base() -> str:
    base = _vendas_config()["pricing"]["base"]
    return f"{base['price']}{base['period']}"

TEMPLATE_ABORDAGEM = (
    "Oi! Vi a {nome} aqui em {local} e reparei que vocês não têm site — só "
    "o Google/Instagram. Sou da área de tecnologia, trabalho criando sites "
    "pra {nicho_lower} da região. Não é nada empurrado, só queria entender: "
    "hoje como é que um cliente novo acha vocês, além de indicação?"
)

# Mensagem de follow-up pra depois que o lead já respondeu (status "respondeu"
# em diante) — o preço vem de vendas-config.json (ver _preco_base), é a
# mesma oferta que a landing mostra.
TEMPLATE_OFERTA = (
    "Oi, {nome}! Que bom que respondeu 🙂 Deixa eu te contar rapidinho como funciona:\n\n"
    "🌐 *Site profissional no ar*, feito especialmente pro seu negócio — não é modelo pronto\n"
    "💬 *WhatsApp integrado* em todo o site, pro cliente já cair direto na conversa\n"
    "🔍 *Aparece no Google* — SEO local desde o primeiro dia\n\n"
    "A partir de *{preco}*, com hospedagem e manutenção inclusas. Dá pra começar já no "
    "plano base, sem precisar contratar mais nada além disso.\n\n"
    "Se topar, eu já preparo uma demonstração pronta do jeito que ficaria o site de vocês — "
    "você só decide depois de ver."
)

ROTULOS_STATUS = {
    "pendente": "Pendente",
    "contatado": "Contatado",
    "respondeu": "Respondeu",
    "demo_enviada": "Demo enviada",
    "cliente": "Cliente",
    "descartado": "Descartado",
}

# Só libera a mensagem de oferta depois que o lead já respondeu o 1º contato —
# evita queimar a abordagem mandando a oferta antes da hora.
STATUS_LIBERA_OFERTA = {"respondeu", "demo_enviada", "cliente"}


class ErroBuscaLeads(Exception):
    pass


def _mensagem(nome: str, local: str, nicho: str) -> str:
    return TEMPLATE_ABORDAGEM.format(nome=nome, local=local, nicho_lower=nicho.lower())


def _mensagem_oferta(nome: str) -> str:
    return TEMPLATE_OFERTA.format(nome=nome, preco=_preco_base())


def _buscar_google(nicho: str, local: str, quantidade: int) -> list[dict]:
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
        telefone = (lugar.get("nationalPhoneNumber") or "").strip() or None
        leads.append({
            "place_id": lugar.get("id"),
            "nome_empresa": nome,
            "nicho": nicho,
            "cidade": local,
            "telefone": telefone,
            "google_maps_url": lugar.get("googleMapsUri") or None,
        })
        if len(leads) >= quantidade:
            break
    return leads


# ============================================================================
# /hunter — buscar (persiste no banco a cada busca)
# ============================================================================

def _pagina_busca(nicho: str, local: str, quantidade: int, leads: list | None, erro: str) -> str:
    if erro:
        resultado_html = f'<p class="erro">Erro: {esc(erro)}</p>'
    elif leads is None:
        resultado_html = ""
    elif not leads:
        resultado_html = '<p class="vazio">Nenhuma empresa sem site encontrada pra esses critérios (ou já estavam salvas de uma busca anterior).</p>'
    else:
        linhas = "".join(
            f"""<tr>
                <td>{esc(l.nome_empresa)}</td>
                <td>{esc(l.telefone or "a validar")}</td>
                <td>{f'<a class="mapa" href="{esc(l.google_maps_url)}" target="_blank" rel="noopener">Ver no mapa</a>' if l.google_maps_url else '—'}</td>
                <td>
                  <button type="button" class="copiar" data-msg="{esc(_mensagem(l.nome_empresa, l.cidade, l.nicho))}">Copiar mensagem</button>
                </td>
            </tr>"""
            for l in leads
        )
        resultado_html = f"""
          <p class="total">{len(leads)} lead(s) novo(s) salvo(s) no banco — <a href="/hunter/leads">ver todos os leads salvos</a>.</p>
          <table>
            <thead><tr><th>Empresa</th><th>Telefone</th><th>Mapa</th><th>Abordagem</th></tr></thead>
            <tbody>{linhas}</tbody>
          </table>
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
  form.busca {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: end; margin: 0; }}
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
  .erro {{ color: #b91c1c; }}
  .vazio {{ color: var(--muted); }}
  .total {{ color: var(--muted); font-size: 0.85rem; margin: 0 0 10px; }}
  a.mapa {{ color: var(--accent); font-weight: 600; text-decoration: none; font-size: 0.88rem; }}
  a.mapa:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
{cabecalho_nav("hunter")}
<div class="wrap">
  <h1>Busca Leads</h1>
  <p class="subtitle">Prospecção interna (Google Places) — resultados salvos no banco, sem disparo automático. <a href="/hunter/leads">Ver leads salvos</a></p>
  <div class="card">
  <form class="busca" method="get" action="/hunter">
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
async def busca_leads(request: Request, nicho: str = "", local: str = "", quantidade: int = 20, db: Session = Depends(get_db)):
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect

    quantidade = max(1, min(quantidade, 20))
    leads_salvos, erro = None, ""
    if nicho and local:
        try:
            encontrados = _buscar_google(nicho, local, quantidade)
            busca = repository.criar_busca_hunter(db, nicho, local, None, None, quantidade, origem="hunter_web")
            leads_salvos = repository.salvar_leads_hunter(db, busca.id, encontrados, origem="google_places")
        except ErroBuscaLeads as e:
            erro = str(e)

    return _pagina_busca(nicho, local, quantidade, leads_salvos, erro)


# ============================================================================
# /hunter/leads — revisão dos leads já salvos (filtros, status, export)
# ============================================================================

def _pagina_leads(leads: list, buscas: list, filtros: dict, stats: dict) -> str:
    opcoes_status = "".join(
        f'<option value="{chave}" {"selected" if filtros.get("status") == chave else ""}>{rotulo}</option>'
        for chave, rotulo in ROTULOS_STATUS.items()
    )

    linhas = "".join(
        f"""<tr>
            <td>{esc(l.nome_empresa)}</td>
            <td>{esc(l.nicho)}</td>
            <td>{esc(l.cidade)}</td>
            <td>{esc(l.telefone or "a validar")}</td>
            <td>
              <form method="post" action="/hunter/leads/{l.id}/status" class="status-form">
                <select name="status" onchange="this.form.submit()">
                  {"".join(f'<option value="{c}" {"selected" if l.status == c else ""}>{r}</option>' for c, r in ROTULOS_STATUS.items())}
                </select>
              </form>
            </td>
            <td>{f'<a class="mapa" href="{esc(l.google_maps_url)}" target="_blank" rel="noopener">mapa</a>' if l.google_maps_url else '—'}</td>
            <td><a class="mapa" href="/demo?nome_empresa={esc(l.nome_empresa)}&nicho={esc(l.nicho)}&localizacao={esc(l.cidade)}&lead_id={l.id}">gerar demo</a></td>
            <td>
              <button type="button" class="copiar" data-msg="{esc(_mensagem(l.nome_empresa, l.cidade, l.nicho))}">1º contato</button>
              {f'<button type="button" class="copiar" data-msg="{esc(_mensagem_oferta(l.nome_empresa))}">Oferta</button>' if l.status in STATUS_LIBERA_OFERTA else '<button type="button" class="copiar" disabled title="Libera depois que o status virar Respondeu">Oferta</button>'}
            </td>
        </tr>"""
        for l in leads
    )
    corpo = linhas or '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:24px">Nenhum lead encontrado com esses filtros.</td></tr>'

    buscas_html = "".join(
        f'<a class="chip" href="/hunter/leads?busca_id={b.id}">{esc(b.nicho)} · {esc(b.cidade)} ({b.quantidade_encontrada}) — {b.created_at.strftime("%d/%m %H:%M")}</a>'
        for b in buscas
    ) or '<span class="muted-txt">nenhuma busca ainda</span>'

    def _v(nome):
        return esc(filtros.get(nome) or "")

    export_qs = f"nicho={_v('nicho')}&cidade={_v('cidade')}&status={_v('status')}&busca_texto={_v('busca_texto')}"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Leads salvos — Fábrica de Sites IA</title>
<style>
{CSS_BASE}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 20px 24px; margin-bottom: 20px; }}
  form.filtros {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: end; margin: 0; }}
  label {{ display: block; font-weight: 600; font-size: 0.8rem; margin-bottom: 5px; }}
  input, select {{ padding: 9px 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 0.9rem; }}
  button[type=submit] {{ padding: 10px 18px; background: var(--accent); color: white; border: none; border-radius: 8px; font-size: 0.9rem; font-weight: 600; cursor: pointer; }}
  .buscas {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }}
  a.chip {{ background: var(--card); border: 1px solid var(--border); border-radius: 999px; padding: 6px 14px; font-size: 0.8rem; color: var(--text); text-decoration: none; }}
  a.chip:hover {{ border-color: var(--accent); color: var(--accent); }}
  .muted-txt {{ color: var(--muted); font-size: 0.85rem; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
  th {{ text-align: left; font-size: 0.78rem; color: var(--muted); padding: 9px 12px; border-bottom: 1px solid var(--border); background: #f8fafc; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #f3f4f6; font-size: 0.88rem; }}
  tr:last-child td {{ border-bottom: none; }}
  select {{ font-size: 0.82rem; padding: 5px 6px; }}
  .status-form {{ margin: 0; }}
  a.mapa {{ color: var(--accent); font-weight: 600; text-decoration: none; font-size: 0.85rem; }}
  .copiar {{ background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; padding: 5px 9px; font-size: 0.8rem; cursor: pointer; }}
  .copiar.copiado {{ background: var(--accent); color: white; border-color: var(--accent); }}
  .copiar:disabled {{ opacity: 0.45; cursor: not-allowed; }}
  .exportar {{ display: inline-block; margin-top: 14px; color: var(--accent); font-weight: 600; text-decoration: none; }}
</style>
</head>
<body>
{cabecalho_nav("hunter")}
<div class="wrap">
  <h1>Leads salvos</h1>
  <p class="subtitle">Todos os leads encontrados pelo Hunter, com histórico e status — <a href="/hunter">nova busca</a></p>

  <div class="stats">
    <div class="stat-card"><div class="valor">{stats['total']}</div><div class="rotulo">Total de leads</div></div>
    <div class="stat-card"><div class="valor">{stats['pendentes']}</div><div class="rotulo">Pendentes</div></div>
    <div class="stat-card"><div class="valor">{stats['contatados']}</div><div class="rotulo">Contatados+</div></div>
    <div class="stat-card"><div class="valor">{stats['clientes']}</div><div class="rotulo">Clientes</div></div>
  </div>

  <p class="subtitle" style="margin-bottom:8px">Buscas recentes</p>
  <div class="buscas">{buscas_html}</div>

  <div class="card">
    <form class="filtros" method="get" action="/hunter/leads">
      <div><label>Nicho</label><input name="nicho" value="{_v('nicho')}" placeholder="qualquer"></div>
      <div><label>Cidade</label><input name="cidade" value="{_v('cidade')}" placeholder="qualquer"></div>
      <div><label>Status</label><select name="status"><option value="">todos</option>{opcoes_status}</select></div>
      <div><label>Buscar por nome/telefone</label><input name="busca_texto" value="{_v('busca_texto')}" placeholder="ex.: sorriso"></div>
      <button type="submit">Filtrar</button>
    </form>
  </div>

  <table>
    <thead><tr><th>Empresa</th><th>Nicho</th><th>Cidade</th><th>Telefone</th><th>Status</th><th>Mapa</th><th>Demo</th><th>Abordagem</th></tr></thead>
    <tbody>{corpo}</tbody>
  </table>
  <a class="exportar" href="/hunter/exportar?{export_qs}">Exportar XLS ({len(leads)} lead(s) filtrado(s))</a>
</div>

<script>
document.querySelectorAll('.copiar').forEach(btn => {{
  btn.addEventListener('click', async () => {{
    await navigator.clipboard.writeText(btn.dataset.msg);
    btn.textContent = 'OK!';
    btn.classList.add('copiado');
    setTimeout(() => {{ btn.textContent = 'Copiar'; btn.classList.remove('copiado'); }}, 2000);
  }});
}});
</script>
</body>
</html>"""


@router.get("/hunter/leads", response_class=HTMLResponse)
async def leads_salvos(
    request: Request,
    nicho: str = "",
    cidade: str = "",
    status: str = "",
    busca_texto: str = "",
    busca_id: int | None = None,
    db: Session = Depends(get_db),
):
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect

    leads = repository.listar_leads_hunter(
        db,
        nicho=nicho or None,
        cidade=cidade or None,
        status=status or None,
        busca_texto=busca_texto or None,
        busca_id=busca_id,
    )
    buscas = repository.listar_buscas_hunter(db, limite=15)

    todos = repository.listar_leads_hunter(db)
    stats = {
        "total": len(todos),
        "pendentes": sum(1 for l in todos if l.status == "pendente"),
        "contatados": sum(1 for l in todos if l.status in ("contatado", "respondeu", "demo_enviada")),
        "clientes": sum(1 for l in todos if l.status == "cliente"),
    }

    filtros = {"nicho": nicho, "cidade": cidade, "status": status, "busca_texto": busca_texto}
    return _pagina_leads(leads, buscas, filtros, stats)


@router.post("/hunter/leads/{lead_id}/status")
async def atualizar_status(lead_id: int, request: Request, db: Session = Depends(get_db)):
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect
    form = await request.form()
    novo_status = str(form.get("status", ""))
    try:
        repository.atualizar_status_lead_hunter(db, lead_id, novo_status)
    except ValueError:
        pass
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/hunter/leads", status_code=303)


@router.post("/hunter/leads/{lead_id}/vincular-demo")
async def vincular_demo(lead_id: int, request: Request, db: Session = Depends(get_db)):
    """Chamado pelo JS de /demo depois de gerar com sucesso, quando a
    geração partiu de um lead do Hunter (?lead_id=... na URL)."""
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect
    corpo = await request.json()
    slug = str(corpo.get("slug", ""))
    if not slug:
        return JSONResponse({"erro": "slug obrigatório"}, status_code=400)
    lead = repository.vincular_demo_ao_lead(db, lead_id, slug)
    if lead is None:
        return JSONResponse({"erro": "lead não encontrado"}, status_code=404)
    return JSONResponse({"ok": True})


# ============================================================================
# /hunter/exportar — export XLS a partir do banco (respeita os filtros)
# ============================================================================

@router.get("/hunter/exportar")
async def exportar_leads(
    request: Request,
    nicho: str = "",
    cidade: str = "",
    status: str = "",
    busca_texto: str = "",
    db: Session = Depends(get_db),
):
    redirect = exigir_login_demo(request)
    if redirect:
        return redirect

    leads = repository.listar_leads_hunter(
        db, nicho=nicho or None, cidade=cidade or None, status=status or None, busca_texto=busca_texto or None
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"
    cabecalho = ["Empresa", "Nicho", "Cidade", "Telefone", "Status", "Google Maps", "Mensagem sugerida", "Salvo em"]
    ws.append(cabecalho)
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)
    for lead in leads:
        ws.append([
            lead.nome_empresa,
            lead.nicho,
            lead.cidade,
            lead.telefone or "a validar",
            ROTULOS_STATUS.get(lead.status, lead.status),
            lead.google_maps_url or "",
            _mensagem(lead.nome_empresa, lead.cidade, lead.nicho),
            lead.created_at.strftime("%d/%m/%Y %H:%M"),
        ])
    for col in ws.columns:
        largura = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(largura + 2, 60)
    ws.freeze_panes = "A2"

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="leads_hunter.xlsx"'},
    )
