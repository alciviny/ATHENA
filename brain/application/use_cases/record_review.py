from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional

from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository
from brain.domain.entities.performance_event import (
    PerformanceEvent,
    PerformanceEventType,
    PerformanceMetric,
)
from brain.domain.entities.knowledge_node import KnowledgeNode, ReviewGrade
from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.domain.services.semantic_propagator import SemanticPropagator
from brain.domain.entities.error_event import ErrorRootCause


class RecordReviewUseCase:
    """
    Caso de uso responsável por registrar uma revisão.
    Suporta tanto 'Inferência Cognitiva' (baseada em tempo) quanto 'Feedback Explícito' (botões).
    """

    FAST_RESPONSE_THRESHOLD = 15.0
    SLOW_RESPONSE_THRESHOLD = 60.0

    def __init__(
        self,
        performance_repo: PerformanceRepository,
        node_repo: KnowledgeRepository,
        intelligence_engine: IntelligenceEngine,
        semantic_propagator: SemanticPropagator,
    ):
        self.performance_repo = performance_repo
        self.node_repo = node_repo
        self.intelligence_engine = intelligence_engine
        self.semantic_propagator = semantic_propagator

    async def execute(
        self,
        student_id: UUID,
        node_id: str,
        success: bool,
        response_time_seconds: float = 0.0,
        explicit_grade: Optional[int] = None, # Novo parâmetro opcional
        root_cause: Optional[ErrorRootCause] = None,
    ):
        print(f"--- Processing Review for Node {node_id} ---")

        # 1. Buscar o nó
        node_uuid = UUID(node_id) if isinstance(node_id, str) else node_id
        node = await self.node_repo.get_by_id(node_uuid)
        if not node:
            raise ValueError(f"Knowledge Node {node_id} not found")

        # 2. Buscar histórico
        recent_history = await self.performance_repo.get_recent_events(
            student_id, limit=50
        )
        node_history = [e for e in recent_history if e.topic == node.name]

        # 3. Determinar a nota (Explícita > Inferida)
        if explicit_grade:
            # Converte int (1-4) para Enum
            # Assumindo: 1=AGAIN, 2=HARD, 3=GOOD, 4=EASY
            grade = self._map_explicit_grade(explicit_grade)
            inference_type = "explicit"
        else:
            grade = self._infer_grade(success, response_time_seconds)
            inference_type = "inferred"

        print(f" Grade decision: {grade.name} (Source: {inference_type})")

        # 4. Intelligence Engine calcula novo estado
        updated_node = self.intelligence_engine.update_node_state(
            node=node,
            grade=grade,
            history=node_history,
            root_cause=root_cause,
        )

        # 5. Propagação Semântica (se necessário)
        if not success and root_cause == ErrorRootCause.LACK_OF_BASE:
            await self.semantic_propagator.propagate_boost(
                origin_node_id=updated_node.id,
                factor=1.5, # Penalidade mais forte para falta de base
                neighborhood_size=3,
            )


        # 6. Persistir
        await self.node_repo.update(updated_node)

        # 7. Registrar evento
        event = PerformanceEvent(
            id=uuid4(),
            student_id=student_id,
            event_type=PerformanceEventType.QUIZ,
            occurred_at=datetime.now(timezone.utc),
            topic=updated_node.name,
            metric=PerformanceMetric.ACCURACY,
            value=1.0 if grade != ReviewGrade.AGAIN else 0.0,
            baseline=updated_node.stability,
            root_cause=root_cause.value if root_cause else None,
            event_metadata={
                "response_time": response_time_seconds,
                "grade_value": grade.value,
                "grade_source": inference_type,
                "difficulty_snapshot": updated_node.difficulty,
            },
        )

        await self.performance_repo.save(event)

        # 8. Lógica de Gatilho para o Desafio de Feynman
        response_data = {
            "status": "recorded",
            "node": updated_node.name,
            "new_stability": updated_node.stability,
            "next_review": updated_node.next_review_at,
            "grade_used": grade.name,
            "lapses": updated_node.lapses,
        }

        if updated_node.lapses >= 3 and root_cause == ErrorRootCause.LACK_OF_BASE:
            print(f"--- FEYNMAN TRIGGERED for Node {node_id} ---")
            response_data["trigger_feynman"] = True


        return response_data

    def _infer_grade(self, success: bool, duration: float) -> ReviewGrade:
        if not success:
            return ReviewGrade.AGAIN
        if duration < self.FAST_RESPONSE_THRESHOLD:
            return ReviewGrade.EASY
        if duration > self.SLOW_RESPONSE_THRESHOLD:
            return ReviewGrade.HARD
        return ReviewGrade.GOOD
    
    def _map_explicit_grade(self, value: int) -> ReviewGrade:
        # Mapeamento direto dos botões do Frontend
        mapping = {
            1: ReviewGrade.AGAIN,
            2: ReviewGrade.HARD,
            3: ReviewGrade.GOOD,
            4: ReviewGrade.EASY
        }
        return mapping.get(value, ReviewGrade.GOOD) # Fallback seguro