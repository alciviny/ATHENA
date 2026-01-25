import sys
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
from brain.application.dto.study_plan_dto import StudyPlanOutputDTO


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
        adaptive_rules: List[AdaptiveRule]
    ):
        self.student_repo = student_repo
        self.performance_repo = performance_repo
        self.knowledge_repo = knowledge_repo
        self.study_plan_repo = study_plan_repo
        self.cognitive_profile_repo = cognitive_profile_repo
        self.adaptive_rules = adaptive_rules

    async def execute(self, student_id: UUID) -> StudyPlanOutputDTO:
        print("--- GenerateStudyPlanUseCase: START ---")
        try:
            # 1. Recuperar os dados necessários através das Ports (Repositórios)
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

            current_time = datetime.now(timezone.utc)
            overdue_nodes = await self.knowledge_repo.get_overdue_nodes(current_time)
            print(f"Found {len(overdue_nodes)} overdue nodes.")

            all_nodes = await self.knowledge_repo.get_full_graph()
            print(f"Found {len(all_nodes)} total nodes in graph.")

            prioritized_nodes = []
            overdue_node_ids = {node.id for node in overdue_nodes}
            prioritized_nodes.extend(overdue_nodes)
            for node in all_nodes:
                if node.id not in overdue_node_ids:
                    prioritized_nodes.append(node)
            print(f"Total prioritized nodes: {len(prioritized_nodes)}")

            # 2. Instanciar o Domain Service (O Cérebro)
            print("Step 2: Instantiating StudyPlanGenerator...")
            generator = StudyPlanGenerator(
                knowledge_graph=prioritized_nodes,
                adaptive_rules=self.adaptive_rules
            )
            print("StudyPlanGenerator instantiated.")

            # 3. Gerar o plano adaptativo
            print("Step 3: Generating adaptive plan...")
            study_plan = generator.generate(
                student=student,
                cognitive_profile=cognitive_profile,
                performance_events=recent_events
            )
            print(f"Study plan generated with {len(study_plan.knowledge_nodes)} nodes.")

            # 4. Persistir o novo plano
            print("Step 4: Saving study plan...")
            await self.study_plan_repo.save(study_plan)
            print("Study plan saved.")

            # 5. Retornar os dados formatados (DTO)
            print("Step 5: Formatting DTO...")
            dto = StudyPlanOutputDTO.from_entity(study_plan)
            print("--- GenerateStudyPlanUseCase: END ---")
            return dto

        except Exception as e:
            print(f"!!! UNEXPECTED ERROR in GenerateStudyPlanUseCase: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            raise e
