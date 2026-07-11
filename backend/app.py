#!/usr/bin/env python3
"""
FastAPI - Fábrica de Sites SaaS
Servidor HTTP que expõe o Agente Construtor como API REST
Pronto para integração com n8n
"""

# Carregar variáveis de ambiente PRIMEIRO
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Se não tiver python-dotenv instalado, continua sem .env

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ConfigDict, HttpUrl
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import os
import sys
import logging
import re
from typing import Optional
from datetime import datetime

# Imports locais
try:
    from agent_construtor import AgenteConstrutor
    from schema_validator import ValidadorSchema
    from metrics import obter_metricas
    from image_utils import normalizar_logo, ErroNormalizacaoLogo, _slugify
    from db import get_db, DATABASE_URL
    import repository
    from routers.whatsapp_inbound import router as whatsapp_inbound_router
except ImportError as e:
    print(f"❌ Erro ao importar módulos locais: {e}")
    sys.exit(1)

# ============================================================================
# SETUP
# ============================================================================

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FabricaSitesAPI")

# Gerenciador de ciclo de vida (Lifespan moderno do FastAPI)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup e shutdown da API"""
    # Startup
    logger.info("🚀 API iniciada com sucesso")
    logger.info(f"📚 Documentação: http://localhost:8000/docs")
    logger.info(f"🔌 Endpoint: POST http://localhost:8000/api/v1/generate-site")
    
    yield  # API rodando aqui
    
    # Shutdown
    logger.info("🛑 API encerrada com sucesso")
    metricas.salvar_metricas()

# Criar app FastAPI com lifespan moderno
app = FastAPI(
    title="Fábrica de Sites SaaS - API",
    description="Gera site-config.json automaticamente via IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS - Permitir requisições de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Roteador de webhook inbound do WhatsApp (só recebe/registra — não qualifica
# nem responde sozinho, ver backend/routers/whatsapp_inbound.py)
app.include_router(whatsapp_inbound_router)

# Inicializar agente (singleton)
try:
    agente = AgenteConstrutor()
    logger.info("✅ Agente Construtor inicializado")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar agente: {e}")
    agente = None

metricas = obter_metricas()

# Chave usada para proteger endpoints de recebimento de leads (ex: webhook do WhatsApp)
WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY")


def verificar_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    """
    Protege endpoints de captura de leads contra acesso público.
    Exige o header `X-API-Key` batendo com WEBHOOK_API_KEY do ambiente.
    """
    if not WEBHOOK_API_KEY:
        logger.error("❌ WEBHOOK_API_KEY não configurada — endpoint protegido está bloqueado até configurar")
        raise HTTPException(
            status_code=503,
            detail="Webhook não configurado: defina WEBHOOK_API_KEY no ambiente do servidor"
        )
    if not x_api_key or x_api_key != WEBHOOK_API_KEY:
        raise HTTPException(status_code=401, detail="API key ausente ou inválida")


# ============================================================================
# MODELOS PYDANTIC (Request/Response)
# ============================================================================

class SiteRequest(BaseModel):
    """Request para geração de site"""
    nome_empresa: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="Nome da empresa/negócio"
    )
    nicho: str = Field(
        ..., 
        min_length=3, 
        max_length=100,
        description="Nicho/ramo de atuação (ex: Software, Consultoria)"
    )
    cor_preferida: str = Field(
        ..., 
        description="Cor primária em hexadecimal (ex: #6366f1)"
    )
    salvar_arquivo: bool = Field(
        default=True,
        description="Salvar JSON em arquivo?"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "nome_empresa": "Tech Solutions",
                "nicho": "Desenvolvimento de Software",
                "cor_preferida": "#4F46E5",
                "salvar_arquivo": True
            }]
        }
    )

    @field_validator('cor_preferida')
    @classmethod
    def validar_cor_hex(cls, v: str) -> str:
        """Valida formato hexadecimal"""
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError('Cor deve estar em formato hex válido: #RRGGBB')
        return v.lower()


class OnboardingWhatsApp(BaseModel):
    """Payload de captura de lead vindo do fluxo n8n/WhatsApp"""
    nome_empresa: str = Field(..., min_length=2, max_length=100, description="Nome da empresa/negócio")
    ramo_atividade: str = Field(..., min_length=3, max_length=100, description="Ramo de atividade do cliente")
    logo_url: HttpUrl = Field(..., description="URL pública do logo enviado pelo cliente")
    localizacao: str = Field(..., min_length=2, max_length=150, description="Cidade/região do negócio")
    whatsapp_contato: str = Field(..., min_length=10, max_length=20, description="WhatsApp de contato do cliente")
    cor_preferida: Optional[str] = Field(default="#6366f1", description="Cor primária em hexadecimal (opcional)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "nome_empresa": "Padaria Sabor Dourado",
                "ramo_atividade": "Padaria Artesanal",
                "logo_url": "https://exemplo.com/logo.png",
                "localizacao": "Curitiba, PR",
                "whatsapp_contato": "+5541999998888",
                "cor_preferida": "#D2691E"
            }]
        }
    )

    @field_validator('cor_preferida')
    @classmethod
    def validar_cor_hex(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato hexadecimal, se informado"""
        if v and not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError('Cor deve estar em formato hex válido: #RRGGBB')
        return v.lower() if v else v


class SiteResponse(BaseModel):
    """Response de sucesso"""
    status: str = "success"
    data: dict
    timestamp: str
    tempo_geracao_segundos: float

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "status": "success",
                "data": {
                    "metadata": {},
                    "company": {},
                    "colors": {},
                    "hero": {},
                    "sections": [],
                    "services": [],
                    "testimonials": [],
                    "contact": {},
                    "cta": {}
                },
                "timestamp": "2026-07-06T10:30:00",
                "tempo_geracao_segundos": 8.5
            }]
        }
    )


class ErrorResponse(BaseModel):
    """Response de erro"""
    status: str = "error"
    error: str
    detail: str
    timestamp: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "status": "error",
                "error": "ValidationError",
                "detail": "Cor deve estar em formato hex válido",
                "timestamp": "2026-07-06T10:30:00"
            }]
        }
    )


class HealthResponse(BaseModel):
    """Response do health check"""
    status: str
    agente_ativo: bool
    api_version: str
    timestamp: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "status": "healthy",
                "agente_ativo": True,
                "api_version": "1.0.0",
                "timestamp": "2026-07-06T10:30:00"
            }]
        }
    )


# ============================================================================
# ROTAS
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Rota raiz - Info da API"""
    return {
        "nome": "Fábrica de Sites SaaS - API",
        "versao": "1.0.0",
        "descricao": "Gera site-config.json automaticamente via IA",
        "endpoints": {
            "health": "GET /health",
            "generate": "POST /api/v1/generate-site",
            "docs": "GET /docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Info"])
async def health_check():
    """Health check - Verifica se API está pronta"""
    return HealthResponse(
        status="healthy" if agente else "degraded",
        agente_ativo=agente is not None,
        api_version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/generate-site", response_model=SiteResponse, tags=["Generation"])
async def generate_site(
    request: SiteRequest,
    background_tasks: BackgroundTasks
):
    """
    Gera site-config.json completo
    
    **Parâmetros:**
    - `nome_empresa`: Nome do negócio (2-100 caracteres)
    - `nicho`: Ramo de atuação (ex: Software, Consultoria)
    - `cor_preferida`: Cor primária em hex (ex: #6366f1)
    - `salvar_arquivo`: Se deve salvar JSON em arquivo (padrão: true)
    
    **Retorna:**
    - `status`: "success" se tudo OK
    - `data`: site-config.json completo e validado
    - `timestamp`: Data/hora da geração
    - `tempo_geracao_segundos`: Quanto tempo levou
    
    **Exemplo de uso:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/generate-site" \\
      -H "Content-Type: application/json" \\
      -d '{
        "nome_empresa": "Tech Solutions",
        "nicho": "Software",
        "cor_preferida": "#4F46E5"
      }'
    ```
    """
    import time
    
    if not agente:
        logger.error("❌ Agente não inicializado")
        raise HTTPException(
            status_code=503,
            detail="Agente Construtor não inicializado. Reinicie a API."
        )

    tempo_inicio = time.time()
    
    try:
        logger.info(f"📝 Gerando site: {request.nome_empresa} ({request.nicho})")
        
        # Gerar config
        config = agente.gerar_config_site(
            request.nome_empresa,
            request.nicho,
            request.cor_preferida
        )
        
        # Validar schema
        valido, erro, config_obj = ValidadorSchema.validar_json(config)
        
        if not valido:
            logger.error(f"❌ Schema inválido: {erro}")
            metricas.registrar_geracao(
                request.nome_empresa,
                request.nicho,
                False,
                time.time() - tempo_inicio,
                erro=erro
            )
            raise HTTPException(
                status_code=400,
                detail=f"Schema inválido: {erro}"
            )
        
        # Salvar arquivo (opcional, background)
        if request.salvar_arquivo:
            background_tasks.add_task(
                _salvar_config_background,
                config,
                request.nome_empresa,
                request.nicho
            )
        
        tempo_total = time.time() - tempo_inicio
        
        # Registrar sucesso
        metricas.registrar_geracao(
            request.nome_empresa,
            request.nicho,
            True,
            tempo_total
        )
        
        logger.info(f"✅ Site gerado com sucesso em {tempo_total:.2f}s")
        
        return SiteResponse(
            status="success",
            data=config,
            timestamp=datetime.now().isoformat(),
            tempo_geracao_segundos=round(tempo_total, 3)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        tempo_total = time.time() - tempo_inicio
        logger.error(f"❌ Erro ao gerar site: {e}")
        
        metricas.registrar_geracao(
            request.nome_empresa,
            request.nicho,
            False,
            tempo_total,
            erro=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar configuração: {str(e)}"
        )


@app.post(
    "/webhook/whatsapp",
    response_model=SiteResponse,
    tags=["Onboarding"],
    dependencies=[Depends(verificar_api_key)],
)
async def webhook_whatsapp(
    payload: OnboardingWhatsApp,
    background_tasks: BackgroundTasks
):
    """
    Recebe um lead capturado via WhatsApp (simulando o n8n) e gera o site
    completo automaticamente: normaliza o logo, roda o Agente Construtor com
    SEO by design (palavra-chave + localização) e salva o site-config.json.

    **Protegido**: exige o header `X-API-Key` igual a WEBHOOK_API_KEY do
    ambiente do servidor — não é um endpoint público.

    **Exemplo de uso:**
    ```bash
    curl -X POST "http://localhost:8000/webhook/whatsapp" \\
      -H "Content-Type: application/json" \\
      -H "X-API-Key: sua-chave-aqui" \\
      -d '{
        "nome_empresa": "Padaria Sabor Dourado",
        "ramo_atividade": "Padaria Artesanal",
        "logo_url": "https://exemplo.com/logo.png",
        "localizacao": "Curitiba, PR",
        "whatsapp_contato": "+5541999998888",
        "cor_preferida": "#D2691E"
      }'
    ```
    """
    import time

    if not agente:
        logger.error("❌ Agente não inicializado")
        raise HTTPException(
            status_code=503,
            detail="Agente Construtor não inicializado. Reinicie a API."
        )

    tempo_inicio = time.time()

    try:
        logger.info(f"📲 Lead recebido via WhatsApp: {payload.nome_empresa} ({payload.ramo_atividade})")

        # Normalizar logo (não bloqueia a geração do site se falhar)
        logo_normalizado = None
        try:
            logo_normalizado = normalizar_logo(str(payload.logo_url), payload.nome_empresa)
            logger.info(f"🖼️  Logo normalizado: {logo_normalizado}")
        except ErroNormalizacaoLogo as e:
            logger.warning(f"⚠️  Falha ao normalizar logo, seguindo sem logo customizado: {e}")

        # Gerar config com SEO by design (palavra-chave + localização)
        config = agente.gerar_config_site(
            payload.nome_empresa,
            payload.ramo_atividade,
            payload.cor_preferida,
            localizacao=payload.localizacao,
            whatsapp_contato=payload.whatsapp_contato,
            logo_url=logo_normalizado,
        )

        # Validar schema
        valido, erro, config_obj = ValidadorSchema.validar_json(config)

        if not valido:
            logger.error(f"❌ Schema inválido: {erro}")
            metricas.registrar_geracao(
                payload.nome_empresa,
                payload.ramo_atividade,
                False,
                time.time() - tempo_inicio,
                erro=erro
            )
            raise HTTPException(
                status_code=400,
                detail=f"Schema inválido: {erro}"
            )

        # Salvar no banco em background
        background_tasks.add_task(
            _salvar_config_background,
            config,
            payload.nome_empresa,
            payload.ramo_atividade
        )

        tempo_total = time.time() - tempo_inicio

        metricas.registrar_geracao(
            payload.nome_empresa,
            payload.ramo_atividade,
            True,
            tempo_total
        )

        logger.info(f"✅ Site gerado via WhatsApp em {tempo_total:.2f}s")

        return SiteResponse(
            status="success",
            data=config,
            timestamp=datetime.now().isoformat(),
            tempo_geracao_segundos=round(tempo_total, 3)
        )

    except HTTPException:
        raise
    except Exception as e:
        tempo_total = time.time() - tempo_inicio
        logger.error(f"❌ Erro ao gerar site via WhatsApp: {e}")

        metricas.registrar_geracao(
            payload.nome_empresa,
            payload.ramo_atividade,
            False,
            tempo_total,
            erro=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar site: {str(e)}"
        )


@app.get("/api/v1/metrics", tags=["Monitoring"])
async def obter_metricas_endpoint():
    """Retorna métricas de uso da API"""
    return metricas.obter_estatisticas()


@app.get("/api/v1/site-config/{slug}", tags=["Generation"])
async def obter_site_config(slug: str, db: Session = Depends(get_db)):
    """
    Recupera um site-config previamente gerado e salvo no banco pelo `slug`
    (nome da empresa "slugificado", ex: "padaria-sao-jose"). Permite que um
    frontend hospedado na Vercel (ex: Lovable) busque a config depois da
    geração inicial, sem depender apenas da resposta síncrona do POST.
    """
    if not re.match(r'^[a-z0-9-]+$', slug):
        raise HTTPException(status_code=400, detail="Slug inválido")

    site = repository.obter_site(db, slug)
    if site is None:
        raise HTTPException(status_code=404, detail=f"Config não encontrada para '{slug}'")

    return site.config


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def _salvar_config_background(config: dict, nome_empresa: str, nicho: str) -> None:
    """Salva config no Postgres (tarefa background)"""
    try:
        slug = _slugify(nome_empresa)
        db = next(get_db())
        try:
            repository.upsert_site(db, slug, nome_empresa, nicho, config)
        finally:
            db.close()
        logger.info(f"💾 Config salva no banco: slug={slug}")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar config: {e}")


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handler para erros de validação"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            status="error",
            error="ValidationError",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).model_dump()
    )


# ============================================================================
# NOTA: Startup/Shutdown agora são gerenciados pelo Lifespan (ver linha ~40)
# ============================================================================


# ============================================================================
# MAIN (Para desenvolvimento local)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Verificar se pelo menos um provedor de IA está configurado
    if not any([
        os.getenv("NVIDIA_NIM_API_KEY"),
        os.getenv("ANTHROPIC_API_KEY"),
        os.getenv("OLLAMA_URL"),
    ]):
        print("⚠️  Nenhum provedor de IA configurado (NVIDIA_NIM_API_KEY / ANTHROPIC_API_KEY / OLLAMA_URL).")
        print("   Configure ao menos um em .env antes de gerar sites.")

    if not WEBHOOK_API_KEY:
        print("⚠️  WEBHOOK_API_KEY não configurada — POST /webhook/whatsapp ficará bloqueado (503).")

    if not DATABASE_URL:
        print("⚠️  DATABASE_URL não configurada — salvar/consultar site-config via API vai falhar.")

    # Rodar servidor
    print("\n" + "="*60)
    print("🚀 Iniciando Fábrica de Sites SaaS - API")
    print("="*60)
    print("\n📚 Documentação interativa:")
    print("   http://localhost:8000/docs")
    print("\n🔌 Endpoints principais:")
    print("   POST http://localhost:8000/api/v1/generate-site")
    print("   POST http://localhost:8000/webhook/whatsapp  (requer header X-API-Key)")
    print("\n✨ Pressione Ctrl+C para parar\n")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
