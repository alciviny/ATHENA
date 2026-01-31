import os
import logging
import asyncio
from typing import List, Optional, Any
from uuid import UUID

import google.generativeai as genai
# MUDANÇA: Usamos o cliente síncrono que é mais compatível e estável
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from brain.application.ports.repositories import KnowledgeVectorRepository
from brain.config.settings import settings

logger = logging.getLogger(__name__)

class QdrantKnowledgeVectorRepository(KnowledgeVectorRepository):
    """
    Adaptador de infraestrutura para Qdrant usando cliente Síncrono (Thread-Safe).
    Isso resolve erros de compatibilidade de versão do AsyncClient.
    """

    def __init__(
        self,
        *,
        url: str,
        api_key: Optional[str] = None,
        collection_name: str = "athena_knowledge",
        timeout: float = 10.0,
    ) -> None:
        self._collection = collection_name
        # MUDANÇA: Instanciando cliente síncrono
        self._client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=timeout,
        )

        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        logger.info(f"QdrantRepo (Sync) initialized at {url}")

    async def _generate_query_embedding(self, text: str) -> List[float]:
        try:
            # Usa thread para não bloquear o loop principal
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return []

    async def search_context(self, query: str, limit: int = 3) -> str:
        """
        Busca contexto semântico usando execução síncrona em thread.
        """
        if not query:
            return ""

        try:
            # 1. Gera embedding
            query_vector = await self._generate_query_embedding(query)
            if not query_vector:
                return ""

            # 2. Define função de busca síncrona
            # ATUALIZADO: Uso de query_points para compatibilidade com qdrant-client >= 1.10
            def _do_search():
                response = self._client.query_points(
                    collection_name=self._collection,
                    query=query_vector,
                    limit=limit,
                )
                return response.points  # Retorna a lista de hits dentro do objeto de resposta

            # 3. Executa em thread separada (Isola o erro de AsyncClient)
            results = await asyncio.to_thread(_do_search)

            context_chunks = [
                hit.payload.get("text", "")
                for hit in results
                if hit.payload and "text" in hit.payload
            ]
            
            found_text = "\n\n".join(context_chunks)
            if found_text:
                logger.info(f"RAG: Encontrado contexto para '{query}' ({len(found_text)} chars)")
            
            return found_text

        except Exception as exc:
            # Loga o erro mas retorna vazio para não quebrar a geração do plano
            logger.error(f"Erro Qdrant search (Ignorado): {exc}")
            return ""

    async def find_semantically_related(self, reference_node_id: UUID, *, limit: int = 5) -> List[UUID]:
        return []