from typing import List, Optional
from uuid import UUID
import logging
from importlib.metadata import version

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from brain.application.ports.repositories import KnowledgeVectorRepository

logger = logging.getLogger(__name__)


class QdrantKnowledgeVectorRepository(KnowledgeVectorRepository):
    """
    Adaptador de infraestrutura responsável por traduzir operações
    semânticas do domínio para consultas vetoriais no Qdrant.
    """

    def __init__(
        self,
        *,
        url: str,
        api_key: Optional[str] = None,
        collection_name: str = "athena_knowledge",
        timeout: float = 5.0,
    ) -> None:
        qdrant_client_version = version('qdrant-client')
        logger.info(f"Qdrant client version: {qdrant_client_version}")
        self._collection = collection_name
        self._client = AsyncQdrantClient(
            url=url,
            api_key=api_key,
            timeout=timeout,
        )

    async def find_semantically_related(
        self,
        reference_node_id: UUID,
        *,
        limit: int = 5,
    ) -> List[UUID]:
        """
        Retorna nós semanticamente relacionados utilizando a API de
        recomendação do Qdrant (server-side similarity).

        Estratégia:
        - Usa o ID do ponto como referência positiva
        - Evita tráfego desnecessário de vetores/payloads
        - Falhas não interrompem o fluxo principal (graceful degradation)
        """
        try:
            results = await self._client.recommend(
                collection_name=self._collection,
                positive=[str(reference_node_id)],
                limit=limit,
                with_payload=False,
                with_vectors=False,
            )

            return [
                UUID(hit.id)
                for hit in results
                if hit.id is not None
            ]

        except UnexpectedResponse as exc:
            logger.warning(
                "Qdrant respondeu de forma inesperada ao recomendar similaridade.",
                extra={
                    "reference_node_id": str(reference_node_id),
                    "collection": self._collection,
                    "error": str(exc),
                },
            )
            return []

        except Exception as exc:
            logger.error(
                "Falha crítica ao acessar Qdrant para busca semântica.",
                exc_info=True,
                extra={
                    "reference_node_id": str(reference_node_id),
                    "collection": self._collection,
                },
            )
            return []

    async def search_context(self, query: str, limit: int = 3) -> str:
        """
        Busca trechos de texto relevantes no banco vetorial para servirem de
        'Grounding' (Base) para a IA. Isso reduz alucinações.
        """
        if not query:
            return ""

        try:
            results = await self._client.search(
                collection_name=self._collection,
                query_text=query,   # ✔ Qdrant >= 1.7 suporta busca textual direta
                limit=limit,
            )

            context_chunks = [
                hit.payload.get("text", "")
                for hit in results
                if hit.payload and "text" in hit.payload
            ]

            return "\n\n".join(context_chunks)

        except Exception as exc:
            logger.error(f"Erro ao buscar contexto no Qdrant: {exc}")
            # Falha segura → IA continua funcionando sem grounding
            return ""
