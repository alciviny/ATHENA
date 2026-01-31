from sqlalchemy import Column, String, Float, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from brain.infrastructure.persistence.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Integer, DateTime

# Tabela de associação para dependências (Muitos-para-Muitos)
node_dependencies = Table(
    "node_dependencies",
    Base.metadata,
    Column("parent_id", UUID(as_uuid=True), ForeignKey("knowledge_nodes.id"), primary_key=True),
    Column("child_id", UUID(as_uuid=True), ForeignKey("knowledge_nodes.id"), primary_key=True),
)

class KnowledgeNodeModel(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    description = Column(String)
    difficulty = Column(Float, default=0.5)
    
    # Nível Sénior: Peso de recorrência em provas (0.0 a 1.0)
    importance_weight = Column(Float, default=1.0)
    
    # Nível Sénior: Tempo estimado de estudo em minutos
    estimated_study_time = Column(Float, default=30.0)
    
    # Campos adicionais esperados pelos testes
    weight_in_exam = Column(Float, default=0.0)
    weight = Column(Float, default=1.0)
    stability = Column(Float, default=1.0)
    reps = Column(Integer, default=0)
    lapses = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)

    # Relacionamento de Dependência: Um nó "filho" depende de nós "pais"
    dependencies = relationship(
        "KnowledgeNodeModel",
        secondary=node_dependencies,
        primaryjoin=id == node_dependencies.c.child_id,
        secondaryjoin=id == node_dependencies.c.parent_id,
        backref="dependents"
    )


# -------------------------------
# Modelos mínimos para testes
# -------------------------------
class CognitiveProfileModel(Base):
    __tablename__ = "cognitive_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False)
    retention_rate = Column(Float, default=0.5)
    learning_speed = Column(Float, default=0.5)
    stress_sensitivity = Column(Float, default=0.5)
    # Campo opcional para armazenar padrões de erro ou metadados relacionados
    error_patterns = Column(JSON, nullable=True)


class StudentModel(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    goal = Column(String, nullable=True)

    # Relação opcional com CognitiveProfileModel
    cognitive_profile_id = Column(UUID(as_uuid=True), ForeignKey("cognitive_profiles.id"))
    cognitive_profile = relationship("CognitiveProfileModel", uselist=False)


class PerformanceEventModel(Base):
    __tablename__ = "performance_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String, nullable=False)
    occurred_at = Column(String, nullable=False)
    topic = Column(String, nullable=True)
    metric = Column(String, nullable=False)
    value = Column(Float, default=0.0)
    baseline = Column(Float, default=0.0)
    event_metadata = Column(String, nullable=True)


class StudyPlanModel(Base):
    __tablename__ = "study_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False)
    # Usa DateTime com timezone para compatibilidade com objetos datetime timezone-aware
    created_at = Column(DateTime(timezone=True), nullable=False)
    # Armazena lista de IDs de nós (JSON) para compatibilidade com os repositórios de teste
    knowledge_nodes = Column(JSON, nullable=True)
    estimated_duration_minutes = Column(Float, default=0.0)
    focus_level = Column(String, default="REVIEW")


class ErrorEventModel(Base):
    __tablename__ = "error_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False)
    subject = Column(String, nullable=True)
    details = Column(String, nullable=True)
