import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock

from brain.infrastructure.persistence.postgres_repositories import (
    PostgresPerformanceRepository,
    PostgresStudentRepository,
    PostgresKnowledgeRepository,
    PostgresStudyPlanRepository,
)
from brain.infrastructure.persistence.models import (
    PerformanceEventModel,
    StudentModel,
    KnowledgeNodeModel,
)
from brain.domain.entities.performance_event import PerformanceEvent, PerformanceEventType, PerformanceMetric
from brain.domain.entities.student import Student, StudentGoal
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.study_plan import StudyPlan

# Mock da sessão do banco de dados para testes
@pytest.fixture
def db_session_mock(mocker):
    mock_result = MagicMock()
    session_mock = mocker.AsyncMock()
    session_mock.execute.return_value = mock_result
    return session_mock

# ==================================
# Testes para PostgresPerformanceRepository
# ==================================

async def test_get_recent_events_returns_empty_list(db_session_mock):
    student_id = uuid4()
    db_session_mock.execute.return_value.scalars.return_value.all.return_value = []
    repo = PostgresPerformanceRepository(db=db_session_mock)
    events = await repo.get_recent_events(student_id=student_id)
    assert events == []

async def test_get_recent_events_returns_events(db_session_mock):
    student_id = uuid4()
    event_id = uuid4()
    mock_event_model = PerformanceEventModel(
        id=event_id, student_id=student_id, event_type=PerformanceEventType.QUIZ.value,
        occurred_at=datetime.now(timezone.utc), topic="Math", metric=PerformanceMetric.ACCURACY.value,
        value=0.8, baseline=0.7
    )
    db_session_mock.execute.return_value.scalars.return_value.all.return_value = [mock_event_model]
    repo = PostgresPerformanceRepository(db=db_session_mock)
    events = await repo.get_recent_events(student_id=student_id)
    assert len(events) == 1
    assert isinstance(events[0], PerformanceEvent)
    assert events[0].id == event_id

# ==================================
# Testes para PostgresStudentRepository
# ==================================

@pytest.mark.asyncio
async def test_student_repo_get_by_id_found(db_session_mock):
    student_id = uuid4()
    mock_student_model = StudentModel(id=student_id, name="Test Student", goal=StudentGoal.POLICIA_FEDERAL)
    db_session_mock.execute.return_value.scalars.return_value.first.return_value = mock_student_model
    
    repo = PostgresStudentRepository(db=db_session_mock)
    student = await repo.get_by_id(student_id)

    assert student is not None
    assert isinstance(student, Student)
    assert student.id == student_id
    assert student.name == "Test Student"

@pytest.mark.asyncio
async def test_student_repo_get_by_id_not_found(db_session_mock):
    student_id = uuid4()
    db_session_mock.execute.return_value.scalars.return_value.first.return_value = None
    
    repo = PostgresStudentRepository(db=db_session_mock)
    student = await repo.get_by_id(student_id)

    assert student is None

# ==================================
# Testes para PostgresKnowledgeRepository
# ==================================

@pytest.mark.asyncio
async def test_knowledge_repo_get_by_id_found(db_session_mock):
    node_id = uuid4()
    mock_node_model = KnowledgeNodeModel(
        id=node_id, name="Test Node", subject="Test Subject", difficulty=5.0, stability=2.0
    )
    db_session_mock.execute.return_value.scalars.return_value.first.return_value = mock_node_model
    
    repo = PostgresKnowledgeRepository(db=db_session_mock)
    node = await repo.get_by_id(node_id)
    
    assert node is not None
    assert isinstance(node, KnowledgeNode)
    assert node.id == node_id
    assert node.name == "Test Node"

# ==================================
# Testes para PostgresStudyPlanRepository
# ==================================

@pytest.mark.asyncio
async def test_study_plan_repo_save(db_session_mock):
    student_id = uuid4()
    plan_id = uuid4()
    study_plan = StudyPlan(id=plan_id, student_id=student_id, knowledge_nodes=[uuid4()], created_at=datetime.now(timezone.utc))
    
    repo = PostgresStudyPlanRepository(db=db_session_mock)
    await repo.save(study_plan)
    
    # Verifica se os métodos da sessão foram chamados, indicando a tentativa de salvar
    db_session_mock.add.assert_called_once()
    db_session_mock.flush.assert_awaited_once()

    # Pega o objeto que foi passado para 'add' e verifica seus dados
    added_object = db_session_mock.add.call_args[0][0]
    assert added_object.id == plan_id
    assert added_object.student_id == student_id