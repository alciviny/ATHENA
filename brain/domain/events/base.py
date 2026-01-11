from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """
    Evento de domínio base.

    Representa um fato que aconteceu no passado e
    é relevante para o negócio.
    """

    # Aggregate que originou o evento (Student, StudyPlan, etc.)
    aggregate_id: UUID

    id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    # Identificação semântica do evento
    event_type: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "event_type", self.__class__.__name__)
