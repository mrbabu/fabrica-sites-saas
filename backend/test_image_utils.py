#!/usr/bin/env python3
"""
Suite de Testes - Categorização de Imagens (image_utils.py)
Valida mapear_categoria() contra uma grande variedade de nichos reais:
os 50 nichos de test_agentes.py, os 6 casos reportados como bugs em
produção (festa, buffet, centro de treinamento, turismo, pedreiro,
estacionamento) e variações de plural/gênero/acentuação.

Uso: python test_image_utils.py
"""

import sys

from image_utils import mapear_categoria, CATEGORIAS_ALIASES, SINAIS_GENERICOS, CATEGORIA_PADRAO

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
    ("Escolinha de Futebol", "sports_training_center__futebol"),  # atributo "futebol" bate no keyword
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
    sys.exit(0 if (integro and passou) else 1)
