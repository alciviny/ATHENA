from uuid import uuid4
from brain.domain.entities.student import Student, Goal
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.policies.rules.retention_drop_rule import RetentionDropRule
from brain.infrastructure.persistence.in_memory_repositories import (
    InMemoryStudentRepository,
    InMemoryPerformanceRepository,
    InMemoryKnowledgeRepository,
    InMemoryStudyPlanRepository
)
from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase


STUDY_PLAN_SUCCESS_MESSAGE = "\n Plano Gerado com Sucesso!"
TEST_STUDENT_NAME = "Concurseiro Elite"
ORCHESTRATION_ERROR_PREFIX = " Erro na orquestração: "



# 1. Setup da Infraestrutura (Mocks/In-Memory)
student_repo = InMemoryStudentRepository()
perf_repo = InMemoryPerformanceRepository()
know_repo = InMemoryKnowledgeRepository()
plan_repo = InMemoryStudyPlanRepository()

# 2. Setup de Dados de Teste
student_id = uuid4()
profile = CognitiveProfile(retention_rate=0.65, learning_speed=1.0) # Retenção baixa
student = Student(id=student_id, name=TEST_STUDENT_NAME, goal=Goal.PF, cognitive_profile=profile)
student_repo.save(student)

# 3. Execução do Use Case
use_case = GenerateStudyPlanUseCase(
    student_repo=student_repo,
    performance_repo=perf_repo,
    knowledge_repo=know_repo,
    study_plan_repo=plan_repo,
    adaptive_rules=[RetentionDropRule()] # Aplicando a regra que você já criou
)

try:
    result = use_case.execute(student_id)
    print(STUDY_PLAN_SUCCESS_MESSAGE)
    print(f"Foco do Plano: {result.focus_level}")
    print(f"Duração Estimada: {result.estimated_duration_minutes} min")
except Exception as e:
    print(f"{ORCHESTRATION_ERROR_PREFIX}{e}")






