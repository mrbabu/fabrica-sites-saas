# ⚙️ Setup - Fábrica de Sites SaaS

## 🔑 Configuração da API Key (IMPORTANTE!)

Antes de rodar a API, você precisa configurar sua chave da Anthropic API.

### 1️⃣ Obtenha Sua Chave API

1. Vá para: **https://console.anthropic.com/**
2. Faça login (crie uma conta se não tiver)
3. No menu lateral, clique em **"API Keys"**
4. Clique em **"Create Key"**
5. Copie a chave que começa com `sk-ant-`

### 2️⃣ Configure o Arquivo `.env`

Um arquivo `.env` foi criado na raiz do projeto. Abra-o e substitua o placeholder pela sua chave real:

**Arquivo:** `E:\fabrica-sites-saas\.env`

```bash
# ❌ ANTES (Placeholder - NÃO FUNCIONA)
ANTHROPIC_API_KEY=sk-ant-sua-chave-real-aqui

# ✅ DEPOIS (Com sua chave real)
ANTHROPIC_API_KEY=sk-ant-v8p7q9x2j4k1m5n8...
```

**⚠️ SEGURANÇA:** 
- O arquivo `.env` está no `.gitignore` e **nunca** será commitado para o Git
- Nunca compartilhe sua chave API com terceiros
- Se vazar, revogue no console e gere uma nova

### 3️⃣ Reinicie o Servidor

```bash
# Pare o servidor atual (Ctrl+C)
# Depois rode novamente:
python app.py
```

Esperado: 
```
🚀 API iniciada com sucesso
📚 Documentação: http://localhost:8000/docs
🔌 Endpoint: POST http://localhost:8000/api/v1/generate-site
```

### 4️⃣ Teste a API

No navegador, acesse:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Ou via terminal:
```bash
python test_api.py
```

---

## 📋 Estrutura do Projeto

```
fabrica-sites-saas/
├── .env                    # ✅ Variáveis de ambiente (NÃO comite!)
├── .env.example           # 📋 Template para documentar variáveis necessárias
├── .gitignore             # 🔒 Arquivo para proteger .env e outros
├── app.py                 # 🚀 FastAPI REST Server
├── agent_construtor.py    # 🤖 Motor IA (Claude 3.5 Sonnet)
├── schema_validator.py    # ✅ Validação Pydantic V2
├── metrics.py             # 📊 Logging e Métricas
├── test_api.py            # 🧪 Testes da API
├── index.html             # 🎨 Template Universal (JSON → HTML)
└── requirements.txt       # 📦 Dependências Python
```

---

## 🚀 Workflow Completo

1. **Usuário envia dados via n8n** (WhatsApp → n8n)
2. **n8n chama** `POST /api/v1/generate-site`
3. **app.py recebe** nome_empresa, nicho, cor_preferida
4. **agent_construtor.py** usa Claude para gerar site-config.json
5. **API retorna** JSON validado e pronto para deploy
6. **n8n commita** em Git e faz deploy na Vercel

---

## ❓ Troubleshooting

### Erro: `invalid x-api-key`
- Verifique se a chave no `.env` está correta
- Cofira se tem espaços extras antes/depois
- Obtenha uma nova chave em https://console.anthropic.com/

### Erro: `ModuleNotFoundError: No module named 'dotenv'`
- Instale: `pip install python-dotenv`
- Já deve estar em `requirements.txt`

### Erro: `ANTHROPIC_API_KEY não fornecida`
- Verifique se o arquivo `.env` existe
- Reinicie o servidor após criar/editar `.env`

---

## 📞 Próximos Passos

- [x] API está pronta com Pydantic V2 (Zero warnings!)
- [x] Autenticação configurada
- [ ] Integração com n8n (Fase 5)
- [ ] Deploy na Vercel (Fase 3)
- [ ] Integração com WhatsApp (Fase 5)

🚀 **Você está pronto para a apresentação com Bruno!**
