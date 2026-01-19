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
