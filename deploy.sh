#!/bin/bash
# Deploy repetível do backend na VM fabrica-postgres (147.15.73.239).
# Rodar via SSH (Tailscale) dentro da VM, no diretório onde o repo já foi
# clonado. Pressupõe que o setup de uma vez só já foi feito — ver
# infra/zero_trust_deploy.md (Tailscale, NSG fechado, internal_net criada
# e fabrica-postgres conectado a ela, .env preenchido).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "==> Atualizando o repositório (origin/main)..."
git fetch origin
git reset --hard origin/main

echo "==> Conferindo se a rede internal_net existe e o Postgres está nela..."
if ! docker network inspect internal_net >/dev/null 2>&1; then
    echo "ERRO: rede 'internal_net' não existe. Rode a seção 4 de"
    echo "infra/zero_trust_deploy.md (docker network create/connect) antes."
    exit 1
fi
if ! docker network inspect internal_net --format '{{range .Containers}}{{.Name}} {{end}}' | grep -qw "fabrica-postgres"; then
    echo "ERRO: container 'fabrica-postgres' não está conectado à internal_net."
    echo "Rode: docker network connect internal_net fabrica-postgres"
    exit 1
fi

echo "==> Build + subida do backend e do túnel Cloudflare..."
docker compose -f docker-compose.prod.yml up -d --build

echo "==> Aguardando o container do backend ficar saudável..."
sleep 3
docker compose -f docker-compose.prod.yml ps backend

echo "==> Últimas linhas do log do backend (migrations do Alembic rodam sozinhas no entrypoint):"
docker compose -f docker-compose.prod.yml logs --tail=30 backend

echo
echo "==> Deploy concluído. Teste com:"
echo "    curl -sS https://<seu-subdominio-cloudflare>/health"
