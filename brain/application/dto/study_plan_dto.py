from dataclasses import dataclass
from datetime import datetime
from typing import List, TYPE_CHECKING
from uuid import UUID

from brain.domain.entities.study_plan import StudyFocusLevel, StudyPlan

if TYPE_CHECKING:
    from brain.domain.entities.study_plan import StudyPlan

@dataclass(frozen=True, slots=True)
class StudyPlanOutputDTO:
    """
    DTO de saída para representar um plano de estudo
    de forma serializável e imutável.
    """

    id: UUID
    student_id: UUID
    created_at: datetime
    knowledge_nodes: List[UUID]
    estimated_duration_minutes: int
    focus_level: str  # string legível do enum

    @classmethod
    def from_entity(cls, entity: "StudyPlan") -> "StudyPlanOutputDTO":
        """
        Cria um DTO a partir da entidade de domínio.
        """
        return cls(
            id=entity.id,
            student_id=entity.student_id,
            created_at=entity.created_at,
            knowledge_nodes=list(entity.knowledge_nodes),
            estimated_duration_minutes=entity.estimated_duration_minutes,
            focus_level=entity.focus_level.value if isinstance(entity.focus_level, StudyFocusLevel) else str(entity.focus_level),
        )
