from brain.domain.policies.adaptive_rule import AdaptiveRule
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.performance_event import PerformanceEvent
from typing import List

class OverloadPreventionRule(AdaptiveRule):
    """
    Detecta exaustão cognitiva baseada em métricas de latência e precisão.
    Quando detectada fadiga, altera o focus_level para "RECOVERY".
    """
    def apply(self, cognitive_profile: CognitiveProfile, performance_events: List[PerformanceEvent]) -> None:
        if len(performance_events) < 8:
            return

        recent = performance_events[-8:]
        accuracy = sum(1 for e in recent if e.success) / 8
        avg_response_time = sum(e.response_time_seconds for e in recent) / 8

        # Se o tempo de reação subiu 50% acima da média ou precisão caiu muito
        if avg_response_time > 30.0 and accuracy < 0.5:
            cognitive_profile.focus_level = "RECOVERY"


# Número máximo de nós permitido quando a prevenção de sobrecarga é aplicada
MAX_NODES = 5
