# brain/infrastructure/persistence/postgres_repositories.py

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import selectinload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from brain.domain.entities.performance_event import PerformanceEvent, PerformanceEventType, PerformanceMetric
from brain.domain.entities.error_event import ErrorEvent
from brain.domain.entities.study_plan import StudyPlan
from brain.domain.entities.knowledge_node import KnowledgeNode


class PostgresStudentRepository(ports.StudentRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, student_id: UUID) -> Optional[Student]:
        query = (
            select(StudentModel)
            .options(selectinload(StudentModel.cognitive_profile))
            .filter(StudentModel.id == student_id)
        )
        result = await self.db.execute(query)
        student_model = result.scalars().first()
        if student_model:
            return Student(
                id=student_model.id,
                name=student_model.name,
                goal=StudentGoal(student_model.goal),
                cognitive_profile_id=student_model.cognitive_profile.id if student_model.cognitive_profile else None,
            )
        return None

class PostgresPerformanceRepository(ports.PerformanceRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_events(self, student_id: UUID, limit: int = 50) -> List[PerformanceEvent]:
        result = await self.db.execute(
            select(PerformanceEventModel)
            .filter(PerformanceEventModel.student_id == student_id)
            .order_by(PerformanceEventModel.occurred_at.desc())
            .limit(limit)
        )
        event_models = result.scalars().all()
        return [
            PerformanceEvent(
                id=model.id,
                student_id=model.student_id,
                event_type=PerformanceEventType(model.event_type),
                occurred_at=model.occurred_at,
                topic=model.topic,
                metric=PerformanceMetric(model.metric),
                value=model.value,
                baseline=model.baseline,
                event_metadata=model.event_metadata or {},
            )
            for model in event_models
        ]

    async def get_history_for_student(self, student_id: UUID) -> List[PerformanceEvent]:
        result = await self.db.execute(
            select(PerformanceEventModel)
            .filter(PerformanceEventModel.student_id == student_id)
            .order_by(PerformanceEventModel.occurred_at.desc())
        )
        event_models = result.scalars().all()
        return [
            PerformanceEvent(
                id=model.id,
                student_id=model.student_id,
                event_type=PerformanceEventType(model.event_type),
                occurred_at=model.occurred_at,
                topic=model.topic,
                metric=PerformanceMetric(model.metric),
                value=model.value,
                baseline=model.baseline,
                event_metadata=model.event_metadata or {},
            )
            for model in event_models
        ]

    async def get_history(self, student_id: UUID, node_id: UUID) -> List[PerformanceEvent]:
        # Placeholder implementation
        return []
        
    async def save(self, event: PerformanceEvent) -> None:
        model = PerformanceEventModel(
            id=event.id,
            student_id=event.student_id,
            event_type=event.event_type.value,
            occurred_at=event.occurred_at,
            topic=event.topic,
            metric=event.metric.value,
            value=event.value,
            baseline=event.baseline,
            event_metadata=event.event_metadata,
        )
        self.db.add(model)
        await self.db.flush()


class PostgresKnowledgeRepository(ports.KnowledgeRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_full_graph(self) -> List[KnowledgeNode]:
        result = await self.db.execute(select(KnowledgeNodeModel))
        node_models = result.scalars().all()
        return [
            KnowledgeNode(
                id=model.id,
                name=model.name,
                subject=model.subject,
                weight_in_exam=model.weight_in_exam,
                weight=model.weight,
                stability=model.stability,
                difficulty=model.difficulty,
                reps=model.reps,
                lapses=model.lapses,
                last_reviewed_at=model.last_reviewed_at,
                next_review_at=model.next_review_at,
            )
            for model in node_models
        ]

    async def get_overdue_nodes(self, current_time: datetime) -> List[KnowledgeNode]:
        result = await self.db.execute(select(KnowledgeNodeModel).filter(KnowledgeNodeModel.next_review_at <= current_time))
        node_models = result.scalars().all()
        return [
            KnowledgeNode(
                id=model.id,
                name=model.name,
                subject=model.subject,
                weight_in_exam=model.weight_in_exam,
                weight=model.weight,
                stability=model.stability,
                difficulty=model.difficulty,
                reps=model.reps,
                lapses=model.lapses,
                last_reviewed_at=model.last_reviewed_at,
                next_review_at=model.next_review_at,
            )
            for model in node_models
        ]

    async def get_node_by_name(self, name: str) -> Optional[KnowledgeNode]:
        result = await self.db.execute(select(KnowledgeNodeModel).filter(KnowledgeNodeModel.name == name))
        model = result.scalars().first()
        if model:
            return KnowledgeNode(
                id=model.id,
                name=model.name,
                subject=model.subject,
                weight_in_exam=model.weight_in_exam,
                weight=model.weight,
                stability=model.stability,
                difficulty=model.difficulty,
                reps=model.reps,
                lapses=model.lapses,
                last_reviewed_at=model.last_reviewed_at,
                next_review_at=model.next_review_at,
            )
        return None

    async def get_by_id(self, node_id: UUID) -> Optional[KnowledgeNode]:
        result = await self.db.execute(select(KnowledgeNodeModel).filter(KnowledgeNodeModel.id == node_id))
        model = result.scalars().first()
        if model:
            return KnowledgeNode(
                id=model.id,
                name=model.name,
                subject=model.subject,
                weight_in_exam=model.weight_in_exam,
                weight=model.weight,
                stability=model.stability,
                difficulty=model.difficulty,
                reps=model.reps,
                lapses=model.lapses,
                last_reviewed_at=model.last_reviewed_at,
                next_review_at=model.next_review_at,
            )
        return None
    
    async def update(self, node: KnowledgeNode) -> None:
        result = await self.db.execute(select(KnowledgeNodeModel).filter(KnowledgeNodeModel.id == node.id))
        model = result.scalars().first()
        if model:
            model.stability = node.stability
            model.difficulty = node.difficulty
            model.reps = node.reps
            model.lapses = node.lapses
            model.last_reviewed_at = node.last_reviewed_at
            model.next_review_at = node.next_review_at
            model.weight = node.weight
            await self.db.flush()

    async def save(self, node: KnowledgeNode) -> None:
        # This is an upsert
        result = await self.db.execute(select(KnowledgeNodeModel).filter(KnowledgeNodeModel.id == node.id))
        model = result.scalars().first()
        if model:
            model.stability = node.stability
            model.difficulty = node.difficulty
            model.reps = node.reps
            model.lapses = node.lapses
            model.last_reviewed_at = node.last_reviewed_at
            model.next_review_at = node.next_review_at
            model.weight = node.weight
        else:
            model = KnowledgeNodeModel(
                id=node.id,
                name=node.name,
                subject=node.subject,
                weight_in_exam=node.weight_in_exam,
                stability=node.stability,
                difficulty=node.difficulty,
                reps=node.reps,
                lapses=node.lapses,
                last_reviewed_at=node.last_reviewed_at,
                next_review_at=node.next_review_at,
            )
            self.db.add(model)
        await self.db.flush()


class PostgresStudyPlanRepository(ports.StudyPlanRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, study_plan: StudyPlan) -> None:
        model = StudyPlanModel(
            id=study_plan.id,
            student_id=study_plan.student_id,
            created_at=study_plan.created_at,
            knowledge_nodes=[str(node_id) for node_id in study_plan.knowledge_nodes],
            estimated_duration_minutes=study_plan.estimated_duration_minutes,
            focus_level=study_plan.focus_level.value
        )
        self.db.add(model)
        await self.db.flush()

class PostgresCognitiveProfileRepository(ports.CognitiveProfileRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_student_id(self, student_id: UUID) -> Optional[CognitiveProfile]:
        result = await self.db.execute(select(CognitiveProfileModel).filter(CognitiveProfileModel.student_id == student_id))
        model = result.scalars().first()
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

    async def save(self, profile: CognitiveProfile) -> None:
        result = await self.db.execute(select(CognitiveProfileModel).filter(CognitiveProfileModel.id == profile.id))
        model = result.scalars().first()
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
        await self.db.flush()

class PostgresErrorEventRepository(ports.ErrorEventRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_student_id(self, student_id: UUID) -> List[ErrorEvent]:
        result = await self.db.execute(select(ErrorEventModel).filter(ErrorEventModel.student_id == student_id))
        error_models = result.scalars().all()
        return [
            ErrorEvent(
                id=model.id,
                student_id=model.student_id,
                knowledge_node_id=model.knowledge_node_id,
                error_type=model.error_type,
                occurred_at=model.occurred_at,
                severity=model.severity,
            )
            for model in error_models
        ]

    async def get_by_student_and_subject(self, student_id: UUID, subject: str) -> List[ErrorEvent]:
        result = await self.db.execute(
            select(ErrorEventModel)
            .join(KnowledgeNodeModel, ErrorEventModel.knowledge_node_id == KnowledgeNodeModel.id)
            .filter(
                ErrorEventModel.student_id == student_id,
                KnowledgeNodeModel.subject == subject,
            )
        )
        error_models = result.scalars().all()
        return [
            ErrorEvent(
                id=model.id,
                student_id=model.student_id,
                knowledge_node_id=model.knowledge_node_id,
                error_type=model.error_type,
                occurred_at=model.occurred_at,
                severity=model.severity,
            )
            for model in error_models
        ]
