# Deploy Zero Trust — Instância Ampere A1.Flex

Arquitetura: nenhuma porta pública. Admin via Tailscale (mesh privada).
Tráfego web via Cloudflare Tunnel (saída). NSG da Oracle Cloud fecha 100%
do Ingress.

> **Ordem importa.** Tailscale precisa estar confirmadamente online antes
> de fechar a porta 22 no NSG, senão você se tranca pra fora da máquina
> (o console serial da OCI ainda funciona como resgate, mas evite depender
> disso).

## 1. Provisionar a VM

Rodar `infra/provision_ampere_ubuntu.sh` na instância (via SSH público,
ainda liberado nesse momento, ou console serial da OCI). Instala Docker +
plugin `docker compose` e Tailscale, e deixa a autenticação do Tailscale
pronta (`sudo tailscale up` imprime uma URL — abra no navegador da sua
máquina, não precisa ser na VM).

Alternativa não-interativa (gera um auth key em
`https://login.tailscale.com/admin/settings/keys`, útil se for repetir
esse provisionamento em outras instâncias):

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
2. Remover **todas** as regras (inclusive a de porta 22/SSH e qualquer
   outra aberta durante o setup inicial).
3. Não recriar nenhuma — nem para 80/443. O tráfego web entra pelo túnel
   Cloudflare (saída), não por Ingress.
4. Egress pode ficar como está (default allow-all) — Tailscale e
   cloudflared só precisam de saída.

Teste de fora da rede Tailscale (ex.: 4G no celular):

```bash
nmap -Pn -p 22,80,443 <IP_PÚBLICO_DA_INSTÂNCIA>
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

## 4. Subir o stack

```bash
cd /caminho/do/repo
cp .env.example .env   # preencher com valores reais, ver seção abaixo
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f backend
```

Preencher no `.env` antes de subir: `POSTGRES_PASSWORD` (senha forte real,
não a do exemplo), `DATABASE_URL` é montada automaticamente pelo compose,
`CLOUDFLARE_TUNNEL_TOKEN` (obtido no passo 5), mais as chaves de IA que já
existem hoje (`GEMINI_API_KEY` etc.) e `WEBHOOK_API_KEY`.

## 5. Criar e rotear o túnel (painel Cloudflare)

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
