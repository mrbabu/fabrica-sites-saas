# Fábrica de Sites SaaS

WaaS (Website as a Service) para MEIs e pequenos negócios locais — hoje
com foco em clínicas médicas (odontologia, fisioterapia, dermatologia) na
Grande Vitória-ES. Um Agente Construtor de IA transforma nome + nicho +
cor em um site profissional completo em segundos, publicado a partir de
uma estrutura de template única controlada 100% por JSON.

Ver `ROADMAP.md` para o plano de negócio completo (fases 0-4, guardrails)
e `CLAUDE.md` para o contexto técnico usado por assistentes de IA neste
repositório.

## Arquitetura

```
Nome + nicho + cor  →  Agente Construtor (IA)  →  site-config.json
                                                          │
                        ┌─────────────────────────────────┤
                        ▼                                  ▼
              index.html (template estático)     Postgres (persistência
              renderiza o JSON, no ar via              via API)
              Vercel — este é o site do cliente
```

- **Motor de produção**: `backend/agent_construtor.py` gera o
  `site-config.json` via IA (cadeia de provedores com fallback: Gemini →
  NVIDIA NIM → Anthropic → Ollama), com fallbacks determinísticos pra
  garantir que nenhum campo (imagem, SEO, rodapé) fique quebrado ou vazio.
  Motor considerado estável — não mexer sem necessidade explícita (ver
  `CLAUDE.md`).
- **Template estático**: `index.html`, HTML/Tailwind puro sem build,
  renderiza qualquer `site-config.json` dinamicamente. É o que o cliente
  final recebe — hospedado como site estático na Vercel.
- **Backend/API**: `backend/app.py` (FastAPI) expõe o Agente Construtor
  como REST, persiste os sites gerados em Postgres (`backend/db.py`,
  `backend/repository.py`, `backend/alembic/`), pronto pra ser chamado
  por automações (n8n, webhook do WhatsApp).
- **Demos de venda (Lovable)**: `backend/agents/vendedor.py` traduz
  qualquer `site-config.json` num prompt pronto pro Lovable (chat
  automatizado via "Build with URL", sem copiar/colar) — gera mockups
  visuais usados **só** pra demonstração comercial. Não substitui o
  motor de produção acima.
- **Agentes especializados** (`backend/agents/`): `hunter.py` (captura de
  lead via WhatsApp), `vendedor.py` (conecta ao Lovable, envia link de
  demo), `financeiro.py` (conciliação PIX) — esqueleto com lógica real,
  ainda sem integração de webhook real. Ver guardrails no topo do
  `ROADMAP.md` antes de mexer neles (risco de banimento de WhatsApp,
  gate de vendas manuais).

## Estrutura do projeto

```
fabrica-sites-saas/
├── index.html                    # template estático de produção
├── site-config.json              # config de exemplo/demo local
├── assets/logos/                 # logos normalizados de clientes (gitignored)
├── backend/
│   ├── agent_construtor.py       # motor de geração via IA (congelado)
│   ├── ai_provider.py            # cadeia de provedores de IA com fallback
│   ├── schema_validator.py       # schema Pydantic do site-config.json
│   ├── image_utils.py            # normalização de logo/slug
│   ├── app.py                    # API FastAPI
│   ├── db.py / models_db.py / repository.py / alembic/   # persistência Postgres
│   ├── agents/                   # hunter.py, vendedor.py, financeiro.py
│   └── scripts/                  # gerar_portfolio_lovable.py, simular_esteira.py
├── docs/
│   └── fase2_scripts_whatsapp.md # scripts de abordagem comercial (Fase 2)
├── leads/
│   └── clinicas_grande_vitoria.example.csv   # estrutura da base de leads
├── infra/
│   ├── provision_ampere_ubuntu.sh   # provisionamento do host de produção
│   └── zero_trust_deploy.md         # runbook Tailscale + Cloudflare Tunnel + NSG
├── lovable_prompts/               # prompts + JSON dos mockups de venda (gitignored)
├── Dockerfile / docker-compose.yml       # stack de desenvolvimento local
├── docker-compose.prod.yml               # stack de produção Zero Trust (ARM64)
├── CLAUDE.md                      # contexto técnico pra assistentes de IA
└── ROADMAP.md                     # plano de negócio + guardrails
```

## Como rodar localmente

### Opção 1 — Docker (recomendado, replica produção)

```bash
cp .env.example .env   # preencher com chaves reais (ao menos um provedor de IA)
docker compose up -d --build
curl http://localhost:8000/health
```

Sobe backend (FastAPI) + Postgres juntos, com migration do Alembic
rodando automaticamente no start (`entrypoint.sh`).

### Opção 2 — Python direto

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Requer `DATABASE_URL` configurada em `.env` (ex.: Postgres local) pra
persistência via API funcionar — sem isso, `GET`/`POST` de site-config
ficam indisponíveis, mas a geração via CLI/`site-config.json` da raiz
continua funcionando.

### Gerar um site via API

```bash
curl -X POST "http://localhost:8000/api/v1/generate-site" \
  -H "Content-Type: application/json" \
  -d '{"nome_empresa": "Clínica Exemplo", "nicho": "Odontologia", "cor_preferida": "#0D9488"}'
```

## Status atual

**Fase 0 (fundação do negócio) concluída** — nicho e região definidos
(Clínicas Médicas/Saúde, Grande Vitória-ES), portfólio semente gerado.
**Fase 1 (MVP técnico) concluída** — motor estável, schema completo,
persistência em Postgres, containerização Docker, pipeline JSON→Lovable
validado ponta a ponta (2 demos publicadas). **Fase 2 (vendas manuais)**
em andamento — scripts de abordagem prontos, estrutura de leads pronta,
coleta de leads reais em progresso. Detalhe completo, checklist e
guardrails: ver `ROADMAP.md`.

Infraestrutura de produção Zero Trust (Tailscale + Cloudflare Tunnel +
Oracle Cloud Ampere ARM64, zero porta pública exposta) está desenhada e
pronta em `infra/`, aguardando disponibilidade de capacidade Ampere na
Oracle Cloud pra deploy.

## Tecnologias

- **Backend**: Python, FastAPI, SQLAlchemy + Alembic, Postgres
- **IA**: Gemini / NVIDIA NIM / Anthropic / Ollama (cadeia com fallback automático)
- **Frontend**: HTML5 + Tailwind (CDN) + JavaScript vanilla, zero build
- **Infra**: Docker, Docker Compose, Tailscale, Cloudflare Tunnel, Oracle Cloud (Always Free)
- **Demos comerciais**: Lovable (React + Tailwind, gerado via prompt)

---

**Fábrica de Sites SaaS** — sites profissionais em menos de 30 segundos.
