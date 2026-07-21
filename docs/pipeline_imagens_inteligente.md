# Pipeline Inteligente de Imagens — Especificação Técnica

**Status: não implementado.** Este documento registra uma arquitetura proposta
para avaliação futura — nenhum código foi alterado a partir dele. Ver
critério de priorização na seção 8 antes de iniciar qualquer implementação.

## 1. Objetivo

Substituir o mapeamento fixo nicho → categoria de imagem
(`backend/image_utils.py::CATEGORIAS_NICHO`) por um sistema que gera um
"briefing de cena" por seção do site via IA, e resolve esse briefing através
de múltiplos provedores de imagem em cascata — banco próprio, bancos de
fotos gratuitos, geração via IA — em vez de depender só de palavra-chave
por nicho inteiro.

## 2. Estado atual (ponto de partida real, verificado em código)

- `mapear_categoria()`: mapeamento determinístico texto-livre → 11
  categorias fixas (bakery, restaurant, medical_clinic, auto_repair, hotel,
  beauty_salon, law_office, accounting_office, gym, pet_shop, construction),
  casamento por substring de palavra-chave, fallback pra `small_business`.
- `QUERY_POR_CATEGORIA`: query curada em inglês por categoria, usada na
  busca Unsplash.
- `obter_imagens_categoria()` + cache em
  `backend/cache/imagens_categorias.json`.
- Fallback de segurança: LoremFlickr com `?lock=` estável quando Unsplash
  falha ou não está configurado — nunca fica um campo de imagem vazio.
- **Limitações conhecidas:**
  - Nichos fora das 11 categorias (ex.: Imobiliária, Educação, Tecnologia)
    caem no genérico `small_business`.
  - A granularidade é por nicho inteiro, não por seção — hero, sobre e
    cada item de `sections[]` usam a mesma categoria de imagem.
  - Ordem de match por substring pode causar colisão (ex.: "Clínica
    Estética" bate em `medical_clinic` antes de `beauty_salon`, porque
    "clinica" aparece primeiro no dicionário).

## 3. Arquitetura proposta

### 3.1 Conceito central: briefing de cena, não categoria

Em vez de "nicho X → categoria Y", o sistema gera, por seção do
`site-config.json` (hero, about, cada item de `sections[]`, equipe se
houver), um briefing estruturado:

```json
{
  "secao": "hero",
  "descricao": "advogado atendendo um cliente em escritório moderno",
  "estilo": "fotografia profissional",
  "proporcao": "16:9",
  "cores_dominantes": "tons sóbrios, azul-marinho"
}
```

Gerado na mesma chamada de IA que já produz o copy (mesma etapa de
`gerar_config_site()`, evita custo de API extra), a partir do nicho +
`descricao_negocio` (campo já existente no formulário DFY) + eventual
descrição de ambiente enviada pelo cliente (campo novo opcional, ver
seção 6).

### 3.2 Interface de provedor (Protocol/ABC — ilustrativo, não código a integrar)

```python
class ProvedorImagem(Protocol):
    def buscar(self, briefing: BriefingCena) -> Optional[ImagemResultado]:
        """Retorna uma imagem que atende ao briefing, ou None se não encontrar."""

class ImagemResultado:
    url: str
    provedor: str          # "banco_proprio" | "pexels" | "unsplash" | "pixabay" | "flux" | "sdxl"
    licenca: str           # rótulo curto pra auditoria/exibição se necessário
    custo_estimado: float  # 0.0 pra bancos gratuitos, custo por imagem pra geração via IA
```

Cada provedor — o atual (Unsplash) e os futuros (Pexels, Pixabay, Hugging
Face, Flux/SDXL) — implementa essa interface, plugável, sem o motor
conhecer detalhes de cada API.

### 3.1.1 Catálogo de cenas (Scene Graph)

Em vez do briefing nascer solto por seção, cada seção do template mapeia
para um pequeno catálogo de cenas possíveis — o motor escolhe (ou a IA
escolhe) qual cena contar, não qual "imagem buscar":

```
Hero      → pessoa atendendo cliente | fachada | ambiente interno | produto em destaque | equipe
Sobre     → profissional trabalhando | bastidores | equipe | processo
Serviços  → execução | equipamento | atendimento | resultado
```

Isso desloca a pergunta de "que imagem usar" para "que história essa
seção precisa contar" — melhora tanto a query de busca em banco de fotos
quanto o prompt de geração por IA, porque a cena já vem com intenção
narrativa, não só palavra-chave solta.

### 3.3 Fluxo de decisão (cascata)

1. Fotos reais do cliente (`portfolio_urls`) — já implementado hoje,
   sempre prioridade máxima, sem mudança.
2. Banco próprio curado (evolução do `CATEGORIAS_NICHO` atual) — zero
   custo, resposta instantânea, mesma governança de qualidade que já
   existe.
3. Bancos de fotos gratuitos (Pexels → Unsplash → Pixabay, ordem a
   validar por disponibilidade de quota) — resolvidos via busca por
   texto derivada do briefing.
4. Geração via IA (Flux/SDXL/Pollinations) — só quando os anteriores não
   retornarem resultado satisfatório; maior custo/latência, deve ser
   último recurso antes do fallback de segurança.
5. Fallback de segurança final: LoremFlickr com `?lock=` estável — mantém
   a garantia atual de "nunca fica vazio".

Cada provedor tem timeout e tratamento de erro isolado — um provedor fora
do ar não derruba a cascata (mesmo princípio de `ErroBancoImagens` hoje).

### 3.4 Pontuação de provedores (evolução futura, pós-MVP deste épico)

Depois que a cascata básica (seção 3.3) estiver rodando, cada resolução
de briefing pode registrar um score simples por provedor — qualidade
percebida, tempo de resposta, custo — pra permitir reordenar a cascata
com base em desempenho real em vez de ordem fixa hardcoded. Não é
pré-requisito pra primeira versão: só vale a pena depois de ter volume
de gerações suficiente pros números terem significado.

## 4. Cache

Mesma estratégia de hoje, generalizada: cache por chave
`(briefing_hash, provedor)` em vez de só por categoria — evita rebuscar a
mesma cena repetidamente. TTL a definir (imagens de banco gratuito não
mudam; imagens geradas por IA podem ser cacheadas indefinidamente já que
têm custo).

## 5. Licenciamento e custo por provedor (a validar antes de habilitar)

- **Pexels/Pixabay/Unsplash:** gratuitos para uso comercial dentro dos
  limites de cada licença — confirmar termos exatos antes de habilitar
  cada um (mesmo cuidado já aplicado a Facebook/Instagram/GetNinjas no
  `ROADMAP.md`: não assumir uso livre sem checar ToS).
- **Hugging Face Inference API:** camada gratuita com rate limit; acima
  disso, custo por chamada.
- **Flux / SDXL:** gratuito se rodado localmente (exige GPU); via API de
  terceiros, custo por imagem.
- **Pollinations AI:** gratuito em vários endpoints, sem SLA — tratar
  como provedor de menor prioridade/confiabilidade.

Custo estimado por site gerado deve ser somado ao custo de IA já
rastreado (`docs/playbook_dfy_v1.md`, seção 7 — "Produto: custo de IA").

## 6. Oportunidade adicional (fora do escopo desta spec, só registrada)

Campo opcional no formulário DFY: "Descreva o ambiente da sua empresa" —
texto livre que alimenta o briefing de cena com mais fidelidade. Não
confundir com upload de imagem pelo cliente (fora de escopo por decisão
já registrada em memória — feature de assets do cliente segue bloqueada).

## 7. Guardrails

- Nunca gerar imagem que sugira depoimento/prova social falsa — mesma
  regra do `playbook_dfy_v1.md` seção 5, também vale pra imagem gerada
  por IA.
- Toda imagem gerada por IA deve ser uma cena genérica (escritório,
  ambiente), nunca tentar simular o cliente/produto real do negócio sem
  que ele tenha fornecido referência.

## 8. Critério para priorizar esta implementação

Só depois do gate de 15-20 vendas DFY fechadas manualmente (mesmo
critério do `playbook_dfy_v1.md` seção 9) **e** quando o banco fixo atual
(`CATEGORIAS_NICHO`) se mostrar insuficiente na prática — ou seja, quando
aparecer um cliente real de nicho não coberto hoje (Imobiliária, Educação,
Tecnologia) e a imagem genérica prejudicar a demo/venda. Não priorizar
por antecipação de nicho que ainda não está sendo vendido.

## 9. Escopo desta versão

Documento apenas. Nenhuma implementação, nenhuma mudança em
`image_utils.py` ou `agent_construtor.py` foi feita a partir desta
especificação.
