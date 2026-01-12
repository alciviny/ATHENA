from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Table, JSON, Integer
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
    cognitive_profile_id = Column(UUID(as_uuid=True), nullable=True) #

class KnowledgeNodeModel(Base):
    __tablename__ = "knowledge_nodes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)         #
    subject = Column(String, nullable=False)      #
    weight_in_exam = Column(Float, nullable=False) #
    difficulty = Column(Float, nullable=False)     #
    
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
    occurred_at = Column(DateTime, nullable=False) #
    topic = Column(String, nullable=False)      #
    metric = Column(String, nullable=False)     #
    value = Column(Float, nullable=False)       #
    baseline = Column(Float, nullable=False)    #

class StudyPlanModel(Base):
    __tablename__ = "study_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    knowledge_nodes = Column(JSON, nullable=False) # Lista de UUIDs
    estimated_duration_minutes = Column(Integer, default=0) #
    focus_level = Column(String, nullable=False) #