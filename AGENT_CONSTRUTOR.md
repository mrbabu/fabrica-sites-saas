# Agente Construtor - Documentação Técnica

## 🤖 Visão Geral

O **Agente Construtor** é o primeiro agente da Fábrica de Sites SaaS. Ele recebe inputs simples e usa Claude 3.5 Sonnet para gerar um `site-config.json` completo e altamente persuasivo.

**Entrada:** 3 dados simples  
**Saída:** `site-config.json` pronto para usar  
**Tempo:** ~10-15 segundos por site  

## 📊 Fluxo de Funcionamento

```
┌─────────────────────┐
│   Inputs Simples    │
│  • Nome Empresa     │
│  • Nicho/Ramo       │
│  • Cor Primária     │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────┐
│  Gerar Paleta de Cores   │
│  (8 cores hexadecimais)  │
│  usando Claude API       │
└──────────┬───────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Claude 3.5 Sonnet gera:            │
│  • Copys persuasivos baseado nicho  │
│  • 3 Serviços principais            │
│  • 3 Depoimentos reais              │
│  • Hero, CTA, Contact Info          │
│  • Tudo em JSON estruturado         │
└──────────┬────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│  site-config.json       │
│  (pronto para usar)     │
└─────────────────────────┘
```

## 🛠️ Instalação

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

Ou manualmente:
```bash
pip install anthropic>=0.25.0
```

### 2. Configurar API Key

A API key do Claude é necessária. Configure como variável de ambiente:

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY='sua-chave-aqui'
```

**Windows (CMD):**
```cmd
set ANTHROPIC_API_KEY=sua-chave-aqui
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY='sua-chave-aqui'
```

Ou adicione a `~/.bashrc` ou `~/.zshrc` para ser persistente.

## 🚀 Como Usar

### Modo 1: CLI Interativo

```bash
python agent_construtor.py
```

Responda às perguntas:
```
📝 Nome da Empresa: Minha Consultoria
🏢 Nicho/Ramo de Atuação: Consultoria Empresarial
🎨 Cor de Preferência em HEX: #6366f1
```

Resultado: `site-config.json` criado na pasta atual

### Modo 2: Exemplo de Uso

Executar exemplos pré-configurados:

```bash
# Exemplo simples
python exemplo_uso.py simples

# Múltiplos clientes
python exemplo_uso.py multiplo

# Interface interativa
python exemplo_uso.py interativo
```

### Modo 3: Uso Programático

```python
from agent_construtor import AgenteConstrutor

# Inicializar agente
agente = AgenteConstrutor()

# Gerar configuração
config = agente.executar(
    nome_empresa="Tech Startup",
    nicho="Desenvolvimento de Software",
    cor_primaria="#4F46E5",
    caminho_saida="tech-config.json"
)

print(config)  # JSON completo
```

## 🎨 Processo de Geração de Cores

O agente gera uma **paleta harmônica de 8 cores**:

1. **primary**: A cor fornecida pelo cliente
2. **primaryDark**: Versão escura (-20% luminosidade) para estados hover
3. **secondary**: Cor complementar para elementos secundários
4. **accent**: Cor que contrasta para highlights
5. **background**: Clara (branca ou muito clara)
6. **text**: Escura para texto principal
7. **textLight**: Cinza para texto secundário
8. **border**: Muito clara para bordas

**Exemplo:**
```json
{
  "primary": "#6366f1",
  "primaryDark": "#4f46e5",
  "secondary": "#ec4899",
  "accent": "#f59e0b",
  "background": "#ffffff",
  "text": "#1f2937",
  "textLight": "#6b7280",
  "border": "#e5e7eb"
}
```

## 💭 Prompt do Claude (Simplificado)

O agente envia um prompt estruturado para Claude que:

1. **Pede geração de conteúdo persuasivo** adaptado ao nicho
2. **Define o schema JSON exato** esperado
3. **Instrui sobre copywriting** para cada seção
4. **Garante formatação válida** (JSON puro, sem markdown)

Exemplo de output esperado para nicho "Agência de Marketing":

```json
{
  "metadata": {
    "siteTitle": "Digital Marketing Pro - Agência Especializada em Crescimento Digital",
    "siteDescription": "Transforme seu negócio com estratégias de marketing digital que geram resultados reais",
    "favicon": "📱"
  },
  "company": {
    "name": "Digital Marketing Pro",
    "tagline": "Seu negócio crescendo 10x em 90 dias",
    "description": "Somos especialistas em transformar pequenas e médias empresas em líderes de mercado através de estratégias digitais inovadoras.",
    "logo": "https://via.placeholder.com/180x50?text=Logo"
  },
  "hero": {
    "title": "Seu Negócio Merece Crescer 10x Mais Rápido",
    "subtitle": "Estratégias de marketing digital que geram leads qualificados e vendas reais",
    "ctaText": "Começar Análise Gratuita",
    "ctaLink": "#contato"
  },
  ...
}
```

## 🔄 Fluxo Completo do MVP

```
┌───────────────────────────────────────────────────────────┐
│ 1. AGENTE CONSTRUTOR (agent_construtor.py)                │
│    Input: Nome, Nicho, Cor                                │
│    Output: site-config.json                               │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│ 2. TEMPLATE BASE (index.html)                             │
│    Carrega: site-config.json                              │
│    Renderiza: Site completo e responsivo                  │
│    Output: HTML dinâmico + CSS                            │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│ 3. AUTOMAÇÃO (n8n/Vercel) - Próxima Fase                  │
│    Webhook recebe: site-config.json                       │
│    Captura: JSON → Injeta em HTML                         │
│    Deploy: Via Vercel API                                 │
│    Output: Site publicado em https://...                  │
└───────────────────────────────────────────────────────────┘
```

## 📦 Estrutura de Arquivos

```
fabrica-sites-saas/
├── agent_construtor.py      # Motor principal do agente
├── exemplo_uso.py           # Exemplos de uso
├── requirements.txt         # Dependências Python
├── AGENT_CONSTRUTOR.md      # Este arquivo
├── index.html               # Template universal
├── site-config.json         # Configuração (gerada)
└── README.md                # Documentação geral
```

## 🧪 Testes e Validação

### Validações Implementadas

1. **Schema JSON**: Verifica se todos os campos obrigatórios existem
2. **Cores Hexadecimais**: Valida formato (#RRGGBB)
3. **URLs**: Valida placeholders e links de contato
4. **Comprimento de Texto**: Não há limite, mas optimizado para web

### Testar Localmente

```bash
# Teste simples
python -c "from agent_construtor import AgenteConstrutor; print('✅ Importação OK')"

# Teste com dados reais
python agent_construtor.py
```

## ⚙️ Configuração Avançada

### Alterar Modelo Claude

No arquivo `agent_construtor.py`, altere:

```python
self.model = "claude-3-5-sonnet-20241022"  # Mudar para outro modelo
```

Modelos disponíveis:
- `claude-3-5-sonnet-20241022` (Recomendado - melhor custo/benefício)
- `claude-3-opus-20250219` (Mais poderoso, mais caro)
- `claude-3-haiku-20250307` (Mais rápido, menos preciso)

### Customizar Prompts

Edite a função `gerar_config_site()` para adaptar o prompt conforme necessário.

### Salvar em Diferentes Locais

```python
config = agente.executar(
    nome_empresa="...",
    nicho="...",
    cor_primaria="...",
    caminho_saida="./output/config.json"  # Pasta customizada
)
```

## 🐛 Troubleshooting

### Erro: "API key não fornecida"
```
Solução: Configure ANTHROPIC_API_KEY como variável de ambiente
```

### Erro: "JSON inválido na resposta"
```
Solução: Claude às vezes retorna markdown. Retry automático vai tentar novamente.
Se persistir, verifique o prompt ou tente com Claude 3-Opus.
```

### Erro: "ModuleNotFoundError: No module named 'anthropic'"
```
Solução: pip install anthropic
```

### Site config gerado mas muito diferente do esperado
```
Solução: Ajuste o prompt ou defina instruções mais específicas no nicho.
Você pode editar o arquivo gerado manualmente.
```

## 📈 Performance

- **Tempo por site**: 10-15 segundos (depende da latência da API)
- **Requisições API**: 2 (1 para cores, 1 para config completa)
- **Tokens usados**: ~1500-2000 por site
- **Custo aproximado**: $0.02-0.05 por site (com Claude 3.5 Sonnet)

## 🔐 Segurança

- ✅ API key nunca aparece em logs
- ✅ Não salva dados sensíveis em cache
- ✅ JSON gerado é apenas dados públicos
- ✅ Sem tracking de usuário

## 🚀 Próximas Melhorias

- [ ] Adicionar backup/versionamento de configs
- [ ] Interface web para o agente
- [ ] Integração com Vercel para deploy automático
- [ ] Webhook n8n pré-configurado
- [ ] Rate limiting e analytics
- [ ] Temas predefinidos (além de cores customizadas)

---

**Desenvolvido com ❤️ por Fábrica de Sites SaaS**
