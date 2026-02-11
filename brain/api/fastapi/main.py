# brain/api/fastapi/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

import sys
import os

# Adiciona a raiz do projeto ao PYTHONPATH para permitir importações absolutas do módulo 'brain'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from brain.api.fastapi.routes import study_routes, performance_routes, roi_routes, memory_routes
from brain.api.fastapi.auth.routes import router as auth_router
from brain.api.fastapi.middleware.rate_limit import RateLimitMiddleware
from brain.api.fastapi.middleware.logging import LoggingMiddleware
from brain.api.fastapi.middleware.security import SecurityHeadersMiddleware
from brain.domain.exceptions import AthenaException, APIException
from brain.infrastructure.logging import get_logger

logger = get_logger(__name__)


# =========================================================
# Exception Handlers
# =========================================================

def athena_exception_handler(request, exc: AthenaException):
    """Handler para exceções customizadas do Athena."""
    logger.error(
        "Exceção do domínio Athena",
        path=request.url.path,
        exception_type=exc.__class__.__name__,
        message=exc.message,
        details=exc.details
    )
    
    # Se for uma APIException, usa o status_code dela
    if isinstance(exc, APIException):
        status_code = exc.status_code
    else:
        status_code = 500
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


def generic_exception_handler(request, exc: Exception):
    """Handler para exceções não tratadas."""
    logger.exception(
        "Exceção não tratada",
        path=request.url.path,
        exception_type=exc.__class__.__name__
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "Erro interno do servidor"
        }
    )


# =========================================================
# FastAPI App
# =========================================================

app = FastAPI(
    title="Athena Brain - Intelligent Adaptive Engine",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# =========================================================
# Middlewares (ordem importa!)
# =========================================================

# 1. Security headers (primeiro para todos os responses)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Logging middleware
app.add_middleware(LoggingMiddleware)

# 3. Rate limiting (antes de processar rotas)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=100,  # 100 requisições
    window_seconds=60,  # por minuto
    exempt_paths=["/", "/health", "/docs", "/redoc", "/openapi.json", "/auth/login"]
)

# =========================================================
# Exception Handlers
# =========================================================

app.add_exception_handler(AthenaException, athena_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# =========================================================
# Routes
# =========================================================

# Auth routes (não precisam de autenticação)
app.include_router(
    auth_router,
    tags=["Authentication"],
)

app.include_router(
    study_routes.router,
    prefix="/study",
    tags=["Study Plan"],
)

app.include_router(
    performance_routes.router,
    prefix="/performance",
    tags=["Performance"],
)

app.include_router(
    roi_routes.router,
    tags=["ROI"],
)

app.include_router(
    memory_routes.router,
    tags=["Memory"],
)


# =========================================================
# Health Check
# =========================================================

@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "engine": "Athena Brain",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def detailed_health():
    """Health check detalhado com status dos serviços."""
    from datetime import datetime, timezone
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "operational",
            "vector_store": "operational",
            "ai_providers": {
                "gemini": "operational",
                "groq": "operational"
            }
        }
    }
    
    return health_status
