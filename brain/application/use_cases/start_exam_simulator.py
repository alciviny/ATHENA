import logging
import asyncio
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import List

from brain.application.ports.repositories import (
    StudentRepository,
    KnowledgeRepository,
    StudyPlanRepository,
    CognitiveProfileRepository,
    KnowledgeVectorRepository,
    PerformanceRepository,
)
from brain.application.ports.ai_service import AIService
from brain.application.dto.study_plan_dto import StudyPlanDTO, StudySessionDTO, StudyItemDTO, StudyPlanType
from brain.domain.entities.study_plan import StudyPlan

from brain.application.services.simulator_service import SimulatorService

logger = logging.getLogger(__name__)


class StartExamSimulatorUseCase:
    """
    Orquestra um simulador de prova do tipo EXAM.

    Garante:
    - criação de um StudyPlan do tipo EXAM
    - definição de `time_limit_seconds` global
    - omissão do feedback/explicações até submissão final (back vazio no DTO)
    """
    def __init__(
        self,
        student_repo: StudentRepository,
        knowledge_repo: KnowledgeRepository,
        study_plan_repo: StudyPlanRepository,
        cognitive_profile_repo: CognitiveProfileRepository,
        vector_repo: KnowledgeVectorRepository,
        performance_repo: PerformanceRepository,
        ai_service: AIService,
    ):
        self.student_repo = student_repo
        self.knowledge_repo = knowledge_repo
        self.study_plan_repo = study_plan_repo
        self.cognitive_profile_repo = cognitive_profile_repo
        self.vector_repo = vector_repo
        self.performance_repo = performance_repo
        self.ai_service = ai_service
        self.simulator_service = SimulatorService(knowledge_repo, performance_repo)

    async def execute(self, student_id: UUID, num_questions: int = 20, time_limit_seconds: int = 3600, stress_level: float = 1.0) -> StudyPlanDTO:
        logger.info(f"Iniciando simulador EXAM para {student_id}")

        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError(f"Estudante {student_id} não encontrado")

        profile = await self.cognitive_profile_repo.get_by_student_id(student_id)
        if not profile:
            # Pode criar um profile padrão simples
            profile = None

        # 1. Selecionar nós para o simulador
        selected_nodes = await self.simulator_service.generate_simulation(
            student_id=student_id,
            num_questions=num_questions,
            stress_level=stress_level,
        )

        # 2. Gerar conteúdo via IA (mantendo RAG e retries), mas OMITE explicação no DTO
        generated_cards = []
        for i, node in enumerate(selected_nodes):
            try:
                rag_context = await self.vector_repo.search_context(query=node.name, limit=1)
            except Exception:
                rag_context = None

            final_context = rag_context if rag_context else f"Conceitos de {node.name}"

            try:
                card = await self.ai_service.generate_flashcard(
                    topic=node.name,
                    difficulty=int(getattr(node, 'difficulty', 5) * 5),
                    context=final_context,
                )
            except Exception as e:
                logger.error(f"IA falhou para {node.name}: {e}")
                card = {
                    "pergunta": f"Questão sobre: {node.name}",
                    "opcoes": ["A", "B", "C", "D"],
                    "correta_index": 0,
                    "explicacao": "Explicação guardada até o final do simulador."
                }

            generated_cards.append(card)
            if i < len(selected_nodes) - 1:
                await asyncio.sleep(0.5)

        # 3. Construir StudyPlan (domain) e DTO
        plan_id = uuid4()
        created_at = datetime.now(timezone.utc)

        # Construir domínio StudyPlan mínimo
        try:
            plan_domain = StudyPlan(id=plan_id, student_id=student_id, created_at=created_at)
        except Exception:
            # Fallback simples caso a assinatura do dataclass seja diferente
            plan_domain = type('Plan', (), {})()
            plan_domain.id = plan_id
            plan_domain.student_id = student_id
            plan_domain.created_at = created_at

        plan_domain.goals = ["Simulador EXAM: Avaliação de Proeficiência"]
        plan_domain.knowledge_nodes = selected_nodes

        # Estimativa de duração total
        total_seconds = sum(getattr(n, 'estimated_time_seconds', 60) for n in selected_nodes)
        plan_domain.estimated_duration_minutes = int(total_seconds / 60)

        # Persistir plano (domínio)
        await self.study_plan_repo.save(plan_domain)

        # Montar DTO sem explicações (feedback ficará oculto até finalização)
        sessions = []
        for i, node in enumerate(selected_nodes):
            content = generated_cards[i] if i < len(generated_cards) else {}
            item = StudyItemDTO(
                id=str(getattr(node, 'id', '')),
                type="flashcard",
                content={
                    "front": content.get('pergunta', f"Questão sobre {node.name}"),
                    "options": content.get('opcoes', []),
                    "correct_index": content.get('correta_index', 0),
                    # OMITE a explicação até submissão final
                    "back": "",
                },
                topic_roi="",
                estimated_time_minutes=int(getattr(node, 'estimated_time_seconds', 60) / 60),
                status="pending",
            )

            session = StudySessionDTO(
                id=str(uuid4()),
                topic=node.name,
                start_time=created_at,
                duration_minutes=int(getattr(node, 'estimated_time_seconds', 60) / 60),
                items=[item],
                focus_level=getattr(profile, 'focus_level', 'DEEP_WORK') if profile else 'DEEP_WORK',
                method="exam"
            )
            sessions.append(session)

        plan_dto = StudyPlanDTO(
            id=str(plan_id),
            student_id=str(student_id),
            goals=plan_domain.goals,
            created_at=created_at,
            sessions=sessions,
            status="created",
            plan_type=StudyPlanType.EXAM,
            time_limit_seconds=time_limit_seconds,
        )

        logger.info(f"Simulador EXAM criado: {plan_id}")
        return plan_dto
