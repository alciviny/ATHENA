import math
from datetime import datetime, timezone, timedelta
from typing import List
from statistics import mean

from brain.domain.entities.performance_event import PerformanceEvent, PerformanceMetric
from brain.domain.entities.knowledge_node import KnowledgeNode, ReviewGrade


class IntelligenceEngine:
    _MIN_STABILITY = 0.5
    _FSRS_WEIGHTS = [
        0.4, 0.6, 2.4, 5.8,
        4.93, 0.94, 0.86, 0.01,
        1.49, 0.14, 0.94, 2.18,
        0.05, 0.34, 1.26, 0.29,
        2.66
    ]

    def analyze_low_accuracy_trend(self, history: List[PerformanceEvent], threshold: float = 0.6) -> bool:
        """Verifica se a acurácia média recente está abaixo do limite aceitável."""
        if not history: return False

        recent_accuracy = [e.value for e in history if e.metric == PerformanceMetric.ACCURACY]
        if not recent_accuracy: return False

        avg_accuracy = sum(recent_accuracy) / len(recent_accuracy)
        return avg_accuracy < threshold

    def should_trigger_priority_boost(
        self, node: KnowledgeNode, history: List[PerformanceEvent], grade: ReviewGrade
    ) -> bool:
        """Regra sênior: Nó difícil + (tendência de erro OU falha crítica) = Boost."""
        is_hard_content = node.difficulty >= 7.0
        has_bad_trend = self.analyze_low_accuracy_trend(history[-5:])
        is_critical_failure = grade == ReviewGrade.AGAIN

        return is_hard_content and (has_bad_trend or is_critical_failure)

    def update_node_state(
        self,
        node: KnowledgeNode,
        grade: ReviewGrade,
        history: List[PerformanceEvent],
    ) -> KnowledgeNode:
        """
        Processa uma revisão e retorna o nó atualizado.
        """
        now = datetime.now(timezone.utc)

        if node.reps == 0:
            self._apply_first_review(node, grade)
        else:
            self._apply_subsequent_review(node, grade, now)

        node.reps += 1
        node.last_reviewed_at = now
        node.next_review_at = now + timedelta(days=node.stability)

        node.validate()
        return node

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

        if grade == ReviewGrade.AGAIN:
            node.lapses += 1
            node.stability = node.stability * self._FSRS_WEIGHTS[4] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[13]
            )
            node.weight *= 1.5
        elif grade == ReviewGrade.HARD:
            node.stability = node.stability * self._FSRS_WEIGHTS[6] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[14]
            )
        elif grade == ReviewGrade.GOOD:
            node.stability = node.stability * self._FSRS_WEIGHTS[8] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[15]
            )
        elif grade == ReviewGrade.EASY:
            node.stability = node.stability * self._FSRS_WEIGHTS[10] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[16]
            )

        node.stability = max(self._MIN_STABILITY, node.stability)

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

    def _elapsed_days(
        self,
        node: KnowledgeNode,
        now: datetime,
    ) -> int:
        if not node.last_reviewed_at:
            return 0
        return max(0, (now - node.last_reviewed_at).days)

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        return max(min_v, min(max_v, value))
