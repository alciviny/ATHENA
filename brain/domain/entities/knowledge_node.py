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
    """
    Representa uma unidade mínima de conhecimento com estado mnemônico.
    Inspirado no modelo FSRS.
    """

    id: UUID
    title: str

    # --- Estado de Memória ---
    stability: float = 0.0      # Dias até R ≈ 0.9
    difficulty: float = 5.0     # [1.0, 10.0]
    reps: int = 0               # Total de revisões
    lapses: int = 0             # Quantidade de falhas completas
    last_review: Optional[datetime] = None
    next_review: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # -------------------------
    # Consultas de Domínio
    # -------------------------

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """
        Verifica se o nó está elegível para revisão.
        """
        now = now or datetime.now(timezone.utc)
        return now >= self.next_review

    def retention_interval(self) -> timedelta:
        """
        Intervalo atual de retenção estimado.
        """
        return timedelta(days=max(self.stability, 0))

    def validate(self) -> None:
        """
        Garante invariantes do domínio.
        """
        if not 1.0 <= self.difficulty <= 10.0:
            raise ValueError("Difficulty must be between 1.0 and 10.0")

        if self.stability < 0:
            raise ValueError("Stability cannot be negative")