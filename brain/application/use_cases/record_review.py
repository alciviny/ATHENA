from datetime import datetime, timezone
from uuid import UUID, uuid4
from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository
from brain.domain.entities.PerformanceEvent import PerformanceEvent, PerformanceEventType, PerformanceMetric


class RecordReviewUseCase:
    def __init__(self, performance_repo: PerformanceRepository, node_repo: KnowledgeRepository):
        self.performance_repo = performance_repo
        self.node_repo = node_repo

    async def execute(self, student_id: UUID, node_id: str, success: bool, response_time_seconds: float = 0.0):
        # 1. Buscar Nó
        node_uuid = UUID(node_id) if isinstance(node_id, str) else node_id
        node = await self.node_repo.get_by_id(node_uuid)
        if not node:
            raise ValueError(f"Knowledge Node {node_id} not found")

        # 2. Atualizar FSRS Simplificado
        node.reps += 1
        node.last_reviewed_at = datetime.now(timezone.utc)
        if success:
            node.stability += 1.0
        else:
            node.stability = 0.0
            node.lapses += 1
        
        await self.node_repo.update(node)

        # 3. Salvar Evento
        event = PerformanceEvent(
            id=uuid4(),
            student_id=student_id,
            event_type=PerformanceEventType.QUIZ, # Assumindo que a revisão do flashcard é um tipo de quiz
            occurred_at=datetime.now(timezone.utc),
            topic=node.name,
            metric=PerformanceMetric.ACCURACY, # Usando ACCURACY para sucesso/falha
            value=1.0 if success else 0.0,
            baseline=0.0, # O baseline pode ser melhorado posteriormente
        )
        await self.performance_repo.save(event)
        
        return {"status": "recorded", "node": node.name, "new_stability": node.stability}