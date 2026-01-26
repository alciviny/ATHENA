import pytest
from uuid import uuid4
from brain.domain.events.performance_analyzed import PerformanceAnalyzed
from brain.domain.entities.performance_event import PerformanceMetric

def test_performance_analyzed_creation():
    aggregate_id = uuid4()  # student_id
    weak_metrics = [PerformanceMetric.ACCURACY, PerformanceMetric.RETENTION]

    event = PerformanceAnalyzed(
        aggregate_id=aggregate_id,
        weak_metrics=weak_metrics,
    )

    # Verifica campos específicos do evento
    assert event.aggregate_id == aggregate_id
    assert event.weak_metrics == weak_metrics

    # Campos herdados do DomainEvent
    assert event.id is not None
    assert event.occurred_at is not None
    assert event.event_type == "PerformanceAnalyzed"
