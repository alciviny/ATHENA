from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from enum import Enum


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Garante que um valor esteja dentro de um intervalo seguro.
    """
    return max(min_value, min(max_value, value))


class ErrorType(str, Enum):
    """
    Tipos de erro cognitivo observados durante estudo ou avaliação.
    """
    CONTEUDO = "conteudo"
    INTERPRETACAO = "interpretacao"
    DESATENCAO = "desatencao"
    GESTAO_TEMPO = "gestao_tempo"


@dataclass(frozen=True)
class ErrorEvent:
    """
    Evento cognitivo que representa um erro cometido pelo aluno.

    Esses eventos alimentam o perfil cognitivo e guiam decisões adaptativas.
    """
    id: UUID
    student_id: UUID
    knowledge_node_id: UUID

    error_type: ErrorType
    occurred_at: datetime
    severity: float  # impacto do erro (0.0 - 1.0)

    def __post_init__(self) -> None:
        """
        Normaliza automaticamente a severidade.
        """
        object.__setattr__(self, "severity", _clamp(self.severity))

    # ==============================
    # Domain Semantics
    # ==============================

    def is_critical(self, threshold: float = 0.7) -> bool:
        """
        Indica se o erro teve impacto crítico.
        """
        return self.severity >= threshold

    def is_minor(self, threshold: float = 0.3) -> bool:
        """
        Indica se o erro teve baixo impacto.
        """
        return self.severity <= threshold
