"""
Gera as sections de portfólio de um cliente a partir de fotos reais locais,
classificando cada foto por conteúdo (categoria/etapa da obra) e escrevendo
o texto correspondente via IA com visão -- reproduzindo pra qualquer cliente
o padrão que hoje só existe manualmente no site da MGR Reformas e Projetos
(configs/mgr-reformas-e-projetos.json).

Uso interno/equipe: aponta pra uma pasta local de fotos já recebidas do
cliente (WhatsApp/e-mail/etc.) -- não é upload público, mantém a mudança
dentro do Guardrail #2 do ROADMAP.md (nada de self-service antes de 15-20
vendas fechadas).

Pré-requisito: configs/<slug>.json já existe (rodar a geração normal do
site antes). Este script só ACRESCENTA sections de portfólio às já
existentes -- não cria site do zero, não mexe em mais nenhum outro campo
do config.

Uso:
    python backend/scripts/gerar_portfolio_fotos.py mgr-teste ./fotos-cliente
    python backend/scripts/gerar_portfolio_fotos.py mgr-teste ./fotos-cliente --hero fachada_final.jpg --nicho "reformas"

Depois de rodar:
    python backend/scripts/otimizar_imagens.py <slug>   # gera variantes WebP/AVIF
"""

import argparse
import io
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

from ai_provider import AIProvider, ErroProvedorIA  # noqa: E402
from image_utils import _slugify  # noqa: E402

EXTS = {".jpg", ".jpeg", ".png", ".webp"}
LARGURA_MAX_CLASSIFICACAO = 1024


class ErroGerarPortfolio(Exception):
    """Erro ao gerar o portfólio a partir das fotos"""


def _reduzir_para_classificacao(caminho: Path) -> bytes:
    """Redimensiona uma cópia EM MEMÓRIA da foto para no máximo
    LARGURA_MAX_CLASSIFICACAO de largura, só para a chamada de IA -- o
    arquivo original em disco nunca é tocado (mesmo espírito de
    otimizar_imagens.py: nunca mexer no original)."""
    im = Image.open(caminho)
    if im.mode != "RGB":
        im = im.convert("RGB")
    if im.width > LARGURA_MAX_CLASSIFICACAO:
        altura = round(im.height * LARGURA_MAX_CLASSIFICACAO / im.width)
        im = im.resize((LARGURA_MAX_CLASSIFICACAO, altura), Image.LANCZOS)
    buffer = io.BytesIO()
    im.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def _montar_prompt(nicho: str, nome_empresa: str, arquivos: list[str], contexto: str | None) -> str:
    lista = "\n".join(f"- {nome}" for nome in arquivos)
    contexto_linha = f"\nContexto adicional fornecido pela equipe: {contexto}\n" if contexto else ""
    return f"""Você é um redator especializado em sites institucionais de pequenas empresas brasileiras.

A empresa "{nome_empresa}" atua no ramo "{nicho}". Você recebeu {len(arquivos)} fotos reais do trabalho dela, nesta ordem, uma imagem por arquivo:
{lista}
{contexto_linha}
Para cada foto, na ordem em que foi enviada:
1. Identifique o que a foto mostra (categoria do trabalho, etapa da obra/serviço -- ex.: estrutura, execução, acabamento, resultado finalizado).
2. Quando várias fotos parecerem ser do MESMO projeto/obra em etapas diferentes, trate-as como uma sequência (ex.: "Estrutura" -> "Revestimento" -> "Finalizado"), com títulos que deixem essa progressão clara.
3. Escreva um título curto no formato "Portfólio: <Categoria> — <Etapa>", um subtítulo de uma linha, e um parágrafo de 1-2 frases descrevendo especificamente o que ESSA foto mostra.

Regra crítica: cada título/subtítulo/parágrafo tem que ser sobre aquela foto especificamente -- nunca reaproveite a mesma frase ou estrutura de frase em duas fotos diferentes, mesmo que sejam da mesma categoria (etapas diferentes da mesma obra têm que soar como etapas diferentes).

Devolva EXCLUSIVAMENTE um JSON no formato:
{{
  "fotos": [
    {{"arquivo": "nome-exato-do-arquivo-recebido", "titulo": "...", "subtitulo": "...", "conteudo": "..."}}
  ]
}}

O array "fotos" precisa ter exatamente {len(arquivos)} objetos, um para cada arquivo listado acima, usando o nome de arquivo EXATO."""


def classificar_fotos(nicho: str, nome_empresa: str, caminhos: list[Path], contexto: str | None = None) -> dict:
    """Chama a IA com visão para classificar as fotos, devolvendo um dict
    {nome_do_arquivo: {"titulo", "subtitulo", "conteudo"}}.

    Sem chamada mockável nem estimativa: se a contagem devolvida não bater
    com o número de fotos enviadas, aborta -- não preenche a diferença com
    texto inventado (mesmo princípio anti-fabricação do agent_construtor).
    """
    prompt = _montar_prompt(nicho, nome_empresa, [c.name for c in caminhos], contexto)
    imagens = [_reduzir_para_classificacao(c) for c in caminhos]

    resposta = AIProvider().gerar_json_com_imagens(prompt, imagens)
    fotos = resposta.get("fotos", [])

    if len(fotos) != len(caminhos):
        raise ErroGerarPortfolio(
            f"A IA devolveu {len(fotos)} fotos classificadas, mas foram enviadas {len(caminhos)}. "
            "Abortando -- não preencher a diferença com texto inventado."
        )

    nomes_esperados = {c.name for c in caminhos}
    por_arquivo = {}
    for item in fotos:
        arquivo = item.get("arquivo")
        if arquivo not in nomes_esperados:
            raise ErroGerarPortfolio(f"A IA devolveu classificação para um arquivo não enviado: '{arquivo}'")
        por_arquivo[arquivo] = item

    faltando = nomes_esperados - por_arquivo.keys()
    if faltando:
        raise ErroGerarPortfolio(f"A IA não classificou: {', '.join(sorted(faltando))}")

    return por_arquivo


def montar_sections(classificacoes: dict, caminhos: list[Path], slug: str) -> list[dict]:
    """Monta as sections[] a partir das classificações + caminho final das
    fotos (assets/portfolio/<slug>/<arquivo>)."""
    sections = []
    for caminho in caminhos:
        item = classificacoes[caminho.name]
        sections.append({
            "id": f"portfolio-{_slugify(caminho.stem)}",
            "type": "content",
            "title": item["titulo"],
            "subtitle": item["subtitulo"],
            "content": item["conteudo"],
            "image": f"assets/portfolio/{slug}/{caminho.name}",
            "enabled": True,
        })
    return sections


def copiar_fotos(caminhos: list[Path], slug: str) -> Path:
    """Copia os arquivos originais (resolução cheia) para
    assets/portfolio/<slug>/. Nunca sobrescreve/apaga nada fora dessa pasta."""
    destino = RAIZ / "assets" / "portfolio" / slug
    destino.mkdir(parents=True, exist_ok=True)
    for caminho in caminhos:
        shutil.copy2(caminho, destino / caminho.name)
    return destino


def mesclar_no_config(slug: str, sections_novas: list[dict], hero_arquivo: str | None = None) -> Path:
    """Carrega configs/<slug>.json, ACRESCENTA as sections novas às
    existentes e regrava. Não mexe em mais nenhum outro campo do config."""
    caminho_config = RAIZ / "configs" / f"{slug}.json"
    if not caminho_config.is_file():
        raise ErroGerarPortfolio(
            f"{caminho_config} não existe. Gere o site desse cliente primeiro "
            "(este script só acrescenta o portfólio, não cria site do zero)."
        )

    config = json.loads(caminho_config.read_text(encoding="utf-8"))
    config.setdefault("sections", []).extend(sections_novas)

    if hero_arquivo:
        config.setdefault("hero", {})["backgroundImage"] = f"assets/portfolio/{slug}/{hero_arquivo}"

    caminho_config.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho_config


def main():
    ap = argparse.ArgumentParser(
        description="Gera sections de portfólio a partir de fotos reais locais, classificando por conteúdo via IA com visão."
    )
    ap.add_argument("slug", help="slug do cliente (mesmo nome de configs/<slug>.json)")
    ap.add_argument("pasta_fotos", help="pasta local com as fotos reais do cliente")
    ap.add_argument("--nicho", default=None, help="nicho/ramo (default: 1ª keyword de configs/<slug>.json)")
    ap.add_argument("--contexto", default=None, help="contexto livre sobre as fotos, opcional")
    ap.add_argument("--hero", default=None, help="nome do arquivo (dentro da pasta) que vira hero.backgroundImage")
    args = ap.parse_args()

    caminho_config = RAIZ / "configs" / f"{args.slug}.json"
    if not caminho_config.is_file():
        print(f"Erro: {caminho_config} não existe. Gere o site desse cliente primeiro.", file=sys.stderr)
        sys.exit(1)

    config_atual = json.loads(caminho_config.read_text(encoding="utf-8"))
    keywords = config_atual.get("metadata", {}).get("keywords") or []
    nicho = args.nicho or (keywords[0] if keywords else "negócio local")
    nome_empresa = config_atual.get("company", {}).get("name", args.slug)

    pasta = Path(args.pasta_fotos)
    if not pasta.is_dir():
        print(f"Erro: pasta '{pasta}' não encontrada.", file=sys.stderr)
        sys.exit(1)

    caminhos = sorted(p for p in pasta.iterdir() if p.suffix.lower() in EXTS)
    if not caminhos:
        print(f"Erro: nenhuma foto (.jpg/.jpeg/.png/.webp) encontrada em '{pasta}'.", file=sys.stderr)
        sys.exit(1)

    if args.hero and args.hero not in {c.name for c in caminhos}:
        print(f"Erro: --hero '{args.hero}' não está entre os arquivos da pasta.", file=sys.stderr)
        sys.exit(1)

    print(f"{len(caminhos)} fotos encontradas em {pasta}. Classificando via IA (nicho: {nicho})...")
    try:
        classificacoes = classificar_fotos(nicho, nome_empresa, caminhos, args.contexto)
    except (ErroProvedorIA, ErroGerarPortfolio) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    sections_novas = montar_sections(classificacoes, caminhos, args.slug)
    destino = copiar_fotos(caminhos, args.slug)
    caminho_salvo = mesclar_no_config(args.slug, sections_novas, args.hero)

    tamanho_total_mb = sum(c.stat().st_size for c in caminhos) / 1024 / 1024
    print(f"\n{len(sections_novas)} sections de portfólio adicionadas a {caminho_salvo}")
    print(f"Fotos copiadas para {destino} ({tamanho_total_mb:.1f} MB no total)")
    print(f"\nPróximo passo: python backend/scripts/otimizar_imagens.py {args.slug}")


if __name__ == "__main__":
    main()
