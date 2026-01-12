from fastapi import APIRouter, HTTPException
from uuid import UUID
from typing import List

from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase, StudentNotFoundError
from brain.infrastructure.persistence.in_memory_repositories import (
    InMemoryStudentRepository,
    InMemoryPerformanceRepository,
    InMemoryKnowledgeRepository,
    InMemoryStudyPlanRepository
)
from brain.domain.policies.rules.retention_drop_rule import RetentionDropRule
from brain.domain.policies.rules.low_accuracy_high_difficulty import LowAccuracyHighDifficultyRule

router = APIRouter()

# --- Instâncias Globais (Para manter os dados vivos na memória) ---
student_repo = InMemoryStudentRepository()
perf_repo = InMemoryPerformanceRepository()
know_repo = InMemoryKnowledgeRepository()
plan_repo = InMemoryStudyPlanRepository()

# Maestro
generate_plan_use_case = GenerateStudyPlanUseCase(
    student_repo=student_repo,
    performance_repo=perf_repo,
    knowledge_repo=know_repo,
    study_plan_repo=plan_repo,
    adaptive_rules=[RetentionDropRule, LowAccuracyHighDifficultyRule]
)

@router.post("/generate-plan/{student_id}")
async def generate_plan(student_id: UUID):
    # O Use Case já lida com a lógica, a rota apenas entrega o resultado
    return generate_plan_use_case.execute(student_id)