#!/bin/bash
# Deploy repetível do backend na VM Ampere de produção (152.67.59.214).
# Rodar via SSH (Tailscale) dentro da VM, no diretório onde o repo já foi
# clonado. Pressupõe que o setup de uma vez só já foi feito — ver
# infra/zero_trust_deploy.md (Docker, Tailscale, NSG fechado, .env
# preenchido). Postgres é gerenciado pelo próprio docker-compose.prod.yml
# (serviço `db`), não precisa de setup manual separado.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "==> Atualizando o repositório (origin/main)..."
git fetch origin
git reset --hard origin/main

echo "==> Build + subida do stack (db + backend + túnel Cloudflare)..."
docker compose -f docker-compose.prod.yml up -d --build

echo "==> Aguardando os containers ficarem saudáveis..."
sleep 3
docker compose -f docker-compose.prod.yml ps

echo "==> Últimas linhas do log do backend (migrations do Alembic rodam sozinhas no entrypoint):"
docker compose -f docker-compose.prod.yml logs --tail=30 backend

echo
echo "==> Deploy concluído. Teste com:"
echo "    curl -sS https://<seu-subdominio-cloudflare>/health"
