from typing import List
from brain.domain.policies.adaptive_rule import AdaptiveRule
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.performance_event import PerformanceEvent, PerformanceMetric, PerformanceEventType


class StressTestRule(AdaptiveRule):
    """
    Regra adaptativa para testes de stress/exame.

    Se o tempo médio de resposta nas últimas 3 questões do simulador for muito baixo
    (respostas muito rápidas), considera-se que o aluno está chutando ou reagindo
    sem processamento profundo — aumentamos a dificuldade sugerida.
    """
    def apply(self, cognitive_profile: CognitiveProfile, performance_events: List[PerformanceEvent]) -> None:
        # Filtrar apenas eventos relevantes de tipo TIME_PER_QUESTION em quizzes/exames
        recent_times = [
            e for e in reversed(performance_events)
            if getattr(e, 'metric', None) == PerformanceMetric.TIME_PER_QUESTION
            and getattr(e, 'event_type', None) in (PerformanceEventType.MOCK_EXAM, PerformanceEventType.QUIZ)
        ]

        if not recent_times:
            return

        # Pegar até as últimas 3
        sample = recent_times[:3]
        avg_time = sum((getattr(e, 'value', 0.0) for e in sample)) / len(sample)

        # Usar baseline médio dos eventos; quando ausente, assumir 30s
        baselines = [getattr(e, 'baseline', 30.0) or 30.0 for e in sample]
        avg_baseline = sum(baselines) / len(baselines)

        # Se respostas muito rápidas (< 50% do baseline), marcar para aumentar dificuldade
        if avg_time < (0.5 * avg_baseline):
            # Registrar um sinal no perfil para que orquestradores (use cases / services)
            # possam ajustar a seleção (ex: aumentar dificuldade dos próximos itens)
            cognitive_profile.register_error_event('stress_test_increase_difficulty', 1.0)
            # Ajuste pequeno na sensibilidade ao stress para monitoramento contínuo
            cognitive_profile.update_stress_sensitivity(0.05)
