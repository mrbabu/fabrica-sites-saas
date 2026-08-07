#!/usr/bin/env python3
"""
Quality Gate -- Definition of Professional Site (DoPS)
docs/definition-of-professional-site.md + docs/roadmap-implementacao-dops.md

MODO RELATÓRIO (Lote 1.C, Fase 0/1 do roadmap): lê um site-config.json já
gerado e reporta quais critérios AUTO passam ou falham. Não bloqueia, não
corrige, não altera o config recebido (R1 -- só observa). Ainda não é
chamado de dentro do pipeline de geração (agent_construtor.py) -- ligar
isso como gate bloqueante é Fase 3 do roadmap, e exige primeiro medir a
taxa de reprovação do corpus (Fase 0).

Critérios cobertos aqui: CNF-01, CNF-02, IMG-04, IMG-05.
"""

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import requests

from schema_validator import _placeholder_de_template, _primeira_duplicata


@dataclass
class ResultadoCriterio:
    """Resultado da checagem de um único critério da DoPS."""
    id: str
    passou: bool
    detalhe: str = ""


_REGEX_E164 = re.compile(r"\+?[1-9]\d{7,14}")
_REGEX_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _whatsapp_e164_valido(numero: Optional[str]) -> bool:
    if not numero:
        return False
    limpo = re.sub(r"[\s\-()]", "", numero)
    return bool(_REGEX_E164.fullmatch(limpo))


def _email_valido(email: Optional[str]) -> bool:
    # Campo opcional e nunca fabricado pela IA (ver _preencher_fallbacks em
    # agent_construtor.py) -- None é o estado esperado e válido.
    if email is None:
        return True
    return bool(_REGEX_EMAIL.fullmatch(email))


def validar_cnf01_contato(config: dict) -> ResultadoCriterio:
    """CNF-01: WhatsApp em E.164 válido, e-mail sintaticamente válido (ou ausente)."""
    contact = config.get("contact") or {}
    whatsapp = contact.get("whatsapp")
    email = contact.get("email")

    if not _whatsapp_e164_valido(whatsapp):
        return ResultadoCriterio("CNF-01", False, f"whatsapp inválido: {whatsapp!r}")
    if not _email_valido(email):
        return ResultadoCriterio("CNF-01", False, f"email inválido: {email!r}")
    return ResultadoCriterio("CNF-01", True)


def validar_cnf02_endereco(
    config: dict,
    localizacao_esperada: Optional[str],
    google_maps_url_esperado: Optional[str],
) -> ResultadoCriterio:
    """
    CNF-02: endereço/link de mapa idênticos ao capturado pelo Hunter (o
    parâmetro `localizacao`/`google_maps_url` original passado a
    gerar_config_site) -- nenhum dos dois pode ter sido reescrito ou
    completado pela IA em algum lugar do pipeline.
    """
    contact = config.get("contact") or {}
    address = contact.get("address")
    google_maps_url = contact.get("googleMapsUrl")

    if address != (localizacao_esperada or None):
        return ResultadoCriterio(
            "CNF-02", False,
            f"address diverge do input do Hunter: {address!r} != {(localizacao_esperada or None)!r}",
        )
    if google_maps_url != (google_maps_url_esperado or None):
        return ResultadoCriterio(
            "CNF-02", False,
            f"googleMapsUrl diverge do input do Hunter: {google_maps_url!r} != {(google_maps_url_esperado or None)!r}",
        )
    return ResultadoCriterio("CNF-02", True)


def _url_valida_formato(url: Optional[str]) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _http_head_padrao(url: str):
    return requests.head(url, timeout=5, allow_redirects=True)


def validar_img05_imagens_resolvem(
    config: dict,
    http_head: Optional[Callable[[str], object]] = None,
) -> ResultadoCriterio:
    """
    IMG-05: toda URL de imagem do config (hero + seções) resolve HTTP 200.
    `http_head` é injetável para teste -- por padrão faz um HEAD real.
    """
    http_head = http_head or _http_head_padrao

    urls = []
    hero = config.get("hero") or {}
    if hero.get("backgroundImage"):
        urls.append(hero["backgroundImage"])
    for secao in config.get("sections", []) or []:
        if secao.get("image"):
            urls.append(secao["image"])

    falhas = []
    for url in urls:
        if not _url_valida_formato(url):
            falhas.append(f"{url}: formato de URL inválido")
            continue
        try:
            resposta = http_head(url)
            if resposta.status_code != 200:
                falhas.append(f"{url}: HTTP {resposta.status_code}")
        except Exception as e:
            falhas.append(f"{url}: erro de rede ({e})")

    if falhas:
        return ResultadoCriterio("IMG-05", False, "; ".join(falhas))
    return ResultadoCriterio("IMG-05", True, f"{len(urls)} imagem(ns) verificada(s)")


def _obter_dimensao_imagem_real(url: str) -> tuple:
    """
    Lê só o cabeçalho do arquivo via streaming (não baixa a imagem inteira)
    -- suficiente pra Pillow inferir as dimensões na maioria dos formatos
    (JPEG/PNG/WebP), que é tudo que o Image Engine e o LoremFlickr entregam.
    """
    from PIL import Image
    import io

    resposta = requests.get(url, timeout=10, stream=True)
    resposta.raise_for_status()
    trecho = resposta.raw.read(65536, decode_content=True)
    with Image.open(io.BytesIO(trecho)) as img:
        return img.size


def validar_img04_hero_dimensao(
    config: dict,
    largura_minima: int = 1920,
    razao_minima: float = 16 / 9,
    obter_dimensao: Optional[Callable[[str], tuple]] = None,
) -> ResultadoCriterio:
    """IMG-04: hero.backgroundImage com largura >= 1920px e proporção >= 16:9."""
    hero = config.get("hero") or {}
    url = hero.get("backgroundImage")
    if not url:
        return ResultadoCriterio("IMG-04", False, "hero.backgroundImage ausente")

    obter_dimensao = obter_dimensao or _obter_dimensao_imagem_real

    try:
        largura, altura = obter_dimensao(url)
    except Exception as e:
        return ResultadoCriterio("IMG-04", False, f"não foi possível ler dimensão: {e}")

    if largura < largura_minima:
        return ResultadoCriterio("IMG-04", False, f"largura {largura}px < mínimo {largura_minima}px")

    razao = largura / altura if altura else 0
    if razao < razao_minima:
        return ResultadoCriterio("IMG-04", False, f"proporção {razao:.2f} < mínimo {razao_minima:.2f}")

    return ResultadoCriterio("IMG-04", True, f"{largura}x{altura}")


def validar_img02_hero_nao_repete(config: dict) -> ResultadoCriterio:
    """IMG-02: hero.backgroundImage não repete em nenhum sections[].image."""
    hero_url = (config.get("hero") or {}).get("backgroundImage")
    if not hero_url:
        return ResultadoCriterio("IMG-02", True, "hero.backgroundImage ausente (nada a comparar)")

    repetida_em = [
        secao.get("id") for secao in config.get("sections", []) or []
        if secao.get("image") == hero_url
    ]
    if repetida_em:
        return ResultadoCriterio("IMG-02", False, f"hero.backgroundImage repete em sections{repetida_em}")
    return ResultadoCriterio("IMG-02", True)


def validar_vis03_icones_repetidos(config: dict) -> ResultadoCriterio:
    """
    VIS-03: nenhum ícone repetido dentro de services[] nem dentro de
    features[] -- mesma regra de unicidade que agent_construtor._autocorrigir
    já aplica (via _resolver_icone), não apenas cards adjacentes como a
    prosa da DoPS sugere; grupos são deduplicados separadamente (repetir o
    mesmo ícone entre services e features não conta como falha).
    """
    falhas = []
    for grupo, itens in (("services", config.get("services") or []), ("features", config.get("features") or [])):
        vistos: dict = {}
        for item in itens:
            icon = item.get("icon")
            if not icon:
                continue
            if icon in vistos:
                falhas.append(f"{grupo}: ícone {icon!r} repetido (ids {vistos[icon]!r} e {item.get('id')!r})")
            else:
                vistos[icon] = item.get("id")
    if falhas:
        return ResultadoCriterio("VIS-03", False, "; ".join(falhas))
    return ResultadoCriterio("VIS-03", True)


def validar_txt01_duplicacao(config: dict) -> ResultadoCriterio:
    """
    TXT-01: reusa o algoritmo de dedupe (_primeira_duplicata, importado de
    schema_validator.py) -- só a enumeração de campos é reconstruída aqui,
    espelhando exatamente os 3 grupos que _validar_regras_conteudo já checa
    (títulos, textos longos, perguntas de FAQ). Não reimplementa o
    algoritmo de similaridade nem altera schema_validator.py/o pipeline
    bloqueante existente.
    """
    sections = config.get("sections") or []
    services = config.get("services") or []
    features = config.get("features") or []
    faq = config.get("faq") or []

    titulos = (
        [(f"sections[{s.get('id')}].title", s.get("title")) for s in sections]
        + [(f"services[{s.get('id')}].title", s.get("title")) for s in services]
        + [(f"features[{f.get('id')}].title", f.get("title")) for f in features]
    )
    erro = _primeira_duplicata("Título", titulos)
    if erro:
        return ResultadoCriterio("TXT-01", False, erro)

    textos_longos = (
        [(f"sections[{s.get('id')}].content", s.get("content")) for s in sections]
        + [(f"services[{s.get('id')}].description", s.get("description")) for s in services]
        + [(f"features[{f.get('id')}].description", f.get("description")) for f in features]
    )
    erro = _primeira_duplicata("Texto", textos_longos)
    if erro:
        return ResultadoCriterio("TXT-01", False, erro)

    perguntas = [(f"faq[{f.get('id')}].question", f.get("question")) for f in faq]
    erro = _primeira_duplicata("Pergunta de FAQ", perguntas)
    if erro:
        return ResultadoCriterio("TXT-01", False, erro)

    return ResultadoCriterio("TXT-01", True)


def validar_txt04_template(config: dict) -> ResultadoCriterio:
    """
    TXT-04: reusa _placeholder_de_template (importado de schema_validator.py)
    -- a lista de campos checados espelha exatamente _validar_regras_conteudo,
    mesmo racional do TXT-01 acima.
    """
    company = config.get("company") or {}
    hero = config.get("hero") or {}
    metadata = config.get("metadata") or {}
    cta = config.get("cta") or {}
    sections = config.get("sections") or []
    services = config.get("services") or []
    features = config.get("features") or []

    campos = [
        ("metadata.siteTitle", metadata.get("siteTitle")),
        ("metadata.siteDescription", metadata.get("siteDescription")),
        ("company.name", company.get("name")),
        ("company.tagline", company.get("tagline")),
        ("company.description", company.get("description")),
        ("hero.title", hero.get("title")),
        ("hero.subtitle", hero.get("subtitle")),
        ("hero.ctaText", hero.get("ctaText")),
        ("cta.title", cta.get("title")),
        ("cta.description", cta.get("description")),
        ("cta.buttonText", cta.get("buttonText")),
    ]
    for secao in sections:
        campos.append((f"sections[{secao.get('id')}].title", secao.get("title")))
        campos.append((f"sections[{secao.get('id')}].subtitle", secao.get("subtitle")))
        campos.append((f"sections[{secao.get('id')}].content", secao.get("content")))
    for servico in services:
        campos.append((f"services[{servico.get('id')}].title", servico.get("title")))
        campos.append((f"services[{servico.get('id')}].description", servico.get("description")))
        for i, feat in enumerate(servico.get("features") or []):
            campos.append((f"services[{servico.get('id')}].features[{i}]", feat))
    for diferencial in features:
        campos.append((f"features[{diferencial.get('id')}].title", diferencial.get("title")))
        campos.append((f"features[{diferencial.get('id')}].description", diferencial.get("description")))

    for identificador, texto in campos:
        placeholder = _placeholder_de_template(texto)
        if placeholder:
            return ResultadoCriterio("TXT-04", False, f"Texto de template vazou em {identificador}: '{placeholder}'")

    return ResultadoCriterio("TXT-04", True)


# LAY-05 ("hero + ao menos 3 blocos de conteúdo real") está marcado AUTO na
# DoPS (docs/definition-of-professional-site.md) mas NÃO tem nenhuma
# implementação correspondente no código -- schema_validator.py não impõe
# min_items em `sections`, e não existe checagem equivalente em nenhum
# lugar do pipeline. Divergência documental real entre a DoPS e o código,
# encontrada na tarefa de extensão deste arquivo (2026-08-06) -- não
# implementada aqui por decisão explícita: não inventar a regra por
# dedução, só documentar a lacuna pra alguém decidir o critério exato
# antes de codificar.


# Severidade por critério, conforme docs/definition-of-professional-site.md
# -- usada só pra agregação do relatório (seção "Por severidade"/Top 10),
# não afeta se um critério passa ou falha.
SEVERIDADE_POR_CRITERIO = {
    "CNF-01": "P0",
    "CNF-02": "P0",
    "IMG-02": "P0",
    "IMG-04": "P2",
    "IMG-05": "P1",
    "TXT-01": "P0",
    "TXT-04": "P0",
    "VIS-03": "P2",
}


def _severidade(criterio_id: str) -> str:
    return SEVERIDADE_POR_CRITERIO.get(criterio_id, "?")


def rodar_gate_completo(
    config: dict,
    http_head: Optional[Callable[[str], object]] = None,
    obter_dimensao: Optional[Callable[[str], tuple]] = None,
) -> list:
    """
    Roda todos os critérios que dependem só do próprio site-config.json --
    por isso NÃO inclui CNF-02, que exige o valor original capturado pelo
    Hunter/DFY (localizacao_esperada/google_maps_url_esperado), dado que não
    existe num corpus solto de configs já gerados. Usado pelo modo CLI
    (--input, sem overrides -- faz rede real de propósito); rodar_gate_relatorio
    continua a função usada pelo caller que já tem o dado do Hunter
    disponível, sem mudança de comportamento. `http_head`/`obter_dimensao`
    injetáveis pro mesmo motivo de rodar_gate_relatorio -- testes não fazem
    rede real.
    """
    return [
        validar_cnf01_contato(config),
        validar_img02_hero_nao_repete(config),
        validar_img04_hero_dimensao(config, obter_dimensao=obter_dimensao),
        validar_img05_imagens_resolvem(config, http_head=http_head),
        validar_txt01_duplicacao(config),
        validar_txt04_template(config),
        validar_vis03_icones_repetidos(config),
    ]


def rodar_gate_relatorio(
    config: dict,
    localizacao_esperada: Optional[str] = None,
    google_maps_url_esperado: Optional[str] = None,
    http_head: Optional[Callable[[str], object]] = None,
    obter_dimensao: Optional[Callable[[str], tuple]] = None,
) -> list:
    """
    Roda os 4 critérios do Lote 1.C e devolve a lista de ResultadoCriterio.
    Modo relatório: nunca lança exceção por reprovação, nunca altera `config`.
    """
    return [
        validar_cnf01_contato(config),
        validar_cnf02_endereco(config, localizacao_esperada, google_maps_url_esperado),
        validar_img04_hero_dimensao(config, obter_dimensao=obter_dimensao),
        validar_img05_imagens_resolvem(config, http_head=http_head),
    ]


# ============================================================================
# CLI (--input <diretório>) -- audita um corpus de site-config.json e gera
# quality_report.json + quality_report.md. Não assume localização padrão de
# corpus (nem configs/ nem nenhuma outra) -- quem chama decide o diretório.
# ============================================================================

def _carregar_configs(pasta: Path) -> list:
    """
    Carrega todo *.json de `pasta` (não recursivo) como [(nome_arquivo, dict)].
    Arquivo que não é JSON válido ou não pôde ser lido entra como
    (nome_arquivo, None) -- quem chama decide como reportar isso, em vez de
    a leitura derrubar o processo inteiro no meio de um corpus grande.
    """
    resultados = []
    for caminho in sorted(pasta.glob("*.json")):
        try:
            resultados.append((caminho.name, json.loads(caminho.read_text(encoding="utf-8"))))
        except (json.JSONDecodeError, OSError):
            resultados.append((caminho.name, None))
    return resultados


def _gerar_relatorio(resultados_por_arquivo: dict) -> dict:
    """Agrega os ResultadoCriterio de todos os arquivos num relatório único
    (resumo por severidade, contagem por critério/site, incidência, ranking,
    top 10) -- puro, sem I/O, testável isoladamente."""
    resumo_severidade = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    contagem_por_criterio: dict = {}
    contagem_por_site: dict = {}
    total_falhas = 0

    for nome_arquivo, resultados in resultados_por_arquivo.items():
        falhas_do_site = [r for r in resultados if not r.passou]
        contagem_por_site[nome_arquivo] = len(falhas_do_site)
        for r in falhas_do_site:
            total_falhas += 1
            sev = _severidade(r.id)
            resumo_severidade[sev] = resumo_severidade.get(sev, 0) + 1
            contagem_por_criterio[r.id] = contagem_por_criterio.get(r.id, 0) + 1

    total_sites = len(resultados_por_arquivo)
    incidencia_por_criterio = {
        criterio: {
            "ocorrencias": qtd,
            "sites_afetados_pct": round(100 * qtd / total_sites, 1) if total_sites else 0.0,
        }
        for criterio, qtd in contagem_por_criterio.items()
    }
    ranking = sorted(contagem_por_criterio.items(), key=lambda par: par[1], reverse=True)

    return {
        "resumo": {
            "total_sites": total_sites,
            "total_falhas": total_falhas,
            "por_severidade": resumo_severidade,
        },
        "quantidade_por_criterio": contagem_por_criterio,
        "quantidade_por_site": contagem_por_site,
        "incidencia_por_criterio": incidencia_por_criterio,
        "ranking": [{"criterio": c, "ocorrencias": q} for c, q in ranking],
        "top10_problemas": [
            {"criterio": c, "ocorrencias": q, "severidade": _severidade(c)}
            for c, q in ranking[:10]
        ],
        "detalhe_por_site": {
            nome: [
                {"criterio": r.id, "passou": r.passou, "detalhe": r.detalhe, "severidade": _severidade(r.id)}
                for r in resultados
            ]
            for nome, resultados in resultados_por_arquivo.items()
        },
    }


def _relatorio_para_markdown(relatorio: dict) -> str:
    """Versão legível do mesmo relatório -- mesmos números de _gerar_relatorio, sem cálculo próprio."""
    resumo = relatorio["resumo"]
    linhas = [
        "# Quality Gate -- Relatório\n",
        f"**Sites analisados:** {resumo['total_sites']}  ",
        f"**Falhas totais:** {resumo['total_falhas']}\n",
        "## Por severidade\n",
    ]
    for sev in ("P0", "P1", "P2", "P3"):
        linhas.append(f"- **{sev}:** {resumo['por_severidade'].get(sev, 0)}")

    linhas.append("\n## Top 10 problemas\n")
    linhas.append("| Critério | Ocorrências | Severidade |")
    linhas.append("|---|---|---|")
    for item in relatorio["top10_problemas"]:
        linhas.append(f"| {item['criterio']} | {item['ocorrencias']} | {item['severidade']} |")

    linhas.append("\n## Quantidade de falhas por site\n")
    linhas.append("| Site | Falhas |")
    linhas.append("|---|---|")
    for site, qtd in sorted(relatorio["quantidade_por_site"].items(), key=lambda par: par[1], reverse=True):
        linhas.append(f"| {site} | {qtd} |")

    return "\n".join(linhas) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Quality Gate DoPS -- audita um diretório de site-config.json em modo relatório (nunca altera os arquivos lidos)."
    )
    parser.add_argument("--input", required=True, help="Diretório com arquivos *.json a auditar (obrigatório, sem padrão assumido)")
    parser.add_argument("--out-json", default="quality_report.json", help="Caminho de saída do relatório JSON")
    parser.add_argument("--out-md", default="quality_report.md", help="Caminho de saída do relatório Markdown")
    args = parser.parse_args()

    pasta = Path(args.input)
    if not pasta.is_dir():
        print(f"Erro: '{pasta}' não é um diretório válido.")
        raise SystemExit(1)

    arquivos = _carregar_configs(pasta)
    if not arquivos:
        print(f"Nenhum arquivo .json encontrado em '{pasta}'.")
        raise SystemExit(1)

    resultados_por_arquivo = {}
    for nome, dados in arquivos:
        if dados is None:
            resultados_por_arquivo[nome] = [ResultadoCriterio("LEITURA", False, "arquivo não é JSON válido")]
            continue
        resultados_por_arquivo[nome] = rodar_gate_completo(dados)

    relatorio = _gerar_relatorio(resultados_por_arquivo)

    Path(args.out_json).write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.out_md).write_text(_relatorio_para_markdown(relatorio), encoding="utf-8")

    print(f"Analisados {relatorio['resumo']['total_sites']} sites, {relatorio['resumo']['total_falhas']} falhas.")
    print(f"CNF-02 não incluído neste modo (exige dado do Hunter não presente num corpus solto).")
    print(f"Relatório salvo em {args.out_json} e {args.out_md}")


if __name__ == "__main__":
    main()
