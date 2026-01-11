from dataclasses import dataclass
from typing import Any, Dict
from uuid import UUID

from brain.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class RuleApplied(DomainEvent):
    """
    Evento emitido quando uma regra adaptativa é aplicada
    e altera o contexto de decisão.
    """

    rule_name: str
    rule_description: str

    # Representa o delta causado pela regra
    # Ex: {"focus_level": "review", "target_nodes_removed": 3}
    changes: Dict[str, Any]
