# brain/api/fastapi/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from brain.infrastructure.persistence.database import SessionLocal
from brain.infrastructure.persistence.postgres_repositories import (
    PostgresStudentRepository,
    PostgresStudyPlanRepository,
    PostgresKnowledgeRepository,
    PostgresPerformanceRepository
)
from brain.application.use_cases.generate_study_plan import GenerateStudyPlan
from brain.application.use_cases.analyze_student_performance import AnalyzeStudentPerformance

# Dependency para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_student_repository(db: Session = Depends(get_db)):
    return PostgresStudentRepository(db)

def get_study_plan_repository(db: Session = Depends(get_db)):
    return PostgresStudyPlanRepository(db)

def get_knowledge_repository(db: Session = Depends(get_db)):
    return PostgresKnowledgeRepository(db)

def get_performance_repository(db: Session = Depends(get_db)):
    return PostgresPerformanceRepository(db)

# Injeção nos Use Cases
def get_generate_study_plan_use_case(
    student_repo = Depends(get_student_repository),
    study_plan_repo = Depends(get_study_plan_repository),
    knowledge_repo = Depends(get_knowledge_repository)
):
    return GenerateStudyPlan(student_repo, study_plan_repo, knowledge_repo)

def get_analyze_performance_use_case(
    performance_repo = Depends(get_performance_repository),
    student_repo = Depends(get_student_repository),
    knowledge_repo = Depends(get_knowledge_repository)
):
    return AnalyzeStudentPerformance(performance_repo, student_repo, knowledge_repo)