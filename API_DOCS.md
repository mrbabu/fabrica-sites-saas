# 🔌 API REST - Fábrica de Sites SaaS

## 📍 Visão Geral

O **FastAPI Server** transforma o `agent_construtor.py` em uma API REST profissional.

Permite que o **n8n** (ou qualquer sistema HTTP) envie dados simples e receba um `site-config.json` completo e validado.

---

## 🚀 Iniciar o Servidor

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

Adiciona:
- `fastapi` — Framework web
- `uvicorn` — Servidor ASGI
- `requests` — Para testar

### 2. Configurar API Key

```powershell
$env:ANTHROPIC_API_KEY='sk-ant-api03-xxxxxxxxxxxxxxxx'
```

### 3. Rodar o Servidor

```bash
python backend/app.py
```

Saída esperada:
```
============================================================
🚀 Iniciando Fábrica de Sites SaaS - API
============================================================

📚 Documentação interativa:
   http://localhost:8000/docs

🔌 Endpoint principal:
   POST http://localhost:8000/api/v1/generate-site

✨ Pressione Ctrl+C para parar
```

---

## 🔗 Endpoints

### 1️⃣ GET `/` — Info da API

**Descrição:** Retorna info básica da API

**URL:** `http://localhost:8000/`

**Response:**
```json
{
  "nome": "Fábrica de Sites SaaS - API",
  "versao": "1.0.0",
  "descricao": "Gera site-config.json automaticamente via IA",
  "endpoints": {
    "health": "GET /health",
    "generate": "POST /api/v1/generate-site",
    "docs": "GET /docs"
  }
}
```

---

### 2️⃣ GET `/health` — Health Check

**Descrição:** Verifica se a API está pronta

**URL:** `http://localhost:8000/health`

**Response:**
```json
{
  "status": "healthy",
  "agente_ativo": true,
  "api_version": "1.0.0",
  "timestamp": "2026-07-06T10:30:00.123456"
}
```

**Uso em shell:**
```bash
curl http://localhost:8000/health
```

---

### 3️⃣ POST `/api/v1/generate-site` ⭐ PRINCIPAL

**Descrição:** Gera um site-config.json completo

**URL:** `http://localhost:8000/api/v1/generate-site`

**Method:** `POST`

**Content-Type:** `application/json`

#### Request Body

```json
{
  "nome_empresa": "Tech Solutions",
  "nicho": "Desenvolvimento de Software",
  "cor_preferida": "#4F46E5",
  "salvar_arquivo": true
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `nome_empresa` | string | ✅ Sim | Nome da empresa (2-100 caracteres) |
| `nicho` | string | ✅ Sim | Ramo de atuação (ex: Software, Consultoria) |
| `cor_preferida` | string | ✅ Sim | Cor primária em hex (#RRGGBB) |
| `salvar_arquivo` | boolean | ❌ Não | Salvar JSON em arquivo? (padrão: true) |

#### Response (Success)

```json
{
  "status": "success",
  "data": {
    "metadata": {
      "siteTitle": "Tech Solutions - Software Inovador",
      "siteDescription": "Transforme seu negócio com soluções de software de ponta",
      "favicon": "💻"
    },
    "company": {
      "name": "Tech Solutions",
      "tagline": "Inovação em Código",
      "description": "Somos especialistas em...",
      "logo": "https://via.placeholder.com/180x50?text=Logo"
    },
    "colors": {
      "primary": "#4F46E5",
      "primaryDark": "#3730A3",
      "secondary": "#7C3AED",
      "accent": "#EC4899",
      "background": "#ffffff",
      "text": "#1f2937",
      "textLight": "#6b7280",
      "border": "#e5e7eb"
    },
    "hero": { /* ... */ },
    "sections": [ /* ... */ ],
    "services": [ /* ... */ ],
    "testimonials": [ /* ... */ ],
    "contact": { /* ... */ },
    "cta": { /* ... */ }
  },
  "timestamp": "2026-07-06T10:30:00.123456",
  "tempo_geracao_segundos": 8.45
}
```

#### Response (Error)

```json
{
  "status": "error",
  "error": "ValidationError",
  "detail": "Cor deve estar em formato hex válido: #RRGGBB",
  "timestamp": "2026-07-06T10:30:00.123456"
}
```

#### Exemplos de Uso

**cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/generate-site" \
  -H "Content-Type: application/json" \
  -d '{
    "nome_empresa": "Tech Solutions",
    "nicho": "Software",
    "cor_preferida": "#4F46E5"
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/generate-site",
    json={
        "nome_empresa": "Tech Solutions",
        "nicho": "Software",
        "cor_preferida": "#4F46E5"
    }
)

if response.status_code == 200:
    config = response.json()
    print(config['data'])  # site-config.json
else:
    print(f"Erro: {response.json()}")
```

**n8n (HTTP Request Node):**
```json
{
  "method": "POST",
  "url": "http://localhost:8000/api/v1/generate-site",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "nome_empresa": "{{ $node.WhatsApp.json.company_name }}",
    "nicho": "{{ $node.WhatsApp.json.business_type }}",
    "cor_preferida": "{{ $node.WhatsApp.json.color }}"
  }
}
```

---

### 4️⃣ GET `/api/v1/metrics` — Métricas

**Descrição:** Retorna estatísticas de uso da API

**URL:** `http://localhost:8000/api/v1/metrics`

**Response:**
```json
{
  "total_eventos": 45,
  "testes": {
    "total": 10,
    "sucesso": 10,
    "falhas": 0,
    "taxa_sucesso": 100.0,
    "tempo_medio_segundos": 8.234
  },
  "geracoes": {
    "total": 35,
    "sucesso": 35,
    "falhas": 0,
    "taxa_sucesso": 100.0,
    "tempo_medio_segundos": 8.150,
    "tokens_total": 52500,
    "custo_total_usd": 0.875
  },
  "validacoes": {
    "total": 35,
    "sucesso": 35,
    "falhas": 0,
    "taxa_sucesso": 100.0
  }
}
```

---

### 5️⃣ GET `/docs` — Swagger UI

**Descrição:** Documentação interativa e testável

**URL:** `http://localhost:8000/docs`

Permite testar todos os endpoints diretamente no navegador com interface visual.

---

## 🧪 Testes Locais

### Teste Rápido (Health Check)

```bash
python backend/test_api.py health
```

### Teste Único

```bash
python backend/test_api.py single "Minha Empresa" "Software" "#6366f1"
```

### Testar 5 Nichos

```bash
python backend/test_api.py
```

Vai testar:
1. Tech Solutions (Software)
2. Digital Boost Agency (Marketing)
3. Spa Wellness (Spa)
4. Pet Shop Amigos (Pet Shop)
5. Pizzaria do João (Pizzaria)

### Ver Métricas

```bash
python backend/test_api.py metrics
```

---

## 🔄 Fluxo com n8n

```
WhatsApp Input
    │
    ├─ Nome Empresa
    ├─ Nicho
    └─ Cor Preferida
    │
    ▼
n8n HTTP Request Node
    │
    POST http://localhost:8000/api/v1/generate-site
    │
    ▼
FastAPI Server (app.py)
    │
    ├─ Valida input (Pydantic)
    ├─ Chama agent_construtor.py
    ├─ Valida schema (ValidadorSchema)
    ├─ Registra métricas
    └─ Retorna JSON
    │
    ▼
n8n recebe site-config.json
    │
    ├─ Atualiza Git
    ├─ Faz commit
    ├─ Push GitHub
    └─ Deploy Vercel
    │
    ▼
URL do site pronta
    │
    ▼
Mensagem WhatsApp com link
```

---

## 📊 Documentação Automática

FastAPI gera documentação automática:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

Lá você pode:
- Ver todos os endpoints
- Testar com interface visual
- Copiar exemplos de código
- Ver schemas de request/response

---

## ⚙️ Configuração Avançada

### Mudar Porta

Por padrão roda em `8000`. Para mudar:

```python
# No final de app.py
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=9000,  # ← Mudar aqui
        reload=True,
        log_level="info"
    )
```

Depois rodar: `python backend/app.py`

### Desabilitar Reload

Para produção, tire `reload=True`:

```python
uvicorn.run(
    "app:app",
    host="0.0.0.0",
    port=8000,
    reload=False,  # ← Produção
    log_level="warning"
)
```

### Variáveis de Ambiente

```bash
# Para produção com Gunicorn/Uvicorn remoto
FASTAPI_ENV=production
FASTAPI_LOG_LEVEL=warning
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 🐳 Deploy em Docker (Próximo Passo)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

EXPOSE 8000

CMD ["python", "app.py"]
```

Build:
```bash
docker build -t fabrica-sites-api .
```

Run:
```bash
docker run -e ANTHROPIC_API_KEY='sk-ant-...' -p 8000:8000 fabrica-sites-api
```

---

## ⚠️ Limitações & Considerações

### Rate Limiting

Não há rate limiting implementado. Para produção com muitas requisições:

```bash
pip install slowapi
```

E adicionar middleware.

### Timeout

Atualmente: 60 segundos por requisição.

Se Claude demorar muito, a requisição falha. Considere:
- Aumentar timeout
- Implementar fila (Celery/Redis)
- Webhook para resposta assíncrona

### Logging

Logs vão para `console` + `metrics.log`.

Para produção, considere:
- Enviar para Datadog/New Relic
- Stack ELK (Elasticsearch, Logstash, Kibana)

---

## 🔐 Segurança

### Production Checklist

- [ ] `reload=False` no uvicorn
- [ ] `CORS` revisado (não use `*` em produção)
- [ ] API Key protegida (variável de ambiente, não hardcoded)
- [ ] HTTPS ativado (use reverse proxy nginx)
- [ ] Rate limiting implementado
- [ ] Logging centralizado
- [ ] Health checks configurados
- [ ] Container Docker com usuário não-root

---

## 📈 Próximos Passos

1. **Testar localmente** com `python backend/test_api.py`
2. **Integrar no n8n** usando endpoint principal
3. **Monitorar métricas** em `/api/v1/metrics`
4. **Containerizar** em Docker
5. **Deploy** em VPS/Cloud (AWS, DigitalOcean, etc)

---

## 📞 Troubleshooting

### "Connection refused on localhost:8000"
```
✅ Solução: Certificar que rodou python backend/app.py
```

### "ANTHROPIC_API_KEY not configured"
```
✅ Solução: 
$env:ANTHROPIC_API_KEY='sua-chave'
```

### "Timeout after 60 seconds"
```
✅ Solução: Claude demorou muito. Tente novamente
ou aumente timeout em app.py
```

### "Validation error on color"
```
✅ Solução: Verificar formato hex: #RRGGBB
Exemplo válido: #6366f1
```

---

## 🎓 Integração com n8n (Próxima Fase)

O n8n pode ser configurado para:

1. Receber dado do WhatsApp
2. Chamar este endpoint
3. Receber site-config.json
4. Fazer git commit
5. Deploy Vercel
6. Enviar link no WhatsApp

Documentação completa em: **FASE2_N8N.md** (será criada)

---

**API pronta para usar. Boa sorte!** 🚀
