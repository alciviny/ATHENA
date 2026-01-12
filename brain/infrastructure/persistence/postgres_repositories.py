from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from brain.application.ports.repositories import (
    KnowledgeRepository,
    PerformanceRepository,
    StudyPlanRepository,
)
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.PerformanceEvent import (
    PerformanceEvent,
    PerformanceEventType,
    PerformanceMetric,
)
from brain.domain.entities.StudyPlan import StudyPlan, StudyFocusLevel

from .models import KnowledgeNodeModel, PerformanceEventModel, StudyPlanModel


class PostgresKnowledgeRepository(KnowledgeRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_full_graph(self) -> List[KnowledgeNode]:
        models = self.db.query(KnowledgeNodeModel).all()
        return [self._to_entity(m) for m in models]

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