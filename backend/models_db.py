#!/usr/bin/env python3
"""
Models SQLAlchemy - Fábrica de Sites SaaS
Um site gerado = uma linha na tabela `sites`. A customização do cliente
inteira (services/testimonials/features/faq/footer/etc.) vive dentro da
coluna JSONB `config`, seguindo o mesmo princípio "JSON Schema Driven" já
usado pelo Agente Construtor (ver CLAUDE.md) - nada é normalizado em tabelas
próprias.
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from db import Base


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
