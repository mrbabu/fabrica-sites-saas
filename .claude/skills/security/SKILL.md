---
name: security
description: Análise de segurança em profundidade — API keys, secrets no Git, exposição de portas/Docker, firewall, CORS, headers HTTP, rate limit, SSL, backups e logs sensíveis. Use quando o usuário perguntar especificamente sobre segurança, exposição de serviços, ou quiser confirmar que algo está pronto/seguro antes de expor a produção.
---

Auditoria focada só na dimensão de segurança — mais rápida e mais funda
que a seção 19 (resumida) do `/audit`. Roda sob demanda (`/security`),
tipicamente antes de expor um endpoint novo, registrar um domínio público,
ou sempre que o usuário perguntar "isso é seguro?".

## Regras

- Somente leitura — nunca corrige nada sozinho. Reporta e classifica; a
  correção vira um item de plano separado, com o usuário decidindo a
  prioridade.
- Nunca imprime o **valor** de um segredo (chave de API, senha, token) —
  só confirma se ele existe, onde, e se está exposto indevidamente
  (versionado no Git, logado em texto claro, hardcoded no código).
- Cheque o estado real da infra (`ACESSO-VM-TAILSCALE.txt`,
  `infra/zero_trust_deploy.md`, `docker-compose.prod.yml`) em vez de só
  confiar no que a documentação afirma — este projeto já teve doc
  desatualizada sobre o próprio deploy mais de uma vez.

## Itens a verificar

Para cada item, classificar ✅ (ok) / ⚠️ (atenção, não crítico) / ❌ (falta
ou risco real), com uma frase de evidência concreta (arquivo:linha ou
comando rodado):

1. **API Keys** — `backend/app.py`: `verificar_api_key()` protege as rotas
   certas? Bloqueia por padrão (fail-closed) se a env var não estiver
   setada, ou abre por padrão (fail-open)? Alguma rota sensível ficou de
   fora da proteção (ex.: `GET /api/v1/site-config/{slug}` expõe dados de
   contato sem nenhuma auth)?
2. **Secrets no Git** — `.env` está no `.gitignore`? Rodar
   `git log --all --full-history -- .env` (deve vir vazio). `Grep` por
   padrões de chave real (`sk-ant-`, `nvapi-`, `AIza`, etc.) em arquivos
   versionados (não em `.md` de exemplo/placeholder).
3. **Docker** — `docker-compose.prod.yml`: alguma porta publicada
   (`ports:`) que não devia? Container roda como root sem necessidade?
   Imagem base desatualizada de forma óbvia?
4. **Firewall** — NSG da Oracle Cloud + UFW: documentado como fechado por
   completo pro Ingress público (`infra/zero_trust_deploy.md`)? Isso é
   estado de infra externa — se não der pra confirmar via `nmap`/acesso
   real na sessão atual, reportar como "documentado, não re-verificado
   nesta rodada" em vez de assumir.
5. **Cloudflare Tunnel** — 100% outbound, sem porta publicada no host?
   Token do tunnel não está commitado em nenhum arquivo versionado?
6. **PostgreSQL exposto** — `docker-compose*.yml`: `5432` publicado pro
   host em produção? (Em dev é aceitável; em prod não deveria estar.)
7. **Headers HTTP** — `backend/app.py`: existe algum middleware de
   segurança (`Strict-Transport-Security`, `X-Content-Type-Options`,
   `X-Frame-Options`, CSP)? Se não existir nenhum, reportar ❌ com nota de
   que hoje isso é mitigado parcialmente pela borda da Cloudflare, mas não
   no nível da aplicação.
8. **Rate Limit** — `Grep` por `slowapi`/`limiter`/middleware de rate limit
   em `backend/`. Se não existir, ❌.
9. **CORS** — `backend/app.py`: `allow_origins`/`allow_credentials`.
   Sinalizar especificamente se `allow_origins=["*"]` estiver combinado
   com `allow_credentials=True` (combinação inconsistente com a spec CORS).
10. **SSL** — onde o TLS termina (borda Cloudflare vs aplicação)? Sem
    domínio público configurado, existe HTTPS real hoje ou só acesso via
    tailnet?
11. **Backups** — existe alguma rotina de backup do Postgres de produção
    (cron, script, serviço gerenciado)? Se não achar nada em `infra/`,
    `deploy.sh`, ou crontab documentado, ❌ — já foi identificado como
    gap em auditoria anterior deste projeto.
12. **Logs sensíveis** — `Grep` por `logger.`/`print(` em `backend/`
    perto de campos como `whatsapp`, `telefone`, `email`, `endereco` — a
    diretriz do `CLAUDE.md` é nunca logar dado de cliente em texto plano.

## Formato de saída

Tabela única:

```
Item                  Status   Evidência
API Keys              ✅/⚠️/❌   <arquivo:linha ou comando>
Secrets no Git        ✅/⚠️/❌   ...
Docker                ✅/⚠️/❌   ...
Firewall              ✅/⚠️/❌   ...
Cloudflare Tunnel     ✅/⚠️/❌   ...
PostgreSQL exposto    ✅/⚠️/❌   ...
Headers HTTP          ✅/⚠️/❌   ...
Rate Limit            ✅/⚠️/❌   ...
CORS                  ✅/⚠️/❌   ...
SSL                   ✅/⚠️/❌   ...
Backups               ✅/⚠️/❌   ...
Logs sensíveis        ✅/⚠️/❌   ...
```

Seguida de uma lista curta "Corrigir antes de produção real" com só os
itens ❌/⚠️ que bloqueiam ou arriscam dado de cliente — não repetir os ✅.
