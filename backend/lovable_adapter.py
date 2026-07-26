#!/usr/bin/env python3
"""
LovableAdapter: converte a EspecificacaoSite (ver prompt_builder.py,
agnóstica de plataforma) para o formato "Build with URL" do Lovable
(https://docs.lovable.dev/integrations/build-with-url) — prompt em texto
+ até 10 imagens de referência no hash da URL, sem API key, sem custo.

Botão opcional "Gerar no Lovable" (ver routers/demo_lista.py). Não
substitui o gerador atual — só traduz o que ele já produziu.
"""

from urllib.parse import quote

from prompt_builder import EspecificacaoSite, construir_especificacao

MAX_REFERENCIAS = 10  # limite combinado do Lovable (imagens + html)


def montar_prompt(spec: EspecificacaoSite) -> str:
    """Prompt em português com os dados já existentes na especificação —
    nada é reperguntado ao cliente nem inventado aqui."""
    partes = [
        f'Crie uma landing page profissional em português (Brasil) para "{spec.nome}".',
        f"Slogan: {spec.tagline}" if spec.tagline else "",
        f"Descrição do negócio: {spec.descricao}" if spec.descricao else "",
        f"Use como cor principal {spec.cor_primaria} e cor de destaque {spec.cor_destaque}." if spec.cor_primaria else "",
        ("Serviços oferecidos:\n" + "\n".join(f"- {t}: {d}" for t, d in spec.servicos)) if spec.servicos else "",
        ("Diferenciais competitivos:\n" + "\n".join(f"- {t}: {d}" for t, d in spec.diferenciais)) if spec.diferenciais else "",
        f'Chamada principal (CTA): "{spec.cta_titulo}" — {spec.cta_descricao}' if spec.cta_titulo else "",
        f"WhatsApp de contato: {spec.whatsapp} (inclua um botão visível de WhatsApp)." if spec.whatsapp else "",
        f"Endereço: {spec.endereco}." if spec.endereco else "",
        f'Link do Google Maps do negócio: {spec.google_maps_url} (inclua um mapa ou botão "como chegar" apontando pra esse link).' if spec.google_maps_url else "",
        spec.instrucao_identidade_visual or "",
        "Sem depoimentos fictícios — não invente avaliações de clientes.",
    ]
    return "\n\n".join(p for p in partes if p)


def montar_url(spec: EspecificacaoSite) -> str:
    """Só envia brand_assets reais do cliente (logo/fachada/equipe/
    portfólio) como referência visual — nunca imagem gerada pelo Image
    Engine (ver guardrail em prompt_builder.py). Sem brand_assets, o
    Lovable gera as imagens e o layout inteiro sozinho."""
    prompt = montar_prompt(spec)
    hash_partes = [f"prompt={quote(prompt)}"]
    for img in spec.brand_assets[:MAX_REFERENCIAS]:
        hash_partes.append(f"images={quote(img)}")
    return "https://lovable.dev/?autosubmit=true#" + "&".join(hash_partes)


def montar_url_lovable(config: dict) -> str:
    """Ponto de entrada usado pelos routers (mesma assinatura de antes:
    site-config -> URL) — agora composto por PromptBuilder (agnóstico de
    plataforma) + este adapter específico do Lovable."""
    return montar_url(construir_especificacao(config))
