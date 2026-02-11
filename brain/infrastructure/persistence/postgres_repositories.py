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
from brain.domain.entities.student import Student
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
                email=student_model.email,
                password_hash=student_model.password_hash,
                goal=student_model.goal,
                is_active=bool(student_model.is_active),
                created_at=student_model.created_at,
                last_login_at=student_model.last_login_at,
                cognitive_profile_id=student_model.cognitive_profile.id if student_model.cognitive_profile else None,
            )
        return None

    async def get_by_email(self, email: str) -> Optional[Student]:
        """Get student by email for authentication."""
        query = (
            select(StudentModel)
            .options(selectinload(StudentModel.cognitive_profile))
            .filter(StudentModel.email == email)
        )
        result = await self.db.execute(query)
        student_model = result.scalars().first()
        if student_model:
            return Student(
                id=student_model.id,
                name=student_model.name,
                email=student_model.email,
                password_hash=student_model.password_hash,
                goal=student_model.goal,
                is_active=bool(student_model.is_active),
                created_at=student_model.created_at,
                last_login_at=student_model.last_login_at,
                cognitive_profile_id=student_model.cognitive_profile.id if student_model.cognitive_profile else None,
            )
        return None

    async def update_last_login(self, student_id: UUID) -> None:
        """Update the last login timestamp for a student."""
        query = (
            select(StudentModel)
            .filter(StudentModel.id == student_id)
        )
        result = await self.db.execute(query)
        student_model = result.scalars().first()
        if student_model:
            student_model.last_login_at = datetime.utcnow()
            await self.db.commit()

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
                root_cause=model.root_cause,
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
                root_cause=model.root_cause,
                event_metadata=model.event_metadata or {},
            )
            for model in event_models
        ]

    async def get_history(self, student_id: UUID, node_id: UUID) -> List[PerformanceEvent]:
        """
        Recupera histórico de performance para um estudante e nó específico.
        Filtra por student_id e usa node_id para matching com topic ou event_metadata.
        """
        from sqlalchemy import select
        
        # Query para buscar eventos filtrando por estudante
        stmt = select(PerformanceEventModel).where(
            PerformanceEventModel.student_id == student_id
        ).order_by(PerformanceEventModel.occurred_at.desc())
        
        result = await self.db.execute(stmt)
        event_models = result.scalars().all()
        
        # Filtrar eventos relacionados ao node_id
        # Pode ser através do topic (se for o nome/id do nó) ou event_metadata
        filtered_events = []
        for model in event_models:
            # Verificar se o node_id está no topic ou em event_metadata
            if (model.topic and str(node_id) in model.topic) or \
               (model.event_metadata and str(node_id) in str(model.event_metadata)):
                filtered_events.append(model)
        
        # Converter para entidades de domínio
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
                root_cause=model.root_cause,
                event_metadata=model.event_metadata or {},
            )
            for model in filtered_events
        ]
        
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
            root_cause=event.root_cause,
            event_metadata=event.event_metadata,
        )
        self.db.add(model)
        await self.db.flush()


class PostgresKnowledgeRepository(ports.KnowledgeRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_full_graph(self) -> List[KnowledgeNode]:
        query = select(KnowledgeNodeModel).options(
            selectinload(KnowledgeNodeModel.dependencies)
        )
        result = await self.db.execute(query)
        node_models = result.scalars().unique().all()
        return [
            KnowledgeNode(
                id=model.id,
                name=model.name,
                subject=model.subject,
                content=model.description or "",  # Mapeia description para content
                dependency_ids=[dep.id for dep in model.dependencies],
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
                content=model.description or "",  # Mapeia description para content
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
                content=model.description or "",  # Mapeia description para content
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
                content=model.description or "",  # Mapeia description para content
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
            model.description = node.content  # Mapeia content para description
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
            model.description = node.content  # Mapeia content para description
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
                description=node.content,  # Mapeia content para description
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
            knowledge_nodes=[
                str(node.id) if hasattr(node, "id") else str(node)
                for node in study_plan.knowledge_nodes
            ],
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

    def _model_to_entity(self, model: ErrorEventModel) -> ErrorEvent:
        """Converte modelo ORM em entidade de domínio com defaults seguros."""
        from brain.domain.entities.error_event import ErrorType
        from datetime import datetime, timezone

        return ErrorEvent(
            id=model.id,
            student_id=model.student_id,
            knowledge_node_id=model.knowledge_node_id or model.student_id,  # fallback
            error_type=ErrorType(model.error_type) if model.error_type else ErrorType.CONTEUDO,
            occurred_at=model.occurred_at or datetime.now(timezone.utc),
            severity=model.severity if model.severity is not None else 0.5,
        )

    async def get_by_student_id(self, student_id: UUID) -> List[ErrorEvent]:
        result = await self.db.execute(
            select(ErrorEventModel).filter(ErrorEventModel.student_id == student_id)
        )
        return [self._model_to_entity(m) for m in result.scalars().all()]

    async def get_by_student_and_subject(self, student_id: UUID, subject: str) -> List[ErrorEvent]:
        # JOIN com KnowledgeNodeModel para filtrar por subject do nó
        result = await self.db.execute(
            select(ErrorEventModel)
            .join(KnowledgeNodeModel, ErrorEventModel.knowledge_node_id == KnowledgeNodeModel.id)
            .filter(
                ErrorEventModel.student_id == student_id,
                KnowledgeNodeModel.subject == subject,
            )
        )
        return [self._model_to_entity(m) for m in result.scalars().all()]
