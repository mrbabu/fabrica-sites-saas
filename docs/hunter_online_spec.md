# Hunter Online — Especificação Técnica

**Status: BACKLOG P2. Não implementado.** Documento arquitetural apenas —
nenhum código, endpoint, agente ou migration deve ser criado a partir dele
antes do critério da seção 9 ser atingido.

## 1. Objetivo

Evoluir a prospecção comercial interna da fábrica de sites: permitir
encontrar empresas potenciais por nicho e localização de forma mais rica
que o script atual (parâmetros dinâmicos, qualificação, exportação),
mantendo a coleta de dados dentro dos mesmos limites legais já adotados
pelo projeto.

## 2. Escopo — ferramenta interna, não produto pro cliente

Uso: Raphael e Bruno, autenticados. **Não é uma feature de SaaS pro cliente
final** — o cliente só vê o resultado final (o link do site gerado em
`/demo/preview/{slug}`), nunca a ferramenta de prospecção ou de geração.
Mesmo modelo de acesso do `/demo` de hoje: login interno
(`backend/auth_demo.py`), nunca público.

```
Login interno (/demo/login)
      |
      v
Hunter Online
      |
      v
Busca empresas por nicho + região
      |
      v
Qualificação (score)
      |
      v
Exportação XLS
      |
      v
Abordagem comercial manual (fora do sistema)
```

## 3. Não confundir com `AgenteHunter`

Existem dois "Hunter" no projeto — nomes iguais, responsabilidades
completamente diferentes. Esta spec é só sobre o segundo.

| | `backend/agents/hunter.py` (`AgenteHunter`) | Hunter Online (esta spec) |
|---|---|---|
| Direção | Inbound — processa mensagem que o lead já mandou | Outbound — sai procurando empresas ativamente |
| Faz o quê | Regex sobre texto de WhatsApp recebido, extrai nome/nicho/cor/localização pro onboarding | Busca na Google Places API por nicho+região, monta lista de oportunidades |
| Base técnica hoje | Já implementado, esqueleto validado (`ROADMAP.md` Fase 3) | `backend/scripts/buscar_leads_google_maps.py` |
| Relação entre os dois | **Nenhuma.** Não há reaproveitamento de código entre eles — só compartilham o nome "Hunter" |

## 4. Base técnica atual (ponto de partida real)

`backend/scripts/buscar_leads_google_maps.py`, estado verificado em código:

- Cidades e buscas **fixas** num dicionário (`CIDADES = {"vitoria": {...}, "paraty": {...}}`), cada uma com uma lista pré-programada de combinações nicho+bairro — não existe hoje "usuário digita nicho + raio".
- Usa Google Places API (Text Search, versão New), campos: `displayName`, `nationalPhoneNumber`, `websiteUri`, `id`.
- Saída: CSV com `nome, bairro, nicho, whatsapp, status, data_contato` — sem site, sem score, sem link do Google Maps, sem Instagram.
- Já filtra por "sem site" (usa `websiteUri` da API pra descartar quem já tem).

## 5. Evolução proposta

### 5.1 Entrada dinâmica

```json
{
  "nicho": "clinica odontologica",
  "cidade": "Vitoria",
  "estado": "ES",
  "raio_km": 20,
  "quantidade": 100
}
```

Substitui o dicionário fixo `CIDADES` por parâmetros informados na hora da
busca.

### 5.2 Dados coletados (primeira versão, via Google Places API)

Nome, categoria, endereço, telefone, cidade, bairro, URL do Google Maps —
tudo já disponível pela mesma API usada hoje.

### 5.3 Enriquecimento futuro

Possui site, qualidade do site, domínio próprio, presença digital,
oportunidade comercial — análise sobre os dados já coletados, sem fonte
de dado nova.

## 6. Redes sociais — regra explícita

**Instagram e Facebook não são coletados automaticamente.** Motivo: o
`ROADMAP.md` já excluiu esses canais da coleta automatizada por risco de
ToS/anti-bot da Meta (decisão vigente, não desta spec). Campo no
resultado fica manual:

```
Instagram: [Não analisado] / [Encontrado manualmente: @perfil]
```

Nunca um checkbox de filtro automático (`☑ Instagram ativo` está errado —
implica coleta automatizada que não deve existir).

## 7. Score comercial (modelo, não implementado)

```
Sem site               +40
Sem WhatsApp           +20
Segmento prioritário   +20
Google Meu Negócio ativo +10
Telefone/contato disponível +10
```

Não depende de nenhum dado de Instagram/Facebook. Modelo especulativo —
os pesos exatos só devem ser calibrados com dados reais de conversão
(ver critério de saída do backlog, seção 9), não fixados agora.

## 8. Exportação

Formato `.xlsx` (mesmo padrão de `exportar_leads_excel.py`, já existente):

| Campo | Origem |
|---|---|
| Empresa | Google |
| Categoria | Google |
| Cidade / Bairro | Google |
| Telefone | Google |
| URL Google Maps | Google |
| Possui site | análise (websiteUri) |
| Score | cálculo interno |
| Observações | manual/IA |
| Status contato | CRM (planilha de funil, ver `MEMORY.md`/discussão do dia) |

## 9. Critério para sair do backlog

Só iniciar quando:
- 15-20 clientes avaliados (mesmo gate do `docs/playbook_dfy_v1.md`, seção 9);
- processo comercial validado com os leads que já existem hoje;
- volume de leads virar o gargalo real (hoje o gargalo é contato/conversão,
  não geração de leads — ver auditoria de 2026-07-21).

Até lá, o script atual (`buscar_leads_google_maps.py`) já é suficiente pro
volume da fase de validação.

## 10. Segurança

Acesso só via o login interno já existente (`/demo/login`), mesma sessão
de 15 minutos — não um sistema de auth separado. Nunca exposto sem
autenticação.

## 11. Política de abordagem comercial — sem disparo automático

**Regra que define a arquitetura inteira: não existe envio automático de
mensagem.** O "Vendedor" aqui não é um agente que dispara WhatsApp sozinho
— é um assistente que prepara texto pra um humano copiar, revisar e
enviar manualmente. Isso não é uma limitação temporária, é a mesma
política já vigente pro guardrail #1 do `ROADMAP.md` (nunca outbound
automatizado no WhatsApp, risco de banimento sem API oficial/opt-in) —
esta seção só deixa explícito que ela também vale aqui, pra não ser
reinterpretada no futuro como "o Vendedor manda mensagem sozinho".

O sistema:
- ✅ gera sugestão de mensagem (inicial, follow-up, resposta a objeção),
  adaptada ao lead encontrado;
- ✅ permite copiar e editar o texto;
- ✅ registra status manual (contatado, respondeu, etc.).

O sistema não:
- ❌ envia WhatsApp automaticamente;
- ❌ acessa a conta de WhatsApp do usuário;
- ❌ dispara campanhas ou controla agenda de contatos;
- ❌ decide sozinho quem abordar ou quando.

Fluxo real:

```
Lead encontrado
      |
      v
IA sugere abordagem
      |
      v
Humano revisa e edita
      |
      v
Humano envia (fora do sistema, no próprio WhatsApp)
      |
      v
Humano atualiza status
```

## 12. Estrutura da página interna (esboço, não implementar ainda)

```
/demo/login
      |
      v
Dashboard interno
      |
      +-- Site Constructor (já existe: /demo, /demo/lista)
      |     - criar demo, selecionar nicho, gerar site, preview
      |
      +-- Busca Leads (esta spec)
            - selecionar nicho + região, executar busca
            - qualificar oportunidades (score)
            - exportar XLS
            - Assistente Comercial: sugestão de mensagem (seção 11),
              nunca envio automático
```

Não vira CRM completo agora — só as duas frentes acima.

## 13. Não implementado

Documento apenas. Nenhum código, agente, endpoint, migration ou dependência
nova foi criado a partir desta spec.
