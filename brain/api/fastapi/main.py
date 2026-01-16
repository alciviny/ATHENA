import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from brain.api.fastapi.routes import study_routes, performance_routes
from brain.application.use_cases.generate_study_plan import StudentNotFoundError
from brain.infrastructure.persistence.database import engine, Base

# ========================
# Logger
# ========================

logger = logging.getLogger("athena.api")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# ========================
# App
# ========================

app = FastAPI(
    title="Athena Brain API",
    version="0.1.0",
    description=(
        "API para geração de planos de estudo adaptativos "
        "com auditabilidade e inteligência cognitiva."
    ),
)

# ========================
# Rotas
# ========================

app.include_router(
    study_routes.router,
    prefix="/api/v1/study",
    tags=["Study"],
)

app.include_router(
    performance_routes.router,
    prefix="/api/v1",
    tags=["Performance"],
)

# ========================
# Middleware
# ========================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now(timezone.utc)

    response = await call_next(request)

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response

# ========================
# Exception Handlers
# ========================

@app.exception_handler(StudentNotFoundError)
async def student_not_found_handler(
    request: Request,
    exc: StudentNotFoundError,
):
    logger.warning(
        "Student not found | path=%s | detail=%s",
        request.url.path,
        exc,
    )

    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc),
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

# ========================
# Health Check
# ========================

@app.get("/", tags=["Health"])
async def health_check():
    """
    Health check do sistema.
    """
    return {
        "status": "online",
        "system": "Athena Brain",
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ========================
# Startup
# ========================

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Athena Brain API...")

    # Cria as tabelas
    Base.metadata.create_all(bind=engine)

    # Imports tardios para evitar custo desnecessário no boot
    from brain.infrastructure.persistence.database import SessionLocal
    from brain.api.fastapi.dependencies import seed_repositories_extended
    from brain.infrastructure.persistence.postgres_repositories import (
        PostgresStudentRepository,
        PostgresKnowledgeRepository,
        PostgresPerformanceRepository,
    )

    with SessionLocal() as db:
        student_repo = PostgresStudentRepository(db)
        knowledge_repo = PostgresKnowledgeRepository(db)
        performance_repo = PostgresPerformanceRepository(db)

        seed_repositories_extended(
            student_repo,
            knowledge_repo,
            performance_repo,
        )

        db.commit()

    logger.info("Startup completed successfully.")
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from brain.api.fastapi.routes import study_routes, performance_routes
from brain.application.use_cases.generate_study_plan import StudentNotFoundError
from brain.infrastructure.persistence.database import engine, Base

# ========================
# Logger
# ========================

logger = logging.getLogger("athena.api")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# ========================
# App
# ========================

app = FastAPI(
    title="Athena Brain API",
    version="0.1.0",
    description=(
        "API para geração de planos de estudo adaptativos "
        "com auditabilidade e inteligência cognitiva."
    ),
)

# ========================
# Rotas
# ========================

app.include_router(
    study_routes.router,
    prefix="/api/v1/study",
    tags=["Study"],
)

app.include_router(
    performance_routes.router,
    prefix="/api/v1",
    tags=["Performance"],
)

# ========================
# Middleware
# ========================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now(timezone.utc)

    response = await call_next(request)

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(
        "%s %s -> %s (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )

    return response

# ========================
# Exception Handlers
# ========================

@app.exception_handler(StudentNotFoundError)
async def student_not_found_handler(
    request: Request,
    exc: StudentNotFoundError,
):
    logger.warning(
        "Student not found | path=%s | detail=%s",
        request.url.path,
        exc,
    )

    return JSONResponse(
        status_code=404,
        content={
            "detail": str(exc),
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

# ========================
# Health Check
# ========================

@app.get("/", tags=["Health"])
async def health_check():
    """
    Health check do sistema.
    """
    return {
        "status": "online",
        "system": "Athena Brain",
        "version": app.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ========================
# Startup
# ========================

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Athena Brain API...")

    # Cria as tabelas
    Base.metadata.create_all(bind=engine)

    # Imports tardios para evitar custo desnecessário no boot
    from brain.infrastructure.persistence.database import SessionLocal
    from brain.api.fastapi.dependencies import seed_repositories_extended
    from brain.infrastructure.persistence.postgres_repositories import (
        PostgresStudentRepository,
        PostgresKnowledgeRepository,
        PostgresPerformanceRepository,
    )

    with SessionLocal() as db:
        student_repo = PostgresStudentRepository(db)
        knowledge_repo = PostgresKnowledgeRepository(db)
        performance_repo = PostgresPerformanceRepository(db)

        seed_repositories_extended(
            student_repo,
            knowledge_repo,
            performance_repo,
        )

        db.commit()

    logger.info("Startup completed successfully.")
