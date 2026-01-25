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
        # 1. Recuperar os dados necessários através das Ports (Repositórios)
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundError(f"Estudante com ID {student_id} não encontrado.")

        cognitive_profile = await self.cognitive_profile_repo.get_by_student_id(student.id)
        if not cognitive_profile:
            raise CognitiveProfileNotFoundError(
                f"Perfil cognitivo para o estudante com ID {student_id} não encontrado."
            )
        
        recent_events = await self.performance_repo.get_recent_events(student_id)

        # Retrieve overdue nodes
        current_time = datetime.now(timezone.utc)
        overdue_nodes = await self.knowledge_repo.get_overdue_nodes(current_time)

        # Retrieve all nodes to be used by the generator
        all_nodes = await self.knowledge_repo.get_full_graph()

        # Combine and prioritize overdue nodes
        prioritized_nodes = []
        overdue_node_ids = {node.id for node in overdue_nodes}
        prioritized_nodes.extend(overdue_nodes)
        for node in all_nodes:
            if node.id not in overdue_node_ids:
                prioritized_nodes.append(node)

        # 2. Instanciar o Domain Service (O Cérebro)
        generator = StudyPlanGenerator(
            knowledge_graph=prioritized_nodes,
            adaptive_rules=self.adaptive_rules
        )

        # 3. Gerar o plano adaptativo
        study_plan = generator.generate(
            student=student,
            cognitive_profile=cognitive_profile,
            performance_events=recent_events
        )

        # 4. Persistir o novo plano
        await self.study_plan_repo.save(study_plan)

        # 5. Retornar os dados formatados (DTO)
        return StudyPlanOutputDTO.from_entity(study_plan)
