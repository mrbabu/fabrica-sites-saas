#!/usr/bin/env python3
"""
Cabeçalho/estilo compartilhado das páginas internas (/demo, /demo/lista,
/hunter) — só polish visual, nenhuma lógica de negócio. Evita duplicar
marcação de navegação em cada router (e ela desalinhar com o tempo).
"""

CSS_BASE = """
  :root { --accent: #0D9488; --accent-dark: #0f766e; --bg: #f8fafc; --card: #ffffff; --border: #e5e7eb; --text: #0f172a; --muted: #64748b; }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, "Inter", "Segoe UI", sans-serif; margin: 0; background: var(--bg); color: var(--text); }
  .wrap { max-width: 960px; margin: 0 auto; padding: 0 24px 60px; }
  nav.topbar { background: linear-gradient(135deg, #0f172a 0%, #134e4a 100%); padding: 16px 24px; margin-bottom: 32px; }
  nav.topbar .inner { max-width: 960px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
  nav.topbar .brand { color: #fff; font-weight: 700; font-size: 1.05rem; letter-spacing: -0.02em; display: flex; align-items: center; gap: 8px; }
  nav.topbar .links { display: flex; gap: 4px; flex-wrap: wrap; }
  nav.topbar a { color: rgba(255,255,255,0.75); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 7px 14px; border-radius: 7px; transition: background .15s, color .15s; }
  nav.topbar a:hover { background: rgba(255,255,255,0.08); color: #fff; }
  nav.topbar a.ativo { background: var(--accent); color: #fff; }
  h1 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; margin: 0 0 4px; }
  p.subtitle { color: var(--muted); margin: 0 0 28px; font-size: 0.95rem; }
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 14px; margin-bottom: 32px; }
  .stat-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 18px 20px; }
  .stat-card .valor { font-size: 1.8rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
  .stat-card .rotulo { font-size: 0.82rem; color: var(--muted); margin-top: 2px; }
"""

_ITENS_NAV = [
    ("demo", "/demo", "Site Constructor"),
    ("hunter", "/hunter", "Busca Leads"),
    ("lista", "/demo/lista", "Sites Gerados"),
]


def cabecalho(pagina_ativa: str) -> str:
    """pagina_ativa: 'demo' | 'hunter' | 'lista' — destaca o item correspondente."""
    links = "".join(
        f'<a href="{href}" class="{"ativo" if chave == pagina_ativa else ""}">{rotulo}</a>'
        for chave, href, rotulo in _ITENS_NAV
    )
    return f"""<nav class="topbar"><div class="inner">
      <div class="brand">🏗️ Fábrica de Sites AI</div>
      <div class="links">{links}<a href="/demo/logout">Sair</a></div>
    </div></nav>"""
