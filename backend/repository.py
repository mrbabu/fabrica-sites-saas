#!/usr/bin/env python3
"""
Persistência de sites gerados - Fábrica de Sites SaaS
Funções finas sobre uma Session do SQLAlchemy: sem camada de repositório
genérica, só o que os endpoints de app.py precisam.
"""

from typing import Optional

from sqlalchemy.orm import Session

from models_db import Site, Lead


def upsert_site(db: Session, slug: str, nome_empresa: str, nicho: str, config: dict) -> Site:
    """Cria o site se o slug ainda não existir, ou atualiza o config se já existir"""
    site = db.query(Site).filter(Site.slug == slug).one_or_none()

    if site is None:
        site = Site(slug=slug, nome_empresa=nome_empresa, nicho=nicho, config=config)
        db.add(site)
    else:
        site.nome_empresa = nome_empresa
        site.nicho = nicho
        site.config = config

    db.commit()
    db.refresh(site)
    return site


def obter_site(db: Session, slug: str) -> Optional[Site]:
    """Busca um site salvo pelo slug, ou None se não existir"""
    return db.query(Site).filter(Site.slug == slug).one_or_none()


def listar_sites(db: Session) -> list[Site]:
    """Lista todos os sites salvos, mais recente primeiro"""
    return db.query(Site).order_by(Site.created_at.desc()).all()


def registrar_lead_inbound(db: Session, whatsapp: str, mensagem: str = "") -> Lead:
    """
    Registra que um número iniciou contato via WhatsApp (idempotente por
    whatsapp). Se o lead já existir, NÃO sobrescreve o status — evita
    apagar um estado que um humano já avançou manualmente depois do
    primeiro contato.
    """
    lead = db.query(Lead).filter(Lead.whatsapp == whatsapp).one_or_none()

    if lead is None:
        lead = Lead(whatsapp=whatsapp, status="inbound_recebido", primeira_mensagem=mensagem)
        db.add(lead)

    db.commit()
    db.refresh(lead)
    return lead
