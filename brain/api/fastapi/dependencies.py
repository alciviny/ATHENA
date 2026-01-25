# brain/api/fastapi/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from brain.infrastructure.persistence.database import get_async_db
from brain.infrastructure.persistence.postgres_repositories import (
    PostgresStudentRepository,
    PostgresStudyPlanRepository,
    PostgresKnowledgeRepository,
    PostgresPerformanceRepository,
    PostgresCognitiveProfileRepository,
    PostgresErrorEventRepository,
)
from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase
from brain.application.use_cases.analyze_student_performance import AnalyzeStudentPerformance
from brain.application.use_cases.record_review import RecordReviewUseCase
from brain.infrastructure.llm.mock_ai_service import MockAIService
from brain.application.ports.ai_service import AIService
from brain.application.services.roi_analysis_service import ROIAnalysisService
from brain.application.services.memory_analysis_service import MemoryAnalysisService


# =========================================================
# Repositories
# =========================================================

async def get_student_repository(
    db: AsyncSession = Depends(get_async_db),
) -> PostgresStudentRepository:
    return PostgresStudentRepository(db)


async def get_study_plan_repository(
    db: AsyncSession = Depends(get_async_db),
) -> PostgresStudyPlanRepository:
    return PostgresStudyPlanRepository(db)


async def get_knowledge_repository(
    db: AsyncSession = Depends(get_async_db),
) -> PostgresKnowledgeRepository:
    return PostgresKnowledgeRepository(db)


async def get_performance_repository(
    db: AsyncSession = Depends(get_async_db),
) -> PostgresPerformanceRepository:
    return PostgresPerformanceRepository(db)


async def get_cognitive_profile_repository(
    db: AsyncSession = Depends(get_async_db),
) -> PostgresCognitiveProfileRepository:
    return PostgresCognitiveProfileRepository(db)


async def get_error_event_repository(
    db: AsyncSession = Depends(get_async_db),
) -> PostgresErrorEventRepository:
    return PostgresErrorEventRepository(db)


from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.application.ports.repositories import KnowledgeRepository


# =========================================================
# Domain & Application Services
# =========================================================

async def get_ai_service() -> AIService:
    return MockAIService()

def get_intelligence_engine() -> IntelligenceEngine:
    return IntelligenceEngine()

async def get_roi_analysis_service(
    engine: IntelligenceEngine = Depends(get_intelligence_engine),
) -> ROIAnalysisService:
    return ROIAnalysisService(engine=engine)

async def get_memory_analysis_service(
    engine: IntelligenceEngine = Depends(get_intelligence_engine),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository),
) -> MemoryAnalysisService:
    return MemoryAnalysisService(engine=engine, knowledge_repo=knowledge_repo)


# =========================================================
# Use Cases
# =========================================================

async def get_generate_study_plan_use_case(
    student_repo: PostgresStudentRepository = Depends(get_student_repository),
    performance_repo: PostgresPerformanceRepository = Depends(get_performance_repository),
    knowledge_repo: PostgresKnowledgeRepository = Depends(get_knowledge_repository),
    study_plan_repo: PostgresStudyPlanRepository = Depends(get_study_plan_repository),
    cognitive_profile_repo: PostgresCognitiveProfileRepository = Depends(get_cognitive_profile_repository),
) -> GenerateStudyPlanUseCase:
    return GenerateStudyPlanUseCase(
        student_repo=student_repo,
        performance_repo=performance_repo,
        knowledge_repo=knowledge_repo,
        study_plan_repo=study_plan_repo,
        cognitive_profile_repo=cognitive_profile_repo,
        adaptive_rules=[],  # TODO: Inject real rules
    )


async def get_analyze_student_performance_use_case(
    error_event_repository: PostgresErrorEventRepository = Depends(get_error_event_repository),
    ai_service: AIService = Depends(get_ai_service),
) -> AnalyzeStudentPerformance:
    return AnalyzeStudentPerformance(
        error_event_repository=error_event_repository,
        ai_service=ai_service,
    )


async def get_record_review_use_case(
    performance_repo: PostgresPerformanceRepository = Depends(get_performance_repository),
    knowledge_repo: PostgresKnowledgeRepository = Depends(get_knowledge_repository),
) -> RecordReviewUseCase:
    return RecordReviewUseCase(
        performance_repo=performance_repo, 
        node_repo=knowledge_repo
    )