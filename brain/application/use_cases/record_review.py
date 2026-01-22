from uuid import UUID
from datetime import datetime, timezone
from brain.domain.entities.knowledge_node import ReviewGrade
from brain.domain.policies.srs_policy import SRSPolicy
from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository
from brain.domain.services.intelligence_engine import IntelligenceEngine

class RecordReviewUseCase:
    def __init__(
        self, 
        node_repo: KnowledgeRepository, 
        perf_repo: PerformanceRepository,
        engine: IntelligenceEngine
    ):
        self.node_repo = node_repo
        self.perf_repo = perf_repo
        self.engine = engine
        self.srs_policy = SRSPolicy()

    async def execute(self, student_id: UUID, node_id: UUID, grade: ReviewGrade):
        # 1. Obter estado atual
        node = await self.node_repo.get_by_id(node_id)
        if not node:
            raise ValueError("Nó não encontrado")

        # 2. Atualizar estado mnemônico (SRS)
        updated_node = self.srs_policy.process_review(node, grade)

        # 3. Verificar Regras Adaptativas (Inteligência)
        history = await self.perf_repo.get_recent_events(student_id, limit=10)
        
        if self.engine.should_trigger_priority_boost(updated_node, history):
            updated_node.apply_penalty(factor=2.0) # Dobra a prioridade de aparição
        elif grade >= ReviewGrade.GOOD:
            updated_node.record_success()

        # 4. Persistir e retornar
        await self.node_repo.update(updated_node)
        return updated_node
