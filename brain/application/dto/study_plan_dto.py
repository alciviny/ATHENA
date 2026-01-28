from dataclasses import dataclass
from datetime import datetime
from typing import List, TYPE_CHECKING
from uuid import UUID

from brain.domain.entities.study_plan import StudyFocusLevel
if TYPE_CHECKING:
    from brain.domain.entities.study_plan import StudyPlan
    from brain.domain.entities.knowledge_node import KnowledgeNode


@dataclass(frozen=True, slots=True)
class KnowledgeNodeDTO:
    """DTO para um nó de conhecimento, correspondendo ao que o frontend espera."""
    id: UUID
    title: str
    context: str # Embora o front chame de 'context', parece ser o nome/tópico.
    difficulty: float

    @classmethod
    def from_entity(cls, entity: "KnowledgeNode") -> "KnowledgeNodeDTO":
        return cls(
            id=entity.id,
            title=entity.name,
            context=f"Conteúdo sobre {entity.name} relacionado à matéria {entity.subject}.",
            difficulty=entity.difficulty,
        )


@dataclass(frozen=True, slots=True)
class StudyPlanOutputDTO:
    """
    DTO de saída para representar um plano de estudo
    de forma serializável e imutável.
    """

    id: UUID
    student_id: UUID
    created_at: datetime
    knowledge_nodes: List[KnowledgeNodeDTO]
    estimated_duration_minutes: int
    focus_level: str

    @classmethod
    def from_entity(cls, entity: "StudyPlan") -> "StudyPlanOutputDTO":
        """
        Cria um DTO a partir da entidade de domínio, enriquecendo os nós.
        """
        return cls(
            id=entity.id,
            student_id=entity.student_id,
            created_at=entity.created_at,
            knowledge_nodes=[KnowledgeNodeDTO.from_entity(node) for node in entity.knowledge_nodes],
            estimated_duration_minutes=entity.estimated_duration_minutes,
            focus_level=entity.focus_level.value if isinstance(entity.focus_level, StudyFocusLevel) else str(entity.focus_level),
        )
