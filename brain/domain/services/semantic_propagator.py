import logging
from uuid import UUID
from typing import Iterable
from brain.application.ports.repositories import (
    KnowledgeRepository,
    KnowledgeVectorRepository,
)

class SemanticPropagator:
    """
    Serviço de domínio responsável por propagar efeitos cognitivos
    (boosts / penalidades suaves) para microconceitos semanticamente próximos.
    """

    def __init__(
        self,
        node_repository: KnowledgeRepository,
        vector_repository: KnowledgeVectorRepository,
    ) -> None:
        self._node_repo = node_repository
        self._vector_repo = vector_repository

    async def propagate_boost(
        self,
        origin_node_id: UUID,
        *,
        factor: float = 1.3,
        neighborhood_size: int = 3,
    ) -> None:
        """
        Propaga um boost/penalidade preventiva para conceitos semanticamente vizinhos.
        """
        try:
            neighbor_ids = await self._vector_repo.find_semantically_related(
                origin_node_id,
                limit=neighborhood_size,
            )

            await self._apply_penalty_to_neighbors(
                origin_node_id,
                neighbor_ids,
                factor,
            )
        except Exception as e:
            logging.error(
                "Falha ao buscar nós semanticamente relacionados no Qdrant. Origin node ID: %s. Error: %s",
                origin_node_id,
                e,
                exc_info=True,
            )


    async def _apply_penalty_to_neighbors(
        self,
        origin_node_id: UUID,
        neighbor_ids: Iterable[UUID],
        factor: float,
    ) -> None:
        for neighbor_id in neighbor_ids:
            # Proteção defensiva
            if neighbor_id == origin_node_id:
                continue

            neighbor_node = await self._node_repo.get_by_id(neighbor_id)
            if not neighbor_node:
                continue

            neighbor_node.apply_penalty(factor=factor)
            
            await self._node_repo.update(neighbor_node)