# brain/api/fastapi/dependencies.py

from fastapi import Depends
from sqlalchemy.orm import Session

from brain.infrastructure.persistence.database import SessionLocal
from brain.infrastructure.persistence.postgres_repositories import (
    PostgresStudentRepository,
    PostgresStudyPlanRepository,
    PostgresKnowledgeRepository,
    PostgresPerformanceRepository,
    PostgresCognitiveProfileRepository,
)

from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase
from brain.application.use_cases.analyze_student_performance import AnalyzeStudentPerformance


# =========================================================
# Database Session (Unit of Work boundary)
# =========================================================

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =========================================================
# Repositories
# =========================================================

def get_student_repository(
    db: Session = Depends(get_db),
) -> PostgresStudentRepository:
    return PostgresStudentRepository(db)


def get_study_plan_repository(
    db: Session = Depends(get_db),
) -> PostgresStudyPlanRepository:
    return PostgresStudyPlanRepository(db)


def get_knowledge_repository(
    db: Session = Depends(get_db),
) -> PostgresKnowledgeRepository:
    return PostgresKnowledgeRepository(db)


def get_performance_repository(
    db: Session = Depends(get_db),
) -> PostgresPerformanceRepository:
    return PostgresPerformanceRepository(db)


def get_cognitive_profile_repository(
    db: Session = Depends(get_db),
) -> PostgresCognitiveProfileRepository:
    return PostgresCognitiveProfileRepository(db)


# =========================================================
# Use Cases
# =========================================================

def get_generate_study_plan_use_case(
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


def get_analyze_student_performance_use_case(
    performance_repo = Depends(get_performance_repository),
    student_repo = Depends(get_student_repository),
    knowledge_repo = Depends(get_knowledge_repository),
) -> AnalyzeStudentPerformance:
    return AnalyzeStudentPerformance(
        performance_repo=performance_repo,
        student_repo=student_repo,
        knowledge_repo=knowledge_repo,
    )

# =========================================================
# Domain & Application Services
# =========================================================

from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.application.services.roi_analysis_service import ROIAnalysisService
from brain.application.services.memory_analysis_service import MemoryAnalysisService

def get_intelligence_engine() -> IntelligenceEngine:
    return IntelligenceEngine()

def get_roi_analysis_service(
    engine: IntelligenceEngine = Depends(get_intelligence_engine)
) -> ROIAnalysisService:
    return ROIAnalysisService(engine)

def get_memory_analysis_service(
    engine: IntelligenceEngine = Depends(get_intelligence_engine),
    knowledge_repo: PostgresKnowledgeRepository = Depends(get_knowledge_repository),
) -> MemoryAnalysisService:
    return MemoryAnalysisService(engine, knowledge_repo)


# =========================================================
# Semantic & Advanced Analysis (Added for RecordReview)
# =========================================================
from functools import lru_cache
from brain.config import settings
from brain.application.use_cases.record_review import RecordReviewUseCase
from brain.domain.services.semantic_propagator import SemanticPropagator
from brain.infrastructure.persistence.qdrant_repository import QdrantKnowledgeVectorRepository


@lru_cache
def get_vector_repository() -> QdrantKnowledgeVectorRepository:
    """
    Factory with cache for the vector repository.
    """
    return QdrantKnowledgeVectorRepository(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION,
    )


# Note: The original get_intelligence_engine is now cached
@lru_cache
def get_cached_intelligence_engine() -> IntelligenceEngine:
    """
    Cached factory for the Intelligence Engine.
    """
    return IntelligenceEngine()


def get_record_review_use_case(
    node_repo: PostgresKnowledgeRepository = Depends(get_knowledge_repository),
    perf_repo: PostgresPerformanceRepository = Depends(get_performance_repository),
    vector_repo: QdrantKnowledgeVectorRepository = Depends(get_vector_repository),
    engine: IntelligenceEngine = Depends(get_cached_intelligence_engine),
) -> RecordReviewUseCase:
    """
    Provider for the Record Review use case.
    """
    propagator = SemanticPropagator(
        knowledge_repository=node_repo,
        vector_repository=vector_repo,
    )
    return RecordReviewUseCase(
        node_repo=node_repo,
        perf_repo=perf_repo,
        engine=engine,
        propagator=propagator,
    )

