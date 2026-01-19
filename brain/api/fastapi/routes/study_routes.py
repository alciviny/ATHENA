from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase
from brain.application.use_cases.record_review import RecordReviewUseCase
from brain.infrastructure.persistence.database import get_db
from brain.infrastructure.persistence.postgres_repositories import (
    PostgresStudentRepository, 
    PostgresPerformanceRepository, 
    PostgresKnowledgeRepository, 
    PostgresStudyPlanRepository
)
from brain.domain.policies.rules.retention_drop_rule import RetentionDropRule
from brain.domain.policies.rules.low_accuracy_high_difficulty import LowAccuracyHighDifficultyRule
from brain.api.fastapi.dependencies import get_node_repository


router = APIRouter()


@router.post("/generate-plan/{student_id}")
async def generate_plan(student_id: UUID, db: Session = Depends(get_db)):
    # Instancia os repositórios reais usando a sessão da requisição
    student_repo = PostgresStudentRepository(db)
    perf_repo = PostgresPerformanceRepository(db)
    know_repo = PostgresKnowledgeRepository(db)
    plan_repo = PostgresStudyPlanRepository(db)

    use_case = GenerateStudyPlanUseCase(
        student_repo=student_repo,
        performance_repo=perf_repo,
        knowledge_repo=know_repo,
        study_plan_repo=plan_repo,
        adaptive_rules=[RetentionDropRule(), LowAccuracyHighDifficultyRule()]
    )
    
    return use_case.execute(student_id)

@router.post("/review/{node_id}")
async def record_review(
    node_id: UUID, 
    review_data: dict, # Contém {"grade": 1..4}
    repo = Depends(get_node_repository)
):
    use_case = RecordReviewUseCase(repo)
    updated_node = await use_case.execute(node_id, review_data["grade"])
    return updated_node