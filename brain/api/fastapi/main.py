import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

from brain.api.fastapi.routes import study_routes
from brain.application.use_cases.generate_study_plan import StudentNotFoundError
from brain.infrastructure.persistence.database import engine, Base


# ========================
# Configuração do Logger
# ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Athena Brain API",
    version="0.1.0",
    description="API para geração de planos de estudo adaptativos com auditabilidade e inteligência cognitiva."
)

# Incluindo as rotas de estudo
app.include_router(study_routes.router, prefix="/api/v1/study", tags=["Study"])

# ========================
# Middlewares e eventos
# ========================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.now(timezone.utc)
    response = await call_next(request)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info(
        "%s %s completed in %.3fs",
        request.method,
        request.url.path,
        duration
    )
    return response

# ========================
# Tratamento global de exceções
# ========================

@app.exception_handler(StudentNotFoundError)
async def student_not_found_handler(request: Request, exc: StudentNotFoundError):
    logger.warning("Student not found for path: %s", request.url.path)
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "path": request.url.path}
    )

# ========================
# Health check
# ========================

@app.get("/", tags=["Health"])
def health_check():
    """
    Endpoint de health check do sistema.
    """
    return {
        "status": "online",
        "system": "Athena Brain",
        "version": app.version,
        "time": datetime.now(timezone.utc).isoformat()
    }

@app.on_event("startup")
async def startup_event():
    # Cria as tabelas se não existirem
    Base.metadata.create_all(bind=engine)
    
    # Chama o seeder (opcional, se quiser popular o banco novo)
    # seed_repositories_extended(student_repo, know_repo, perf_repo)