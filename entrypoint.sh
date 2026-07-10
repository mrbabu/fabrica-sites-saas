#!/bin/bash
set -euo pipefail

echo "Aguardando o Postgres ficar disponivel em ${DATABASE_URL}..."
until python -c "
import os, sys
import psycopg

url = os.environ['DATABASE_URL'].replace('postgresql+psycopg://', 'postgresql://', 1)
try:
    psycopg.connect(url, connect_timeout=3).close()
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "  Postgres ainda nao respondeu, tentando de novo em 2s..."
    sleep 2
done
echo "Postgres disponivel."

echo "Rodando migrations do Alembic (alembic upgrade head)..."
alembic upgrade head

echo "Iniciando uvicorn..."
exec uvicorn app:app --host 0.0.0.0 --port 8000
