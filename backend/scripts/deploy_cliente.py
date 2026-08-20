"""
Publica o site de um cliente na Vercel a partir de configs/<slug>.json.

Existe porque o processo era manual e frágil: montar pasta, copiar assets na mão,
lembrar de recompilar o Tailwind e de trocar o ?v= do stylesheet. Já quase publicou
uma grade colapsada em 1 coluna porque o CSS do pacote estava velho (2026-08-09).

O que faz, em ordem:
  1. recompila o CSS estático (classe nova só existe no build);
  2. monta um pacote isolado com index.html, o config do cliente e SÓ os assets que
     esse config referencia (varre o JSON atrás de caminhos "assets/...");
  3. troca a query do stylesheet pelo hash do próprio CSS -- cache-busting automático,
     sem depender de alguém lembrar de incrementar um número à mão;
  4. bloqueia se o Quality Gate acusar falha P0 (P1/P2 passam com aviso: a MGR reprova
     IMG-04 por decisão consciente de usar foto real em vez de banco de imagens);
  5. publica com `vercel deploy --prod` no projeto de mesmo nome do slug.

Uso:
    python backend/scripts/deploy_cliente.py mgr-reformas-e-projetos --dry-run
    python backend/scripts/deploy_cliente.py mgr-reformas-e-projetos

--dry-run monta e valida o pacote sem publicar nada. Rode sempre antes.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

CSS = "assets/css/tailwind.css"


def _run(cmd, **kw):
    """Executa e devolve (returncode, saída). shell=False, nunca interpola input do usuário."""
    p = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True, **kw)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _caminhos_de_assets(no):
    """Todo string 'assets/...' em qualquer profundidade do config.

    Um srcset ("a.webp 480w, b.webp 960w") é uma string só carregando vários
    caminhos -- cada descritor precisa virar um arquivo do pacote, e não o texto
    inteiro virar um caminho inexistente.
    """
    if isinstance(no, str):
        if not no.startswith("assets/"):
            return set()
        return {p.strip().split()[0] for p in no.split(",") if p.strip()}
    if isinstance(no, dict):
        return set().union(*(_caminhos_de_assets(v) for v in no.values())) if no else set()
    if isinstance(no, list):
        return set().union(*(_caminhos_de_assets(v) for v in no)) if no else set()
    return set()


def compilar_css():
    cod, saida = _run(["npx", "tailwindcss", "-i", "./assets/css/tailwind-input.css",
                       "-o", f"./{CSS}", "--minify"], shell=(os.name == "nt"))
    if cod != 0:
        raise SystemExit(f"Falha ao compilar o Tailwind:\n{saida}")
    print(f"CSS recompilado ({(RAIZ / CSS).stat().st_size} bytes)")


def montar_pacote(slug, destino):
    config = RAIZ / "configs" / f"{slug}.json"
    if not config.is_file():
        raise SystemExit(f"Config não encontrado: {config}")
    dados = json.loads(config.read_text(encoding="utf-8"))

    destino.mkdir(parents=True, exist_ok=True)
    (destino / "site-config.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSS + cache-busting pelo hash do conteúdo
    (destino / "assets/css").mkdir(parents=True, exist_ok=True)
    shutil.copy2(RAIZ / CSS, destino / CSS)
    digest = hashlib.sha256((RAIZ / CSS).read_bytes()).hexdigest()[:8]
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    html, trocas = re.subn(r'(/assets/css/tailwind\.css)\?v=[^"\']*', rf"\1?v={digest}", html)
    if trocas != 1:
        raise SystemExit(f"Esperava 1 referência ao {CSS} no index.html, encontrei {trocas}.")
    (destino / "index.html").write_text(html, encoding="utf-8")
    print(f"index.html empacotado com ?v={digest} (hash do CSS)")

    faltando = []
    for rel in sorted(_caminhos_de_assets(dados)):
        origem = RAIZ / rel
        if not origem.is_file():
            faltando.append(rel)
            continue
        alvo = destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, alvo)
    if faltando:
        raise SystemExit("Assets referenciados pelo config não existem no disco:\n  " + "\n  ".join(faltando))

    arquivos = [p for p in destino.rglob("*") if p.is_file()]
    print(f"Pacote: {len(arquivos)} arquivo(s), {sum(p.stat().st_size for p in arquivos) // 1024} KB")
    return dados


def rodar_quality_gate(dados):
    from quality_gate import rodar_gate_completo, _severidade

    resultados = rodar_gate_completo(dados)
    falhas = [r for r in resultados if not r.passou]
    ok = len(resultados) - len(falhas)
    print(f"Quality Gate: {ok}/{len(resultados)}")
    for r in falhas:
        print(f"  {_severidade(r.id)} {r.id}: {r.detalhe or 'reprovou'}")
    p0 = [r for r in falhas if _severidade(r.id) == "P0"]
    if p0:
        raise SystemExit("Deploy abortado: falha P0 no Quality Gate.")


def publicar(slug, pacote, token):
    for etapa in (["npx", "vercel", "link", "--yes", "--project", slug, "--token", token, "--cwd", str(pacote)],
                  ["npx", "vercel", "deploy", "--prod", "--yes", "--token", token, "--cwd", str(pacote)]):
        # o link grava um .env.local no pacote; ele não pode subir junto
        cod, saida = _run(etapa, shell=(os.name == "nt"))
        (pacote / ".env.local").unlink(missing_ok=True)
        if cod != 0:
            raise SystemExit(f"Comando falhou ({etapa[2]}):\n{saida}")
    url = re.search(r"https://[\w.-]+\.vercel\.app", saida)
    print(f"Publicado: {url.group(0) if url else '(URL não encontrada na saída)'}")


def main():
    ap = argparse.ArgumentParser(description="Empacota e publica o site de um cliente.")
    ap.add_argument("slug", help="nome do config em configs/ e do projeto na Vercel")
    ap.add_argument("--dry-run", action="store_true", help="monta e valida sem publicar")
    ap.add_argument("--out", help="onde montar o pacote (padrão: pasta temporária)")
    args = ap.parse_args()

    token = os.environ.get("VERCEL_TOKEN")
    if not token and not args.dry_run:
        env = RAIZ / ".env"
        linha = next((l for l in env.read_text(encoding="utf-8").splitlines()
                      if l.startswith("VERCEL_TOKEN=")), "") if env.is_file() else ""
        token = linha.partition("=")[2].strip().strip('"\'')
        if not token:
            raise SystemExit("VERCEL_TOKEN ausente (nem no ambiente, nem no .env da raiz).")

    pacote = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix=f"deploy-{args.slug}-"))
    if pacote.exists() and args.out:
        shutil.rmtree(pacote)

    compilar_css()
    dados = montar_pacote(args.slug, pacote)
    rodar_quality_gate(dados)

    if args.dry_run:
        print(f"\n--dry-run: nada publicado. Pacote em {pacote}")
        return
    publicar(args.slug, pacote, token)


if __name__ == "__main__":
    main()
