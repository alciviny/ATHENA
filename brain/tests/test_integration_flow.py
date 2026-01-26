import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from brain.domain.entities.knowledge_node import ReviewGrade, KnowledgeNode
from brain.application.use_cases.record_review import RecordReviewUseCase
from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.domain.services.semantic_propagator import SemanticPropagator
from brain.infrastructure.persistence.in_memory_repositories import (
    InMemoryKnowledgeRepository,
    InMemoryPerformanceRepository
)

# ==============================================================================
# 📜 CONTRATOS DO SISTEMA (Shared Knowledge)
# ==============================================================================
GO_INTERVENTION_WEIGHT_THRESHOLD = 1.5
GO_INTERVENTION_REVIEW_WINDOW_HOURS = 2

# ==============================================================================
# 🛠️ FIXTURES
# ==============================================================================

@pytest.fixture
def knowledge_repository():
    return InMemoryKnowledgeRepository()

@pytest.fixture
def performance_repository():
    return InMemoryPerformanceRepository()

@pytest.fixture
def mock_vector_repository():
    class MockVectorRepo:
        async def find_semantically_related(self, node_id, limit=5):
            return [uuid4()] 
    return MockVectorRepo()

@pytest.fixture
def record_review_use_case(
    knowledge_repository,
    performance_repository,
    mock_vector_repository
):
    propagator = SemanticPropagator(
        node_repository=knowledge_repository,
        vector_repository=mock_vector_repository,
    )
    
    return RecordReviewUseCase(
        node_repo=knowledge_repository,
        performance_repo=performance_repository,
        intelligence_engine=IntelligenceEngine(),
    )

# ==============================================================================
# 🧪 TESTE DE INTEGRAÇÃO
# ==============================================================================

@pytest.mark.asyncio
async def test_python_prepares_state_for_go_worker(
    record_review_use_case,
    knowledge_repository
):
    """
    Valida se o Python cumpre sua parte no contrato distribuído.
    """
    # 1. Setup
    student_id = uuid4()
    node_id = uuid4()
    
    # Nó difícil, vulnerável a intervenção
    initial_node = KnowledgeNode(
        id=node_id,
        name="Go Channels",
        subject="Go Concurrency", # <--- CORREÇÃO: Campo 'subject' adicionado!
        difficulty=8.0, 
        weight=1.0,
        next_review_at=datetime.now(timezone.utc) # Mantemos next_review_at
    )
    await knowledge_repository.save(initial_node)

    # 2. Ação: Erro Crítico
    await record_review_use_case.execute(
        student_id=student_id,
        node_id=node_id,
        success=False,  # <--- CORREÇÃO: Usando o parâmetro booleano correto
        response_time_seconds=30.0 # Tempo médio para não ser fácil nem difícil
    )

    # 3. Verificação de Contrato (Python side)
    updated_node = await knowledge_repository.get_by_id(node_id)
    
    # Verifica se o peso subiu o suficiente para o Go priorizar
    assert updated_node.weight >= GO_INTERVENTION_WEIGHT_THRESHOLD, \
        f"Peso {updated_node.weight} abaixo do gatilho do Worker ({GO_INTERVENTION_WEIGHT_THRESHOLD})"

    print(f"\n✅ Contrato Python cumprido: Node {node_id} está 'marcado' para o Worker.")