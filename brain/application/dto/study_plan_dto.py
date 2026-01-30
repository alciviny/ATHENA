from dataclasses import dataclass
from datetime import datetime
from typing import List, TYPE_CHECKING, Dict, Any
from uuid import UUID

from brain.domain.entities.study_plan import StudyFocusLevel
if TYPE_CHECKING:
    from brain.domain.entities.study_plan import StudyPlan


@dataclass(frozen=True, slots=True)
class StudyItemDTO:
    """DTO para um item de estudo, como um flashcard gerado por IA."""
    id: UUID
    title: str
    type: str  # e.g., 'flashcard', 'theory'
    difficulty: float
    question: str
    options: List[str]
    correct_index: int
    explanation: str


@dataclass(frozen=True, slots=True)
class StudyPlanOutputDTO:
    """
    DTO de saída para representar um plano de estudo
    de forma serializável e imutável.
    """

    id: UUID
    student_id: UUID
    created_at: datetime
    study_items: List[StudyItemDTO]
    estimated_duration_minutes: int
    focus_level: str

    @classmethod
    def from_entity(cls, entity: "StudyPlan", study_items: List[StudyItemDTO]) -> "StudyPlanOutputDTO":
        """
        Cria um DTO a partir da entidade de domínio e dos itens de estudo gerados.
        """
        return cls(
            id=entity.id,
            student_id=entity.student_id,
            created_at=entity.created_at,
            study_items=study_items,
            estimated_duration_minutes=entity.estimated_duration_minutes,
            focus_level=entity.focus_level.value if isinstance(entity.focus_level, StudyFocusLevel) else str(entity.focus_level),
        )
