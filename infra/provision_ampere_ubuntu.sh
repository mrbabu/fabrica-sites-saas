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

echo "== Instalando Docker Engine via repositório oficial apt (arm64) =="
# Repositório assinado em vez de curl | sh - evita pipe-to-root-shell num
# host de produção, alinhado com a postura Zero Trust do resto do setup.
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
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
