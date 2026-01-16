import logging
from uuid import uuid4, UUID
from typing import Tuple, List, Optional
from datetime import datetime, timedelta

from brain.domain.entities.student import Student, StudentGoal
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.application.use_cases.analyze_student_performance import (
    AnalyzeStudentPerformance,
)
from brain.infrastructure.llm.mock_ai_service import MockAIService
from brain.infrastructure.persistence.in_memory_repositories import (
    InMemoryErrorEventRepository,
    InMemoryKnowledgeRepository,
)

logger = logging.getLogger(__name__)

# ========================
# Constantes de Seed
# ========================

MATERIA_DIREITO_ADMINISTRATIVO = "Direito Administrativo"
MATERIA_INFORMATICA = "Informática"
MATERIA_DIREITO_CONSTITUCIONAL = "Direito Constitucional"
MATERIA_LINGUA_PORTUGUESA = "Língua Portuguesa"

TOPICO_REDES_DE_COMPUTADORES = "Redes de Computadores"
TEST_STUDENT_NAME = "Jose Alcionis"

# ========================
# Seed helpers
# ========================

def seed_students(student_repo) -> List[UUID]:
    students_data = [
        (TEST_STUDENT_NAME, StudentGoal.POLICIA_FEDERAL),
        ("Maria Silva", StudentGoal.INSS),
        ("João Santos", StudentGoal.RECEITA_FEDERAL),
    ]

    student_ids: List[UUID] = []

    for name, goal in students_data:
        student_id = uuid4()
        student_repo.add(Student(id=student_id, name=name, goal=goal))
        student_ids.append(student_id)

    logger.info("Seeded %s students", len(student_ids))
    return student_ids


def seed_knowledge_graph(know_repo) -> List[UUID]:
    knowledge_data = [
        (MATERIA_DIREITO_ADMINISTRATIVO, "Atos Administrativos", 0.8, 1.0),
        (MATERIA_DIREITO_ADMINISTRATIVO, "Princípios da Administração Pública", 0.6, 0.9),
        (MATERIA_DIREITO_ADMINISTRATIVO, "Licitações e Contratos", 0.7, 0.85),
        (MATERIA_INFORMATICA, TOPICO_REDES_DE_COMPUTADORES, 0.6, 0.9),
        (MATERIA_INFORMATICA, "Segurança da Informação", 0.7, 0.95),
        (MATERIA_INFORMATICA, "Sistemas Operacionais", 0.5, 0.8),
        (MATERIA_DIREITO_CONSTITUCIONAL, "Direitos Fundamentais", 0.7, 1.0),
        (MATERIA_DIREITO_CONSTITUCIONAL, "Organização do Estado", 0.6, 0.85),
        (MATERIA_LINGUA_PORTUGUESA, "Sintaxe e Semântica", 0.5, 0.9),
        (MATERIA_LINGUA_PORTUGUESA, "Interpretação de Textos", 0.6, 1.0),
    ]

    nodes = []
    node_ids = []

    for subject, name, difficulty, weight in knowledge_data:
        node_id = uuid4()
        nodes.append(
            KnowledgeNode(
                id=node_id,
                subject=subject,
                name=name,
                difficulty=difficulty,
                weight_in_exam=weight,
            )
        )
        node_ids.append(node_id)

    know_repo.set_graph(nodes)

    logger.info("Seeded %s knowledge nodes", len(nodes))
    return node_ids


def seed_performance_events(performance_repo, student_id: UUID) -> None:
    from brain.domain.entities.PerformanceEvent import (
        PerformanceEvent,
        PerformanceEventType,
        PerformanceMetric,
    )

    base_date = datetime.now() - timedelta(days=7)

    events = [
        (MATERIA_DIREITO_ADMINISTRATIVO, 1.0),
        (MATERIA_INFORMATICA, 0.0),
        (MATERIA_DIREITO_CONSTITUCIONAL, 1.0),
    ]

    for idx, (topic, value) in enumerate(events, 1):
        performance_repo.add_event(
            PerformanceEvent(
                id=uuid4(),
                student_id=student_id,
                event_type=PerformanceEventType.QUIZ,
                occurred_at=base_date + timedelta(days=idx),
                topic=topic,
                metric=PerformanceMetric.ACCURACY,
                value=value,
                baseline=0.5,
            )
        )

    logger.info("Seeded %s performance events", len(events))


# ========================
# Seed Orquestrador
# ========================

def seed_repositories_extended(
    student_repo,
    know_repo,
    performance_repo: Optional[object] = None,
) -> Tuple[UUID, List[UUID]]:
    student_ids = seed_students(student_repo)
    node_ids = seed_knowledge_graph(know_repo)

    if performance_repo:
        seed_performance_events(performance_repo, student_ids[0])

    logger.info("System seeded successfully")
    return student_ids[0], node_ids


# ========================
# Reset helpers
# ========================

def clear_repositories(student_repo, know_repo, performance_repo=None):
    if hasattr(student_repo, "students"):
        student_repo.students.clear()

    if hasattr(know_repo, "nodes"):
        know_repo.nodes.clear()

    if performance_repo and hasattr(performance_repo, "events"):
        performance_repo.events.clear()

    logger.info("Repositories cleared successfully")


# ========================
# Instâncias Singleton
# ========================

knowledge_repo_instance = InMemoryKnowledgeRepository()
error_event_repo_instance = InMemoryErrorEventRepository(
    knowledge_repo=knowledge_repo_instance
)
ai_service_instance = MockAIService(delay_seconds=0)


# ========================
# Providers FastAPI
# ========================

def get_analyze_student_performance_use_case() -> AnalyzeStudentPerformance:
    return AnalyzeStudentPerformance(
        error_event_repository=error_event_repo_instance,
        ai_service=ai_service_instance,
    )
