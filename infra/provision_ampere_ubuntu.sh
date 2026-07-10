#!/bin/bash
# Provisionamento da instância Ampere A1.Flex (Ubuntu 24.04 ARM64) para
# rodar o stack de produção Zero Trust (docker-compose.prod.yml).
#
# Uso: rodar direto na VM, via console serial ou SSH (antes de fechar o
# NSG - ver infra/zero_trust_deploy.md pra ordem correta dos passos).
#   chmod +x provision_ampere_ubuntu.sh && ./provision_ampere_ubuntu.sh
set -euo pipefail

echo "== Atualizando o sistema =="
sudo apt-get update -y
sudo apt-get upgrade -y

echo "== Instalando Docker Engine (inclui o plugin 'docker compose') =="
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"

echo "== Instalando Tailscale =="
curl -fsSL https://tailscale.com/install.sh | sh

echo "== Autenticando o Tailscale =="
# Modo interativo: imprime uma URL - abra no seu navegador (fora da VM) pra
# aprovar o dispositivo na sua conta Tailscale.
sudo tailscale up

echo
echo "== Provisionamento concluído =="
echo "IP privado Tailscale desta máquina:"
tailscale ip -4
echo
echo "PRÓXIMO PASSO: confirme 'tailscale status' mostrando este nó como"
echo "online ANTES de fechar a porta 22 no NSG da Oracle Cloud - ver"
echo "infra/zero_trust_deploy.md."
