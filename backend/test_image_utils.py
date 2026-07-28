#!/usr/bin/env python3
"""
Suite de Testes - Categorização de Imagens (image_utils.py)
Valida mapear_categoria() contra uma grande variedade de nichos reais:
os 50 nichos de test_agentes.py, os 6 casos reportados como bugs em
produção (festa, buffet, centro de treinamento, turismo, pedreiro,
estacionamento) e variações de plural/gênero/acentuação.

Uso: python test_image_utils.py
"""

import os
import sys

# Desliga o fallback via LLM (image_utils._reclassificar_nicho_via_ia) antes de
# importar/rodar qualquer coisa - mantém esta suíte 100% determinística e sem
# rede (senão "Xyz Abstrato Sem Sentido" e outros casos de CATEGORIA_PADRAO
# chamariam um provedor de IA de verdade a cada execução). O comportamento do
# fallback em si é testado à parte, com um mock, em checar_fallback_llm().
os.environ["IMAGE_ENGINE_LLM_FALLBACK"] = "0"

import image_utils
from image_utils import (
    mapear_categoria, CATEGORIAS_ALIASES, SINAIS_GENERICOS, CATEGORIA_PADRAO, _montar_query,
    obter_cor_primaria, REGEX_COR_HEX, COR_PRIMARIA_PADRAO,
)

# (nicho, categoria_esperada) — cobre os 50 nichos de test_agentes.py mais
# os casos reais reportados como incompatíveis e variações de escrita.
CASOS_ESPERADOS: list[tuple[str, str]] = [
    # --- Casos reais reportados como bug (critério de aceitação) ---
    ("Festa Infantil", "events_venue__infantil"),
    ("Buffet de Festas", "events_venue"),
    ("Centro de Treinamento", "sports_training_center"),
    ("CBF Centro de Treinamento", "sports_training_center"),
    ("Agência de Turismo", "tourism_agency"),
    ("Pedreiro", "construction"),
    ("Estacionamento", "parking"),

    # --- Os 50 nichos de test_agentes.py (NICHOS_TESTE) ---
    ("Auto Elétrica", "auto_repair"),
    ("Mecânica Geral", "auto_repair"),
    ("Lavagem de Veículos", "car_wash"),
    ("Academia de Ginástica", "gym"),
    ("Clínica Médica", "medical_clinic"),
    ("Odontologia", "medical_clinic"),
    ("Spa e Bem-estar", "wellness_spa"),
    ("Fisioterapia", "medical_clinic"),
    ("Consultoria Jurídica", "law_office"),
    ("Advocacia Geral", "law_office"),
    ("Pet Shop", "pet_shop"),
    ("Veterinária", "pet_shop"),
    ("Banho e Tosa", "pet_shop"),
    ("Pizzaria", "restaurant"),
    ("Restaurante", "restaurant"),
    ("Padaria", "bakery"),
    ("Sorveteria", "ice_cream_shop"),
    ("Confeitaria", "bakery"),
    ("Lanchonete", "restaurant"),
    ("Loja de Roupas", "clothing_store"),
    ("Sapetaria", "clothing_store"),
    ("Brechó", "clothing_store"),
    ("Salão de Beleza", "beauty_salon"),
    ("Barbearia", "beauty_salon"),
    ("Manicure", "beauty_salon"),
    ("Imobiliária", "real_estate"),
    ("Aluguel de Imóveis", "real_estate"),
    ("Escola de Idiomas", "education_school"),
    ("Curso Online", "education_school"),
    ("Escola de Artes", "education_school"),
    ("Software/SaaS", "tech_software"),
    ("Web Design", "tech_software"),
    ("Consultoria Tecnológica", "tech_software"),
    ("Agência de Marketing", "marketing_creative"),
    ("Estúdio de Design", "marketing_creative"),
    ("Social Media", "marketing_creative"),
    ("Encanador", "construction"),
    ("Eletricista", "construction"),
    ("Serralharia", "construction"),
    ("Construção Civil", "construction"),
    ("Limpeza de Ambientes", "construction"),
    ("Hotel", "hotel"),
    ("Pousada", "hotel"),
    ("Agência de Viagens", "tourism_agency"),
    ("Floricultura", "florist_shop"),
    ("Fotografia", "photography_studio"),
    ("DJ Services", "events_venue"),

    # --- Variações de plural / gênero / grafia (Etapa 1 do pedido) ---
    ("Clínica Veterinária", "pet_shop"),  # mais específico vence o genérico
    ("Consultório Odontológico", "medical_clinic"),
    ("Escolinha de Futebol", "sports_training_center__infantil__futebol"),  # "escolinha" bate no atributo infantil também (2026-07-28: atributo infantil generalizado, achado do benchmark visual)
    ("Advogada", "law_office"),
    ("Contador", "accounting_office"),
    ("Contadores Associados", "accounting_office"),
    ("Nutricionista", "medical_clinic"),
    ("Psicóloga Clínica", "medical_clinic"),
    ("Corretor de Imóveis", "real_estate"),

    # --- Novas categorias (Etapa 11 do pedido) ---
    ("Escritório de Arquitetura", "architecture_office"),
    ("Arquiteto", "architecture_office"),
    ("Energia Solar", "solar_energy"),
    ("Instalação Fotovoltaica", "solar_energy"),
    ("Farmácia", "medical_clinic"),

    # --- Atributos compostos (Etapa 12/Arquiteto Principal) ---
    ("Buffet Corporativo", "events_venue__corporativo"),
    ("Casamento e Cerimonial", "events_venue__casamento"),
    ("Construção Residencial", "construction__residential"),
    ("Reforma Comercial", "construction__commercial"),

    # --- Múltiplos atributos simultâneos + global_attributes (Image Engine v2) ---
    ("Buffet Infantil Premium", "events_venue__infantil__premium"),  # infantil (peso 8) > premium (peso 7)
    ("Academia Premium", "gym__premium"),
    ("Spa Premium", "wellness_spa"),  # wellness_spa não referencia "premium" — sem atributo
    ("Escritório de Advocacia Corporativo", "law_office__corporativo"),
    ("Contabilidade Corporativa", "accounting_office__corporativo"),

    # --- Sinais genéricos (camada 2) — nicho sem categoria específica ---
    ("Loja de Presentes Variados", "retail_general"),
    ("Escritório de Representação Comercial", "professional_office"),
    ("Fábrica de Embalagens", "workshop_industrial"),

    # --- Fallback padrão (camada 3) — nicho realmente sem sinal nenhum ---
    ("Xyz Abstrato Sem Sentido", CATEGORIA_PADRAO),
]


def normalizar_erro(msg: str) -> str:
    return f"❌ {msg}"


def rodar_testes() -> bool:
    total = len(CASOS_ESPERADOS)
    falhas = []

    print(f"🧪 Testando mapear_categoria() com {total} nichos...\n")

    for nicho, esperado in CASOS_ESPERADOS:
        obtido = mapear_categoria(nicho)
        ok = obtido == esperado
        marca = "✅" if ok else "❌"
        print(f"{marca} {nicho!r:45} -> esperado={esperado!r:28} obtido={obtido!r}")
        if not ok:
            falhas.append((nicho, esperado, obtido))

    print(f"\n{'=' * 70}")
    print(f"Resultado: {total - len(falhas)}/{total} passaram")

    if falhas:
        print(f"\n{len(falhas)} falha(s):")
        for nicho, esperado, obtido in falhas:
            print(f"  - {nicho!r}: esperado {esperado!r}, obtido {obtido!r}")
        return False

    print("✅ Todos os casos passaram — nenhuma regressão nas categorias antigas,")
    print("   todos os casos reais reportados agora caem na categoria certa.")
    return True


def checar_dedup_query_preserva_termo_central() -> bool:
    """Regressão do bug encontrado no benchmark visual 2026-07-28: dedup por
    palavra individual (versão antiga de _montar_query) apagava o termo
    central de um atributo/categoria quando ele se repetia entre clauses
    (ex.: "acai smoothie bowl" -> "smoothie", "law books" -> "books").
    Dedup por clause idêntica não deve mais fazer isso."""
    casos = [
        # (categoria, termo que precisa sobreviver na query final)
        ("ice_cream_shop__acai", "acai"),
        ("law_office", "law"),
    ]
    falhas = []
    for categoria, termo in casos:
        query = _montar_query(categoria)
        ocorrencias = query.lower().count(termo.lower())
        if ocorrencias < 2:
            falhas.append((categoria, termo, ocorrencias, query))

    if falhas:
        for categoria, termo, ocorrencias, query in falhas:
            print(normalizar_erro(
                f"_montar_query({categoria!r}): termo {termo!r} apareceu só "
                f"{ocorrencias}x (esperado >=2) -> query={query!r}"
            ))
        return False
    print("✅ _montar_query preserva termos centrais repetidos entre clauses (dedup por clause, não por palavra).\n")
    return True


def checar_fallback_llm() -> bool:
    """Achado real 2026-07-28: nomes próprios que não batem em nenhum alias
    (ex.: "Botafogo Futebol Clube") caiam direto em CATEGORIA_PADRAO. Testa
    o novo 4º nível (_reclassificar_nicho_via_ia) com um mock — nunca chama
    um provedor de IA de verdade nesta suíte. Cobre: sucesso (LLM reescreve
    pra algo que bate), falha graciosa (LLM indisponível/erro -> comportamento
    idêntico ao de antes) e cache (não chama o mock 2x pro mesmo texto)."""
    nicho_teste = "Botafogo Futebol Clube"
    assert mapear_categoria(nicho_teste) == CATEGORIA_PADRAO, (
        "pré-condição do teste: sem LLM, esse nicho precisa cair no fallback padrão"
    )

    falhas = []

    # --- Caso 1: LLM reescreve com sucesso -> categoria correta ---
    image_utils._CACHE_RECLASSIFICACAO_LLM.clear()
    chamadas = []

    def _mock_sucesso(nicho: str):
        chamadas.append(nicho)
        return "escola de futebol"

    original = image_utils._reclassificar_nicho_via_ia
    image_utils._reclassificar_nicho_via_ia = _mock_sucesso
    try:
        obtido = mapear_categoria(nicho_teste)
        if obtido != "sports_training_center__futebol":
            falhas.append(f"caso sucesso: esperado 'sports_training_center__futebol', obtido {obtido!r}")
    finally:
        image_utils._reclassificar_nicho_via_ia = original

    # --- Caso 2: LLM falha/indisponível (retorna None) -> comportamento igual ao de sempre ---
    def _mock_falha(nicho: str):
        return None

    image_utils._reclassificar_nicho_via_ia = _mock_falha
    try:
        obtido = mapear_categoria(nicho_teste)
        if obtido != CATEGORIA_PADRAO:
            falhas.append(f"caso falha graciosa: esperado {CATEGORIA_PADRAO!r}, obtido {obtido!r}")
    finally:
        image_utils._reclassificar_nicho_via_ia = original

    # --- Caso 3: cache real (a função de produção, não o mock) não chama o
    # provedor 2x pro mesmo texto normalizado ---
    image_utils._CACHE_RECLASSIFICACAO_LLM.clear()
    contador = {"n": 0}

    class _ProvedorFake:
        def gerar_json(self, prompt, max_tokens=100):
            contador["n"] += 1
            return {"tipo_negocio": "escola de futebol"}

    # Este sub-caso testa a função real (não um mock dela), então precisa
    # religar a flag que o topo do arquivo desliga globalmente pra suíte
    # inteira não bater rede - só pelo tempo deste bloco.
    import ai_provider
    original_obter = ai_provider.obter_ai_provider
    ai_provider.obter_ai_provider = lambda: _ProvedorFake()
    os.environ["IMAGE_ENGINE_LLM_FALLBACK"] = "1"
    try:
        image_utils.mapear_categoria(nicho_teste)
        image_utils.mapear_categoria(nicho_teste)
        if contador["n"] != 1:
            falhas.append(f"cache: provedor foi chamado {contador['n']}x pro mesmo nicho, esperado 1x")
    finally:
        os.environ["IMAGE_ENGINE_LLM_FALLBACK"] = "0"
        ai_provider.obter_ai_provider = original_obter
        image_utils._CACHE_RECLASSIFICACAO_LLM.clear()

    if falhas:
        for f in falhas:
            print(normalizar_erro(f))
        return False
    print("✅ Fallback via LLM: reescreve nome próprio corretamente, falha graciosamente sem LLM, e cacheia por nicho.\n")
    return True


def checar_cor_primaria_por_categoria() -> bool:
    """Fase 1 da identidade visual automática (2026-07-28): toda categoria
    (specific/generic/default) precisa resolver pra uma cor hex válida via
    obter_cor_primaria(), seja a cadastrada em niches.json ou o fallback
    COR_PRIMARIA_PADRAO — nenhum nicho pode ficar sem cor nem gerar uma cor
    mal formatada. Cobre também categorias compostas (com atributo) e um
    nome de categoria totalmente desconhecido (fallback puro)."""
    from image_utils import _ESTRUTURAS

    falhas = []
    todas_categorias = list(CATEGORIAS_ALIASES) + list(SINAIS_GENERICOS) + [CATEGORIA_PADRAO]
    for categoria in todas_categorias:
        cor = obter_cor_primaria(categoria)
        if not REGEX_COR_HEX.match(cor):
            falhas.append(f"{categoria}: cor {cor!r} não é hex válido")

    # categoria composta (com atributo) usa a cor da categoria base
    cor_base = obter_cor_primaria("sports_training_center")
    cor_composta = obter_cor_primaria("sports_training_center__infantil__futebol")
    if cor_base != cor_composta:
        falhas.append(f"categoria composta deveria herdar a cor da base: {cor_base!r} != {cor_composta!r}")

    # categoria totalmente desconhecida -> fallback, nunca erro
    cor_desconhecida = obter_cor_primaria("categoria_que_nao_existe")
    if cor_desconhecida != COR_PRIMARIA_PADRAO:
        falhas.append(f"categoria desconhecida deveria cair no fallback {COR_PRIMARIA_PADRAO!r}, veio {cor_desconhecida!r}")

    # toda categoria em niches.json realmente tem primary_color cadastrado
    # (a Fase 1 seed cobriu 100% - se uma categoria nova for adicionada sem
    # cor, isso não falha aqui de propósito, só confirma o fallback funciona)
    sem_cor_cadastrada = [c for c in todas_categorias if c not in _ESTRUTURAS["cor_por_categoria"]]

    if falhas:
        for f in falhas:
            print(normalizar_erro(f))
        return False
    print(f"✅ Todas as {len(todas_categorias)} categorias resolvem pra uma cor hex válida "
          f"({len(todas_categorias) - len(sem_cor_cadastrada)} cadastradas, {len(sem_cor_cadastrada)} via fallback).\n")
    return True


def checar_integridade_bancos() -> bool:
    """Toda categoria referenciada em CATEGORIAS_ALIASES/SINAIS_GENERICOS e
    CATEGORIA_PADRAO precisa ter uma query correspondente — evita o erro
    silencioso de uma categoria nova sem query cadastrada."""
    from image_utils import QUERY_POR_CATEGORIA

    faltando = [
        categoria
        for categoria in list(CATEGORIAS_ALIASES) + list(SINAIS_GENERICOS) + [CATEGORIA_PADRAO]
        if categoria not in QUERY_POR_CATEGORIA
    ]
    if faltando:
        print(normalizar_erro(f"Categorias sem query cadastrada: {faltando}"))
        return False
    print("✅ Todas as categorias têm query cadastrada em QUERY_POR_CATEGORIA.\n")
    return True


if __name__ == "__main__":
    integro = checar_integridade_bancos()
    passou = rodar_testes()
    dedup_ok = checar_dedup_query_preserva_termo_central()
    llm_ok = checar_fallback_llm()
    cor_ok = checar_cor_primaria_por_categoria()
    sys.exit(0 if (integro and passou and dedup_ok and llm_ok and cor_ok) else 1)
