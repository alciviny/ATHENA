
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from brain.infrastructure.persistence.postgres_repositories import PostgresPerformanceRepository
from brain.infrastructure.persistence.models import PerformanceEventModel
from brain.domain.entities.performance_event import PerformanceEvent, PerformanceEventType, PerformanceMetric

# Mock da sessão do banco de dados para testes
@pytest.fixture
def db_session_mock(mocker):
    return mocker.MagicMock()

def test_get_recent_events_returns_empty_list(db_session_mock):
    # Arrange
    student_id = uuid4()
    db_session_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    repo = PostgresPerformanceRepository(db=db_session_mock)

    # Act
    events = repo.get_recent_events(student_id=student_id)

    # Assert
    assert events == []

def test_get_recent_events_returns_events(db_session_mock):
    # Arrange
    student_id = uuid4()
    event_id = uuid4()
    event_time = datetime.now(timezone.utc)
    
    mock_event_model = PerformanceEventModel(
        id=event_id,
        student_id=student_id,
        event_type=PerformanceEventType.QUIZ.value,
        occurred_at=event_time,
        topic="Math",
        metric=PerformanceMetric.ACCURACY.value,
        value=0.8,
        baseline=0.7
    )
    
    db_session_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_event_model]
    repo = PostgresPerformanceRepository(db=db_session_mock)

    # Act
    events = repo.get_recent_events(student_id=student_id)

    # Assert
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, PerformanceEvent)
    assert event.id == event_id
    assert event.student_id == student_id
    assert event.topic == "Math"

