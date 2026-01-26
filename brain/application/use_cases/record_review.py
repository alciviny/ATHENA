from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import List

from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository
from brain.domain.entities.performance_event import (
    PerformanceEvent,
    PerformanceEventType,
    PerformanceMetric,
)
from brain.domain.entities.knowledge_node import KnowledgeNode, ReviewGrade
from brain.domain.services.intelligence_engine import IntelligenceEngine


class RecordReviewUseCase:
    """
    Caso de uso responsável por registrar uma revisão e atualizar o estado cognitivo
    do KnowledgeNode usando inferência automática de dificuldade + IntelligenceEngine.
    """

    # Limiar de tempo (em segundos) para inferência de dificuldade
    FAST_RESPONSE_THRESHOLD = 15.0   # Muito rápido → EASY
    SLOW_RESPONSE_THRESHOLD = 60.0   # Muito lento → HARD

    def __init__(
        self,
        performance_repo: PerformanceRepository,
        node_repo: KnowledgeRepository,
        intelligence_engine: IntelligenceEngine,
    ):
        self.performance_repo = performance_repo
        self.node_repo = node_repo
        self.intelligence_engine = intelligence_engine

    async def execute(
        self,
        student_id: UUID,
        node_id: str,
        success: bool,
        response_time_seconds: float = 0.0,
    ):
        print(f"--- Processing Review for Node {node_id} ---")

        # 1. Buscar o nó
        node_uuid = UUID(node_id) if isinstance(node_id, str) else node_id
        node = await self.node_repo.get_by_id(node_uuid)
        if not node:
            raise ValueError(f"Knowledge Node {node_id} not found")

        # 2. Buscar histórico recente (contexto para o IntelligenceEngine)
        recent_history = await self.performance_repo.get_recent_events(
            student_id, limit=50
        )

        # Filtra eventos relacionados ao mesmo tópico/nó
        node_history = [e for e in recent_history if e.topic == node.name]

        # 3. Inferir a nota cognitivamente (automação sensorial)
        grade = self._infer_grade(success, response_time_seconds)
        print(
            f" inferred grade: {grade.name} "
            f"(Time: {response_time_seconds}s)"
        )

        # 4. O “cérebro” calcula o novo estado (FSRS / SM-2 / híbrido)
        updated_node = self.intelligence_engine.update_node_state(
            node=node,
            grade=grade,
            history=node_history,
        )

        # 5. Persistir o nó atualizado
        await self.node_repo.update(updated_node)

        # 6. Registrar evento de performance rico (telemetria cognitiva)
        event = PerformanceEvent(
            id=uuid4(),
            student_id=student_id,
            event_type=PerformanceEventType.QUIZ,
            occurred_at=datetime.now(timezone.utc),
            topic=updated_node.name,
            metric=PerformanceMetric.ACCURACY,
            value=1.0 if success else 0.0,
            baseline=updated_node.stability,
            event_metadata={
                "response_time": response_time_seconds,
                "inferred_grade": grade.value,
                "difficulty_snapshot": updated_node.difficulty,
            },
        )

        await self.performance_repo.save(event)

        return {
            "status": "recorded",
            "node": updated_node.name,
            "new_stability": updated_node.stability,
            "next_review": updated_node.next_review_at,
            "inferred_grade": grade.name,
        }

    def _infer_grade(self, success: bool, duration: float) -> ReviewGrade:
        """
        Transforma dados brutos (acerto + tempo) em uma avaliação cognitiva (FSRS Grade).
        Remove a necessidade do aluno marcar manualmente Fácil/Médio/Difícil.
        """
        if not success:
            return ReviewGrade.AGAIN  # FSRS 1

        if duration < self.FAST_RESPONSE_THRESHOLD:
            return ReviewGrade.EASY   # FSRS 4

        if duration > self.SLOW_RESPONSE_THRESHOLD:
            return ReviewGrade.HARD   # FSRS 2

        return ReviewGrade.GOOD       # FSRS 3
