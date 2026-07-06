# 🏗️ ROADMAP - Fábrica de Sites SaaS

## Visão de Longo Prazo

Transformar de um agente isolado para uma fábrica capaz de produzir centenas/milhares de sites com intervenção humana mínima.

```
├─ Fase 1: Validar o Motor (AGORA)
├─ Fase 2: Melhorar Confiabilidade  
├─ Fase 3: Separar Responsabilidades
├─ Fase 4: Template Único & Imutável
├─ Fase 5: Deploy Automático (n8n)
├─ Fase 6: Banco de Dados de Clientes
├─ Fase 7: Múltiplos Templates
├─ Fase 8: Agentes Especializados
└─ Fase 9: Escala em Produção
```

---

## 📊 FASE 1 — Validar o Construtor (FOCO ATUAL)

**Objetivo**: Garantir que o agente sempre produz JSON válido em qualquer nicho.

### Tarefas

- [x] ✅ Criar agent_construtor.py funcional
- [ ] Criar schema validator com Pydantic
- [ ] Criar suite de testes com 50 nichos
- [ ] Adicionar retry automático em falhas
- [ ] Registrar métricas de qualidade
- [ ] Documentar problemas encontrados

### Nichos para Testar (Prioridade)

```
1. Auto Elétrica
2. Academia
3. Consultoria Jurídica
4. Consultório Odontológico
5. Pet Shop
6. Pizzaria
7. Loja de Roupas
8. Clínica Médica
9. Agência de Marketing
10. Software/SaaS
... (40+ mais)
```

### Métricas a Acompanhar

- ✅ JSON válido (0 erros)
- ✅ Todos os campos preenchidos
- ✅ Paleta de cores harmônica
- ✅ Copys sem repetição
- ✅ Tempo de geração
- ✅ Custo por chamada API
- ✅ Taxa de sucesso/erro

---

## 🔧 FASE 2 — Melhorar Confiabilidade

**Objetivo**: Sistema de auto-correção que elimina falhas humanas.

### Arquitetura

```
Input
  ↓
Validação (Schema)
  ↓
Claude Gera
  ↓
Validação do Output
  ├─ Se OK → Salvar ✅
  └─ Se ERRO → Tentar Correção Automática
      ↓
      Claude Corrige
      ↓
      Validação 2x
      ├─ Se OK → Salvar ✅
      └─ Se ERRO → Log + Falha
```

### Implementar

- Validador com Pydantic Schema
- Retry automático (até 3x)
- Fallback para valores padrão
- Logging completo

---

## 📦 FASE 3 — Separar Responsabilidades

**Objetivo**: Modularizar para facilitar manutenção e trocar modelos IA.

### Nova Estrutura

```
/agentes/
├── agent_paleta.py       # Gera 8 cores hex
├── agent_copy.py         # Cria conteúdo persuasivo
├── agent_json.py         # Estrutura JSON final
├── agent_validator.py    # Valida schema
└── agent_builder.py      # Orquestra tudo
```

### Benefício

- Trocar Claude por GPT/Gemini em uma seção
- Testar agentes isoladamente
- Versionar cada componente
- Facilitar debug

---

## 🎨 FASE 4 — Template Único & Imutável

**Objetivo**: HTML NUNCA muda após lançamento.

### Contrato

```
Se o JSON segue o schema → HTML renderiza perfeito
Se faltar campo no JSON → Usa fallback padrão
Se campo errado → Ignora com log
```

### Implementar

- Testes de compatibilidade template ↔ JSON
- Versionamento de schema
- Documentação de breaking changes
- Testes de regressão

---

## 🚀 FASE 5 — Deploy Automático (n8n)

**Objetivo**: Do input até URL pronta sem abrir VSCode.

### Fluxo n8n

```
WhatsApp Input
  ↓
Validar Dados
  ↓
Webhook → Python
  ↓
Gerar site-config.json
  ↓
Atualizar Arquivos
  ↓
Git Commit + Push
  ↓
Deploy Vercel (Automático)
  ↓
Receber URL
  ↓
Mensagem WhatsApp ✅
```

### Componentes

- Webhook n8n recebendo dados
- Integração Vercel API
- GitHub Actions trigger
- Notificação automática

---

## 💾 FASE 6 — Banco de Dados de Clientes

**Objetivo**: Persistência + Histórico.

### Schema Banco

```sql
clientes:
├── id (UUID)
├── nome
├── nicho
├── cor_primaria
├── dominio
├── subdominio
├── config_json (JSONB)
├── status (ativo/inativo)
├── plano (básico/pro/enterprise)
├── pagamento_status
├── created_at
├── updated_at
└── deploy_url
```

### Benefício

- Rastrear clientes
- Histórico de alterações
- Analytics
- Regenerar sites facilmente

---

## 🎭 FASE 7 — Múltiplos Templates

**Objetivo**: Diferentes layouts, mesmo schema JSON.

### Tipos de Template

```
├── Landing (Conversão)
├── Institucional (Apresentação)
├── Clínica (Agendamento)
├── Restaurante (Delivery)
├── Advogado (Contato)
├── Imobiliária (Listings)
├── Academia (Membros)
└── Hotel (Reserva)
```

### Implementar

- Cada template em pasta própria
- Mesmo schema JSON
- Sistema de seleção no n8n
- Testes de compatibilidade

---

## 🤖 FASE 8 — Agentes Especializados

**Objetivo**: Qualidade superior com agentes focados.

### Equipe de Agentes

```
Agente Copy
  ↓ Gera copys persuasivas

Agente SEO  
  ↓ Otimiza títulos, metas

Agente Paleta
  ↓ Paleta harmônica

Agente Imagens
  ↓ Gera/seleciona imagens

Agente JSON
  ↓ Estrutura final

Agente QA
  ↓ Valida tudo
```

### Comunicação

- Todos conversam pelo JSON
- Cada um adiciona/atualiza seu campo
- Validação incremental
- Rollback se algo quebrar

---

## 🌍 FASE 9 — Escala em Produção

**Objetivo**: Sistema robusto, escalável, 24/7.

### Arquitetura Finalizada

```
┌─────────────────┐
│   WhatsApp      │
│   (Interface)   │
└────────┬────────┘
         │
┌────────▼────────┐
│   n8n (Cloud)   │
│   (Orquestrador)│
└────────┬────────┘
         │
┌────────▼──────────┐
│  Python API       │
│  (Servidores VPS) │
├─ Agent Builder    │
├─ Validator        │
└─ Logger/Metrics   │
         │
┌────────┴──────────┐
│                   │
▼                   ▼
PostgreSQL      Redis Cache
(Clientes)      (Config)
│                   │
└────────┬──────────┘
         │
┌────────▼──────────┐
│   GitHub + CI/CD  │
│   (Versionamento) │
└────────┬──────────┘
         │
┌────────▼──────────┐
│  Vercel (Deploy)  │
│  (Sites ao Vivo)  │
└────────┬──────────┘
         │
    Centenas
    de Sites
    Rodando
```

### Tecnologias

- **Message Broker**: RabbitMQ/Redis
- **Container**: Docker + Docker Compose
- **Orquestração**: n8n (ou Airflow para escala)
- **Banco**: PostgreSQL + Redis
- **Versionamento**: Git + GitHub
- **Logs**: ELK Stack ou Datadog
- **Monitoramento**: Prometheus + Grafana

---

## ⚙️ Princípios Arquiteturais

### 1. JSON Schema Driven

```
Template HTML → Depende APENAS de site-config.json
site-config.json → Segue um schema fixo
Agentes → Preenchem campos específicos do schema
```

### 2. Validação Rigorosa

```
IA não escreve livremente
IA preenche um "contrato" (schema) já definido
Validador rejeita qualquer coisa fora do contrato
```

### 3. Separação de Responsabilidades

```
Cada agente = uma tarefa
Cada agente = testável isoladamente
Comunicação via JSON
Fácil trocar um agente depois
```

### 4. Idempotência

```
Mesmo input → Mesmo output
Reexecutar ≠ Duplicar
Sistema é determinístico
```

### 5. Observabilidade

```
Tudo é logado
Métricas de tudo
Possível rastrear qualquer erro
```

---

## 📋 Próxima Ação (Imediata)

### Passar de:
```
agent_construtor.py
↓
JSON (às vezes ruim)
```

### Para:
```
schema_validator.py (Pydantic)
test_suite.py (50 nichos)
metrics.py (logging)
agent_construtor.py (melhorado)
↓
JSON (sempre válido) ✅
```

### Checklist Fase 1

- [ ] Validador com Pydantic
- [ ] Suite de testes com 50 nichos
- [ ] Retry automático (3x)
- [ ] Logging completo
- [ ] Relatório de qualidade
- [ ] Documentação de problemas
- [ ] Confiança > 99% de sucesso

---

## 📚 Documentação Viva

Este roadmap será atualizado conforme evoluirmos.

Cada fase concluída = nova fase iniciada.

Objetivo final: Uma máquina de gerar sites que dispensa intervenção manual.

---

**Desenvolvido com estratégia e visão de longo prazo.**
