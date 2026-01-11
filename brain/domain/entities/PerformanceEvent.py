from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from enum import Enum


class PerformanceEventType(str, Enum):
    """
    Tipo de evento de performance.
    """
    STUDY_SESSION = "study_session"
    MOCK_EXAM = "mock_exam"
    QUIZ = "quiz"


class PerformanceMetric(str, Enum):
    """
    Métricas observadas no desempenho do aluno.
    """
    ACCURACY = "accuracy"
    TIME_PER_QUESTION = "time_per_question"
    RETENTION = "retention"
    SCORE = "score"


@dataclass(frozen=True)
class PerformanceEvent:
    """
    Evento que registra uma métrica observada e sua comparação com baseline.

    Esses eventos alimentam regras adaptativas e ajustes no perfil cognitivo.
    """
    id: UUID
    student_id: UUID

    event_type: PerformanceEventType
    occurred_at: datetime

    metric: PerformanceMetric
    value: float
    baseline: float

    # ==============================
    # Domain Semantics
    # ==============================

    def deviation(self) -> float:
        """
        Quanto o desempenho desviou do esperado.
        """
        return self.value - self.baseline

    def is_negative(self) -> bool:
        """
        Indica se houve queda de performance.
        """
        return self.deviation() < 0

    def is_positive(self) -> bool:
        """
        Indica se houve melhora de performance.
        """
        return self.deviation() > 0

    def relative_deviation(self) -> float:
        """
        Desvio relativo em relação ao baseline.
        """
        if self.baseline == 0:
            return 0.0
        return self.deviation() / self.baseline
