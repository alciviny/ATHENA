
import logging
from uuid import UUID
from typing import Dict, Any

from brain.application.ports.ai_service import AIService
from brain.application.ports.repositories import KnowledgeNodeRepository, PerformanceRepository
from brain.domain.entities.performance_event import PerformanceEvent, PerformanceType
from brain.domain.services.intelligence_engine import IntelligenceEngine

logger = logging.getLogger(__name__)

class ValidateFeynmanExplanation:
    """
    Use Case para validar a explicação de um aluno (Técnica de Feynman),
    avaliar a resposta com um serviço de IA e registrar o desempenho.
    """

    def __init__(
        self,
        node_repository: KnowledgeNodeRepository,
        performance_repository: PerformanceRepository,
        ai_service: AIService,
    ):
        self.node_repository = node_repository
        self.performance_repository = performance_repository
        self.ai_service = ai_service
        self.intelligence_engine = IntelligenceEngine()

    async def execute(
        self,
        student_id: UUID,
        node_id: UUID,
        explanation: str,
    ) -> Dict[str, Any]:
        """
        Executa a validação da explicação de Feynman.

        Args:
            student_id: ID do aluno.
            node_id: ID do nó de conhecimento.
            explanation: A explicação fornecida pelo aluno.

        Returns:
            Um dicionário contendo o resultado da validação da IA.

        Raises:
            ValueError: Se o nó de conhecimento não for encontrado.
            RuntimeError: Se o serviço de IA falhar.
        """
        logger.info(
            f"[FEYNMAN_UC] Iniciando validação | StudentId={student_id} | "
            f"NodeId={node_id}"
        )

        # 1. Buscar o KnowledgeNode
        node = await self.node_repository.get_by_id(node_id)
        if not node:
            logger.error(f"[FEYNMAN_UC] Nó não encontrado | NodeId={node_id}")
            raise ValueError("Nó de conhecimento não encontrado.")

        # 2. Enviar para o serviço de IA para validação
        try:
            validation_result = await self.ai_service.validate_feynman_explanation(
                node_content=node.content,
                explanation=explanation,
                subject=node.subject,
                difficulty=node.difficulty,
            )
            logger.info(
                "[FEYNMAN_UC] Validação da IA recebida | "
                f"Score={validation_result.get('score')}"
            )
        except Exception as e:
            logger.critical(
                "[FEYNMAN_UC] Falha crítica no serviço de IA", exc_info=e
            )
            raise RuntimeError("Falha ao validar a explicação com o serviço de IA.")

        # 3. Processar o resultado e atualizar o estado do nó
        is_success = validation_result.get("score", 0.0) >= 0.8

        if is_success:
            self.intelligence_engine.apply_success(node)
            logger.info(
                f"[FEYNMAN_UC] Sucesso registrado no nó | NodeId={node_id}"
            )
        else:
            # Em caso de falha, registramos o erro de base para o motor de inteligência
            self.intelligence_engine.apply_failure(node, is_base_error=True)
            logger.warning(
                f"[FEYNMAN_UC] Falha registrada no nó (erro de base) | NodeId={node_id}"
            )
        
        await self.node_repository.update(node)

        # 4. Registrar o evento de performance
        performance_event = PerformanceEvent(
            student_id=student_id,
            node_id=node_id,
            performance_type=PerformanceType.FEYNMAN_VALIDATION,
            is_success=is_success,
            metadata={
                "explanation": explanation,
                "feedback": validation_result.get("feedback"),
                "score": validation_result.get("score"),
                "missing_concepts": validation_result.get("missing_concepts"),
            },
        )

        await self.performance_repository.create(performance_event)
        logger.info(
            f"[FEYNMAN_UC] Evento de performance registrado | EventId={performance_event.id}"
        )

        return validation_result

