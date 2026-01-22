import math
from datetime import datetime, timezone
from typing import List
from statistics import mean

from brain.domain.entities.performance_event import PerformanceEvent, PerformanceMetric
from brain.domain.entities.knowledge_node import KnowledgeNode


class IntelligenceEngine:
    def analyze_low_accuracy_trend(self, history: List[PerformanceEvent], threshold: float = 0.6) -> bool:
        """Verifica se a acurácia média recente está abaixo do limite aceitável."""
        if not history: return False
        
        recent_accuracy = [e.value for e in history if e.metric == PerformanceMetric.ACCURACY]
        if not recent_accuracy: return False
        
        avg_accuracy = sum(recent_accuracy) / len(recent_accuracy)
        return avg_accuracy < threshold

    def should_trigger_priority_boost(self, node: KnowledgeNode, history: List[PerformanceEvent]) -> bool:
        """Regra sênior: Nó difícil + tendência de erro = Boost de prioridade."""
        is_hard_content = node.difficulty >= 7.0
        has_bad_trend = self.analyze_low_accuracy_trend(history[-5:]) # Últimos 5 eventos
        
        return is_hard_content and has_bad_trend
