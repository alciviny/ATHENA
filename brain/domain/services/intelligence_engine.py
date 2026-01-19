import math
from datetime import datetime, timezone
from typing import Dict, List
from statistics import mean

from brain.domain.entities.student import Student
from brain.domain.entities.performance_event import PerformanceEvent


class IntelligenceEngine:
    """
    Motor de Inteligência Unificado.

    Responsabilidades:
    - Planejamento Cognitivo (ROI de Estudo)
    - Agendamento de Revisão (Estabilidade de Memória)

    Observação:
    Embora coexistam aqui, são motores conceitualmente distintos.
    Esta unificação é intencional nesta fase do produto.
    """

    # -----------------------------
    # Configurações Globais (TUNÁVEIS)
    # -----------------------------

    MIN_EVENTS_FOR_TREND = 10
    MAX_TREND_WINDOW = 20

    INITIAL_STABILITY_DAYS = 2.0
    MIN_STABILITY_DAYS = 0.5
    MAX_STABILITY_DAYS = 120.0  # evita explosão irreal de intervalos

    BASE_RETENTION_TARGET = 0.90
    LN_RETENTION_TARGET = math.log(BASE_RETENTION_TARGET)  # ≈ -0.10536

    # -----------------------------
    # ROI – Planejamento de Estudo
    # -----------------------------

    def calculate_roi_per_subject(
        self,
        student: Student,
        history: List[PerformanceEvent]
    ) -> Dict[str, float]:
        """
        ROI = (Delta Precisão / Horas Estudadas) * Peso da Matéria
        """

        roi_report: Dict[str, float] = {}

        for subject in student.subjects:
            accuracy_gain = self._get_accuracy_trend(history, subject.id)
            hours_spent = self._get_hours_spent(student, subject.id)

            if hours_spent <= 0:
                roi_report[str(subject.id)] = 0.0
                continue

            roi_score = (accuracy_gain / hours_spent) * subject.weight
            roi_report[str(subject.id)] = round(roi_score, 4)

        return roi_report

    def _get_accuracy_trend(
        self,
        history: List[PerformanceEvent],
        subject_id
    ) -> float:
        """
        Mede a evolução da precisão comparando o início e o fim da série.
        """

        events = [e for e in history if e.subject_id == subject_id]

        if len(events) < self.MIN_EVENTS_FOR_TREND:
            return 0.0

        events.sort(key=lambda e: e.timestamp)
        window = min(self.MAX_TREND_WINDOW, len(events) // 2)

        first_accuracy = mean(e.success for e in events[:window])
        last_accuracy = mean(e.success for e in events[-window:])

        return last_accuracy - first_accuracy

    def _get_hours_spent(self, student: Student, subject_id) -> float:
        """
        Soma o tempo total de estudo por matéria (em horas).
        """

        total_minutes = sum(
            session.duration_minutes
            for session in student.study_sessions
            if session.subject_id == subject_id
        )

        return total_minutes / 60.0

    # -----------------------------
    # MEMÓRIA – Estabilidade e Retenção
    # -----------------------------

    def calculate_retention_probability(
        self,
        last_review: datetime,
        stability: float
    ) -> float:
        """
        R = exp( ln(0.9) * t / S )
        """

        now = datetime.now(timezone.utc)
        elapsed_days = (now - last_review).total_seconds() / 86400.0

        if elapsed_days <= 0 or stability <= 0:
            return 1.0

        retention = math.exp(
            self.LN_RETENTION_TARGET * elapsed_days / stability
        )

        return round(retention, 4)

    def update_memory_stability(
        self,
        current_stability: float,
        success: bool,
        retention_at_test: float
    ) -> float:
        """
        Atualiza a estabilidade baseada no princípio de Desirable Difficulty.

        - Acerto próximo do esquecimento → grande ganho
        - Erro cedo → punição forte
        - Erro tardio → punição moderada
        """

        if success:
            gain_factor = 1 + (2.0 * (1 - retention_at_test))
            new_stability = current_stability * gain_factor * 1.5
        else:
            # Penalização proporcional ao quanto ainda lembrava
            penalty_factor = 0.3 + (0.4 * retention_at_test)
            new_stability = current_stability * penalty_factor

        return round(
            min(
                max(new_stability, self.MIN_STABILITY_DAYS),
                self.MAX_STABILITY_DAYS
            ),
            2
        )

    def analyze_memory_state(
        self,
        subject_history: List[PerformanceEvent]
    ) -> Dict:
        """
        Processa o histórico de uma matéria e projeta o estado atual da memória.
        """

        if not subject_history:
            return {
                "current_retention": 1.0,
                "stability_days": self.INITIAL_STABILITY_DAYS,
                "last_review": None,
                "needs_review": False,
            }

        subject_history.sort(key=lambda e: e.timestamp)

        stability = self.INITIAL_STABILITY_DAYS
        last_date = subject_history[0].timestamp

        for event in subject_history:
            retention_at_test = self.calculate_retention_probability(
                last_date,
                stability
            )
            stability = self.update_memory_stability(
                stability,
                event.success,
                retention_at_test
            )
            last_date = event.timestamp

        current_retention = self.calculate_retention_probability(
            last_date,
            stability
        )

        # Threshold adaptativo: quanto maior a estabilidade, mais exigente
        review_threshold = 0.9 if stability > 20 else 0.8

        return {
            "current_retention": current_retention,
            "stability_days": stability,
            "last_review": last_date,
            "needs_review": current_retention < review_threshold,
        }
