# brain/api/fastapi/dependencies.py

from fastapi import Depends
from sqlalchemy.orm import Session

from brain.infrastructure.persistence.database import SessionLocal
from brain.infrastructure.persistence.postgres_repositories import (
    PostgresStudentRepository,
    PostgresStudyPlanRepository,
    PostgresKnowledgeRepository,
    PostgresPerformanceRepository,
)

from brain.application.use_cases.generate_study_plan import GenerateStudyPlan
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


# =========================================================
# Use Cases
# =========================================================

def get_generate_study_plan_use_case(
    student_repo = Depends(get_student_repository),
    study_plan_repo = Depends(get_study_plan_repository),
    knowledge_repo = Depends(get_knowledge_repository),
) -> GenerateStudyPlan:
    return GenerateStudyPlan(
        student_repo=student_repo,
        study_plan_repo=study_plan_repo,
        knowledge_repo=knowledge_repo,
    )


def get_analyze_performance_use_case(
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
