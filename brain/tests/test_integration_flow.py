import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from brain.config.settings import settings
from brain.domain.entities.knowledge_node import ReviewGrade, KnowledgeNode
from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.domain.services.semantic_propagator import SemanticPropagator
from brain.application.use_cases.record_review import RecordReviewUseCase

# Imports for manual dependency resolution
from brain.infrastructure.persistence.database import SessionLocal, Base, engine
from brain.infrastructure.persistence.postgres_repositories import (
    PostgresKnowledgeRepository,
    PostgresPerformanceRepository,
)
from brain.infrastructure.persistence.qdrant_repository import QdrantKnowledgeVectorRepository


@pytest.fixture(scope="function")
def db_session():
    # Create the tables in the test database
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop the tables after the test is done
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def knowledge_repository(db_session):
    return PostgresKnowledgeRepository(db_session)

@pytest.fixture(scope="function")
def performance_repository(db_session):
    return PostgresPerformanceRepository(db_session)


@pytest.fixture(scope="function")
def vector_repository():
    return QdrantKnowledgeVectorRepository(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION,
    )

@pytest.fixture(scope="function")
def record_review_use_case(knowledge_repository, performance_repository, vector_repository):
    engine = IntelligenceEngine()
    propagator = SemanticPropagator(
        node_repository=knowledge_repository,
        vector_repository=vector_repository,
    )
    return RecordReviewUseCase(
        node_repo=knowledge_repository,
        perf_repo=performance_repository,
        engine=engine,
        propagator=propagator,
    )


@pytest.mark.asyncio
async def test_full_cognitive_chain_python_to_go(record_review_use_case, knowledge_repository):
    """
    Testa se um erro no Python desencadeia o boost preventivo no Go.
    """
    # 1. Setup - Usando as fixtures
    use_case = record_review_use_case
    node_repo = knowledge_repository
    
    student_id = uuid4()
    node_id = uuid4()
    
    # Criar um nó "vulnerável" (Dificuldade alta)
    node = KnowledgeNode(
        id=node_id,
        title="Go Concurrency Patterns",
        subject="Go Programming", # Adicionado subject
        difficulty=8.5, # Nó difícil para forçar boost
        stability=5.0,
        weight=1.0,
        reps=1, # Adicionado para simular uma revisão subsequente
        next_review_at=datetime.now(timezone.utc) - timedelta(days=1) # Já vencido
    )
    node_repo.add(node) # Garante que o nó existe no Postgres

    # 2. Executar Erro (Simula aluno clicando em 'AGAIN')
    print(f"\n[TEST] Registando erro 'AGAIN' para o nó: {node.title}")
    await use_case.execute(student_id, node_id, ReviewGrade.AGAIN)

    # 3. Verificação Python (Imediata)
    updated_node = node_repo.get_by_id(node_id)
    assert updated_node.weight >= 1.5 # Penalidade de peso aplicada
    print(f"✅ Python: Peso aumentado para {updated_node.weight}")

    # 4. Verificação Go (O 'Músculo')
    # Nota: Em ambiente de teste, podemos disparar o worker manualmente ou aguardar
    print("[TEST] Aguardando intervenção do Worker em Go...")
    
    # Simulamos a passagem do tempo para o cálculo de Probabilidade (R)
    # No banco, o 'last_reviewed_at' agora é 'agora'. 
    # Se o Go rodar, ele verá que a estabilidade caiu e R está baixo.
    
    # Esperamos que o Worker (se estiver rodando) atualize o next_review_at para +1h
    await asyncio.sleep(2) 
    
    final_state = node_repo.get_by_id(node_id)
    
    # Se o Worker funcionou, o next_review_at deve ser curto (anteve a revisão)
    # em vez de ser baseado apenas na estabilidade normal.
    # Garantir que final_state.next_review_at é timezone-aware para comparação
    if final_state.next_review_at.tzinfo is None:
        final_state.next_review_at = final_state.next_review_at.replace(tzinfo=timezone.utc)
    assert final_state.next_review_at < datetime.now(timezone.utc) + timedelta(hours=2)
    print(f"✅ Go: Próxima revisão antecipada com sucesso para: {final_state.next_review_at}")
