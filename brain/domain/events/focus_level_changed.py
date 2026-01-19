from dataclasses import dataclass
from uuid import UUID

from brain.domain.events.base import DomainEvent
from brain.domain.entities.study_plan import StudyFocusLevel


@dataclass(frozen=True, slots=True, kw_only=True)
class FocusLevelChanged(DomainEvent):
    """
    Evento emitido quando o foco de um plano de estudo
    é alterado por decisão adaptativa.
    """

    previous_focus: StudyFocusLevel
    new_focus: StudyFocusLevel
