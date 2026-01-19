from uuid import UUID
from typing import List
from datetime import datetime, timezone

from brain.domain.services.study_plan_generator import StudyPlanGenerator
from brain.domain.policies.adaptive_rule import AdaptiveRule
from brain.application.ports.repositories import (
    StudentRepository,
    PerformanceRepository,
    KnowledgeRepository,
    StudyPlanRepository
)
from brain.application.dto.study_plan_dto import StudyPlanOutputDTO


class StudentNotFoundError(Exception):
    """Exceção lançada quando um estudante não é encontrado no repositório."""
    pass


class GenerateStudyPlanUseCase:
    def __init__(
        self,
        student_repo: StudentRepository,
        performance_repo: PerformanceRepository,
        knowledge_repo: KnowledgeRepository,
        study_plan_repo: StudyPlanRepository,
        adaptive_rules: List[AdaptiveRule]
    ):
        self.student_repo = student_repo
        self.performance_repo = performance_repo
        self.knowledge_repo = knowledge_repo
        self.study_plan_repo = study_plan_repo
        self.adaptive_rules = adaptive_rules

    def execute(self, student_id: UUID) -> StudyPlanOutputDTO:
        # 1. Recuperar os dados necessários através das Ports (Repositórios)
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundError(f"Estudante com ID {student_id} não encontrado.")

        # Aqui assumimos que o perfil cognitivo vem com o estudante ou de repositório próprio
        # Para este exemplo, vamos extrair do perfil do estudante
        cognitive_profile = student.cognitive_profile 
        
        recent_events = self.performance_repo.get_recent_events(student_id)

        # Retrieve overdue nodes
        current_time = datetime.now(timezone.utc)
        overdue_nodes = self.knowledge_repo.get_overdue_nodes(current_time)

        # Retrieve all nodes to be used by the generator
        # The generator will prioritize overdue nodes
        all_nodes = self.knowledge_repo.get_full_graph()

        # Combine and prioritize overdue nodes
        # Ensure unique nodes and overdue nodes are at the top
        prioritized_nodes = []
        overdue_node_ids = {node.id for node in overdue_nodes}

        # Add overdue nodes first
        prioritized_nodes.extend(overdue_nodes)

        # Add remaining nodes, ensuring no duplicates
        for node in all_nodes:
            if node.id not in overdue_node_ids:
                prioritized_nodes.append(node)

        # 2. Instanciar o Domain Service (O Cérebro)
        generator = StudyPlanGenerator(
            knowledge_graph=prioritized_nodes, # Use prioritized nodes
            adaptive_rules=self.adaptive_rules
        )

        # 3. Gerar o plano adaptativo
        study_plan = generator.generate(
            student=student,
            cognitive_profile=cognitive_profile,
            performance_events=recent_events
        )

        # 4. Persistir o novo plano
        self.study_plan_repo.save(study_plan)

        # 5. Retornar os dados formatados (DTO)
        return StudyPlanOutputDTO.from_entity(study_plan)