from typing import Dict, List, Any

from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.PerformanceEvent import PerformanceMetric
from brain.domain.entities.study_plan import StudyFocusLevel
from brain.domain.policies.adaptive_rule import AdaptiveRule


HIGH_DIFFICULTY_THRESHOLD = 7.0


def low_accuracy_high_difficulty_condition(ctx: Dict[str, Any]) -> bool:
    """
    A regra é aplicável se:
    - Acurácia está entre as métricas fracas
    - Existem nós de alta dificuldade no plano atual
    """
    weak_metrics: List[PerformanceMetric] = ctx.get("weak_metrics", [])
    target_nodes: List[KnowledgeNode] = ctx.get("target_nodes", [])

    if PerformanceMetric.ACCURACY not in weak_metrics:
        return False

    return any(node.difficulty >= HIGH_DIFFICULTY_THRESHOLD for node in target_nodes)


def low_accuracy_high_difficulty_action(ctx: Dict[str, Any]) -> None:
    """
    Estratégia:
    - Reduz o plano apenas aos nós críticos
    - Força o foco para revisão
    """
    target_nodes: List[KnowledgeNode] = ctx.get("target_nodes", [])

    critical_nodes = [
        node for node in target_nodes if node.difficulty >= HIGH_DIFFICULTY_THRESHOLD
    ]

    if not critical_nodes:
        return

    ctx["target_nodes"] = critical_nodes
    ctx["focus_level"] = StudyFocusLevel.REVIEW


LowAccuracyHighDifficultyRule = AdaptiveRule(
    name="Low Accuracy on High Difficulty Content",
    description=(
        "Quando a acurácia está baixa em conteúdos difíceis, "
        "o plano é reduzido para focar apenas nos tópicos críticos "
        "e o foco é alterado para revisão."
    ),
    condition=low_accuracy_high_difficulty_condition,
    action=low_accuracy_high_difficulty_action,
)
