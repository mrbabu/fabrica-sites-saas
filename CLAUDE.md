# Fábrica de Sites SaaS - Contexto do Projeto

## Visão Geral
Plataforma SaaS automatizada baseada em IA Multi-Agente. O sistema gera e publica sites profissionais em menos de 30 segundos injetando variáveis de clientes em uma única estrutura de template padronizada (HTML/Tailwind), controlada por arquivos JSON.

## Arquitetura do Sistema
1. **Agente Construtor (MVP):** Atua como preenchedor inteligente. Recebe dados brutos (nome, nicho, cor) e cospe a estrutura de dados em um arquivo `site-config.json`.
2. **Template Base:** Estrutura estática universal em HTML/Tailwind que renderiza dinamicamente as variáveis contidas no `site-config.json`.
3. **Automação (n8n/Vercel):** Captura o JSON, injeta no HTML e executa o Deploy via API da Vercel.

## Diretrizes de Desenvolvimento
- Manter código limpo, modular e focado em altíssima performance para carregamento rápido.
- Toda e qualquer customização de cliente deve residir obrigatoriamente no arquivo JSON de configuração, nunca hardcoded no HTML.