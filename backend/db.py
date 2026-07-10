#!/usr/bin/env python3
"""
Configuração de acesso ao banco de dados - Fábrica de Sites SaaS
Engine/sessão SQLAlchemy para persistência de sites gerados (tabela `sites`).
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

Base = declarative_base()


def get_db():
    """Dependency do FastAPI: abre uma sessão por request e garante o fechamento"""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL não configurada - defina no .env antes de usar rotas com persistência")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
