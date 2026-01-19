from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta

from brain.domain.entities.knowledge_node import KnowledgeNode, ReviewGrade


class SRSPolicy:
    """
    Motor de Spaced Repetition inspirado em FSRS.

    A política é determinística, pura e orientada a carga cognitiva real.
    """

    # -------------------------
    # Constantes de Modelo
    # -------------------------

    _INITIAL_STABILITY = {
        ReviewGrade.AGAIN: 0.5,
        ReviewGrade.HARD: 1.5,
        ReviewGrade.GOOD: 3.5,
        ReviewGrade.EASY: 7.0,
    }

    _STABILITY_GROWTH = 1.4
    _MIN_STABILITY = 0.5

    # -------------------------
    # API Pública
    # -------------------------

    def process_review(
        self,
        node: KnowledgeNode,
        grade: ReviewGrade,
        now: datetime | None = None,
    ) -> KnowledgeNode:
        """
        Processa uma revisão e retorna o nó atualizado.
        """
        now = now or datetime.now(timezone.utc)

        if node.reps == 0:
            self._apply_first_review(node, grade)
        else:
            self._apply_subsequent_review(node, grade, now)

        node.reps += 1
        node.last_review = now
        node.next_review = now + timedelta(days=node.stability)

        node.validate()
        return node

    # -------------------------
    # Regras de Negócio
    # -------------------------

    def _apply_first_review(
        self,
        node: KnowledgeNode,
        grade: ReviewGrade,
    ) -> None:
        """
        Inicialização mnemônica do conhecimento.
        """
        node.stability = self._INITIAL_STABILITY[grade]
        node.difficulty = self._initial_difficulty(grade)

    def _apply_subsequent_review(
        self,
        node: KnowledgeNode,
        grade: ReviewGrade,
        now: datetime,
    ) -> None:
        """
        Atualização após revisões subsequentes.
        """
        elapsed_days = self._elapsed_days(node, now)
        retrievability = self._retrievability(
            elapsed_days,
            node.stability,
        )

        node.difficulty = self._update_difficulty(
            node.difficulty,
            grade,
        )

        if grade is ReviewGrade.AGAIN:
            node.lapses += 1
            node.stability = max(
                self._MIN_STABILITY,
                node.stability * 0.2,
            )
            return

        growth_factor = self._stability_growth_factor(grade)
        node.stability *= growth_factor * (1 + (1 - retrievability))

    # -------------------------
    # Matemática
    # -------------------------

    def _retrievability(
        self,
        elapsed_days: int,
        stability: float,
    ) -> float:
        """
        Probabilidade de recuperação (R).
        """
        if stability <= 0:
            return 0.0

        return math.exp(
            math.log(0.9) * elapsed_days / stability
        )

    def _stability_growth_factor(self, grade: ReviewGrade) -> float:
        """
        Crescimento não-linear baseado na qualidade da recuperação.
        """
        return 1 + (self._STABILITY_GROWTH * (grade.value - 2))

    # -------------------------
    # Dificuldade
    # -------------------------

    def _initial_difficulty(self, grade: ReviewGrade) -> float:
        """
        Dificuldade inicial inversamente proporcional à nota.
        """
        return self._clamp(
            10.0 - (grade.value * 2.0),
            1.0,
            10.0,
        )

    def _update_difficulty(
        self,
        current: float,
        grade: ReviewGrade,
    ) -> float:
        """
        Ajuste incremental da dificuldade percebida.
        """
        delta = {
            ReviewGrade.AGAIN: 1.5,
            ReviewGrade.HARD: 0.5,
            ReviewGrade.GOOD: 0.0,
            ReviewGrade.EASY: -1.0,
        }[grade]

        return self._clamp(
            current + delta,
            1.0,
            10.0,
        )

    # -------------------------
    # Utilitários
    # -------------------------

    def _elapsed_days(
        self,
        node: KnowledgeNode,
        now: datetime,
    ) -> int:
        if not node.last_review:
            return 0
        return max(0, (now - node.last_review).days)

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        return max(min_v, min(max_v, value))