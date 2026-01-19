from typing import Dict, List, Any

from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.policies.adaptive_rule import AdaptiveRule


MAX_NODES = 6


def overload_prevention_condition(ctx: Dict[str, Any]) -> bool:
    """
    A regra é aplicável se o plano exceder o número máximo de nós.
    """
    target_nodes: List[KnowledgeNode] = ctx.get("target_nodes", [])
    return len(target_nodes) > MAX_NODES


def overload_prevention_action(ctx: Dict[str, Any]) -> None:
    """
    Estratégia:
    - Limita o plano ao número máximo de nós
    - Prioriza conteúdos de maior impacto na prova
    """
    target_nodes: List[KnowledgeNode] = ctx.get("target_nodes", [])

    if not target_nodes:
        return

    sorted_nodes = sorted(
        target_nodes,
        key=lambda node: node.difficulty,
        reverse=True,
    )

    ctx["target_nodes"] = sorted_nodes[:MAX_NODES]


OverloadPreventionRule = AdaptiveRule(
    name="Overload Prevention",
    description=(
        "Evita planos excessivamente longos limitando o número de tópicos "
        "e priorizando aqueles com maior dificuldade."
    ),
    condition=overload_prevention_condition,
    action=overload_prevention_action,
)

