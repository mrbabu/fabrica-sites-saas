# Fábrica de Sites SaaS - MVP v1

## 🚀 Visão Geral
Plataforma SaaS automatizada que gera e publica sites profissionais em menos de 30 segundos. Sistema baseado em **Template Universal + Configuração JSON**.

## 📁 Estrutura do Projeto

```
fabrica-sites-saas/
├── index.html              # Template universal (renderiza o JSON)
├── site-config.json        # Configuração do cliente (dados dinâmicos)
├── README.md              # Este arquivo
└── CLAUDE.md              # Contexto do projeto
```

## 🎯 Como Funciona

### 1. **site-config.json** - Schema de Configuração
Arquivo JSON que contém **TODAS** as variáveis do site:

```json
{
  "metadata": { /* SEO e info do site */ },
  "company": { /* Nome, logo, descrição */ },
  "colors": { /* Paleta hex (primária, secundária, acentos) */ },
  "hero": { /* Seção hero (título, CTA) */ },
  "sections": [ /* Seções de conteúdo dinâmico */ ],
  "services": [ /* Lista de serviços */ ],
  "testimonials": [ /* Depoimentos com ratings */ ],
  "contact": { /* Email, phone, redes sociais */ },
  "cta": { /* Call-to-action final */ }
}
```

### 2. **index.html** - Template Universal
Template em HTML/Tailwind que:
- ✅ Carrega o `site-config.json` dinamicamente
- ✅ Renderiza todas as seções com base no JSON
- ✅ Aplica cores customizadas em tempo real
- ✅ É responsivo e otimizado para performance
- ✅ **NENHUMA** informação hardcoded (tudo vem do JSON)

## ⚙️ Como Usar

### Passo 1: Personalizar `site-config.json`
Edite o arquivo preenchendo todos os campos com dados do cliente:

```bash
{
  "company": {
    "name": "Nome da Empresa",
    "tagline": "Proposta de valor"
  },
  "colors": {
    "primary": "#6366f1",      # Cor principal (hex)
    "secondary": "#ec4899",    # Cor secundária
    "accent": "#f59e0b"        # Cor de destaque
  },
  "hero": {
    "title": "Título do Hero",
    "subtitle": "Subtítulo",
    "ctaText": "Botão CTA",
    "ctaLink": "#contato"
  },
  "services": [ /* ... */ ],
  "testimonials": [ /* ... */ ]
}
```

### Passo 2: Abrir no Navegador
```bash
# Opção 1: Usar Live Server do VS Code
# Opção 2: Python
python -m http.server 8000

# Opção 3: Node.js
npx http-server
```

Acesse: `http://localhost:8000`

### Passo 3: Deploy via Vercel/n8n
A automação capturará o JSON, injetará no HTML e fará deploy automático.

## 📊 Schema Completo do `site-config.json`

### Metadata
```json
{
  "siteTitle": "Título da página",
  "siteDescription": "Meta description",
  "favicon": "🚀" // Emoji ou URL
}
```

### Company
```json
{
  "name": "Nome Empresa",
  "tagline": "Slogan",
  "description": "Descrição longa",
  "logo": "https://..."
}
```

### Colors
```json
{
  "primary": "#6366f1",      // Cor primária
  "primaryDark": "#4f46e5",  // Variação escura
  "secondary": "#ec4899",    // Cor secundária
  "accent": "#f59e0b",       // Acentos
  "background": "#ffffff",   // Fundo
  "text": "#1f2937",         // Texto principal
  "textLight": "#6b7280",    // Texto secundário
  "border": "#e5e7eb"        // Bordas
}
```

### Hero
```json
{
  "title": "Bem-vindo",
  "subtitle": "Subtítulo",
  "ctaText": "Começar",
  "ctaLink": "#contato",
  "backgroundImage": "https://...",
  "enabled": true
}
```

### Sections (Array)
```json
{
  "id": "sobre",
  "type": "content",
  "title": "Sobre Nós",
  "subtitle": "Subtítulo",
  "content": "Conteúdo...",
  "image": "https://...",
  "enabled": true
}
```

### Services (Array)
```json
{
  "id": 1,
  "title": "Serviço 1",
  "description": "Descrição",
  "icon": "⚡",
  "features": ["Feature 1", "Feature 2"],
  "enabled": true
}
```

### Testimonials (Array)
```json
{
  "id": 1,
  "name": "João Silva",
  "role": "CEO - Tech",
  "content": "Excelente!",
  "avatar": "https://...",
  "rating": 5,
  "enabled": true
}
```

### Contact
```json
{
  "email": "contato@empresa.com",
  "phone": "+55 11 99999-9999",
  "whatsapp": "+5511999999999",
  "address": "Endereço completo",
  "social": {
    "instagram": "https://...",
    "facebook": "https://...",
    "linkedin": "https://...",
    "twitter": "https://..."
  }
}
```

## 🎨 Recursos Principais

### ✅ Implementados
- [x] Renderização dinâmica do JSON
- [x] Paleta de cores configurável
- [x] Hero section responsivo
- [x] Seções de conteúdo
- [x] Grid de serviços (3 colunas)
- [x] Testimonials com ratings
- [x] Call-to-action final
- [x] Footer completo com redes sociais
- [x] Navegação sticky
- [x] Animações fade-in
- [x] Design responsivo (mobile-first)
- [x] Otimizado para performance

### 🔮 Próximos Passos (Agente Construtor)
- [ ] API que recebe dados brutos (nome, nicho, cor)
- [ ] Gera `site-config.json` automaticamente
- [ ] Integração com n8n para automação
- [ ] Deploy automático via Vercel

## 🛠️ Tecnologias
- **HTML5** - Markup semântico
- **Tailwind CSS** - Estilização via CDN
- **JavaScript Vanilla** - Renderização dinâmica (sem dependências)
- **JSON** - Configuração driver

## 📈 Performance
- Zero build process
- Carregamento instantâneo
- Sem JavaScript framework pesado
- CSS via CDN (cached globalmente)
- Fonte Inter otimizada do Google Fonts

## 🚀 Próximas Fases

### Fase 2: Agente Construtor
- API que recebe: nome, nicho, cor primária
- Retorna: `site-config.json` pré-preenchido
- Exemplo: `POST /api/generate-config` → JSON

### Fase 3: Automação n8n
- Webhook que captura JSON
- Injeta no template HTML
- Deploy automático via Vercel API

### Fase 4: Dashboard
- Interface para editar JSON visualmente
- Preview em tempo real
- Histórico de versões

---

**Desenvolvido com ❤️ por Fábrica de Sites SaaS**
