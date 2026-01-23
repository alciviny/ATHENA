import logging
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from brain.domain.services.semantic_propagator import SemanticPropagator
from brain.application.ports.repositories import (
    KnowledgeRepository,
    KnowledgeVectorRepository,
)
from brain.domain.entities.knowledge_node import KnowledgeNode


@pytest.fixture
def mock_node_repository():
    return AsyncMock(spec=KnowledgeRepository)


@pytest.fixture
def mock_vector_repository():
    return AsyncMock(spec=KnowledgeVectorRepository)


@pytest.fixture
def semantic_propagator(mock_node_repository, mock_vector_repository):
    return SemanticPropagator(mock_node_repository, mock_vector_repository)


@pytest.mark.asyncio
async def test_propagate_boost_success(
    semantic_propagator, mock_node_repository, mock_vector_repository
):
    origin_node_id = UUID("a1a2a3a4-b1b2-c1c2-d1d2-e1e2e3e4e5e6")
    neighbor_ids = [
        UUID("f1f2f3f4-a1b2-c1d2-e1f2-a1b2c3d4e5f6"),
        UUID("a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6"),
    ]
    mock_vector_repository.find_semantically_related.return_value = neighbor_ids

    mock_node_1 = AsyncMock(spec=KnowledgeNode)
    mock_node_2 = AsyncMock(spec=KnowledgeNode)
    mock_node_repository.get_by_id.side_effect = [
        mock_node_1,
        mock_node_2,
    ]
    mock_node_repository.update.side_effect = [
        None,
        None,
    ]

    await semantic_propagator.propagate_boost(origin_node_id)

    mock_vector_repository.find_semantically_related.assert_awaited_once_with(
        origin_node_id, limit=3
    )
    mock_node_repository.get_by_id.assert_any_call(neighbor_ids[0])
    mock_node_repository.get_by_id.assert_any_call(neighbor_ids[1])
    mock_node_1.apply_penalty.assert_called_once()
    mock_node_2.apply_penalty.assert_called_once()
    mock_node_repository.update.assert_any_call(mock_node_1)
    mock_node_repository.update.assert_any_call(mock_node_2)


@pytest.mark.asyncio
async def test_propagate_boost_qdrant_failure(
    semantic_propagator, mock_vector_repository, caplog
):
    origin_node_id = UUID("a1a2a3a4-b1b2-c1c2-d1d2-e1e2e3e4e5e6")
    mock_vector_repository.find_semantically_related.side_effect = Exception(
        "Qdrant error"
    )

    with caplog.at_level("ERROR"):
        await semantic_propagator.propagate_boost(origin_node_id)

    # Ensure the log message contains the expected part
    assert "Falha ao buscar nós semanticamente relacionados no Qdrant." in caplog.text
    # Ensure the log record contains the extra data
    assert any(
        record.levelno == logging.ERROR and
        "Falha ao buscar nós semanticamente relacionados no Qdrant." in record.message
        for record in caplog.records
    )
    # Ensure no further calls are made
    semantic_propagator._node_repo.get_by_id.assert_not_called()
    semantic_propagator._node_repo.update.assert_not_called()
