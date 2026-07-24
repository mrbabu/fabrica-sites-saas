# 02 — Arquitetura

> Fonte: leitura direta de `backend/app.py`, `backend/routers/*.py`, `Dockerfile`, `docker-compose.prod.yml`, `infra/zero_trust_deploy.md`, `index.html`, `vendas.html`. Diagramas descrevem o que o código faz hoje, não o que a documentação antiga (`CLAUDE.md`) descreve — ver seção "Divergência" ao final.

## Visão geral: dois sistemas independentes

O projeto não é um site só — são **dois sites estáticos** (Vercel) e **um backend** (VM própria), com fronteiras deliberadas entre eles:

- **`vendas.html`** — a landing comercial (vende o produto). Zero dependência do backend: busca `vendas-config.json` direto do CDN da Vercel via `fetch()`. Continua no ar mesmo se o backend cair.
- **`index.html`** — o template que vira o site de cada cliente pago. Também estático, também na Vercel, injeta os dados de `site-config.json` (por cliente).
- **Backend FastAPI** (`backend/app.py`) — roda numa VM Oracle Cloud, nunca na Vercel. É onde vivem: o motor de geração de site, o Postgres, o Hunter, o login da ferramenta interna.

```mermaid
flowchart TB
    subgraph Vercel["Vercel — estático, sem backend"]
        VENDAS["vendas.html<br/>(landing comercial)"]
        INDEX["index.html<br/>(template do site do cliente)"]
    end

    subgraph VM["VM Oracle Cloud — Zero Trust"]
        subgraph Docker["Docker Compose"]
            BACKEND["backend (FastAPI)<br/>porta 8000, só rede interna"]
            DB[("Postgres<br/>só rede interna")]
            TUNNEL["cloudflared<br/>(Cloudflare Tunnel, saída)"]
        end
    end

    LEAD_FINAL["Cliente final<br/>(nunca faz login)"]
    OPERADOR["Operador interno<br/>(login em /demo/login)"]

    LEAD_FINAL -->|acessa| VENDAS
    LEAD_FINAL -->|recebe link /demo/preview/slug<br/>fora do sistema, manual| BACKEND
    VENDAS -.->|fetch client-side, zero dependência| VENDAS
    OPERADOR -->|Tailscale + login| BACKEND
    BACKEND <--> DB
    BACKEND <--> TUNNEL
    INDEX -.->|consome site-config.json por cliente| INDEX
```

## Fluxo interno do backend (ferramenta que o operador usa)

```mermaid
flowchart TB
    LOGIN["/demo/login<br/>auth_demo.py<br/>sessão de 15 min"]

    LOGIN --> HUNTER["/hunter<br/>routers/hunter.py<br/>busca Google Places"]
    HUNTER --> HUNTERDB[("hunter_buscas /<br/>hunter_leads<br/>(Postgres)")]
    HUNTERDB --> LEADS["/hunter/leads<br/>pipeline de status<br/>+ templates de mensagem"]

    LOGIN --> DEMO["/demo<br/>routers/demo.py<br/>formulário de geração"]
    DEMO --> API["POST /api/v1/demo-dfy<br/>routers/demo_dfy.py"]
    API --> AGENTE["AgenteConstrutor.executar()<br/>agent_construtor.py<br/>(congelado, estável)"]

    AGENTE --> AI["AIProvider<br/>ai_provider.py<br/>Gemini → NVIDIA NIM → Anthropic → Ollama"]
    AGENTE --> IMG["image_utils.py<br/>banco de imagens por categoria<br/>+ fallback determinístico"]
    AGENTE --> VALID["schema_validator.py<br/>Pydantic, valida antes de aceitar"]

    AGENTE --> SITESDB[("tabela sites<br/>(Postgres, JSONB)")]
    SITESDB --> LISTA["/demo/lista<br/>Biblioteca de Demos"]
    SITESDB --> PREVIEW["/demo/preview/slug<br/>injeta config no index.html"]

    LEADS -.->|link manual, fora do fluxo automatizado| DEMO
```

## Deploy: dois pipelines independentes

```mermaid
flowchart LR
    subgraph Frontend["Frontend estático"]
        GIT1["git push origin main"] --> VERCEL["Vercel<br/>auto-deploy"]
        VERCEL --> SITE["vendas.html / index.html<br/>no ar em segundos"]
    end

    subgraph Backend["Backend"]
        GIT2["git push origin main"] --> SSH["SSH via Tailscale<br/>(100.64.197.76)"]
        SSH --> PULL["git pull"]
        PULL --> BUILD["docker compose -f docker-compose.prod.yml<br/>up -d --build backend"]
        BUILD --> LIVE["Container atualizado<br/>Postgres roda migrations Alembic no boot"]
    end
```

Nenhum dos dois pipelines depende do outro. Um push que só mexe em `vendas.html` não precisa (e não deve) disparar rebuild do backend — e vice-versa.

## Modelo de dados (Postgres, `backend/models_db.py`)

```mermaid
erDiagram
    SITES {
        string slug PK
        string nome_empresa
        string nicho
        jsonb config
    }
    LEADS {
        string whatsapp PK
        string status "default: inbound_recebido"
    }
    HUNTER_BUSCAS {
        int id PK
        string nicho
        string cidade
        int quantidade
        datetime created_at
    }
    HUNTER_LEADS {
        int id PK
        int busca_id FK
        string place_id
        string nome_empresa
        string status "pendente|contatado|respondeu|demo_enviada|cliente|descartado"
        string slug_demo "nullable, texto solto — SEM FK real pra sites.slug"
    }

    HUNTER_BUSCAS ||--o{ HUNTER_LEADS : "gera"
    HUNTER_LEADS }o..o{ SITES : "vínculo manual por texto (slug_demo), sem integridade referencial"
```

`LEADS` (webhook do WhatsApp) e `HUNTER_LEADS` (prospecção do Hunter) são tabelas **separadas e não relacionadas** hoje — um contato que chega pelo WhatsApp oficial não se cruza automaticamente com um lead que o Hunter encontrou.

## Zero Trust — por que não há porta aberta

`docker-compose.prod.yml` não publica nenhuma porta de `db`/`backend` pro host (sem `ports:` nesses serviços — só existem na rede Docker interna `internal_net`). O único jeito de entrar é:
- **Tailscale** (mesh privada) — pra administração da máquina (SSH).
- **Cloudflare Tunnel** (`cloudflared`, saída apenas) — pra tráfego HTTP chegar no backend de fora, sem nunca abrir porta de entrada na VM.

Isso está documentado em `infra/zero_trust_deploy.md` e é a razão pela qual, por exemplo, tentar conectar direto num Postgres de produção a partir de uma máquina de desenvolvimento comum simplesmente não funciona — não é bug, é a arquitetura funcionando como projetada.

## Divergência entre documentação antiga e arquitetura real

`CLAUDE.md` (raiz) e `ROADMAP.md` ainda descrevem o backend como pendente de deploy em **Render/Railway**. Isso foi substituído pela arquitetura Zero Trust em Oracle Cloud (commits a partir de `8b1e736`, documentado em `infra/zero_trust_deploy.md`), mas os dois documentos-fonte nunca foram atualizados para refletir essa mudança. Qualquer leitura futura desses dois arquivos (por uma pessoa ou por uma IA) deve desconfiar dessa seção específica até que seja corrigida.
