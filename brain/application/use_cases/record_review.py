from uuid import UUID
from brain.domain.services.semantic_propagator import SemanticPropagator
from brain.domain.entities.knowledge_node import ReviewGrade
from brain.application.ports.repositories import (
    KnowledgeRepository,
    PerformanceRepository,
)
from brain.domain.services.intelligence_engine import IntelligenceEngine


class RecordReviewUseCase:
    def __init__(
        self,
        node_repo: KnowledgeRepository,
        perf_repo: PerformanceRepository,
        engine: IntelligenceEngine,
        propagator: SemanticPropagator,
    ) -> None:
        self._node_repo = node_repo
        self._perf_repo = perf_repo
        self._engine = engine
        self._propagator = propagator

    async def execute(
        self,
        student_id: UUID,
        node_id: UUID,
        grade: ReviewGrade,
    ):
        # 1. Carregar estado
        node = self._node_repo.get_by_id(node_id)
        history = self._perf_repo.get_history_for_student(student_id)

        # 2. Atualizar performance básica
        updated_node = self._engine.update_node_state(
            node=node,
            grade=grade,
            history=history,
        )

        # 3. Decisão cognitiva
        if self._engine.should_trigger_priority_boost(updated_node, history, grade):
            updated_node.apply_penalty(factor=2.0)

            # Propagação semântica (efeito colateral consciente)
            await self._propagator.propagate_boost(node_id)

        elif grade >= ReviewGrade.GOOD:
            updated_node.record_success()

        # 4. Persistência
        self._node_repo.update(updated_node)
        return updated_node
