#!/usr/bin/env python3
"""
Roteador de webhook inbound do WhatsApp (API Cloud oficial da Meta).

Escopo deliberadamente restrito (ver ROADMAP.md, guardrails #1 e #2, e a
decisão tomada na sessão que criou este arquivo):
- Só responde ao handshake de verificação da Meta e recebe eventos.
- NÃO qualifica lead, NÃO decide o que responder, NÃO envia mensagem
  nenhuma automaticamente.
- Se N8N_WEBHOOK_URL estiver configurada, só espelha o payload bruto pra
  lá — a lógica de conversa fica num fluxo desenhado por um humano no n8n.
- Caso contrário, só registra o lead como "inbound_recebido" no Postgres
  (tabela `leads`) pra um humano ver e responder manualmente.

O motor de qualificação automático e o disparo de mensagens via Graph API
foram deixados de fora de propósito: automatizar a conversa de vendas
antes de 15-20 vendas fechadas manualmente viola o guardrail #2 do
ROADMAP.md, mesmo sendo inbound. Não adicionar isso aqui sem essa fase
ter fechado.
"""

import logging
import os

import httpx
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

import repository
from db import get_db

logger = logging.getLogger("FabricaSitesAPI.whatsapp_inbound")

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp Inbound"])

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")


@router.get("/webhook")
async def verificar_webhook(request: Request):
    """Handshake de verificação exigido pela Meta ao registrar o webhook do app."""
    params = request.query_params
    modo = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if modo == "subscribe" and WHATSAPP_VERIFY_TOKEN and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ Webhook do WhatsApp verificado pela Meta")
        return Response(content=challenge or "", media_type="text/plain")

    logger.warning("❌ Falha na verificação do webhook do WhatsApp (token não configurado ou não bateu)")
    return Response(status_code=403)


def _extrair_mensagem(payload: dict):
    """
    Extrai (whatsapp, texto) da primeira mensagem de um payload da Meta
    Cloud API, ou None se não houver uma mensagem de texto reconhecível
    (ex.: evento de status de entrega/leitura, não uma mensagem nova).
    """
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        mensagens = value.get("messages")
        if not mensagens:
            return None
        msg = mensagens[0]
        whatsapp = msg.get("from")
        if not whatsapp:
            return None
        texto = msg.get("text", {}).get("body", "")
        return whatsapp, texto
    except (KeyError, IndexError, TypeError):
        return None


async def _encaminhar_para_n8n(payload: dict) -> None:
    """Espelha o payload bruto pro n8n (fire-and-forget, não bloqueia a resposta pra Meta)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=payload)
            logger.info(f"↪️  Payload do WhatsApp encaminhado pro n8n (status {resp.status_code})")
    except Exception as e:
        logger.error(f"❌ Falha ao encaminhar payload do WhatsApp pro n8n: {e}")


@router.post("/webhook")
async def receber_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recebe eventos do webhook do WhatsApp. Precisa sempre responder 200 —
    a Meta desativa o webhook automaticamente depois de falhas repetidas —
    então qualquer erro interno é logado e engolido, nunca propagado.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"❌ Payload do webhook do WhatsApp inválido (não é JSON): {e}")
        return Response(status_code=200)

    try:
        if N8N_WEBHOOK_URL:
            await _encaminhar_para_n8n(payload)
            return Response(status_code=200)

        extraido = _extrair_mensagem(payload)
        if extraido is None:
            return Response(status_code=200)  # evento sem mensagem nova (ex.: status), ignora

        whatsapp, mensagem = extraido
        lead = repository.registrar_lead_inbound(db, whatsapp=whatsapp, mensagem=mensagem)
        logger.info(
            f"📩 Lead inbound registrado: {whatsapp} (status={lead.status}) "
            f"— aguardando resposta humana, nenhuma mensagem foi enviada automaticamente"
        )
    except Exception as e:
        logger.error(f"❌ Erro processando webhook do WhatsApp (não propagado pra Meta): {e}")

    return Response(status_code=200)
