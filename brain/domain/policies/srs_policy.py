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



    _MIN_STABILITY = 0.5

    # FSRS-v4 Default Parameters (example set, usually optimized via ML)
    # These map to w_0, w_1, ..., w_16 in typical FSRS equations.
    # w[0]..w[3] for initial stability
    # w[4]..w[16] for calculating new stability
    _FSRS_WEIGHTS = [
        0.4, 0.6, 2.4, 5.8,      # Initial S (0-3)
        4.93, 0.94, 0.86, 0.01, # Factor for S (4-7)
        1.49, 0.14, 0.94, 2.18, # Factor for S (8-11)
        0.05, 0.34, 1.26, 0.29, # Factor for S (12-15)
        2.66                   # Factor for S (16)
    ]

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
        node.stability = self._FSRS_WEIGHTS[grade.value - 1]
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

        # Apply FSRS stability update
        if grade == ReviewGrade.AGAIN:
            node.lapses += 1
            # FSRS "Again" often leads to a significant drop in stability.
            # Use w[4] for retention sustain, w[13] for decay.
            node.stability = node.stability * self._FSRS_WEIGHTS[4] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[13]
            )
        elif grade == ReviewGrade.HARD:
            # "Hard" increases stability but less than "Good" or "Easy".
            # Use w[6] for stability multiplier, w[14] for decay.
            node.stability = node.stability * self._FSRS_WEIGHTS[6] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[14]
            )
        elif grade == ReviewGrade.GOOD:
            # "Good" provides a solid increase in stability.
            # Use w[8] for stability multiplier, w[15] for decay.
            node.stability = node.stability * self._FSRS_WEIGHTS[8] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[15]
            )
        elif grade == ReviewGrade.EASY:
            # "Easy" provides the largest increase in stability.
            # Use w[10] for stability multiplier, w[16] for decay.
            node.stability = node.stability * self._FSRS_WEIGHTS[10] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[16]
            )

        node.stability = max(self._MIN_STABILITY, node.stability)

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