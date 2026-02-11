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
        """
        Gera embedding para texto usando Gemini com fallback robusto.
        """
        if not text or not text.strip():
            logger.warning("Texto vazio fornecido para geração de embedding")
            return []

        try:
            # Valida se a API key está configurada
            if not settings.GEMINI_API_KEY:
                logger.error("GEMINI_API_KEY não configurada")
                return []

            # Limpa e prepara o texto
            clean_text = text.strip()
            if len(clean_text) > 10000:  # Limite do Gemini
                clean_text = clean_text[:10000]
                logger.warning(f"Texto truncado para 10000 caracteres")

            # Usa thread para não bloquear o loop principal
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/gemini-embedding-001",
                content=clean_text,
                task_type="retrieval_query"
            )

            embedding = result.get('embedding', [])
            if not embedding:
                logger.error("Embedding vazio retornado pela API")
                return []

            # Valida se é uma lista de floats
            if not isinstance(embedding, list) or not all(isinstance(x, (int, float)) for x in embedding):
                logger.error(f"Embedding inválido: {type(embedding)}")
                return []

            logger.debug(f"Embedding gerado com {len(embedding)} dimensões")
            return embedding

        except Exception as e:
            logger.error(f"Erro ao gerar embedding para texto '{text[:50]}...': {e}")
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
        """
        Encontra nós semanticamente relacionados usando busca vetorial por similaridade.
        Estratégia: busca nós próximos ao vetor do nó de referência.
        """
        try:
            # Primeiro, recupera o vetor do nó de referência
            reference_vector = await self._get_node_vector(str(reference_node_id))
            if not reference_vector:
                logger.warning(f"Vetor não encontrado para nó {reference_node_id}")
                return []

            # Faz busca por similaridade vetorial
            def _do_search():
                response = self._client.query_points(
                    collection_name=self._collection,
                    query=reference_vector,
                    limit=limit + 1,  # +1 para excluir o próprio nó
                    with_payload=False,
                    with_vectors=False,
                )
                return response.points

            # Executa busca em thread para não bloquear
            points = await asyncio.to_thread(_do_search)

            # Extrai IDs, excluindo o próprio nó de referência
            related_ids = []
            for point in points:
                try:
                    node_id = UUID(str(point.id))
                    if node_id != reference_node_id:  # Exclui o próprio nó
                        related_ids.append(node_id)
                        if len(related_ids) >= limit:
                            break
                except (ValueError, AttributeError):
                    continue

            logger.info(f"Encontrados {len(related_ids)} nós relacionados para {reference_node_id}")
            return related_ids

        except Exception as exc:
            logger.error(f"Falha ao buscar nós semanticamente relacionados: {exc}", exc_info=exc)
            return []

    async def _get_node_vector(self, node_id: str) -> Optional[List[float]]:
        """
        Recupera o vetor de um nó específico do Qdrant.
        """
        try:
            def _retrieve_vector():
                response = self._client.retrieve(
                    collection_name=self._collection,
                    ids=[node_id],
                    with_vectors=True
                )
                return response

            points = await asyncio.to_thread(_retrieve_vector)

            if points and len(points) > 0:
                vector = points[0].vector
                if vector:
                    return vector
                else:
                    logger.warning(f"Nó {node_id} não possui vetor")
                    return None
            else:
                logger.warning(f"Nó {node_id} não encontrado na coleção")
                return None

        except Exception as exc:
            logger.error(f"Erro ao recuperar vetor do nó {node_id}: {exc}")
            return None