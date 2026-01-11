import pytest
from uuid import uuid4
from brain.domain.events.study_plan_generated import StudyPlanGenerated
from brain.domain.entities.StudyPlan import StudyFocusLevel

def test_study_plan_generated_creation():
    aggregate_id = uuid4()
    nodes = [uuid4(), uuid4()]
    focus = StudyFocusLevel.REVIEW
    duration = 50

    event = StudyPlanGenerated(
        aggregate_id=aggregate_id,
        knowledge_nodes=nodes,
        focus_level=focus,
        estimated_duration_minutes=duration,
    )

    # Verifica campos específicos
    assert event.aggregate_id == aggregate_id
    assert event.knowledge_nodes == nodes
    assert event.focus_level == focus
    assert event.estimated_duration_minutes == duration

    # Campos herdados de DomainEvent
    assert event.id is not None
    assert event.occurred_at is not None
    assert event.event_type == "StudyPlanGenerated"
