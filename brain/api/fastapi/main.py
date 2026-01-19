# brain/api/fastapi/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI

from brain.api.fastapi.routes import study_routes, performance_routes, roi_routes, memory_routes


# =========================================================
# Application Lifespan
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ponto único de inicialização e finalização da aplicação.
    Ideal para:
    - conexões externas
    - warmup de cache
    - verificação de dependências
    """
    yield
    # shutdown hooks aqui se necessário


# =========================================================
# FastAPI App
# =========================================================

app = FastAPI(
    title="Athena Brain - Intelligent Adaptive Engine",
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================================
# Routes
# =========================================================

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
def health_check():
    return {
        "status": "online",
        "engine": "Athena Brain",
    }
