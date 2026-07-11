# Deploy Zero Trust — VM fabrica-postgres (147.15.73.239)

Arquitetura: nenhuma porta pública. Admin via Tailscale (mesh privada).
Tráfego web via Cloudflare Tunnel (saída). NSG da Oracle Cloud fecha 100%
do Ingress.

**Decisão (sessão de 2026-07-11): reaproveitar a VM `fabrica-postgres`
já existente (AMD `VM.Standard.E2.1.Micro`) em vez de esperar capacidade
Ampere.** O backend passa a rodar na mesma VM que já hospeda o Postgres,
via Docker, conectado ao Postgres existente pela rede interna (ver seção
"Reaproveitando o Postgres existente" abaixo) — nunca pela porta 5432
pública. Se `fabrica-prod-ampere` (VM dedicada) for criada no futuro, este
runbook se aplica igual, só o passo de provisionamento muda pra
`infra/provision_ampere_ubuntu.sh` numa VM zerada.

> **Ordem importa.** Tailscale precisa estar confirmadamente online antes
> de fechar a porta 22 no NSG, senão você se tranca pra fora da máquina
> (o console serial da OCI ainda funciona como resgate, mas evite depender
> disso).

> **Estado atual conhecido desta VM (do provisionamento anterior):**
> Docker já instalado (via `get.docker.com`), Postgres 16 já rodando como
> container `fabrica-postgres` com `--restart unless-stopped`. **Portas 22
> e 5432 estão abertas para `0.0.0.0/0`** no NSG — isso é o oposto de Zero
> Trust e precisa ser corrigido nesta sessão de deploy (seção 2), não só a
> porta do backend.

## 1. Instalar Tailscale na VM (Docker já existe)

Via SSH público (ainda liberado nesse momento) ou console serial da OCI:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

`sudo tailscale up` imprime uma URL — abra no navegador da sua máquina
(não precisa ser na VM) pra autenticar. Alternativa não-interativa (gera
um auth key em `https://login.tailscale.com/admin/settings/keys`):

```bash
sudo tailscale up --authkey=tskey-auth-XXXXXXXXXXXX
```

Confirme antes de continuar:

```bash
tailscale status        # este nó deve aparecer "online"
tailscale ip -4         # anote o IP 100.x.x.x - é por ele que você vai SSHar daqui pra frente
```

## 2. Fechar o NSG da Oracle Cloud (Ingress)

Painel OCI → **Compute → Instances → (sua instância) → Primary VNIC →
Subnet** → abre a lista de **Security Lists** e **Network Security
Groups** anexados ao VNIC.

Para cada Security List / NSG anexado:

1. Aba **Ingress Rules**.
2. Remover **todas** as regras — inclusive a de porta 22/SSH **e a de
   porta 5432/Postgres**, que ficou aberta para `0.0.0.0/0` desde o
   provisionamento inicial dessa VM. Sem Tailscale online e confirmado
   (passo 1), não remova a de 22 ainda.
3. Não recriar nenhuma — nem para 80/443. O tráfego web entra pelo túnel
   Cloudflare (saída), não por Ingress.
4. Egress pode ficar como está (default allow-all) — Tailscale e
   cloudflared só precisam de saída.

Depois de fechar o NSG, atualize `DATABASE_URL` no `.env` **da sua
máquina local** (o que usamos pra desenvolvimento) — ela vai parar de
funcionar, porque a 5432 não estará mais acessível de fora. Isso é
esperado: local passa a não ter mais acesso direto ao Postgres de
produção, só o backend rodando na própria VM (via `internal_net`). Se
precisar consultar o banco de produção do seu computador depois disso,
instale o Tailscale localmente também e entre na mesma tailnet — aí dá
pra apontar `DATABASE_URL` para o IP `100.x.x.x` da VM em vez do IP
público.

Teste de fora da rede Tailscale (ex.: 4G no celular):

```bash
nmap -Pn -p 22,5432,80,443 <IP_PÚBLICO_DA_INSTÂNCIA>
# esperado: todas as portas "filtered" ou sem resposta
```

## 3. UFW — defesa em profundidade (recomendado, não obrigatório)

O NSG já bloqueia tudo na borda da rede da Oracle — isso sozinho já cumpre
"zero exposição pública". UFW no host é uma segunda camada (protege contra
um NSG mal configurado no futuro, ou tráfego lateral se a VM algum dia
ganhar outra interface):

```bash
sudo apt-get install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow in on tailscale0   # libera SSH e tudo mais só pela interface do Tailscale
sudo ufw --force enable
sudo ufw status verbose
```

Nada precisa ser liberado para o cloudflared — ele é 100% outbound, UFW
não bloqueia conexões que a própria VM inicia.

## 4. Reaproveitando o Postgres existente

O `docker-compose.prod.yml` não sobe um serviço `db` — o Postgres já roda
nessa VM como container standalone (`fabrica-postgres`). Pra o backend
enxergá-lo pelo nome do container (sem publicar a 5432 em rede nenhuma),
crie a rede que o compose espera encontrar e conecte o container existente
a ela, uma vez só:

```bash
docker network create internal_net
docker network connect internal_net fabrica-postgres
```

Confirme que o Postgres está de fato alcançável por esse nome dentro da
rede (roda um container temporário só pra testar):

```bash
docker run --rm --network internal_net postgres:16-alpine \
  pg_isready -h fabrica-postgres -p 5432
# esperado: "fabrica-postgres:5432 - accepting connections"
```

## 5. Subir o stack

```bash
cd /caminho/do/repo
cp .env.example .env   # preencher com valores reais, ver seção abaixo
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f backend
```

Preencher no `.env` antes de subir: `POSTGRES_USER`/`POSTGRES_PASSWORD`
(as credenciais reais já usadas pelo container `fabrica-postgres`
existente — não uma senha nova), `CLOUDFLARE_TUNNEL_TOKEN` (obtido no
passo 6), mais as chaves de IA que já existem hoje (`GEMINI_API_KEY` etc.),
`WEBHOOK_API_KEY` e `WHATSAPP_VERIFY_TOKEN`. `DATABASE_URL` é montada
automaticamente pelo compose a partir de `POSTGRES_USER`/`POSTGRES_PASSWORD`
+ o nome do container `fabrica-postgres`.

## 6. Criar e rotear o túnel (painel Cloudflare)

Pré-requisito: o domínio já precisa estar em Cloudflare (nameservers
apontando pra lá) — sem isso o passo de DNS automático abaixo não
funciona.

1. **Zero Trust → Networks → Tunnels → Create a tunnel.**
2. Tipo de conector: **Cloudflared**. Dê um nome (ex.: `fabrica-prod`).
3. Ambiente escolhido: **Docker**. A tela mostra um comando
   `docker run cloudflare/cloudflared:latest tunnel run --token eyJ...` —
   copie só o valor do `--token` e cole em `CLOUDFLARE_TUNNEL_TOKEN` no
   `.env` (o serviço `cloudflare_tunnel` do compose já roda esse comando
   sozinho, não precisa rodar o `docker run` manual da tela).
4. Aba **Public Hostname → Add a public hostname**:
   - **Subdomain**: `api` (ou o que preferir)
   - **Domain**: seu domínio já conectado à Cloudflare
   - **Service → Type**: `HTTP`
   - **Service → URL**: `backend:8000` — nome do serviço no
     `docker-compose.prod.yml`, resolvido pela rede interna do Docker;
     nunca o IP da máquina.
5. Salvar. A Cloudflare cria o registro DNS (CNAME para
   `<tunnel-id>.cfargotunnel.com`) automaticamente — nenhum passo manual
   de DNS é necessário.

Teste final:

```bash
curl -sS https://api.seudominio.com.br/health
```

Deve responder normalmente, sem que a porta 8000 (ou qualquer porta)
esteja aberta publicamente na instância.
