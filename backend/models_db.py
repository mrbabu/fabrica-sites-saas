#!/usr/bin/env python3
"""
Models SQLAlchemy - Fábrica de Sites SaaS
Um site gerado = uma linha na tabela `sites`. A customização do cliente
inteira (services/testimonials/features/faq/footer/etc.) vive dentro da
coluna JSONB `config`, seguindo o mesmo princípio "JSON Schema Driven" já
usado pelo Agente Construtor (ver CLAUDE.md) - nada é normalizado em tabelas
próprias.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from db import Base


class Lead(Base):
    """
    Lead que iniciou contato via WhatsApp (inbound). Criado só pelo webhook
    de recebimento (backend/routers/whatsapp_inbound.py) — nunca por
    outbound automatizado (guardrail #1 do ROADMAP.md).

    status começa em "inbound_recebido" e fica assim até um humano
    atualizar manualmente — este projeto não qualifica/responde sozinho
    ainda (guardrail #2: automação de vendas só depois de 15-20 vendas
    fechadas manualmente).
    """

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    whatsapp = Column(String(20), unique=True, index=True, nullable=False)
    nome = Column(String(150), nullable=True)
    status = Column(String(50), nullable=False, default="inbound_recebido")
    primeira_mensagem = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Site(Base):
    """Um site gerado e salvo via API (POST /api/v1/generate-site ou /webhook/whatsapp)"""

    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    slug = Column(String(150), unique=True, index=True, nullable=False)
    nome_empresa = Column(String(100), nullable=False)
    nicho = Column(String(100), nullable=False)
    config = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
