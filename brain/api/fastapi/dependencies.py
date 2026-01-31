from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from brain.config.settings import Settings
from brain.infrastructure.persistence.database import get_async_db
from brain.application.ports.ai_service import AIService
from brain.application.services.roi_analysis_service import ROIAnalysisService
from brain.application.services.memory_analysis_service import MemoryAnalysisService
from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.application.ports import repositories as ports

# --- IMPORTS DOS SERVIÇOS DE IA ---
from brain.infrastructure.llm.gemini_service import GeminiService
from brain.infrastructure.llm.groq_service import GroqService
from brain.infrastructure.llm.mock_ai_service import MockAIService

from brain.infrastructure.persistence.qdrant_repository import QdrantKnowledgeVectorRepository
from brain.application.ports.repositories import KnowledgeVectorRepository

# Use Cases
from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase
from brain.application.use_cases.analyze_student_performance import AnalyzeStudentPerformance
from brain.application.use_cases.record_review import RecordReviewUseCase

# Postgres Repositories
from brain.infrastructure.persistence.postgres_repositories import (
    PostgresStudentRepository,
    PostgresStudyPlanRepository,
    PostgresKnowledgeRepository,
    PostgresPerformanceRepository,
    PostgresCognitiveProfileRepository,
    PostgresErrorEventRepository,
)

# In-Memory Repositories (for fallback or testing)
from brain.infrastructure.persistence.in_memory_repositories import (
    InMemoryStudentRepository,
    InMemoryStudyPlanRepository,
    InMemoryKnowledgeRepository,
    InMemoryPerformanceRepository,
    InMemoryCognitiveProfileRepository,
    InMemoryErrorEventRepository,
)

# =========================================================
# Settings and Singletons
# =========================================================

@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the settings."""
    return Settings()

# Create singleton instances of in-memory repositories
@lru_cache()
def get_in_memory_student_repo() -> InMemoryStudentRepository:
    return InMemoryStudentRepository()

@lru_cache()
def get_in_memory_study_plan_repo() -> InMemoryStudyPlanRepository:
    return InMemoryStudyPlanRepository()

@lru_cache()
def get_in_memory_knowledge_repo() -> InMemoryKnowledgeRepository:
    return InMemoryKnowledgeRepository()

@lru_cache()
def get_in_memory_performance_repo() -> InMemoryPerformanceRepository:
    return InMemoryPerformanceRepository()

@lru_cache()
def get_in_memory_cognitive_profile_repo() -> InMemoryCognitiveProfileRepository:
    return InMemoryCognitiveProfileRepository()

@lru_cache()
def get_in_memory_error_event_repo() -> InMemoryErrorEventRepository:
    return InMemoryErrorEventRepository()


# =========================================================
# Conditional Repository Providers
# =========================================================

async def get_student_repository(
    db: AsyncSession = Depends(get_async_db),
    settings: Settings = Depends(get_settings),
) -> ports.StudentRepository:
    if settings.USE_IN_MEMORY_DB:
        return get_in_memory_student_repo()
    return PostgresStudentRepository(db)

async def get_study_plan_repository(
    db: AsyncSession = Depends(get_async_db),
    settings: Settings = Depends(get_settings),
) -> ports.StudyPlanRepository:
    if settings.USE_IN_MEMORY_DB:
        return get_in_memory_study_plan_repo()
    return PostgresStudyPlanRepository(db)

async def get_knowledge_repository(
    db: AsyncSession = Depends(get_async_db),
    settings: Settings = Depends(get_settings),
) -> ports.KnowledgeRepository:
    if settings.USE_IN_MEMORY_DB:
        return get_in_memory_knowledge_repo()
    return PostgresKnowledgeRepository(db)

async def get_performance_repository(
    db: AsyncSession = Depends(get_async_db),
    settings: Settings = Depends(get_settings),
) -> ports.PerformanceRepository:
    if settings.USE_IN_MEMORY_DB:
        return get_in_memory_performance_repo()
    return PostgresPerformanceRepository(db)

async def get_cognitive_profile_repository(
    db: AsyncSession = Depends(get_async_db),
    settings: Settings = Depends(get_settings),
) -> ports.CognitiveProfileRepository:
    if settings.USE_IN_MEMORY_DB:
        return get_in_memory_cognitive_profile_repo()
    return PostgresCognitiveProfileRepository(db)

async def get_error_event_repository(
    db: AsyncSession = Depends(get_async_db),
    settings: Settings = Depends(get_settings),
) -> ports.ErrorEventRepository:
    if settings.USE_IN_MEMORY_DB:
        return get_in_memory_error_event_repo()
    return PostgresErrorEventRepository(db)

def get_knowledge_vector_repository(
    settings: Settings = Depends(get_settings),
) -> KnowledgeVectorRepository:
    """Provides a vector repository instance based on settings."""
    return QdrantKnowledgeVectorRepository(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )


# =========================================================
# Domain & Application Services
# =========================================================

def get_ai_service(settings: Settings = Depends(get_settings)) -> AIService:
    """
    Fábrica de Serviços de IA com estratégia de Fallback:
    1. GroqService (Híbrido) -> Preferencial (Rápido + Gratuito)
    2. GeminiService (Puro) -> Backup (Cota limitada)
    3. MockAIService -> Desenvolvimento/Testes
    """
    
    # OPÇÃO 1: Groq (Híbrido: Groq p/ Texto + Gemini p/ Vetor)
    if settings.GROQ_API_KEY:
        return GroqService(
            groq_api_key=settings.GROQ_API_KEY,
            gemini_api_key=settings.GEMINI_API_KEY, # Necessário para embeddings
            model=settings.GROQ_MODEL
        )
    
    # OPÇÃO 2: Gemini Puro (Texto + Vetor)
    # Útil se não tiver chave da Groq configurada
    if settings.GEMINI_API_KEY:
        return GeminiService(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL
        )

    # OPÇÃO 3: Mock (Sem chaves configuradas)
    return MockAIService()

def get_intelligence_engine() -> IntelligenceEngine:
    return IntelligenceEngine()

async def get_roi_analysis_service(
    engine: IntelligenceEngine = Depends(get_intelligence_engine),
) -> ROIAnalysisService:
    return ROIAnalysisService(engine=engine)

async def get_memory_analysis_service(
    engine: IntelligenceEngine = Depends(get_intelligence_engine),
    knowledge_repo: ports.KnowledgeRepository = Depends(get_knowledge_repository),
) -> MemoryAnalysisService:
    return MemoryAnalysisService(engine=engine, knowledge_repo=knowledge_repo)


# =========================================================
# Use Cases
# =========================================================

async def get_generate_study_plan_use_case(
    student_repo: ports.StudentRepository = Depends(get_student_repository),
    performance_repo: ports.PerformanceRepository = Depends(get_performance_repository),
    knowledge_repo: ports.KnowledgeRepository = Depends(get_knowledge_repository),
    study_plan_repo: ports.StudyPlanRepository = Depends(get_study_plan_repository),
    cognitive_profile_repo: ports.CognitiveProfileRepository = Depends(get_cognitive_profile_repository),
    vector_repo: KnowledgeVectorRepository = Depends(get_knowledge_vector_repository),
    ai_service: AIService = Depends(get_ai_service),
) -> GenerateStudyPlanUseCase:
    return GenerateStudyPlanUseCase(
        student_repo=student_repo,
        performance_repo=performance_repo,
        knowledge_repo=knowledge_repo,
        study_plan_repo=study_plan_repo,
        cognitive_profile_repo=cognitive_profile_repo,
        vector_repo=vector_repo,
        ai_service=ai_service,
        adaptive_rules=[],  # TODO: Inject real rules
    )

async def get_analyze_student_performance_use_case(
    error_event_repository: ports.ErrorEventRepository = Depends(get_error_event_repository),
    ai_service: AIService = Depends(get_ai_service),
) -> AnalyzeStudentPerformance:
    return AnalyzeStudentPerformance(
        error_event_repository=error_event_repository,
        ai_service=ai_service,
    )

async def get_record_review_use_case(
    performance_repo: ports.PerformanceRepository = Depends(get_performance_repository),
    knowledge_repo: ports.KnowledgeRepository = Depends(get_knowledge_repository),
    intelligence_engine: IntelligenceEngine = Depends(get_intelligence_engine),
) -> RecordReviewUseCase:
    return RecordReviewUseCase(
        performance_repo=performance_repo,
        node_repo=knowledge_repo,
        intelligence_engine=intelligence_engine,
    )