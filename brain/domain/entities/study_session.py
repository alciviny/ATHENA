from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID


@dataclass
class StudySession:
    """
    Representa uma sessão de estudo do aluno.

    É uma entidade fundamental para gerar eventos de performance,
    atualizar o perfil cognitivo e alimentar o planner adaptativo.
    """
    id: UUID
    student_id: UUID

    started_at: datetime
    ended_at: datetime

    # Conhecimentos estudados durante a sessão
    studied_nodes: List[UUID] = field(default_factory=list)

    # Métricas de desempenho
    questions_answered: int = 0
    correct_answers: int = 0

    def __post_init__(self) -> None:
        """
        Valida consistência temporal e métricas básicas.
        """
        if self.ended_at <= self.started_at:
            raise ValueError("ended_at must be after started_at")

        if self.questions_answered < 0 or self.correct_answers < 0:
            raise ValueError("Question counts cannot be negative")

        if self.correct_answers > self.questions_answered:
            raise ValueError("correct_answers cannot exceed questions_answered")

    # ==============================
    # Time Metrics
    # ==============================

    def duration_minutes(self) -> float:
        """
        Retorna a duração total da sessão em minutos.
        """
        return (self.ended_at - self.started_at).total_seconds() / 60.0

    def duration_hours(self) -> float:
        """
        Retorna a duração total da sessão em horas.
        """
        return self.duration_minutes() / 60.0

    # ==============================
    # Performance Metrics
    # ==============================

    def accuracy(self) -> float:
        """
        Taxa de acerto da sessão (0.0 - 1.0).
        """
        if self.questions_answered == 0:
            return 0.0
        return self.correct_answers / self.questions_answered

    def effectiveness(self) -> float:
        """
        Métrica composta simples:
        precisão ponderada pelo tempo de estudo.
        """
        if self.duration_minutes() == 0:
            return 0.0
        return self.accuracy() * self.duration_minutes()

    # ==============================
    # Domain Semantics
    # ==============================

    def is_productive(self, min_accuracy: float = 0.6) -> bool:
        """
        Indica se a sessão foi produtiva.
        """
        return self.accuracy() >= min_accuracy

    def studied_multiple_topics(self) -> bool:
        """
        Indica se mais de um nó de conhecimento foi estudado.
        """
        return len(self.studied_nodes) > 1
