from dataclasses import dataclass, field
from typing import List
from uuid import UUID

from brain.domain.events.base import DomainEvent
from brain.domain.entities.study_plan import StudyFocusLevel


@dataclass(frozen=True, slots=True, kw_only=True)
class StudyPlanGenerated(DomainEvent):
    """
    Evento emitido quando um plano de estudo é gerado
    para um estudante após análise adaptativa.
    """

    knowledge_nodes: List[UUID]
    focus_level: StudyFocusLevel
    estimated_duration_minutes: int
