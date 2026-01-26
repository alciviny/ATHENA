from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Table, JSON, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .database import Base

# Tabela de associação para as dependências do Grafo de Conhecimento
node_dependencies = Table(
    'node_dependencies',
    Base.metadata,
    Column('node_id', UUID(as_uuid=True), ForeignKey('knowledge_nodes.id'), primary_key=True),
    Column('dependency_id', UUID(as_uuid=True), ForeignKey('knowledge_nodes.id'), primary_key=True)
)

class StudentModel(Base):
    __tablename__ = "students"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    goal = Column(String, nullable=False)  # Armazena o valor do StudentGoal Enum
    
    # Relação 1-para-1: Um estudante tem um perfil cognitivo.
    cognitive_profile = relationship("CognitiveProfileModel", back_populates="student", uselist=False)

class CognitiveProfileModel(Base):
    __tablename__ = "cognitive_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, unique=True)
    retention_rate = Column(Float, nullable=False, default=0.7)
    learning_speed = Column(Float, nullable=False, default=0.5)
    stress_sensitivity = Column(Float, nullable=False, default=0.3)
    error_patterns = Column(JSON, nullable=False, default={})

    # Relação de volta para o estudante
    student = relationship("StudentModel", back_populates="cognitive_profile")

class KnowledgeNodeModel(Base):
    __tablename__ = "knowledge_nodes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)         #
    subject = Column(String, nullable=False)      #
    weight_in_exam = Column(Float, nullable=False) #
    weight = Column(Float, default=1.0) #
    difficulty = Column(Float, default=5.0)     #
    # FSRS fields
    stability = Column(Float, default=0.0)
    reps = Column(Integer, default=0)
    lapses = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_at = Column(DateTime(timezone=True), default=func.now())
    
    dependencies = relationship(
        "KnowledgeNodeModel",
        secondary=node_dependencies,
        primaryjoin=id == node_dependencies.c.node_id,
        secondaryjoin=id == node_dependencies.c.dependency_id,
        backref="required_by"
    )

class PerformanceEventModel(Base):
    __tablename__ = "performance_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    event_type = Column(String, nullable=False) #
    occurred_at = Column(DateTime(timezone=True), nullable=False) #
    topic = Column(String, nullable=False)      #
    metric = Column(String, nullable=False)     #
    value = Column(Float, nullable=False)       #
    baseline = Column(Float, nullable=False)    #
    event_metadata = Column(JSON, nullable=True, default={})

class StudyPlanModel(Base):
    __tablename__ = "study_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    knowledge_nodes = Column(JSON, nullable=False) # Lista de UUIDs
    estimated_duration_minutes = Column(Integer, default=0) #
    focus_level = Column(String, nullable=False) #

class ErrorEventModel(Base):
    __tablename__ = "error_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    knowledge_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_nodes.id"), nullable=False)
    error_type = Column(String, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    severity = Column(Float, nullable=False)