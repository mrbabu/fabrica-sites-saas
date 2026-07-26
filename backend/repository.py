#!/usr/bin/env python3
"""
Persistência de sites gerados - Fábrica de Sites SaaS
Funções finas sobre uma Session do SQLAlchemy: sem camada de repositório
genérica, só o que os endpoints de app.py precisam.
"""

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models_db import Site, Lead, HunterBusca, HunterLead

STATUS_HUNTER_VALIDOS = {"pendente", "contatado", "respondeu", "demo_enviada", "cliente", "descartado"}


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


def mapa_lovable_url_por_slug(db: Session, slugs: list[str]) -> dict:
    """Busca em lote o link do Lovable já salvo (se houver) pros slugs de
    demo informados — usado pra embutir na mensagem de oferta do Hunter
    quando for o link publicado (ver _e_link_publicado_lovable em hunter.py)."""
    if not slugs:
        return {}
    sites = db.query(Site).filter(Site.slug.in_(slugs)).all()
    return {
        site.slug: site.config.get("lovableResultUrl")
        for site in sites
        if site.config.get("lovableResultUrl")
    }


def salvar_lovable_url(db: Session, slug: str, url: str) -> Optional[Site]:
    """Guarda o link do projeto real já gerado no Lovable (depois que a
    equipe passou pelo fluxo manual) dentro do próprio config JSON — sem
    coluna/migration nova. None se o slug não existir."""
    site = db.query(Site).filter(Site.slug == slug).one_or_none()
    if site is None:
        return None
    site.config = {**site.config, "lovableResultUrl": url}
    db.commit()
    db.refresh(site)
    return site


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


# ============================================================================
# Hunter (busca de leads) — ver backend/routers/hunter.py e models_db.py
# ============================================================================

def criar_busca_hunter(
    db: Session,
    nicho: str,
    cidade: str,
    bairro: Optional[str],
    raio_km: Optional[int],
    quantidade_solicitada: int,
    origem: str = "hunter_web",
) -> HunterBusca:
    busca = HunterBusca(
        nicho=nicho,
        cidade=cidade,
        bairro=bairro,
        raio_km=raio_km,
        quantidade_solicitada=quantidade_solicitada,
        quantidade_encontrada=0,
        origem=origem,
    )
    db.add(busca)
    db.commit()
    db.refresh(busca)
    return busca


def _lead_hunter_existente(db: Session, place_id: Optional[str], nome_empresa: str, cidade: str) -> Optional[HunterLead]:
    """Dedup: por place_id quando disponível (mais confiável), senão por
    (nome_empresa, cidade) — mesmo critério que buscar_leads_google_maps.py
    já usava pro CSV, agora contra o banco."""
    if place_id:
        existente = db.query(HunterLead).filter(HunterLead.place_id == place_id).one_or_none()
        if existente:
            return existente
    return (
        db.query(HunterLead)
        .filter(HunterLead.nome_empresa == nome_empresa, HunterLead.cidade == cidade)
        .one_or_none()
    )


def salvar_leads_hunter(
    db: Session, busca_id: Optional[int], leads: list[dict], origem: str = "google_places"
) -> list[HunterLead]:
    """
    Insere os leads encontrados, pulando duplicados (já vistos antes, de
    qualquer busca). `leads`: lista de dicts com nome_empresa, nicho,
    cidade, bairro (opcional), telefone (opcional), google_maps_url
    (opcional), place_id (opcional).

    Retorna só os leads efetivamente novos (não os duplicados ignorados).
    """
    novos = []
    for dados in leads:
        existente = _lead_hunter_existente(db, dados.get("place_id"), dados["nome_empresa"], dados["cidade"])
        if existente:
            continue
        lead = HunterLead(
            busca_id=busca_id,
            place_id=dados.get("place_id"),
            nome_empresa=dados["nome_empresa"],
            nicho=dados["nicho"],
            cidade=dados["cidade"],
            bairro=dados.get("bairro"),
            telefone=dados.get("telefone"),
            google_maps_url=dados.get("google_maps_url"),
            status=dados.get("status", "pendente"),
            origem=origem,
        )
        db.add(lead)
        novos.append(lead)

    db.commit()
    for lead in novos:
        db.refresh(lead)

    if busca_id is not None and novos:
        busca = db.query(HunterBusca).filter(HunterBusca.id == busca_id).one_or_none()
        if busca:
            busca.quantidade_encontrada = len(novos)
            db.commit()

    return novos


def listar_buscas_hunter(db: Session, limite: int = 50) -> list[HunterBusca]:
    return db.query(HunterBusca).order_by(HunterBusca.created_at.desc()).limit(limite).all()


def listar_leads_hunter(
    db: Session,
    nicho: Optional[str] = None,
    cidade: Optional[str] = None,
    status: Optional[str] = None,
    busca_texto: Optional[str] = None,
    busca_id: Optional[int] = None,
    ordenar_por: str = "recentes",
) -> list[HunterLead]:
    query = db.query(HunterLead)
    if nicho:
        query = query.filter(HunterLead.nicho.ilike(f"%{nicho}%"))
    if cidade:
        query = query.filter(HunterLead.cidade.ilike(f"%{cidade}%"))
    if status:
        query = query.filter(HunterLead.status == status)
    if busca_id is not None:
        query = query.filter(HunterLead.busca_id == busca_id)
    if busca_texto:
        termo = f"%{busca_texto}%"
        query = query.filter(or_(HunterLead.nome_empresa.ilike(termo), HunterLead.telefone.ilike(termo)))

    if ordenar_por == "nome":
        query = query.order_by(HunterLead.nome_empresa.asc())
    elif ordenar_por == "status":
        query = query.order_by(HunterLead.status.asc(), HunterLead.created_at.desc())
    else:
        query = query.order_by(HunterLead.created_at.desc())

    return query.all()


def contar_leads_hunter(db: Session) -> int:
    return db.query(HunterLead).count()


def obter_lead_hunter(db: Session, lead_id: int) -> Optional[HunterLead]:
    return db.query(HunterLead).filter(HunterLead.id == lead_id).one_or_none()


def atualizar_status_lead_hunter(db: Session, lead_id: int, novo_status: str) -> Optional[HunterLead]:
    if novo_status not in STATUS_HUNTER_VALIDOS:
        raise ValueError(f"status inválido: '{novo_status}' — use um de {sorted(STATUS_HUNTER_VALIDOS)}")
    lead = obter_lead_hunter(db, lead_id)
    if lead is None:
        return None
    lead.status = novo_status
    db.commit()
    db.refresh(lead)
    return lead


def vincular_demo_ao_lead(db: Session, lead_id: int, slug_demo: str) -> Optional[HunterLead]:
    lead = obter_lead_hunter(db, lead_id)
    if lead is None:
        return None
    lead.slug_demo = slug_demo
    if lead.status == "pendente":
        lead.status = "demo_enviada"
    db.commit()
    db.refresh(lead)
    return lead
