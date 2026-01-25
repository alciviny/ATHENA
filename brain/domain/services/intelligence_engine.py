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

    def calculate_roi_per_subject(self, student: "Student", history: List[PerformanceEvent]) -> dict[str, float]:
        """
        # TODO: Esta é uma implementação de placeholder para o cálculo de ROI.
        # A lógica atual usa uma métrica simplificada (média de acurácia por matéria).
        # Uma implementação final deve ser mais sofisticada, considerando por exemplo:
        # - O ganho de 'stability' em relação ao tempo de estudo.
        # - A importância (peso) da matéria para o objetivo do aluno.
        # - A frequência de erros (lapses).

        Placeholder ROI Calculation.
        Calculates a simple score based on accuracy per subject found in history.
        Returns a dictionary of {subject_name: score}
        """
        subject_events: dict[str, list[float]] = {}
        for event in history:
            if event.metric == PerformanceMetric.ACCURACY:
                # O 'topic' do evento de performance é usado como proxy para a matéria
                if event.topic not in subject_events:
                    subject_events[event.topic] = []
                subject_events[event.topic].append(event.value)

        subject_roi: dict[str, float] = {}
        for subject, values in subject_events.items():
            if values:
                # Média simples da acurácia como "ROI score"
                subject_roi[subject] = mean(values)
            else:
                subject_roi[subject] = 0.0
        
        return subject_roi

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

    def analyze_memory_state(self, subject_history: List[PerformanceEvent]) -> dict:
        """
        # TODO: Esta é uma implementação de placeholder para a análise de memória.
        # A lógica atual é supersimplificada e deriva o estado apenas do último evento.
        # Uma implementação final deve:
        # 1. Receber ou buscar o `KnowledgeNode` atual para o tópico.
        # 2. Usar o método `_retrievability` desta classe para calcular a real probabilidade
        #    de retenção com base na estabilidade (S) e no tempo decorrido (t).
        # 3. Retornar a `stability` real do nó em `stability_days`.

        Placeholder Memory State Analysis.
        Derives a simple memory state from the performance history of a single subject.
        """
        if not subject_history:
            return {
                "current_retention": 0.0,
                "stability_days": 0.0,
                "needs_review": True,
            }

        # Assumes history is ordered by date, which is a reasonable expectation
        last_event = subject_history[-1]
        
        current_retention = 0.0
        if last_event.metric == PerformanceMetric.ACCURACY:
            current_retention = last_event.value
        
        # Simple rule for needing review, e.g., if last attempt was below 70%
        needs_review = current_retention < 0.7

        # Cannot calculate real stability without the node itself, so we return a dummy value
        # In a real scenario, this method would likely receive the node or fetch it.
        stability_days = 1.0  # Dummy value

        return {
            "current_retention": current_retention,
            "stability_days": stability_days,
            "needs_review": needs_review,
        }

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        return max(min_v, min(max_v, value))
