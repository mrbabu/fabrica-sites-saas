"""
Gera variantes responsivas (WebP/AVIF) das fotos de um cliente, AO LADO dos originais.

Motivo (medido em 2026-08-20, MGR): as 11 fotos do portfólio somavam 7,7 MB -- 87% do
peso da página -- servidas em tamanho único, sem WebP e sem srcset. Duas fotos sozinhas
respondiam por metade disso. Cada foto nova que o cliente manda encarece a página no
mesmo ritmo, o que inviabiliza o pedido de "mais imagens e vídeos no portfólio".

Regras que este script respeita:
  * o original NUNCA é sobrescrito nem apagado -- as variantes vão para _otim/ ao lado;
  * nunca faz upscale: só gera largura menor ou igual à original;
  * qualidade alta de propósito (a foto da obra é o ativo do cliente, não é lugar de
    economizar pixel); o ganho vem do formato e do tamanho servido, não de esmagar JPEG.

Uso:
    python backend/scripts/otimizar_imagens.py mgr-reformas-e-projetos
    python backend/scripts/otimizar_imagens.py mgr-reformas-e-projetos --larguras 480,960,1600
"""

import argparse
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
LARGURAS_PADRAO = (480, 960, 1600)
QUALIDADE = {"webp": 82, "avif": 60}   # visualmente transparentes nestes formatos
EXTS = {".jpg", ".jpeg", ".png"}


def variantes_de(origem: Path, saida: Path, larguras, formatos):
    im = Image.open(origem)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGB")
    larguras_uteis = sorted({w for w in larguras if w <= im.width} | {im.width})
    gerados = []
    for w in larguras_uteis:
        altura = round(im.height * w / im.width)
        redim = im.resize((w, altura), Image.LANCZOS)
        for fmt in formatos:
            destino = saida / f"{origem.stem}-{w}.{fmt}"
            try:
                redim.save(destino, format=fmt.upper(), quality=QUALIDADE[fmt], method=6) \
                    if fmt == "webp" else redim.save(destino, format="AVIF", quality=QUALIDADE[fmt])
            except Exception as e:                      # formato indisponível nesta máquina
                print(f"  ! {fmt} falhou em {origem.name} ({e})")
                continue
            gerados.append(destino)
    return im.size, gerados


def main():
    ap = argparse.ArgumentParser(description="Gera variantes responsivas das fotos de um cliente.")
    ap.add_argument("slug")
    ap.add_argument("--larguras", default=",".join(map(str, LARGURAS_PADRAO)))
    ap.add_argument("--formatos", default="webp,avif")
    args = ap.parse_args()

    larguras = [int(x) for x in args.larguras.split(",")]
    formatos = [f.strip() for f in args.formatos.split(",")]

    pastas = [RAIZ / "assets/portfolio" / args.slug, RAIZ / "assets/hero" / args.slug]
    total_antes = total_depois = 0
    for pasta in pastas:
        if not pasta.is_dir():
            continue
        saida = pasta / "_otim"
        saida.mkdir(exist_ok=True)
        for origem in sorted(p for p in pasta.iterdir() if p.suffix.lower() in EXTS):
            antes = origem.stat().st_size
            dim, gerados = variantes_de(origem, saida, larguras, formatos)
            if not gerados:
                continue
            # o "depois" que importa é a maior variante WebP -- é ela que um desktop baixa
            maior_webp = max((g for g in gerados if g.suffix == ".webp"), key=lambda g: g.stat().st_size)
            depois = maior_webp.stat().st_size
            total_antes += antes
            total_depois += depois
            print(f"  {origem.name:28s} {str(dim):12s} {antes/1024:6.0f} KB -> {depois/1024:6.0f} KB "
                  f"({len(gerados)} variantes)")

    if total_antes:
        print(f"\nTotal servido no desktop: {total_antes/1024/1024:.2f} MB -> {total_depois/1024/1024:.2f} MB "
              f"({100 - 100*total_depois/total_antes:.0f}% menor)")
        print("Originais preservados; variantes em <pasta>/_otim/")

    # srcset pronto do hero: o template só emite <source> quando o tenant declara
    # hero.srcset, então imprimir aqui evita montar o caminho à mão -- e evita
    # apontar para uma variante que não existe.
    hero = RAIZ / "assets/hero" / args.slug
    if hero.is_dir():
        for origem in sorted(p for p in hero.iterdir() if p.suffix.lower() in EXTS):
            variantes = sorted((hero / "_otim").glob(origem.stem + "-*.webp"),
                               key=lambda f: int(f.stem.rsplit("-", 1)[1]))
            partes = [f"assets/hero/{args.slug}/_otim/{v.name} {v.stem.rsplit('-', 1)[1]}w"
                      for v in variantes]
            if partes:
                print(f"\nhero.srcset para {origem.name}:\n  " + ", ".join(partes))


if __name__ == "__main__":
    main()
