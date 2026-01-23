import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from qdrant_client.http.models import PointStruct, ScoredPoint
from qdrant_client.http.exceptions import UnexpectedResponse

from brain.infrastructure.persistence.qdrant_repository import (
    QdrantKnowledgeVectorRepository,
)


@pytest.fixture
def mock_qdrant_client():
    return AsyncMock()


@pytest.fixture
def qdrant_repository(mock_qdrant_client):
    repo = QdrantKnowledgeVectorRepository(url="http://localhost:6333")
    repo._client = mock_qdrant_client  # Inject the mock client
    return repo


@pytest.mark.asyncio
async def test_find_semantically_related_success(qdrant_repository, mock_qdrant_client):
    reference_node_id = UUID("a1a2a3a4-b1b2-c1c2-d1d2-e1e2e3e4e5e6")
    mock_qdrant_client.recommend.return_value = [
        ScoredPoint(id="f1f2f3f4-a1b2-c1d2-e1f2-a1b2c3d4e5f6", version=0, score=0.9, payload=None, vector=None),
        ScoredPoint(id="a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6", version=0, score=0.8, payload=None, vector=None),
    ]

    result = await qdrant_repository.find_semantically_related(reference_node_id, limit=2)

    mock_qdrant_client.recommend.assert_awaited_once_with(
        collection_name="athena_knowledge",
        positive=[str(reference_node_id)],
        limit=2,
        with_payload=False,
        with_vectors=False,
    )
    assert len(result) == 2
    assert result[0] == UUID("f1f2f3f4-a1b2-c1d2-e1f2-a1b2c3d4e5f6")
    assert result[1] == UUID("a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6")


@pytest.mark.asyncio
async def test_find_semantically_related_unexpected_response(qdrant_repository, mock_qdrant_client, caplog):
    reference_node_id = UUID("a1a2a3a4-b1b2-c1c2-d1d2-e1e2e3e4e5e6")
    mock_qdrant_client.recommend.side_effect = UnexpectedResponse(status_code=500, reason_phrase="Test reason", content="Test content", headers={})

    with caplog.at_level("WARNING"):
        result = await qdrant_repository.find_semantically_related(reference_node_id)

    mock_qdrant_client.recommend.assert_awaited_once()
    assert result == []
    assert "Qdrant respondeu de forma inesperada ao recomendar similaridade." in caplog.text


@pytest.mark.asyncio
async def test_find_semantically_related_generic_exception(qdrant_repository, mock_qdrant_client, caplog):
    reference_node_id = UUID("a1a2a3a4-b1b2-c1c2-d1d2-e1e2e3e4e5e6")
    mock_qdrant_client.recommend.side_effect = Exception("Generic test error")

    with caplog.at_level("ERROR"):
        result = await qdrant_repository.find_semantically_related(reference_node_id)

    mock_qdrant_client.recommend.assert_awaited_once()
    assert result == []
    assert "Falha crítica ao acessar Qdrant para busca semântica." in caplog.text
