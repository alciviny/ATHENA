import sys
import asyncio
from uuid import UUID
from typing import List
from datetime import datetime, timezone

from brain.domain.services.study_plan_generator import StudyPlanGenerator
from brain.domain.policies.adaptive_rule import AdaptiveRule
from brain.application.ports.repositories import (
    StudentRepository,
    PerformanceRepository,
    KnowledgeRepository,
    StudyPlanRepository,
    CognitiveProfileRepository,
)
from brain.application.ports.ai_service import AIService
from brain.application.dto.study_plan_dto import StudyPlanOutputDTO, StudyItemDTO


class StudentNotFoundError(Exception):
    """Exceção lançada quando um estudante não é encontrado no repositório."""
    pass


class CognitiveProfileNotFoundError(Exception):
    """Exceção para quando o perfil cognitivo do estudante não é encontrado."""
    pass


class GenerateStudyPlanUseCase:
    def __init__(
        self,
        student_repo: StudentRepository,
        performance_repo: PerformanceRepository,
        knowledge_repo: KnowledgeRepository,
        study_plan_repo: StudyPlanRepository,
        cognitive_profile_repo: CognitiveProfileRepository,
        ai_service: AIService,
        adaptive_rules: List[AdaptiveRule]
    ):
        self.student_repo = student_repo
        self.performance_repo = performance_repo
        self.knowledge_repo = knowledge_repo
        self.study_plan_repo = study_plan_repo
        self.cognitive_profile_repo = cognitive_profile_repo
        self.ai_service = ai_service
        self.adaptive_rules = adaptive_rules

    async def execute(self, student_id: UUID) -> StudyPlanOutputDTO:
        print("--- GenerateStudyPlanUseCase: START ---")
        try:
            # 1. Recuperar os dados necessários
            print("Step 1: Fetching data...")
            student = await self.student_repo.get_by_id(student_id)
            if not student:
                raise StudentNotFoundError(f"Estudante com ID {student_id} não encontrado.")
            print(f"Found student: {student.id}")

            cognitive_profile = await self.cognitive_profile_repo.get_by_student_id(student.id)
            if not cognitive_profile:
                raise CognitiveProfileNotFoundError(
                    f"Perfil cognitivo para o estudante com ID {student_id} não encontrado."
                )
            print(f"Found cognitive profile for student: {student.id}")

            recent_events = await self.performance_repo.get_recent_events(student_id)
            print(f"Found {len(recent_events)} recent events.")
            
            # TODO: Usar apenas os nós relevantes para o estudante
            all_nodes = await self.knowledge_repo.get_full_graph()
            print(f"Found {len(all_nodes)} total nodes in graph.")

            # 2. Instanciar o Domain Service para selecionar os nós
            print("Step 2: Instantiating StudyPlanGenerator...")
            generator = StudyPlanGenerator(
                knowledge_graph=all_nodes,
                adaptive_rules=self.adaptive_rules
            )
            print("StudyPlanGenerator instantiated.")

            # 3. Gerar o plano adaptativo (apenas a estrutura de nós)
            print("Step 3: Generating adaptive plan...")
            study_plan = generator.generate(
                student=student,
                cognitive_profile=cognitive_profile,
                performance_events=recent_events
            )
            print(f"Study plan generated with {len(study_plan.knowledge_nodes)} nodes.")

            # 4. Gerar conteúdo de estudo para cada nó com o serviço de IA
            print("Step 4: Generating study items with AI Service...")
            generated_contents = []
            for node in study_plan.knowledge_nodes:
                content = await self.ai_service.generate_flashcard(
                    topic=node.name,
                    difficulty=int(node.difficulty * 5),
                    context=f"Conteúdo sobre {node.name}" # Placeholder, idealmente viria do VectorDB
                )
                generated_contents.append(content)
                await asyncio.sleep(1) # Delay to avoid hitting rate limits
            print(f"Generated {len(generated_contents)} flashcards.")

            study_items = []
            for i, node in enumerate(study_plan.knowledge_nodes):
                content = generated_contents[i]
                item = StudyItemDTO(
                    id=node.id,
                    title=node.name,
                    type='flashcard',
                    difficulty=node.difficulty,
                    question=content['pergunta'],
                    options=content['opcoes'],
                    correct_index=content['correta_index'],
                    explanation=content['explicacao']
                )
                study_items.append(item)
            
            # 5. Persistir o novo plano (ainda sem o conteúdo gerado)
            print("Step 5: Saving study plan...")
            await self.study_plan_repo.save(study_plan)
            print("Study plan saved.")

            # 6. Retornar os dados formatados (DTO com conteúdo)
            print("Step 6: Formatting DTO...")
            dto = StudyPlanOutputDTO.from_entity(study_plan, study_items)
            print("--- GenerateStudyPlanUseCase: END ---")
            return dto

        except Exception as e:
            print(f"!!! UNEXPECTED ERROR in GenerateStudyPlanUseCase: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            raise e
