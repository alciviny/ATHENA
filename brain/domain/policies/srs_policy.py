from __future__ import annotations

from datetime import datetime

from brain.domain.entities.knowledge_node import KnowledgeNode, ReviewGrade


class SRSPolicy:
    """
    DEPRECATED: A lógica do Spaced Repetition System foi movida para
    a classe IntelligenceEngine.
    Esta classe é mantida para fins de compatibilidade, mas não
    deve ser usada para novos desenvolvimentos.
    """

    def process_review(
        self,
        node: KnowledgeNode,
        grade: ReviewGrade,
        now: datetime | None = None,
    ) -> KnowledgeNode:
        """
        Este método está obsoleto. A lógica de revisão agora reside em
        IntelligenceEngine.update_node_state.
        """
        # A lógica foi movida. Apenas retorna o nó sem modificação
        # para evitar quebrar chamadas existentes.
        return node