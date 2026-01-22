# brain/infrastructure/persistence/postgres_repositories.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from brain.application.ports import repositories as ports
from brain.infrastructure.persistence.models import (
    StudentModel,
    CognitiveProfileModel,
    KnowledgeNodeModel,
    PerformanceEventModel,
    StudyPlanModel,
    ErrorEventModel
)
from brain.domain.entities.student import Student, StudentGoal
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.performance_event import PerformanceEvent
from brain.domain.entities.error_event import ErrorEvent
from brain.domain.entities.study_plan import StudyPlan


class PostgresStudentRepository(ports.StudentRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, student_id: UUID) -> Optional[Student]:
        student_model = self.db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if student_model:
            return Student(
                id=student_model.id,
                name=student_model.name,
                goal=StudentGoal(student_model.goal),
                cognitive_profile_id=student_model.cognitive_profile_id,
            )
        return None

class PostgresPerformanceRepository(ports.PerformanceRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_recent_events(self, student_id: UUID, limit: int = 50) -> List[PerformanceEvent]:
        event_models = (
            self.db.query(PerformanceEventModel)
            .filter(PerformanceEventModel.student_id == student_id)
            .order_by(PerformanceEventModel.occurred_at.desc())
            .limit(limit)
            .all()
        )
        if not event_models:
            return []

        return [
            PerformanceEvent(
                id=model.id,
                student_id=model.student_id,
                event_type=model.event_type,
                occurred_at=model.occurred_at,
                topic=model.topic,
                metric=model.metric,
                value=model.value,
                baseline=model.baseline,
            )
            for model in event_models
        ]

    def get_history_for_student(self, student_id: UUID) -> List[PerformanceEvent]:
        pass

from brain.domain.entities.knowledge_node import KnowledgeNode

class PostgresKnowledgeRepository(ports.KnowledgeRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_full_graph(self) -> List[KnowledgeNode]:
        node_models = self.db.query(KnowledgeNodeModel).all()
        return [
            KnowledgeNode(
                id=model.id,
                title=model.name,
                stability=model.stability,
                difficulty=model.difficulty,
                reps=model.reps,
                lapses=model.lapses,
                last_review=model.last_review,
                next_review=model.next_review,
            )
            for model in node_models
        ]

    def get_overdue_nodes(self, current_time: datetime) -> List[KnowledgeNode]:
        node_models = self.db.query(KnowledgeNodeModel).filter(KnowledgeNodeModel.next_review <= current_time).all()
        return [
            KnowledgeNode(
                id=model.id,
                title=model.name,
                stability=model.stability,
                difficulty=model.difficulty,
                reps=model.reps,
                lapses=model.lapses,
                last_review=model.last_review,
                next_review=model.next_review,
            )
            for model in node_models
        ]

    def get_node_by_title(self, title: str) -> Optional[KnowledgeNode]:
        pass

    # Added to satisfy RecordReviewUseCase
    def get_by_id(self, node_id: UUID) -> Optional[KnowledgeNode]:
        pass
    
    # Added to satisfy RecordReviewUseCase
    def update(self, node: KnowledgeNode) -> None:
        pass


class PostgresStudyPlanRepository(ports.StudyPlanRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, study_plan: StudyPlan) -> None:
        print(f"--- FAKE: Saving study plan {study_plan.id} to Postgres ---")
        pass

class PostgresCognitiveProfileRepository(ports.CognitiveProfileRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_student_id(self, student_id: UUID) -> Optional[CognitiveProfile]:
        model = self.db.query(CognitiveProfileModel).filter(CognitiveProfileModel.student_id == student_id).first()
        if model:
            return CognitiveProfile(
                id=model.id,
                student_id=model.student_id,
                retention_rate=model.retention_rate,
                learning_speed=model.learning_speed,
                stress_sensitivity=model.stress_sensitivity,
                error_patterns=model.error_patterns or {}
            )
        return None

    def save(self, profile: CognitiveProfile) -> None:
        model = self.db.query(CognitiveProfileModel).filter(CognitiveProfileModel.id == profile.id).first()
        if not model:
            model = CognitiveProfileModel(
                id=profile.id,
                student_id=profile.student_id,
                retention_rate=profile.retention_rate,
                learning_speed=profile.learning_speed,
                stress_sensitivity=profile.stress_sensitivity,
                error_patterns=profile.error_patterns
            )
            self.db.add(model)
        else:
            model.retention_rate = profile.retention_rate
            model.learning_speed = profile.learning_speed
            model.stress_sensitivity = profile.stress_sensitivity
            model.error_patterns = profile.error_patterns
        self.db.flush()

class PostgresErrorEventRepository(ports.ErrorEventRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_student_id(self, student_id: UUID) -> List[ErrorEvent]:
        pass
    
    def get_by_student_and_subject(self, student_id: UUID, subject: str) -> List[ErrorEvent]:
        pass
