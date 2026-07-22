#!/usr/bin/env python3
"""
Models SQLAlchemy - Fábrica de Sites SaaS
Um site gerado = uma linha na tabela `sites`. A customização do cliente
inteira (services/testimonials/features/faq/footer/etc.) vive dentro da
coluna JSONB `config`, seguindo o mesmo princípio "JSON Schema Driven" já
usado pelo Agente Construtor (ver CLAUDE.md) - nada é normalizado em tabelas
próprias.
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, func
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


class HunterBusca(Base):
    """Uma execução de busca no Hunter (ver backend/routers/hunter.py) —
    histórico permanente de pesquisas, mesmo que não tenham encontrado
    nada aproveitável."""

    __tablename__ = "hunter_buscas"

    id = Column(Integer, primary_key=True)
    nicho = Column(String(150), nullable=False)
    cidade = Column(String(150), nullable=False)
    bairro = Column(String(150), nullable=True)
    raio_km = Column(Integer, nullable=True)
    quantidade_solicitada = Column(Integer, nullable=False)
    quantidade_encontrada = Column(Integer, nullable=False, default=0)
    origem = Column(String(30), nullable=False, default="hunter_web")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class HunterLead(Base):
    """
    Um lead encontrado pelo Hunter (Google Places) ou importado dos CSVs
    legados — fonte de verdade agora é esta tabela; CSV vira só mecanismo
    de import/export (decisão de produto 2026-07-22).

    status começa em "pendente" e avança manualmente (contatado, respondeu,
    demo_enviada, cliente, descartado) — nunca avançado sozinho pelo
    sistema, mesmo guardrail de não-automação de contato do resto do projeto.
    """

    __tablename__ = "hunter_leads"

    id = Column(Integer, primary_key=True)
    busca_id = Column(Integer, ForeignKey("hunter_buscas.id"), nullable=True)
    place_id = Column(String(150), nullable=True, index=True)
    nome_empresa = Column(String(200), nullable=False)
    nicho = Column(String(150), nullable=False)
    cidade = Column(String(150), nullable=False)
    bairro = Column(String(150), nullable=True)
    telefone = Column(String(30), nullable=True)
    google_maps_url = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="pendente")
    slug_demo = Column(String(150), nullable=True)
    origem = Column(String(30), nullable=False, default="google_places")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
