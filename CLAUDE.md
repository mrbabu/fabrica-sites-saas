# Fábrica de Sites SaaS - Contexto do Projeto

## Visão Geral
Plataforma SaaS automatizada baseada em IA Multi-Agente. O sistema gera e publica sites profissionais em menos de 30 segundos injetando variáveis de clientes em uma única estrutura de template padronizada (HTML/Tailwind), controlada por arquivos JSON.

## Arquitetura do Sistema
1. **Agente Construtor (MVP):** Atua como preenchedor inteligente. Recebe dados brutos (nome, nicho, cor) e cospe a estrutura de dados em um arquivo `site-config.json`.
2. **Template Base:** Estrutura estática universal em HTML/Tailwind que renderiza dinamicamente as variáveis contidas no `site-config.json`.
3. **Backend/Gateway:** `app.py` expõe o Agente Construtor como API REST (FastAPI), pronta para ser chamada pelo n8n. Deve atuar estritamente como gateway — validação (via `schema_validator.py`) e repasse, sem lógica de negócio pesada.
4. **Normalização de assets:** `image_utils.py` já baixa e normaliza logos de clientes (Pillow) para um formato padrão antes de injetar no `site-config.json`.
5. **Automação (n8n):** Orquestra webhooks e integrações externas.
6. **Deploy:** Vercel (`vercel.json` já configurado, runtime `@vercel/python`, headers de segurança aplicados). Não migrar para outro provedor sem decisão explícita.

## Diretrizes de Desenvolvimento
- Manter código limpo, modular e focado em altíssima performance para carregamento rápido.
- Toda e qualquer customização de cliente deve residir obrigatoriamente no arquivo JSON de configuração, nunca hardcoded no HTML.
- Dados de cliente (nome, contato, logo) são sensíveis: tratar com validação estrita na entrada (`app.py`/`schema_validator.py`) e nunca logar em texto plano.
- Para tarefas simples (formatação de JSON, ajustes pontuais de template), prefira soluções diretas — evite over-engineering ou abstrações não pedidas.

## Roadmap de Desenvolvimento
- [ ] Consolidar `app.py` como gateway fino, delegando processamento pesado ao workflow do n8n.
- [ ] Configurar o workflow no n8n (recebimento do webhook → Agente Construtor → deploy Vercel).
- [x] Normalização de logo via Pillow (`image_utils.py`) — concluído.
