from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Dict, List

from brain.domain.entities.student import Student, StudentGoal
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.performance_event import (
    PerformanceEvent,
    PerformanceMetric,
    PerformanceEventType,
)
from brain.domain.entities.knowledge_node import KnowledgeNode


# =========================
# STUDENT
# =========================

def fake_student(
    *,
    student_id: UUID | None = None,
    name: str = "Test Student",
    goal: StudentGoal = StudentGoal.POLICIA_FEDERAL,
) -> Student:
    return Student(
        id=student_id or uuid4(),
        name=name,
        goal=goal,
    )


# =========================
# COGNITIVE PROFILE
# =========================

def fake_cognitive_profile(
    *,
    id: UUID | None = None,
    student_id: UUID | None = None,
    retention_rate: float = 0.5,
    learning_speed: float = 0.5,
    stress_sensitivity: float = 0.5,
    error_patterns: Dict[str, float] | None = None,
) -> CognitiveProfile:
    return CognitiveProfile(
        id=id or uuid4(),
        student_id=student_id or uuid4(),
        retention_rate=retention_rate,
        learning_speed=learning_speed,
        stress_sensitivity=stress_sensitivity,
        error_patterns=error_patterns or {},
    )


# =========================
# PERFORMANCE EVENT
# =========================

def fake_performance_event(
    *,
    metric: PerformanceMetric,
    value: float = 0.4,
    baseline: float = 0.7,
    student_id: UUID | None = None,
    event_type: PerformanceEventType = PerformanceEventType.STUDY_SESSION,
    occurred_at: datetime | None = None,
    topic: str = "Test Topic",
) -> PerformanceEvent:
    return PerformanceEvent(
        id=uuid4(),
        student_id=student_id or uuid4(),
        event_type=event_type,
        occurred_at=occurred_at or datetime.now(timezone.utc),
        topic=topic,
        metric=metric,
        value=value,
        baseline=baseline,
    )


# =========================
# KNOWLEDGE NODE
# =========================

def fake_knowledge_node(
    *,
    node_id: UUID | None = None,
    name: str = "Test Node",
    subject: str = "Test Subject",
    stability: float = 0.0,
    difficulty: float = 5.0,
) -> KnowledgeNode:
    return KnowledgeNode(
        id=node_id or uuid4(),
        name=name,
        subject=subject,
        stability=stability,
        difficulty=difficulty,
    )


# =========================
# HELPERS SEMÂNTICOS (OPCIONAL, MAS PODEROSO)
# =========================

def high_difficulty_node(**kwargs) -> KnowledgeNode:
    return fake_knowledge_node(difficulty=8.0, **kwargs)


def high_impact_node(**kwargs) -> KnowledgeNode:
    # TODO: O conceito de "impacto" foi removido do nó. 
    # Este helper pode precisar ser repensado ou removido.
    return fake_knowledge_node(**kwargs)


def weak_accuracy_event() -> PerformanceEvent:
    return fake_performance_event(metric=PerformanceMetric.ACCURACY)


def retention_drop_event() -> PerformanceEvent:
    return fake_performance_event(metric=PerformanceMetric.RETENTION)
