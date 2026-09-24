FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY index.html index.html
COPY assets/css/ assets/css/
COPY vendas-config.json vendas-config.json
COPY entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh

RUN useradd -u 1000 appuser && chown -R appuser:appuser /app

WORKDIR /app/backend

USER appuser
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
