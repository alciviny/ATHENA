from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import IntEnum
from uuid import UUID
from typing import Optional


class ReviewGrade(IntEnum):
    """
    Avaliação cognitiva da recuperação da memória.
    Os valores são intencionais e fazem parte da matemática.
    """
    AGAIN = 1   # Falha total de recuperação
    HARD = 2    # Recuperação com alto esforço
    GOOD = 3    # Recuperação normal
    EASY = 4    # Recuperação imediato


@dataclass
class KnowledgeNode:
    id: UUID
    title: str
    stability: float = 0.0
    difficulty: float = 5.0
    reps: int = 0
    lapses: int = 0
    weight: float = 1.0  # Fator de prioridade no algoritmo de seleção
    last_review: Optional[datetime] = None
    next_review: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def apply_penalty(self, factor: float = 1.5):
        """Aumenta a prioridade do nó quando detectada fraqueza cognitiva."""
        self.weight *= factor
        # Força uma revisão mais próxima se a dificuldade for alta
        if self.difficulty > 7.0:
            self.stability *= 0.8 

    def record_success(self):
        """Normaliza o peso conforme o aluno domina o assunto."""
        self.weight = max(1.0, self.weight * 0.9)

    def validate(self) -> None:
        if not 1.0 <= self.difficulty <= 10.0:
            raise ValueError("Difficulty must be between 1.0 and 10.0")