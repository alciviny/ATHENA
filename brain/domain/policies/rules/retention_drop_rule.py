from typing import Dict, List, Any

from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.PerformanceEvent import PerformanceMetric
from brain.domain.entities.study_plan import StudyFocusLevel
from brain.domain.policies.adaptive_rule import AdaptiveRule


LOW_STABILITY_THRESHOLD = 10.0


def retention_drop_condition(ctx: Dict[str, Any]) -> bool:
    """
    A regra é aplicável se:
    - Retenção está entre as métricas fracas
    - Existem nós de baixa estabilidade (alto impacto de revisão) no plano
    """
    weak_metrics: List[PerformanceMetric] = ctx.get("weak_metrics", [])
    target_nodes: List[KnowledgeNode] = ctx.get("target_nodes", [])

    if PerformanceMetric.RETENTION not in weak_metrics:
        return False

    return any(node.stability < LOW_STABILITY_THRESHOLD for node in target_nodes)


def retention_drop_action(ctx: Dict[str, Any]) -> None:
    """
    Estratégia:
    - Prioriza apenas nós de baixa estabilidade
    - Força o foco do plano para revisão
    """
    target_nodes: List[KnowledgeNode] = ctx.get("target_nodes", [])

    critical_nodes = [
        node for node in target_nodes if node.stability < LOW_STABILITY_THRESHOLD
    ]

    if not critical_nodes:
        return

    ctx["target_nodes"] = critical_nodes
    ctx["focus_level"] = StudyFocusLevel.REVIEW


RetentionDropRule = AdaptiveRule(
    name="Retention Drop on Low Stability Content",
    description=(
        "Quando há queda de retenção, o plano prioriza a revisão de "
        "tópicos com baixa estabilidade de memória (mais fáceis de esquecer)."
    ),
    condition=retention_drop_condition,
    action=retention_drop_action,
)
