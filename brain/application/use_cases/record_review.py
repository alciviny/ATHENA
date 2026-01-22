from uuid import UUID
from brain.domain.entities.knowledge_node import ReviewGrade
from brain.domain.policies.srs_policy import SRSPolicy
from brain.application.ports.repositories import KnowledgeRepository

class RecordReviewUseCase:
    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository
        self.policy = SRSPolicy()

    async def execute(self, node_id: UUID, grade: ReviewGrade):
        # 1. Recupera o estado atual do conhecimento
        node = await self.repository.get_by_id(node_id)
        if not node:
            raise ValueError("Nó de conhecimento não encontrado")

        # 2. Aplica a inteligência de repetição espaçada
        updated_node = self.policy.process_review(node, grade)

        # 3. Persiste o novo estado mnemônico
        await self.repository.update(updated_node)
        
        return updated_node
