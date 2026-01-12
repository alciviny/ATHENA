from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from brain.application.ports.repositories import (
    KnowledgeRepository,
    PerformanceRepository,
    StudyPlanRepository,
    StudentRepository,
)
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.student import Student
from brain.domain.entities.PerformanceEvent import (
    PerformanceEvent,
    PerformanceEventType,
    PerformanceMetric,
)
from brain.domain.entities.StudyPlan import StudyPlan, StudyFocusLevel

from .models import KnowledgeNodeModel, PerformanceEventModel, StudentModel, StudyPlanModel


class PostgresKnowledgeRepository(KnowledgeRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_full_graph(self) -> List[KnowledgeNode]:
        models = self.db.query(KnowledgeNodeModel).all()
        return [self._to_entity(m) for m in models]

    def set_graph(self, nodes: List[KnowledgeNode]) -> None:
        """Implementação necessária para o seeder funcionar com Postgres"""
        for node in nodes:
            model = KnowledgeNodeModel(
                id=node.id,
                name=node.name,
                subject=node.subject,
                weight_in_exam=node.weight_in_exam,
                difficulty=node.difficulty
            )
            # O merge faz o 'upsert' (insere se não existir, atualiza se existir)
            self.db.merge(model)
        # Após todos os nós serem adicionados/atualizados, configuramos as dependências
        for node in nodes:
            if node.dependencies:
                model = self.db.query(KnowledgeNodeModel).get(node.id)
                if model:
                    # Limpa dependências existentes para evitar duplicatas
                    model.dependencies.clear()
                    # Adiciona as novas dependências
                    for dep_id in node.dependencies:
                        dep_model = self.db.query(KnowledgeNodeModel).get(dep_id)
                        if dep_model:
                            model.dependencies.append(dep_model)


    def _to_entity(self, model: KnowledgeNodeModel) -> KnowledgeNode:
        return KnowledgeNode(
            id=model.id,
            name=model.name,
            subject=model.subject,
            weight_in_exam=model.weight_in_exam,
            difficulty=model.difficulty,
            # Carrega os IDs das dependências a partir do relacionamento do SQLAlchemy
            dependencies=[dep.id for dep in model.dependencies],
        )


class PostgresStudentRepository(StudentRepository):
    def __init__(self, db: Session):
        self.db = db

    def add(self, student: Student) -> None:
        model = StudentModel(
            id=student.id,
            name=student.name,
            goal=student.goal.value,  # Armazena o valor do enum
            cognitive_profile_id=student.cognitive_profile_id,
        )
        self.db.add(model)

    def get_by_id(self, student_id: UUID) -> Student | None:
        model = self.db.query(StudentModel).get(student_id)
        if model:
            return self._to_entity(model)
        return None

    def _to_entity(self, model: StudentModel) -> Student:
        from brain.domain.entities.student import StudentGoal
        return Student(
            id=model.id, 
            name=model.name, 
            goal=StudentGoal(model.goal),
            cognitive_profile_id=model.cognitive_profile_id
        )




class PostgresPerformanceRepository(PerformanceRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_recent_events(
        self, student_id: UUID, limit: int = 50
    ) -> List[PerformanceEvent]:
        models = (
            self.db.query(PerformanceEventModel)
            .filter(PerformanceEventModel.student_id == student_id)
            .order_by(PerformanceEventModel.occurred_at.desc())
            .limit(limit)
            .all()
        )

        return [self._to_entity(m) for m in reversed(models)]

    def add_event(self, event: PerformanceEvent) -> None:
        model = PerformanceEventModel(
            id=event.id,
            student_id=event.student_id,
            event_type=event.event_type.value,
            occurred_at=event.occurred_at,
            topic=event.topic,
            metric=event.metric.value,
            value=event.value,
            baseline=event.baseline,
        )
        self.db.add(model)

    def _to_entity(self, model: PerformanceEventModel) -> PerformanceEvent:
        return PerformanceEvent(
            id=model.id,
            student_id=model.student_id,
            event_type=PerformanceEventType(model.event_type),
            occurred_at=model.occurred_at,
            topic=model.topic,
            metric=PerformanceMetric(model.metric),
            value=model.value,
            baseline=model.baseline,
        )


class PostgresStudyPlanRepository(StudyPlanRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, study_plan: StudyPlan) -> None:
        model = StudyPlanModel(
            id=study_plan.id,
            student_id=study_plan.student_id,
            created_at=study_plan.created_at,
            knowledge_nodes=study_plan.knowledge_nodes,  # Postgres lida bem com JSON/Lista
            estimated_duration_minutes=study_plan.estimated_duration_minutes,
            focus_level=study_plan.focus_level.value,
        )
        self.db.merge(model)

    def get_active_plan(self, student_id: UUID) -> StudyPlan | None:
        model = (
            self.db.query(StudyPlanModel)
            .filter(StudyPlanModel.student_id == student_id)
            .order_by(StudyPlanModel.created_at.desc())  # Pega o mais novo primeiro
            .first()
        )
        if not model:
            return None
        return self._to_entity(model)
    
    def _to_entity(self, model: StudyPlanModel) -> StudyPlan:
        return StudyPlan(
            id=model.id,
            student_id=model.student_id,
            created_at=model.created_at,
            knowledge_nodes=model.knowledge_nodes,
            estimated_duration_minutes=model.estimated_duration_minutes,
            focus_level=StudyFocusLevel(model.focus_level)
        )