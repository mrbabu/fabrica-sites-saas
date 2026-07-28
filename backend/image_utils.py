#!/usr/bin/env python3
"""
Utilitários de Imagem - Fábrica de Sites SaaS
Normaliza logos recebidos no onboarding (via URL) para um formato padrão,
pronto para ser injetado no site-config.json do cliente, e mapeia o nicho
(texto livre) para um banco de imagens curado por categoria (Unsplash),
usado como fallback quando o cliente não manda foto própria.
"""

import io
import json
import logging
import os
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple, Optional

import requests
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("FabricaSitesAPI.image_utils")

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    _RESAMPLE = Image.LANCZOS

# assets/logos vive na raiz do repo (é servido pelo frontend estático junto
# com o index.html), não dentro de backend/ — por isso sobe um nível a partir
# deste arquivo em vez de usar Path(__file__).parent diretamente.
PASTA_LOGOS = Path(__file__).parent.parent / "assets" / "logos"
TAMANHO_PADRAO = (512, 512)


class ErroNormalizacaoLogo(Exception):
    """Erro ao baixar ou normalizar um logo"""


class ErroBancoImagens(Exception):
    """Erro ao buscar ou cachear imagens curadas por categoria (Unsplash) —
    quem chama decide o fallback, nunca propaga pra quebrar a geração do site."""


class ErroBaseNichos(Exception):
    """Erro ao carregar/validar backend/data/niches.json — falha rápido e
    com mensagem precisa (categoria/campo exatos) em vez de deixar a
    categorização quebrar silenciosamente em produção."""


# ============================================================================
# BANCO DE IMAGENS CURADO POR NICHO (Unsplash)
# ============================================================================
# Todo o conhecimento de nichos (categorias, aliases, pesos, queries em
# inglês, atributos e termos proibidos) vive fora do código, em
# backend/data/niches.json — editar esse arquivo NUNCA exige tocar aqui.
# Arquitetura em 3 camadas, do mais específico pro mais genérico — sempre
# determinística, sem chamada de IA/tradução (custo zero, latência zero,
# nenhum novo ponto de falha por site gerado):
#
#   1. tier "specific"  — dezenas de categorias de nicho específicas (saúde,
#      alimentação, eventos, esporte, etc.), cada uma com uma lista de
#      aliases/sinônimos/variações com peso próprio. Primeira tentativa,
#      sempre. Uma categoria específica pode ter "attributes" — variantes
#      (ex.: "infantil"/"corporativo" em events_venue) que, se um keyword
#      do atributo bater no nicho, geram uma chave composta
#      "categoria__atributo" com sua própria query em inglês.
#   2. tier "generic"   — só entra em jogo se NADA em (1) bateu. Sinais
#      fracos e genéricos ("loja", "escritório", "fábrica"...) que ao menos
#      aproximam o tipo de ambiente quando o nicho é atípico demais pra ter
#      categoria própria.
#   3. tier "default"   — último recurso, só quando nem (1) nem (2)
#      bateram. Deve disparar raramente; quando disparar, vira um WARNING
#      no log (ver mapear_categoria) e incrementa um contador em
#      backend/cache/nichos_desconhecidos.json, sinalizando que vale a pena
#      cadastrar uma categoria/alias novo para aquele nicho.
#
# Como estender: adicionar um alias numa lista existente cobre uma variação
# de um nicho já suportado; criar uma nova entrada em "categories" cobre um
# nicho totalmente novo — em ambos os casos, incluir "base_queries".
#
# Regra de casamento (ver _bate_alias): alias com espaço = frase, testada
# como substring do nicho normalizado inteiro (baixo risco de colisão,
# frases são específicas). Alias de uma palavra só = testado como PREFIXO
# de cada palavra do nicho (não substring solta) — isso é o que permite
# aceitar plural/gênero/variação ("juridic" bate "jurídica" e "jurídico",
# "veterinari" bate "veterinária" e "veterinário") sem também bater no meio
# de palavras não relacionadas (ex.: "spa" não bate dentro de "espaço").
#
# Desempate por especificidade: cada categoria recebe um score = soma do
# peso (campo "weight" em niches.json) dos aliases que bateram. Empate
# exato usa a ordem de definição no arquivo JSON.
#
# v2 (schema version=2): uma categoria pode casar com MAIS DE UM atributo ao
# mesmo tempo (ex.: "Buffet Infantil Premium" -> events_venue__infantil__premium),
# ordenados por score decrescente. Atributos podem ser definidos por
# categoria ("attributes", como antes) ou reaproveitados de um banco
# compartilhado ("global_attributes" no topo do arquivo + a categoria lista
# os nomes que quer usar em seu próprio campo "global_attributes") — assim
# "premium"/"corporativo" não precisam ser redigitados em cada categoria que
# faz sentido. "global_forbidden" (topo do arquivo) é uma lista de termos
# universalmente penalizados no ranking, além do "forbidden" próprio de cada
# categoria — usar só para termos que NUNCA são desejáveis em nenhum nicho
# (ex.: "generic office"), nunca termos como "storefront" que são desejados
# em algumas categorias (padaria, loja de roupas) e indesejados em outras.
CAMINHO_NICHOS = Path(__file__).parent / "data" / "niches.json"
VERSAO_SUPORTADA = 2
CATEGORIA_PADRAO = "default_business"

TIERS_VALIDOS = {"specific", "generic", "default"}
CAMPOS_OBRIGATORIOS_CATEGORIA = ("tier", "aliases", "base_queries")
REGEX_COR_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
COR_PRIMARIA_PADRAO = "#0D9488"  # usada quando a categoria não define primary_color (compatibilidade)


def _validar_definicao_atributo(dado_attr: object, prefixo_attr: str) -> None:
    if not isinstance(dado_attr, dict):
        raise ErroBaseNichos(f"{prefixo_attr}: definição deve ser um objeto")
    keywords = dado_attr.get("keywords")
    if not isinstance(keywords, list) or not keywords:
        raise ErroBaseNichos(f"{prefixo_attr}: campo 'keywords' ausente ou vazio")
    queries = dado_attr.get("queries")
    if not isinstance(queries, list) or not queries or not all(isinstance(q, str) and q.strip() for q in queries):
        raise ErroBaseNichos(f"{prefixo_attr}: campo 'queries' ausente ou vazio")


def _hook_detectar_duplicatas(pares: list[tuple[str, object]]) -> dict:
    """object_pairs_hook do json.loads: json.loads normal descarta chaves
    duplicadas silenciosamente (fica só a última). Aqui, qualquer objeto do
    arquivo (categoria duplicada, alias duplicado como chave, etc.) com
    chave repetida vira erro explícito na carga."""
    vistas = set()
    resultado = {}
    for chave, valor in pares:
        if chave in vistas:
            raise ErroBaseNichos(f"{CAMINHO_NICHOS.name}: chave duplicada '{chave}'")
        vistas.add(chave)
        resultado[chave] = valor
    return resultado


def _validar_base_nichos(dados: dict) -> None:
    if "version" not in dados:
        raise ErroBaseNichos(f"{CAMINHO_NICHOS.name}: campo obrigatório 'version' ausente")
    if dados["version"] != VERSAO_SUPORTADA:
        raise ErroBaseNichos(
            f"{CAMINHO_NICHOS.name}: version={dados['version']!r} incompatível com este "
            f"código (esperado {VERSAO_SUPORTADA}). Atualize o loader em image_utils.py "
            f"ou corrija o campo 'version' do arquivo."
        )
    if "categories" not in dados or not isinstance(dados["categories"], dict):
        raise ErroBaseNichos(f"{CAMINHO_NICHOS.name}: campo obrigatório 'categories' ausente ou inválido")

    categorias = dados["categories"]
    if CATEGORIA_PADRAO not in categorias:
        raise ErroBaseNichos(
            f"{CAMINHO_NICHOS.name}: categoria padrão '{CATEGORIA_PADRAO}' é obrigatória e está ausente"
        )

    global_attributes = dados.get("global_attributes", {})
    if not isinstance(global_attributes, dict):
        raise ErroBaseNichos(f"{CAMINHO_NICHOS.name}: campo 'global_attributes' deve ser um objeto")
    for nome_attr, dado_attr in global_attributes.items():
        _validar_definicao_atributo(dado_attr, f"{CAMINHO_NICHOS.name} / global_attributes / '{nome_attr}'")

    if "global_synonyms" in dados and not isinstance(dados["global_synonyms"], dict):
        raise ErroBaseNichos(f"{CAMINHO_NICHOS.name}: campo 'global_synonyms' deve ser um objeto")

    global_forbidden = dados.get("global_forbidden", [])
    if not isinstance(global_forbidden, list) or not all(isinstance(f, str) for f in global_forbidden):
        raise ErroBaseNichos(f"{CAMINHO_NICHOS.name}: campo 'global_forbidden' deve ser uma lista de strings")

    for nome, dado in categorias.items():
        prefixo = f"Erro carregando {CAMINHO_NICHOS.name} / Categoria '{nome}'"

        if not isinstance(dado, dict):
            raise ErroBaseNichos(f"{prefixo}: definição da categoria deve ser um objeto")

        for campo in CAMPOS_OBRIGATORIOS_CATEGORIA:
            if campo not in dado:
                raise ErroBaseNichos(f"{prefixo}: campo obrigatório '{campo}' ausente")

        tier = dado["tier"]
        if tier not in TIERS_VALIDOS:
            raise ErroBaseNichos(f"{prefixo}: tier '{tier}' inválido (use um de {sorted(TIERS_VALIDOS)})")

        aliases = dado["aliases"]
        if not isinstance(aliases, list):
            raise ErroBaseNichos(f"{prefixo}: campo 'aliases' deve ser uma lista")
        if tier != "default" and not aliases:
            raise ErroBaseNichos(f"{prefixo}: tier '{tier}' exige ao menos 1 alias")

        textos_vistos = set()
        for alias in aliases:
            if not isinstance(alias, dict) or "text" not in alias or "weight" not in alias:
                raise ErroBaseNichos(f"{prefixo}: alias {alias!r} precisa dos campos 'text' e 'weight'")
            texto = alias["text"]
            if texto in textos_vistos:
                raise ErroBaseNichos(f"{prefixo}: alias duplicado '{texto}'")
            textos_vistos.add(texto)
            if not isinstance(alias["weight"], int) or alias["weight"] <= 0:
                raise ErroBaseNichos(f"{prefixo}: alias '{texto}' tem weight inválido ({alias['weight']!r})")

        base_queries = dado["base_queries"]
        if (
            not isinstance(base_queries, list)
            or not base_queries
            or not all(isinstance(q, str) and q.strip() for q in base_queries)
        ):
            raise ErroBaseNichos(f"{prefixo}: campo 'base_queries' deve ser uma lista não vazia de strings não vazias")

        # Opcional (compatibilidade com categorias antigas sem cor definida —
        # obter_cor_primaria() cai pra COR_PRIMARIA_PADRAO nesse caso), mas
        # formato estrito quando presente, mesmo rigor dos outros campos.
        if "primary_color" in dado and not REGEX_COR_HEX.match(dado["primary_color"] or ""):
            raise ErroBaseNichos(
                f"{prefixo}: campo 'primary_color' deve estar em formato hex válido "
                f"#RRGGBB (recebido {dado['primary_color']!r})"
            )

        nomes_atributos_inline = set()
        if "attributes" in dado:
            atributos = dado["attributes"]
            if not isinstance(atributos, dict):
                raise ErroBaseNichos(f"{prefixo}: campo 'attributes' deve ser um objeto")
            for nome_attr, dado_attr in atributos.items():
                _validar_definicao_atributo(dado_attr, f"{prefixo} / Atributo '{nome_attr}'")
            nomes_atributos_inline = set(atributos)

        if "global_attributes" in dado:
            refs = dado["global_attributes"]
            if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
                raise ErroBaseNichos(f"{prefixo}: campo 'global_attributes' deve ser uma lista de nomes (strings)")
            for nome_ref in refs:
                if nome_ref not in global_attributes:
                    raise ErroBaseNichos(
                        f"{prefixo}: 'global_attributes' referencia '{nome_ref}', que não existe em "
                        f"global_attributes no topo do arquivo"
                    )
                if nome_ref in nomes_atributos_inline:
                    raise ErroBaseNichos(
                        f"{prefixo}: atributo '{nome_ref}' definido tanto em 'attributes' quanto "
                        f"referenciado em 'global_attributes' — ambíguo, escolha um"
                    )

        if "concepts" in dado and not isinstance(dado["concepts"], list):
            raise ErroBaseNichos(f"{prefixo}: campo 'concepts' deve ser uma lista")

        if "forbidden" in dado and not isinstance(dado["forbidden"], list):
            raise ErroBaseNichos(f"{prefixo}: campo 'forbidden' deve ser uma lista")

    if categorias[CATEGORIA_PADRAO]["tier"] != "default":
        raise ErroBaseNichos(f"Erro carregando {CAMINHO_NICHOS.name} / Categoria '{CATEGORIA_PADRAO}': precisa ter tier='default'")


def _carregar_base_nichos() -> dict:
    if not CAMINHO_NICHOS.exists():
        raise ErroBaseNichos(f"Arquivo de base de nichos não encontrado: {CAMINHO_NICHOS}")
    texto = CAMINHO_NICHOS.read_text(encoding="utf-8")
    try:
        dados = json.loads(texto, object_pairs_hook=_hook_detectar_duplicatas)
    except json.JSONDecodeError as e:
        raise ErroBaseNichos(f"Erro carregando {CAMINHO_NICHOS.name}: JSON inválido — {e}") from e
    _validar_base_nichos(dados)
    return dados


def _construir_estruturas(dados: dict) -> dict:
    categorias = dados["categories"]
    global_attributes = dados.get("global_attributes", {})
    global_forbidden = dados.get("global_forbidden", [])

    categorias_aliases: dict[str, list[tuple[str, int]]] = {}
    sinais_genericos: dict[str, list[tuple[str, int]]] = {}
    query_por_categoria: dict[str, str] = {}
    atributos_por_categoria: dict[str, dict[str, list[tuple[str, int]]]] = {}
    atributos_query: dict[str, dict[str, str]] = {}
    concepts_por_categoria: dict[str, list[str]] = {}
    forbidden_por_categoria: dict[str, list[str]] = {}
    categorias_dados: dict[str, dict] = {}
    cor_por_categoria: dict[str, str] = {}

    for nome, dado in categorias.items():
        pares_aliases = [(a["text"], a["weight"]) for a in dado["aliases"]]
        tier = dado["tier"]
        if tier == "specific":
            categorias_aliases[nome] = pares_aliases
        elif tier == "generic":
            sinais_genericos[nome] = pares_aliases

        base_query = dado["base_queries"][0]
        concepts = dado.get("concepts", [])
        query_por_categoria[nome] = base_query
        concepts_por_categoria[nome] = concepts
        forbidden_por_categoria[nome] = dado.get("forbidden", [])
        categorias_dados[nome] = {"base_query": base_query, "concepts": concepts}
        if "primary_color" in dado:
            cor_por_categoria[nome] = dado["primary_color"]

        # Une atributos definidos inline na categoria com os referenciados do
        # banco compartilhado (global_attributes) — validado previamente que
        # não há colisão de nome entre os dois.
        definicoes_attr = dict(dado.get("attributes", {}))
        for nome_ref in dado.get("global_attributes", []):
            definicoes_attr[nome_ref] = global_attributes[nome_ref]

        if definicoes_attr:
            atributos_por_categoria[nome] = {
                nome_attr: [(kw, len(kw)) for kw in dado_attr["keywords"]]
                for nome_attr, dado_attr in definicoes_attr.items()
            }
            atributos_query[nome] = {
                nome_attr: dado_attr["queries"][0] for nome_attr, dado_attr in definicoes_attr.items()
            }

    return {
        "categorias_aliases": categorias_aliases,
        "sinais_genericos": sinais_genericos,
        "query_por_categoria": query_por_categoria,
        "atributos_por_categoria": atributos_por_categoria,
        "atributos_query": atributos_query,
        "concepts_por_categoria": concepts_por_categoria,
        "forbidden_por_categoria": forbidden_por_categoria,
        "categorias_dados": categorias_dados,
        "global_forbidden": global_forbidden,
        "cor_por_categoria": cor_por_categoria,
    }


_DADOS_NICHOS = _carregar_base_nichos()
_ESTRUTURAS = _construir_estruturas(_DADOS_NICHOS)

# Visões derivadas, mantidas por compatibilidade com quem já importa estes
# nomes (ex.: backend/test_image_utils.py) — o dado-fonte é sempre o JSON.
CATEGORIAS_ALIASES: dict[str, list[str]] = {
    nome: [texto for texto, _ in pares] for nome, pares in _ESTRUTURAS["categorias_aliases"].items()
}
SINAIS_GENERICOS: dict[str, list[str]] = {
    nome: [texto for texto, _ in pares] for nome, pares in _ESTRUTURAS["sinais_genericos"].items()
}
QUERY_POR_CATEGORIA: dict[str, str] = _ESTRUTURAS["query_por_categoria"]

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
QTD_IMAGENS_POR_CATEGORIA = 10
QTD_CANDIDATOS_BUSCA = 24  # candidatos brutos por chamada — o ranking escolhe os melhores QTD_IMAGENS_POR_CATEGORIA

# Pesos do ranking determinístico de imagens (ver _rankear_imagens). Usa só
# metadados que o Unsplash já retorna na mesma chamada paga — nunca um
# "score de visão computacional" inventado.
PESO_TEXTO = 20
PESO_ATRIBUTO = 12
PESO_LIKES = 30
PESO_RESOLUCAO = 20
PENALIDADE_FORBIDDEN = 25
TETO_LIKES = 500
TETO_PIXELS = 4000 * 3000

# Meta de saúde do banco de conhecimento: taxa de nichos que caem no fallback
# padrão (CATEGORIA_PADRAO) sobre o total de categorizações. Acima disso,
# vale a pena olhar categorias_desconhecidas em stats.json e cadastrar
# aliases novos — ver gerar_estatisticas().
META_TAXA_FALLBACK = 0.02

# backend/cache/ — estado gerado em runtime, não código-fonte (gitignored).
# stats.json/unknown_categories.jsonl ficam aqui (não em backend/data/, que é
# reservado para conhecimento cadastrado à mão e versionado no Git).
PASTA_CACHE = Path(__file__).parent / "cache"
CAMINHO_CACHE_IMAGENS = PASTA_CACHE / "imagens_categorias.json"
CAMINHO_TELEMETRIA = PASTA_CACHE / "telemetria_imagens.jsonl"
CAMINHO_NICHOS_DESCONHECIDOS = PASTA_CACHE / "unknown_categories.jsonl"
CAMINHO_STATS = PASTA_CACHE / "stats.json"


def _normalizar_texto(texto: str) -> str:
    """Remove acentos e pontuação, minúsculo — usado só para o casamento de categoria"""
    texto_normalizado = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", " ", texto_normalizado).strip().lower()


def _bate_alias(texto: str, palavras: list[str], alias: str) -> bool:
    """Frase (com espaço) = substring do texto inteiro. Palavra única =
    prefixo de alguma palavra do texto (aceita plural/gênero sem bater no
    meio de palavras não relacionadas, ver comentário da seção acima)."""
    if " " in alias:
        return alias in texto
    return any(palavra.startswith(alias) for palavra in palavras)


class _Match(NamedTuple):
    categoria: Optional[str]
    score: int
    aliases_batidos: list[str]


def _melhor_categoria(texto: str, palavras: list[str], banco: dict[str, list[tuple[str, int]]]) -> _Match:
    melhor = _Match(None, 0, [])
    for categoria, pares in banco.items():
        batidos = [(txt, peso) for txt, peso in pares if _bate_alias(texto, palavras, txt)]
        if not batidos:
            continue
        score = sum(peso for _, peso in batidos)
        if score > melhor.score:
            melhor = _Match(categoria, score, [txt for txt, _ in batidos])
    return melhor


def _atributos_batidos(texto: str, palavras: list[str], categoria: str) -> list[str]:
    """Retorna TODOS os nomes de atributo cujo keyword bateu no nicho (não só
    o melhor) — ordenados por score decrescente (empate preserva a ordem de
    definição no JSON, já que sorted() é estável). É isso que permite chaves
    compostas com mais de um atributo, ex.: "events_venue__infantil__premium"."""
    banco = _ESTRUTURAS["atributos_por_categoria"].get(categoria)
    if not banco:
        return []
    batidos = []
    for nome_attr, pares in banco.items():
        match = [(txt, peso) for txt, peso in pares if _bate_alias(texto, palavras, txt)]
        if match:
            batidos.append((nome_attr, sum(peso for _, peso in match)))
    batidos.sort(key=lambda par: par[1], reverse=True)
    return [nome for nome, _ in batidos]


def _registrar_telemetria_categorizacao(
    nicho: str, categoria: str, tier: str, aliases_batidos: list[str],
    atributos: list[str], tempo_ms: float,
) -> None:
    _append_telemetria({
        "evento": "categorizacao",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nicho": nicho,
        "categoria": categoria,
        "tier": tier,
        "aliases": aliases_batidos,
        "atributos": atributos,
        "tempo_ms": tempo_ms,
    })


def _registrar_nicho_desconhecido(nicho: str, tokens: list[str]) -> None:
    """Log append-only (JSONL) de todo nicho que caiu no fallback padrão —
    texto original, tokens normalizados e timestamp — para orientar quais
    categorias/aliases cadastrar em seguida. Nunca bloqueia a geração do
    site: falha de disco é só logada (best-effort)."""
    _append_jsonl(CAMINHO_NICHOS_DESCONHECIDOS, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "texto_original": nicho,
        "tokens": tokens,
        "categoria": CATEGORIA_PADRAO,
    })


_CACHE_RECLASSIFICACAO_LLM: dict[str, Optional[str]] = {}
_ENV_LLM_FALLBACK_ATIVO = "IMAGE_ENGINE_LLM_FALLBACK"


def _llm_fallback_ativo() -> bool:
    return os.getenv(_ENV_LLM_FALLBACK_ATIVO, "1").strip().lower() not in ("0", "false", "off")


def _vocabulario_reclassificacao() -> dict[str, str]:
    """1 alias representativo (o de maior peso) por categoria conhecida
    (specific + generic) — é exatamente o vocabulário fechado que o LLM pode
    escolher em _reclassificar_nicho_via_ia. Usar o próprio texto do alias
    (não o nome técnico da categoria) garante que, se o LLM escolher um
    item dessa lista, ele necessariamente bate em _melhor_categoria depois
    - elimina o caso de "clube de futebol" (sinônimo plausível mas nunca
    cadastrado) passar sem achar nada."""
    vocabulario: dict[str, str] = {}
    for banco in (_ESTRUTURAS["categorias_aliases"], _ESTRUTURAS["sinais_genericos"]):
        for categoria, pares in banco.items():
            if not pares:
                continue
            melhor_alias = max(pares, key=lambda par: par[1])[0]
            vocabulario[categoria] = melhor_alias
    return vocabulario


_VOCABULARIO_RECLASSIFICACAO = _vocabulario_reclassificacao()


def _reclassificar_nicho_via_ia(nicho: str) -> Optional[str]:
    """Último recurso ANTES do fallback pro CATEGORIA_PADRAO — só entra em
    jogo quando nem categoria específica nem sinal genérico bateram (ver
    mapear_categoria). Pede ao AIProvider (mesma cadeia gemini/nvidia_nim/
    anthropic/ollama de ai_provider.py, já usada em agent_construtor.py) pra
    ESCOLHER, dentre o vocabulário fechado de _vocabulario_reclassificacao()
    (aliases já cadastrados em niches.json), qual mais se parece com o texto
    livre recebido - que pode ser um NOME PRÓPRIO (ex.: "Botafogo Futebol
    Clube"), não uma descrição de negócio. Nunca pede texto livre/gerado:
    a saída só é aceita se for EXATAMENTE um item do vocabulário (checado
    depois da resposta) - isso garante que, se aceita, o resultado bate em
    _melhor_categoria depois (mesmo alias, mesmo texto). Achado real
    2026-07-28: pedir pro LLM parafrasear livremente ("clube de futebol")
    produzia texto plausível mas que não batia em nenhum alias existente
    ("clube esportivo"/"time de futebol") - restringir ao vocabulário fechado
    resolve isso sem enfraquecer o matcher determinístico.

    Nunca levanta exceção - qualquer falha (provedor indisponível, timeout,
    resposta inválida ou fora do vocabulário) retorna None e quem chama
    segue pro CATEGORIA_PADRAO, exatamente como se esta função não
    existisse. Cacheado em memória por texto de nicho (normalizado), nunca
    chama o LLM duas vezes pro mesmo texto no mesmo processo. Desligável via
    env var IMAGE_ENGINE_LLM_FALLBACK=0, sem precisar mudar código."""
    if not _llm_fallback_ativo():
        return None

    chave_cache = nicho.strip().lower()
    if chave_cache in _CACHE_RECLASSIFICACAO_LLM:
        return _CACHE_RECLASSIFICACAO_LLM[chave_cache]

    resultado: Optional[str] = None
    try:
        from ai_provider import obter_ai_provider  # import local: caminho comum de mapear_categoria nunca depende de IA

        opcoes = sorted(set(_VOCABULARIO_RECLASSIFICACAO.values()))
        lista_opcoes = "\n".join(f"- {op}" for op in opcoes)
        prompt = (
            "O texto abaixo é o que um usuario digitou como \"tipo de negocio\" de "
            "uma empresa, mas pode ser na verdade o NOME PROPRIO da empresa (ex.: "
            "nome de clube, marca ou fantasia), nao uma descricao do que ela faz.\n\n"
            f'Texto: "{nicho}"\n\n'
            "Aqui esta a lista FECHADA de tipos de negocio que o sistema conhece:\n"
            f"{lista_opcoes}\n\n"
            'Responda em JSON com um unico campo "tipo_negocio": copie EXATAMENTE '
            "(mesma grafia, sem mudar nenhuma palavra) o item da lista acima mais "
            "parecido com o texto. Nunca invente um item novo, nunca combine dois "
            "itens, nunca traduza ou reescreva - copie um item literal da lista. "
            "Se nenhum item da lista se aplicar razoavelmente, responda "
            '{"tipo_negocio": null}.'
        )
        resposta = obter_ai_provider().gerar_json(prompt, max_tokens=100)
        tipo = resposta.get("tipo_negocio")
        if isinstance(tipo, str) and tipo.strip().lower() in {op.lower() for op in opcoes}:
            resultado = tipo.strip()
        elif tipo:
            logger.debug(
                "Reclassificação via LLM para nicho '%s' devolveu item fora do "
                "vocabulário fechado (%r) - descartado, segue fallback normal",
                nicho, tipo,
            )
    except Exception:
        logger.debug(
            "Reclassificação via LLM falhou para nicho '%s' (fallback normal segue)",
            nicho, exc_info=True,
        )
        resultado = None

    _CACHE_RECLASSIFICACAO_LLM[chave_cache] = resultado
    return resultado


def mapear_categoria(nicho: str) -> str:
    """Mapeia o texto livre de nicho para uma categoria controlada de imagens.

    3 camadas, nessa ordem — ver comentário da seção BANCO DE IMAGENS para a
    lógica completa: categoria específica (podendo virar uma chave composta
    "categoria__atributo1__atributo2..." se um ou mais atributos baterem) ->
    sinal genérico -> CATEGORIA_PADRAO (raro, logado como warning e
    registrado em backend/cache/unknown_categories.jsonl).
    """
    tempo_inicio = time.perf_counter()
    texto = _normalizar_texto(nicho)
    palavras = texto.split()

    especifica = _melhor_categoria(texto, palavras, _ESTRUTURAS["categorias_aliases"])
    if especifica.categoria:
        atributos = _atributos_batidos(texto, palavras, especifica.categoria)
        categoria_final = "__".join([especifica.categoria, *atributos])
        logger.debug(
            "Nicho '%s' -> categoria específica '%s' (score=%d, aliases=%s, atributos=%s)",
            nicho, categoria_final, especifica.score, especifica.aliases_batidos, atributos,
        )
        tempo_ms = round((time.perf_counter() - tempo_inicio) * 1000, 3)
        _registrar_telemetria_categorizacao(nicho, categoria_final, "specific", especifica.aliases_batidos, atributos, tempo_ms)
        return categoria_final

    generica = _melhor_categoria(texto, palavras, _ESTRUTURAS["sinais_genericos"])
    if generica.categoria:
        logger.info(
            "Nicho '%s' sem categoria específica -> sinal genérico '%s' "
            "(score=%d, aliases=%s)",
            nicho, generica.categoria, generica.score, generica.aliases_batidos,
        )
        tempo_ms = round((time.perf_counter() - tempo_inicio) * 1000, 3)
        _registrar_telemetria_categorizacao(nicho, generica.categoria, "generic", generica.aliases_batidos, [], tempo_ms)
        return generica.categoria

    tipo_reescrito = _reclassificar_nicho_via_ia(nicho)
    if tipo_reescrito:
        texto_llm = _normalizar_texto(tipo_reescrito)
        palavras_llm = texto_llm.split()

        especifica_llm = _melhor_categoria(texto_llm, palavras_llm, _ESTRUTURAS["categorias_aliases"])
        if especifica_llm.categoria:
            atributos = _atributos_batidos(texto_llm, palavras_llm, especifica_llm.categoria)
            categoria_final = "__".join([especifica_llm.categoria, *atributos])
            logger.info(
                "Nicho '%s' sem match direto -> LLM reescreveu como '%s' -> categoria específica '%s'",
                nicho, tipo_reescrito, categoria_final,
            )
            tempo_ms = round((time.perf_counter() - tempo_inicio) * 1000, 3)
            _registrar_telemetria_categorizacao(nicho, categoria_final, "specific_llm", especifica_llm.aliases_batidos, atributos, tempo_ms)
            return categoria_final

        generica_llm = _melhor_categoria(texto_llm, palavras_llm, _ESTRUTURAS["sinais_genericos"])
        if generica_llm.categoria:
            logger.info(
                "Nicho '%s' sem match direto -> LLM reescreveu como '%s' -> sinal genérico '%s'",
                nicho, tipo_reescrito, generica_llm.categoria,
            )
            tempo_ms = round((time.perf_counter() - tempo_inicio) * 1000, 3)
            _registrar_telemetria_categorizacao(nicho, generica_llm.categoria, "generic_llm", generica_llm.aliases_batidos, [], tempo_ms)
            return generica_llm.categoria

    logger.warning(
        "Nicho '%s' não bateu em nenhuma categoria específica nem sinal "
        "genérico -> fallback '%s'. Considere cadastrar uma categoria/alias "
        "novo para esse nicho em backend/data/niches.json.",
        nicho, CATEGORIA_PADRAO,
    )
    _registrar_nicho_desconhecido(nicho, palavras)
    tempo_ms = round((time.perf_counter() - tempo_inicio) * 1000, 3)
    _registrar_telemetria_categorizacao(nicho, CATEGORIA_PADRAO, "default", [], [], tempo_ms)
    return CATEGORIA_PADRAO


def obter_cor_primaria(categoria: str) -> str:
    """Cor primária (hex) sugerida pra categoria, cadastrada em
    niches.json (campo "primary_color"). Reaproveita a mesma categoria
    que mapear_categoria() já resolveu pra imagem — nenhuma categorização
    nova, nenhuma duplicação entre nichos que compartilham categoria (ex.:
    "Odontologia" e "Fisioterapia" caem ambos em medical_clinic e usam a
    mesma cor).

    categoria pode ser composta ("categoria_base__atributo1__atributo2") —
    a cor sempre vem da categoria BASE (atributos não têm cor própria,
    são variantes visuais/textuais da mesma categoria, não identidades
    visuais diferentes). Cai pra COR_PRIMARIA_PADRAO se a categoria base
    não tiver primary_color definido (compatibilidade)."""
    categoria_base = categoria.split("__", 1)[0]
    return _ESTRUTURAS["cor_por_categoria"].get(categoria_base, COR_PRIMARIA_PADRAO)


def _carregar_cache_imagens() -> dict:
    if not CAMINHO_CACHE_IMAGENS.exists():
        return {}
    try:
        return json.loads(CAMINHO_CACHE_IMAGENS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _salvar_cache_imagens(cache: dict) -> None:
    PASTA_CACHE.mkdir(parents=True, exist_ok=True)
    CAMINHO_CACHE_IMAGENS.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _append_jsonl(caminho: Path, evento: dict) -> None:
    """Grava um evento em JSON Lines (append-only — evita risco de corrupção
    por read-modify-write concorrente que um único array JSON teria). Nunca
    bloqueia a geração do site: falha de disco é só logada (best-effort)."""
    try:
        PASTA_CACHE.mkdir(parents=True, exist_ok=True)
        with caminho.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("Falha ao gravar em %s (não bloqueia a geração)", caminho.name, exc_info=True)


def _append_telemetria(evento: dict) -> None:
    _append_jsonl(CAMINHO_TELEMETRIA, evento)


def _registrar_telemetria_busca_imagens(
    categoria: str, query: Optional[str], candidatos: int, mantidas: int,
    melhor_score: Optional[float], tempo_ms: float, cache_hit: bool,
    tentativa: Optional[int] = None,
) -> None:
    _append_telemetria({
        "evento": "busca_imagens",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "categoria": categoria,
        "query": query,
        "candidatos": candidatos,
        "mantidas": mantidas,
        "melhor_score": melhor_score,
        "tempo_ms": tempo_ms,
        "cache_hit": cache_hit,
        # Nível de _construir_niveis_query que trouxe resultado (1=query
        # completa, 2=1ª clause de cada fragmento, 3=só 1ª clause da base) —
        # None em cache_hit, onde nenhuma busca nova foi feita. Dado real pra
        # decidir depois, com número, se vale reescrever base_queries longas.
        "tentativa": tentativa,
        "palavras_query": len(query.split()) if query else None,
    })


def _buscar_candidatos_unsplash(query: str) -> list[dict]:
    """Busca QTD_CANDIDATOS_BUSCA candidatos brutos no Unsplash para a query
    dada (metadados completos, não só a URL) — o ranking em _rankear_imagens
    escolhe os melhores QTD_IMAGENS_POR_CATEGORIA a partir daqui, na mesma
    chamada de API (sem custo/latência extra por imagem).

    Raises:
        ErroBancoImagens: se a chave não estiver configurada, a chamada
            falhar (rede/rate limit/HTTP erro) ou não vier nenhum resultado.
    """
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        raise ErroBancoImagens("UNSPLASH_ACCESS_KEY não configurada")

    try:
        resposta = requests.get(
            UNSPLASH_API_URL,
            params={
                "query": query,
                "per_page": QTD_CANDIDATOS_BUSCA,
                "orientation": "landscape",
            },
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=10,
        )
        resposta.raise_for_status()
    except requests.RequestException as e:
        raise ErroBancoImagens(f"Falha ao consultar Unsplash para '{query}': {e}") from e

    candidatos = [
        item for item in resposta.json().get("results", [])
        if item.get("urls", {}).get("regular")
    ]
    if not candidatos:
        raise ErroBancoImagens(f"Unsplash não retornou imagens para a query '{query}'")
    return candidatos


def _rankear_imagens(
    candidatos: list[dict], concepts: list[str], atributos_termos: list[str], forbidden: list[str],
) -> list[tuple[dict, float]]:
    """Ranking determinístico e explicável, usando só metadados reais que o
    Unsplash já retorna na mesma chamada (alt_description/description,
    likes, resolução) — nunca um score de "visão computacional" ou
    "confiança" inventado. Critérios, todos auditáveis:

      score = score_texto + score_atributos + score_likes + score_resolucao - penalidade_forbidden

    - score_texto: +PESO_TEXTO para cada conceito da categoria (ex.:
      "contractor", "renovation") encontrado no texto da imagem — quanto
      mais conceitos batem, maior o score (critério "quantidade de
      conceitos encontrados").
    - score_atributos: +PESO_ATRIBUTO para cada keyword de atributo batido
      (ex.: "premium", "futebol") encontrado no texto da imagem — mesmo
      princípio, peso menor por ser um sinal mais fraco que o conceito
      central da categoria.
    - score_likes: popularidade normalizada (0..PESO_LIKES), capada em
      TETO_LIKES pra imagem super popular não dominar sozinha o ranking.
    - score_resolucao: resolução normalizada (0..PESO_RESOLUCAO), capada em
      TETO_PIXELS pelo mesmo motivo.
    - penalidade_forbidden: -PENALIDADE_FORBIDDEN por termo proibido (da
      categoria ou global) encontrado no texto da imagem (ex.: "storefront"
      numa categoria de construção, "generic office" em qualquer categoria).

    Retorna a lista completa ordenada (maior score primeiro) — quem chama
    decide quantos itens manter."""
    conceitos_norm = [c.lower() for c in concepts]
    atributos_norm = [a.lower() for a in atributos_termos]
    proibidos_norm = [f.lower() for f in forbidden]

    pontuados = []
    for item in candidatos:
        texto_imagem = " ".join(
            filter(None, [item.get("alt_description"), item.get("description")])
        ).lower()

        score_texto = sum(PESO_TEXTO for c in conceitos_norm if c in texto_imagem)
        score_atributos = sum(PESO_ATRIBUTO for a in atributos_norm if a in texto_imagem)

        likes = item.get("likes") or 0
        score_likes = min(likes, TETO_LIKES) / TETO_LIKES * PESO_LIKES

        largura = item.get("width") or 0
        altura = item.get("height") or 0
        score_resolucao = min(largura * altura, TETO_PIXELS) / TETO_PIXELS * PESO_RESOLUCAO

        penalidade = sum(PENALIDADE_FORBIDDEN for p in proibidos_norm if p in texto_imagem)

        pontuados.append((item, score_texto + score_atributos + score_likes + score_resolucao - penalidade))

    pontuados.sort(key=lambda par: par[1], reverse=True)
    return pontuados


def _montar_query(categoria: str) -> str:
    """Compõe a query em inglês dinamicamente: base_query da categoria +
    conceitos + fragmento de query de cada atributo batido (ver
    mapear_categoria) — nunca texto livre do cliente nem tradução
    automática, tudo a partir do que já está cadastrado em niches.json.
    Clauses idênticas repetidas são deduplicadas (uma categoria com N
    atributos combinados não gera uma query artificialmente maior que o
    necessário)."""
    nomes = categoria.split("__")
    categoria_base, nomes_atributos = nomes[0], nomes[1:]

    dado_base = _ESTRUTURAS["categorias_dados"].get(categoria_base)
    if dado_base is None:
        return QUERY_POR_CATEGORIA[CATEGORIA_PADRAO]

    partes = [dado_base["base_query"]]
    # concepts NÃO entram na query — são usados apenas como sinais de
    # ranking em _rankear_imagens (chamada por buscar_imagens). Adicioná-los
    # aqui redundancia com base_query e infla a query desnecessariamente.

    queries_attr = _ESTRUTURAS["atributos_query"].get(categoria_base, {})
    for nome_attr in nomes_atributos:
        fragmento = queries_attr.get(nome_attr)
        if fragmento:
            partes.append(fragmento)

    # Dedup por clause inteira e idêntica (case-insensitive) — nunca remove
    # uma palavra isolada de dentro de uma clause. Quem escreveu niches.json
    # decidiu a composição de cada clause de propósito (ex.: repetir "acai"/
    # "law" em mais de uma clause reforça o termo central do atributo ou da
    # categoria); dedup por palavra individual mutilava essas clauses em
    # fragmentos sem sentido (ex.: "acai smoothie bowl" virava só "smoothie").
    clauses_vistas: set[str] = set()
    tokens_final: list[str] = []
    for frase in partes:
        for t in frase.split(","):
            t = t.strip()
            if not t:
                continue
            chave = t.lower()
            if chave in clauses_vistas:
                continue
            clauses_vistas.add(chave)
            tokens_final.append(t)

    return ", ".join(tokens_final)


def _primeira_clausula(frase: str) -> str:
    return frase.split(",", 1)[0].strip()


def _construir_niveis_query(categoria: str) -> list[str]:
    """3 níveis fixos de query, do mais completo pro mais restrito — usados
    em ordem por obter_imagens_categoria quando a Unsplash zera resultado
    (confirmado empiricamente 2026-07-28: acima de ~6 palavras a taxa de
    zero-resultado sobe muito). Cada nível remove o mínimo de informação
    necessário pra reduzir o tamanho, nunca uma cadeia aberta de tentativas:

      1. _montar_query(categoria) — base_query + query de cada atributo
         batido, clauses deduplicadas (nível padrão, sem nenhum corte).
      2. só a 1ª clause da base_query + só a 1ª clause de cada atributo —
         mais curta, mas ainda carrega o termo central de cada atributo
         (ex.: "ice cream shop interior, acai bowl", não só a base).
      3. só a 1ª clause da base_query — última tentativa, sem atributo.

    Níveis idênticos ao anterior (ex.: categoria sem atributo, onde o nível
    2 e o nível 3 seriam a mesma coisa) não são repetidos."""
    nomes = categoria.split("__")
    categoria_base, nomes_atributos = nomes[0], nomes[1:]

    dado_base = _ESTRUTURAS["categorias_dados"].get(categoria_base)
    if dado_base is None:
        return [QUERY_POR_CATEGORIA[CATEGORIA_PADRAO]]

    nivel1 = _montar_query(categoria)

    queries_attr = _ESTRUTURAS["atributos_query"].get(categoria_base, {})
    fragmentos_attr = [queries_attr[nome] for nome in nomes_atributos if nome in queries_attr]
    partes_nivel2 = [_primeira_clausula(dado_base["base_query"])] + [_primeira_clausula(f) for f in fragmentos_attr]
    nivel2 = ", ".join(dict.fromkeys(p for p in partes_nivel2 if p))

    nivel3 = _primeira_clausula(dado_base["base_query"])

    niveis = [nivel1]
    for nivel in (nivel2, nivel3):
        if nivel and nivel not in niveis:
            niveis.append(nivel)
    return niveis


def _termos_atributos(categoria: str) -> list[str]:
    """Coleta as keywords de todos os atributos presentes na chave composta,
    pra alimentar o bônus de ranking (_rankear_imagens)."""
    nomes = categoria.split("__")
    categoria_base, nomes_atributos = nomes[0], nomes[1:]
    banco = _ESTRUTURAS["atributos_por_categoria"].get(categoria_base, {})
    termos = []
    for nome_attr in nomes_atributos:
        termos.extend(txt for txt, _ in banco.get(nome_attr, []))
    return termos


def _ler_jsonl(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    eventos = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            eventos.append(json.loads(linha))
        except json.JSONDecodeError:
            continue
    return eventos


def gerar_estatisticas() -> dict:
    """Agrega backend/cache/telemetria_imagens.jsonl e
    backend/cache/unknown_categories.jsonl num resumo (backend/cache/stats.json)
    pra orientar evolução do banco de conhecimento com dado real, não achismo:
    quais categorias mais aparecem, quais nichos mais caem em fallback, quais
    atributos e queries mais são usados, e a taxa geral de fallback.

    Não roda a cada geração de site (custaria I/O redundante sem necessidade)
    — é chamada sob demanda via `python gerar_stats.py`."""
    categorizacoes = [e for e in _ler_jsonl(CAMINHO_TELEMETRIA) if e.get("evento") == "categorizacao"]
    buscas = [e for e in _ler_jsonl(CAMINHO_TELEMETRIA) if e.get("evento") == "busca_imagens"]
    desconhecidos = _ler_jsonl(CAMINHO_NICHOS_DESCONHECIDOS)

    contagem_categorias: dict[str, int] = {}
    contagem_atributos: dict[str, int] = {}
    for evento in categorizacoes:
        categoria = evento.get("categoria", "")
        contagem_categorias[categoria] = contagem_categorias.get(categoria, 0) + 1
        for atributo in evento.get("atributos") or []:
            contagem_atributos[atributo] = contagem_atributos.get(atributo, 0) + 1

    contagem_desconhecidos: dict[str, int] = {}
    for evento in desconhecidos:
        chave = evento.get("texto_original", "")
        contagem_desconhecidos[chave] = contagem_desconhecidos.get(chave, 0) + 1

    contagem_queries: dict[str, int] = {}
    for evento in buscas:
        query = evento.get("query")
        if query:
            contagem_queries[query] = contagem_queries.get(query, 0) + 1

    # Quantas buscas (não cache_hit) resolveram em cada nível de
    # _construir_niveis_query — dado real pra decidir depois, com número, se
    # vale reescrever base_queries longas em vez de continuar dependendo do
    # fallback (pedido do usuário 2026-07-28, ver project_image_engine_evolution).
    contagem_tentativas: dict[str, int] = {}
    for evento in buscas:
        tentativa = evento.get("tentativa")
        if tentativa is not None:
            chave = f"nivel_{tentativa}"
            contagem_tentativas[chave] = contagem_tentativas.get(chave, 0) + 1

    total_categorizacoes = len(categorizacoes)
    total_fallback = contagem_categorias.get(CATEGORIA_PADRAO, 0)
    taxa_fallback = round(total_fallback / total_categorizacoes, 4) if total_categorizacoes else 0.0

    def _ordenado(contagem: dict[str, int]) -> dict[str, int]:
        return dict(sorted(contagem.items(), key=lambda par: par[1], reverse=True))

    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "total_categorizacoes": total_categorizacoes,
        "total_buscas_imagens": len(buscas),
        "taxa_fallback": taxa_fallback,
        "meta_taxa_fallback": META_TAXA_FALLBACK,
        "dentro_da_meta": taxa_fallback <= META_TAXA_FALLBACK,
        "categorias_mais_usadas": _ordenado(contagem_categorias),
        "categorias_desconhecidas": _ordenado(contagem_desconhecidos),
        "atributos_mais_usados": _ordenado(contagem_atributos),
        "queries_mais_usadas": _ordenado(contagem_queries),
        "buscas_por_nivel_fallback": _ordenado(contagem_tentativas),
    }


def salvar_estatisticas() -> dict:
    stats = gerar_estatisticas()
    PASTA_CACHE.mkdir(parents=True, exist_ok=True)
    CAMINHO_STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def obter_imagens_categoria(categoria: str) -> list[str]:
    """
    Retorna a lista de URLs de imagem cacheada para a categoria (ou chave
    composta "categoria__atributo", ver mapear_categoria), buscando no
    Unsplash — com ranking determinístico por metadados (_rankear_imagens) —
    e cacheando em disco na primeira vez que a chave é necessária. Chamadas
    seguintes pra mesma chave não geram nova requisição — é isso que mantém
    o consumo de rate limit baixo (1 busca por categoria×atributo, não por
    site gerado).

    Raises:
        ErroBancoImagens: se não houver chave configurada ou a busca
            falhar — quem chama decide o fallback (ver agent_construtor.py).
    """
    tempo_inicio = time.perf_counter()
    cache = _carregar_cache_imagens()
    if cache.get(categoria):
        tempo_ms = round((time.perf_counter() - tempo_inicio) * 1000, 3)
        _registrar_telemetria_busca_imagens(categoria, None, 0, len(cache[categoria]), None, tempo_ms, True)
        return cache[categoria]

    categoria_base = categoria.split("__", 1)[0]
    concepts = _ESTRUTURAS["concepts_por_categoria"].get(categoria_base, [])
    atributos_termos = _termos_atributos(categoria)
    forbidden = list(dict.fromkeys(
        _ESTRUTURAS["forbidden_por_categoria"].get(categoria_base, []) + _ESTRUTURAS["global_forbidden"]
    ))

    # Confirmado empiricamente (benchmark 2026-07-28): a Unsplash retorna cada
    # vez menos resultados conforme a query cresce em número de palavras
    # (acima de ~6 palavras a taxa de zero-resultado sobe muito). 3 níveis
    # fixos (ver _construir_niveis_query), nunca uma cadeia aberta — cada
    # nível remove só o mínimo necessário, preservando o termo do atributo
    # pelo maior número de tentativas possível antes de descartá-lo.
    niveis_query = _construir_niveis_query(categoria)
    candidatos = None
    query = niveis_query[0]
    tentativa_usada = None
    erro_final = None
    for tentativa, tentativa_query in enumerate(niveis_query, start=1):
        try:
            candidatos = _buscar_candidatos_unsplash(tentativa_query)
            query = tentativa_query
            tentativa_usada = tentativa
            break
        except ErroBancoImagens as e:
            erro_final = e
            if "não retornou imagens" not in str(e):
                raise  # erro real (chave ausente, rede, rate limit) — não mascarar com retry
    if candidatos is None:
        raise erro_final

    ranqueados = _rankear_imagens(candidatos, concepts, atributos_termos, forbidden)
    melhores = ranqueados[:QTD_IMAGENS_POR_CATEGORIA]
    urls = [item["urls"]["regular"] for item, _ in melhores]

    cache[categoria] = urls
    _salvar_cache_imagens(cache)

    tempo_ms = round((time.perf_counter() - tempo_inicio) * 1000, 3)
    melhor_score = melhores[0][1] if melhores else None
    _registrar_telemetria_busca_imagens(categoria, query, len(candidatos), len(urls), melhor_score, tempo_ms, False, tentativa_usada)
    return urls


def _slugify(texto: str) -> str:
    """Converte um nome de empresa em um slug seguro para nome de arquivo"""
    texto_normalizado = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", texto_normalizado).strip("-").lower()
    return slug or "logo"


def normalizar_logo(logo_url: str, nome_empresa: str) -> str:
    """
    Baixa o logo a partir de uma URL e normaliza para um formato padrão:
    PNG quadrado 512x512, fundo transparente, imagem centralizada preservando
    o aspect ratio original. Salva em /assets/logos/{slug-da-empresa}.png

    Args:
        logo_url: URL pública da imagem do logo
        nome_empresa: Nome da empresa, usado para nomear o arquivo salvo

    Returns:
        Caminho relativo do arquivo salvo (ex: "assets/logos/padaria-sabor.png")

    Raises:
        ErroNormalizacaoLogo: Se o download ou o processamento da imagem falhar
    """
    try:
        resposta = requests.get(logo_url, timeout=15)
        resposta.raise_for_status()
    except requests.RequestException as e:
        raise ErroNormalizacaoLogo(f"Falha ao baixar logo de {logo_url}: {e}") from e

    try:
        imagem = Image.open(io.BytesIO(resposta.content))
        imagem.load()
    except UnidentifiedImageError as e:
        raise ErroNormalizacaoLogo(f"Conteúdo em {logo_url} não é uma imagem válida") from e
    except Exception as e:
        raise ErroNormalizacaoLogo(f"Erro ao processar imagem de {logo_url}: {e}") from e

    imagem = imagem.convert("RGBA")

    # Redimensiona preservando o aspect ratio dentro do tamanho padrão
    imagem.thumbnail(TAMANHO_PADRAO, _RESAMPLE)

    # Centraliza em um canvas quadrado transparente
    canvas = Image.new("RGBA", TAMANHO_PADRAO, (0, 0, 0, 0))
    offset = (
        (TAMANHO_PADRAO[0] - imagem.width) // 2,
        (TAMANHO_PADRAO[1] - imagem.height) // 2,
    )
    canvas.paste(imagem, offset, imagem)

    PASTA_LOGOS.mkdir(parents=True, exist_ok=True)
    slug = _slugify(nome_empresa)
    caminho_arquivo = PASTA_LOGOS / f"{slug}.png"
    canvas.save(caminho_arquivo, format="PNG")

    return str(Path("assets") / "logos" / f"{slug}.png").replace("\\", "/")
