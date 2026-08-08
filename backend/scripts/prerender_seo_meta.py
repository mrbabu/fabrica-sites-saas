"""
Corrige o SEO/preview de link (WhatsApp, Facebook, Google) dos sites de cliente.

Causa raiz confirmada (2026-08-08, evidência: print de compartilhamento no WhatsApp
mostrando "Carregando..." no lugar do título/descrição real): o <head> estático de
index.html só tem placeholders ("Carregando...", atributos vazios) -- title/description/
og:* só ganham o valor real via JS (render() em index.html), depois que o navegador
busca site-config.json. Crawlers de link preview (WhatsApp, Facebook, Twitter, e o
primeiro passe do Googlebot) não executam esse JS, então veem só o placeholder.

Este script substitui os placeholders pelos valores reais do site-config.json do
cliente, direto nos bytes estáticos do index.html -- roda uma vez, antes do deploy
de cada cliente (não em runtime, não precisa de servidor). O JS de render() continua
existindo e reescreve os mesmos valores no load -- redundante e inofensivo, serve de
rede de segurança se alguém editar o config sem rodar este script de novo.

`--origin` (opcional) resolve caminhos relativos (ogImage, logo usado como favicon)
pra URL absoluta -- a spec do Open Graph exige URL absoluta em og:image, e crawlers
não sabem contra qual domínio resolver um caminho relativo. O domínio é sempre
passado na chamada, nunca hardcoded aqui nem no template: cada tenant tem seu próprio
domínio de deploy (MGR, Padaria, Bike Center...), e este script é genérico pra
qualquer um deles. URLs já absolutas (http(s)://, data:) passam direto, sem prefixo
duplicado.

Uso: python prerender_seo_meta.py <pasta_do_cliente> [--origin https://dominio-do-tenant]
     (a pasta precisa conter index.html e site-config.json)
"""
import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import quote, urljoin


def _escape(texto: str) -> str:
    return html.escape(texto or "", quote=True)


def _absolutizar(url: str, origin: str | None) -> str:
    if not url or not origin or re.match(r"^(https?:)?//|^data:", url):
        return url
    return urljoin(origin.rstrip("/") + "/", url.lstrip("/"))


def _favicon_href(company: dict, emoji: str, origin: str | None) -> str:
    logo = company.get("logo")
    if logo:
        return _absolutizar(logo, origin)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="0.9em" font-size="90">{emoji}</text></svg>'
    return "data:image/svg+xml," + quote(svg)


def prerender_meta(html_original: str, config: dict, origin: str | None = None) -> str:
    """Substitui os placeholders do <head> pelos valores reais do config.

    Espelha exatamente a lógica de render()/setFavicon() em index.html --
    qualquer mudança lá precisa ser refletida aqui também. `origin` (opcional)
    resolve ogImage/logo relativos pra URL absoluta -- ver docstring do módulo.
    """
    metadata = config.get("metadata", {})
    company = config.get("company", {})

    site_title = metadata.get("siteTitle", "")
    site_description = metadata.get("siteDescription", "")
    keywords = ", ".join(metadata.get("keywords", []))
    og_title = metadata.get("ogTitle") or site_title
    og_description = metadata.get("ogDescription") or site_description
    og_image = _absolutizar(metadata.get("ogImage", ""), origin)
    favicon_emoji = metadata.get("favicon", "🚀")
    favicon_href = _favicon_href(company, favicon_emoji, origin)

    substituicoes = [
        (r"<title>.*?</title>", f"<title>{_escape(site_title)}</title>"),
        (
            r'<meta name="description" content=".*?">',
            f'<meta name="description" content="{_escape(site_description)}">',
        ),
        (
            r'<meta name="keywords" content=".*?">',
            f'<meta name="keywords" content="{_escape(keywords)}">',
        ),
        (
            r'<meta property="og:title" content=".*?">',
            f'<meta property="og:title" content="{_escape(og_title)}">',
        ),
        (
            r'<meta property="og:description" content=".*?">',
            f'<meta property="og:description" content="{_escape(og_description)}">',
        ),
        (
            r'<meta property="og:image" content=".*?">',
            f'<meta property="og:image" content="{_escape(og_image)}">',
        ),
        (
            r'<link id="favicon-link" rel="icon" href="[^"]*">',
            f'<link id="favicon-link" rel="icon" href="{_escape(favicon_href)}">',
        ),
    ]

    resultado = html_original
    for padrao, substituto in substituicoes:
        novo = re.sub(padrao, substituto, resultado, count=1, flags=re.DOTALL)
        if novo == resultado:
            raise ValueError(f"Placeholder não encontrado no index.html (padrão: {padrao[:50]}...)")
        resultado = novo
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pasta", type=Path, help="Pasta do cliente com index.html e site-config.json")
    parser.add_argument(
        "--origin",
        default=None,
        help="Domínio público do deploy desse tenant (ex.: https://mgr-reformas-e-projetos.vercel.app) -- resolve ogImage/logo relativos pra URL absoluta. Omitido: caminhos relativos ficam como estão no JSON.",
    )
    args = parser.parse_args()

    index_path = args.pasta / "index.html"
    config_path = args.pasta / "site-config.json"

    if not index_path.exists() or not config_path.exists():
        raise SystemExit(f"Esperava index.html e site-config.json em {args.pasta}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    html_original = index_path.read_text(encoding="utf-8")
    html_corrigido = prerender_meta(html_original, config, origin=args.origin)
    index_path.write_text(html_corrigido, encoding="utf-8")
    print(f"OK: <head> de {index_path} atualizado com dados reais de {config['company']['name']}.")


if __name__ == "__main__":
    main()
