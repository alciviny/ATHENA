from typing import Dict, List, Any

from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.PerformanceEvent import PerformanceMetric
from brain.domain.entities.StudyPlan import StudyFocusLevel
from brain.domain.policies.adaptive_rule import AdaptiveRule


def retention_drop_condition(ctx: Dict[str, Any]) -> bool:
    """
    A regra é aplicável se:
    - Retenção está entre as métricas fracas
    - Existem nós de alto impacto no plano atual
    """
    weak_metrics: List[PerformanceMetric] = ctx.get("weak_metrics", [])
    target_nodes: List[KnowledgeNode] = ctx.get("target_nodes", [])

    if PerformanceMetric.RETENTION not in weak_metrics:
        return False

    return any(node.is_high_impact() for node in target_nodes)


def retention_drop_action(ctx: Dict[str, Any]) -> None:
    """
    Estratégia:
    - Prioriza apenas nós de alto impacto
    - Força o foco do plano para revisão
    """
    target_nodes: List[KnowledgeNode] = ctx.get("target_nodes", [])

    critical_nodes = [
        node for node in target_nodes if node.is_high_impact()
    ]

    if not critical_nodes:
        return

    ctx["target_nodes"] = critical_nodes
    ctx["focus_level"] = StudyFocusLevel.REVIEW


RetentionDropRule = AdaptiveRule(
    name="Retention Drop on High Impact Content",
    description=(
        "Quando há queda de retenção em conteúdos de alto impacto, "
        "o plano prioriza revisão desses tópicos críticos."
    ),
    condition=retention_drop_condition,
    action=retention_drop_action,
)
