import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from statistics import mean

from brain.domain.entities.performance_event import PerformanceEvent, PerformanceMetric
from brain.domain.entities.knowledge_node import KnowledgeNode, ReviewGrade
from brain.domain.entities.error_event import ErrorRootCause


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
        Calcula ROI (Return on Investment) avançado por matéria usando múltiplas dimensões.

        Considera:
        - Ganho de estabilidade (FSRS-based)
        - Importância estratégica da matéria para o objetivo do aluno
        - Frequência e severidade de erros
        - Tendência de melhoria ao longo do tempo
        - Eficiência temporal (tempo vs. ganho)
        - Perfil cognitivo do aluno

        Returns: dict[subject_name: roi_score] onde score > 1.0 indica alto ROI
        """
        if not history:
            return {}

        # Agrupar eventos por matéria
        subject_data = self._group_events_by_subject(history)

        # Calcular pesos baseados no objetivo do aluno
        subject_weights = self._calculate_subject_importance_weights(student.goal)

        # Calcular ROI para cada matéria
        roi_scores = {}
        for subject, events in subject_data.items():
            try:
                roi_scores[subject] = self._calculate_single_subject_roi(
                    subject=subject,
                    events=events,
                    subject_weight=subject_weights.get(subject, 0.5),
                    student=student
                )
            except Exception as e:
                # Fallback para média simples em caso de erro
                accuracy_events = [e.value for e in events if e.metric == PerformanceMetric.ACCURACY]
                roi_scores[subject] = mean(accuracy_events) if accuracy_events else 0.5

        return roi_scores

    def _group_events_by_subject(self, history: List[PerformanceEvent]) -> dict[str, List[PerformanceEvent]]:
        """Agrupa eventos por matéria (topic)."""
        subject_data = {}
        for event in history:
            if event.topic:
                if event.topic not in subject_data:
                    subject_data[event.topic] = []
                subject_data[event.topic].append(event)
        return subject_data

    def _calculate_subject_importance_weights(self, student_goal: str) -> dict[str, float]:
        """
        Calcula pesos de importância das matérias baseado no objetivo do aluno.
        Usa conhecimento especialista sobre concursos públicos brasileiros.
        """
        # Pesos baseados em concursos federais (0.0 = irrelevante, 1.0 = crítico)
        base_weights = {
            # Matérias críticas para Polícia Federal
            "Direito Constitucional": 1.0,
            "Direito Administrativo": 0.95,
            "Direito Penal": 0.90,
            "Direito Processual Penal": 0.85,
            "Direito Civil": 0.80,
            "Direito Processual Civil": 0.75,
            "Direito Previdenciário": 0.70,
            "Direito Tributário": 0.65,
            "Direito Financeiro": 0.60,
            "Contabilidade": 0.55,
            "Matemática": 0.50,
            "Português": 0.45,
            "Inglês": 0.40,
            "Informática": 0.35,
            "Raciocínio Lógico": 0.30,
        }

        # Ajustar pesos baseado no concurso específico
        if student_goal == "POLICIA_FEDERAL":
            # PF dá mais ênfase em Direito Penal e Constitucional
            adjustments = {
                "Direito Penal": 1.0,
                "Direito Processual Penal": 0.95,
                "Direito Constitucional": 0.98,
                "Direito Administrativo": 0.92,
            }
        elif student_goal == "INSS":
            # INSS foca em Previdenciário e Administrativo
            adjustments = {
                "Direito Previdenciário": 1.0,
                "Direito Administrativo": 0.95,
                "Direito Constitucional": 0.90,
                "Direito Civil": 0.80,
            }
        elif student_goal == "RECEITA_FEDERAL":
            # Receita foca em Tributário e Administrativo
            adjustments = {
                "Direito Tributário": 1.0,
                "Direito Administrativo": 0.95,
                "Direito Constitucional": 0.90,
                "Contabilidade": 0.85,
            }
        else:
            adjustments = {}

        # Aplicar ajustes
        weights = base_weights.copy()
        for subject, weight in adjustments.items():
            weights[subject] = weight

        return weights

    def _calculate_single_subject_roi(self, subject: str, events: List[PerformanceEvent],
                                    subject_weight: float, student: "Student") -> float:
        """
        Calcula ROI para uma matéria específica usando múltiplas métricas.
        """
        if not events:
            return 0.0

        # 1. Métrica de Estabilidade (FSRS-inspired)
        stability_score = self._calculate_stability_score(events)

        # 2. Métrica de Melhoria/Tendência
        improvement_score = self._calculate_improvement_trend(events)

        # 3. Métrica de Eficiência de Erros
        error_efficiency = self._calculate_error_efficiency(events)

        # 4. Métrica de Consistência
        consistency_score = self._calculate_consistency_score(events)

        # 5. Fator de Perfil Cognitivo
        cognitive_factor = self._calculate_cognitive_factor(student, events)

        # 6. Fator Temporal (recência)
        recency_factor = self._calculate_recency_factor(events)

        # Combinação ponderada das métricas
        weights = {
            'stability': 0.25,
            'improvement': 0.20,
            'error_efficiency': 0.20,
            'consistency': 0.15,
            'cognitive': 0.10,
            'recency': 0.10
        }

        raw_roi = (
            stability_score * weights['stability'] +
            improvement_score * weights['improvement'] +
            error_efficiency * weights['error_efficiency'] +
            consistency_score * weights['consistency'] +
            cognitive_factor * weights['cognitive'] +
            recency_factor * weights['recency']
        )

        # Aplicar peso estratégico da matéria
        strategic_roi = raw_roi * (0.5 + subject_weight * 0.5)  # 0.5-1.0 range

        # Normalizar para escala 0-2 (2 = excelente ROI)
        return min(max(strategic_roi, 0.0), 2.0)

    def _calculate_stability_score(self, events: List[PerformanceEvent]) -> float:
        """Calcula ganho de estabilidade baseado em FSRS principles."""
        accuracy_events = [e for e in events if e.metric == PerformanceMetric.ACCURACY]
        if not accuracy_events:
            return 0.5

        # Usar FSRS-inspired formula: stability aumenta com acurácia consistente
        recent_accuracy = sorted([e.value for e in accuracy_events[-10:]], reverse=True)
        if len(recent_accuracy) < 3:
            return mean(recent_accuracy)

        # Penalizar variabilidade alta
        mean_acc = mean(recent_accuracy)
        variance = sum((x - mean_acc) ** 2 for x in recent_accuracy) / len(recent_accuracy)
        stability_penalty = min(variance * 2, 0.5)  # Máximo 50% penalty

        return max(mean_acc - stability_penalty, 0.0)

    def _calculate_improvement_trend(self, events: List[PerformanceEvent]) -> float:
        """Calcula tendência de melhoria ao longo do tempo."""
        accuracy_events = sorted(
            [e for e in events if e.metric == PerformanceMetric.ACCURACY],
            key=lambda e: e.occurred_at
        )

        if len(accuracy_events) < 5:
            return 0.5

        # Calcular slope da regressão linear simples
        n = len(accuracy_events)
        x = list(range(n))  # índices temporais
        y = [e.value for e in accuracy_events]

        # Regressão linear: y = mx + b
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi ** 2 for xi in x)

        if n * sum_xx - sum_x ** 2 == 0:
            return 0.5

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)

        # Converter slope para score 0-1 (slope positivo = melhoria)
        return min(max(slope * 10 + 0.5, 0.0), 1.0)  # slope * 10 para amplificar

    def _calculate_error_efficiency(self, events: List[PerformanceEvent]) -> float:
        """Calcula eficiência no tratamento de erros."""
        error_events = [e for e in events if e.metric == PerformanceMetric.ERROR_RATE]
        if not error_events:
            return 0.8  # Assumir bom se não há dados de erro

        recent_errors = [e.value for e in error_events[-5:]]
        avg_error_rate = mean(recent_errors)

        # Penalizar taxa de erro alta, mas recompensar redução consistente
        if len(recent_errors) >= 3:
            error_trend = recent_errors[-1] - recent_errors[0]
            trend_bonus = max(-error_trend * 2, -0.3)  # Bônus por redução de erro
        else:
            trend_bonus = 0

        return max(1.0 - avg_error_rate + trend_bonus, 0.0)

    def _calculate_consistency_score(self, events: List[PerformanceEvent]) -> float:
        """Calcula consistência de performance."""
        accuracy_events = [e.value for e in events if e.metric == PerformanceMetric.ACCURACY]
        if len(accuracy_events) < 3:
            return 0.5

        # Medir variabilidade (desvio padrão normalizado)
        mean_acc = mean(accuracy_events)
        if mean_acc == 0:
            return 0.0

        variance = sum((x - mean_acc) ** 2 for x in accuracy_events) / len(accuracy_events)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_acc  # Coeficiente de variação

        # Score baseado em consistência (CV baixo = alto score)
        return max(1.0 - cv, 0.0)

    def _calculate_cognitive_factor(self, student: "Student", events: List[PerformanceEvent]) -> float:
        """Calcula fator baseado no perfil cognitivo do aluno."""
        # Este método assume que o perfil cognitivo está disponível
        # Em implementação real, seria necessário buscar o perfil do repositório
        try:
            # Placeholder - em produção, buscar do repositório
            cognitive_profile = getattr(student, 'cognitive_profile', None)
            if not cognitive_profile:
                return 0.5

            # Usar fatores cognitivos para ajustar ROI
            retention_factor = cognitive_profile.retention_rate
            speed_factor = cognitive_profile.learning_speed
            stress_factor = 1.0 - cognitive_profile.stress_sensitivity  # Inverter (menos sensível = melhor)

            return (retention_factor * 0.4 + speed_factor * 0.4 + stress_factor * 0.2)

        except AttributeError:
            return 0.5

    def _calculate_recency_factor(self, events: List[PerformanceEvent]) -> float:
        """Calcula fator de recência (performance recente tem mais peso)."""
        if not events:
            return 0.5

        # Encontrar evento mais recente
        most_recent = max(events, key=lambda e: e.occurred_at)
        days_since_last = (datetime.now(timezone.utc) - most_recent.occurred_at).days

        # Decaimento exponencial: performance muito antiga perde relevância
        if days_since_last > 30:
            return 0.3  # Muito antigo
        elif days_since_last > 7:
            return 0.7  # Recente
        else:
            return 1.0  # Muito recente

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
        root_cause: Optional[ErrorRootCause] = None,
    ) -> KnowledgeNode:
        """
        Processa uma revisão e retorna o nó atualizado.
        """
        now = datetime.now(timezone.utc)

        if node.reps == 0:
            self._apply_first_review(node, grade)
        else:
            self._apply_subsequent_review(node, grade, now, root_cause)

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
        if grade == ReviewGrade.AGAIN:
            node.weight *= 1.5
            
        node.stability = self._FSRS_WEIGHTS[grade.value - 1]
        node.difficulty = self._initial_difficulty(grade)

    def _apply_subsequent_review(
        self,
        node: KnowledgeNode,
        grade: ReviewGrade,
        now: datetime,
        root_cause: Optional[ErrorRootCause] = None,
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

        penalty_factor = 1.0
        if root_cause == ErrorRootCause.ATTENTION:
            penalty_factor = 0.5 # Penalidade menor para desatenção
        elif root_cause == ErrorRootCause.LACK_OF_BASE:
            node.weight *= 2.0 # Aumenta o peso agressivamente

        if grade == ReviewGrade.AGAIN:
            node.lapses += 1
            node.stability = node.stability * self._FSRS_WEIGHTS[4] * (
                (elapsed_days / node.stability) ** self._FSRS_WEIGHTS[13]
            ) * penalty_factor
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

    def analyze_memory_state(self, subject_history: List[PerformanceEvent], node: KnowledgeNode = None) -> dict:
        """
        Analisa o estado de memória para um tópico.
        Se um KnowledgeNode for fornecido, usa a curva de esquecimento real: R = e^(-t/S).
        Caso contrário, faz estimativa baseada no último evento de performance.
        """
        # Se temos o nó, usar a fórmula real de retenção
        if node and node.last_reviewed_at and node.stability > 0:
            now = datetime.now(timezone.utc)
            last_review = node.last_reviewed_at
            if last_review.tzinfo is None:
                last_review = last_review.replace(tzinfo=timezone.utc)
            elapsed_days = max(0, (now - last_review).total_seconds() / 86400.0)
            
            current_retention = self._retrievability(int(elapsed_days), node.stability)
            stability_days = node.stability
            needs_review = current_retention < 0.7

            return {
                "current_retention": round(current_retention, 3),
                "stability_days": round(stability_days, 1),
                "needs_review": needs_review,
            }

        # Fallback: estimativa pelo histórico de eventos
        if not subject_history:
            return {
                "current_retention": 0.0,
                "stability_days": 0.0,
                "needs_review": True,
            }

        last_event = subject_history[-1]
        
        current_retention = 0.0
        if last_event.metric == PerformanceMetric.ACCURACY:
            current_retention = last_event.value
        elif last_event.metric == PerformanceMetric.SCORE:
            current_retention = last_event.value
        
        needs_review = current_retention < 0.7
        stability_days = 1.0 if needs_review else 3.0

        return {
            "current_retention": round(current_retention, 3),
            "stability_days": stability_days,
            "needs_review": needs_review,
        }

    @staticmethod
    def _clamp(value: float, min_v: float, max_v: float) -> float:
        return max(min_v, min(max_v, value))
