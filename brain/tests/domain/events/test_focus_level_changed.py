import pytest
from uuid import uuid4
from brain.domain.events.focus_level_changed import FocusLevelChanged
from brain.domain.entities.StudyPlan import StudyFocusLevel

def test_focus_level_changed_creation():
    aggregate_id = uuid4()  # student_id ou study_plan_id
    previous = StudyFocusLevel.NEW_CONTENT
    new = StudyFocusLevel.REVIEW

    event = FocusLevelChanged(
        aggregate_id=aggregate_id,
        previous_focus=previous,
        new_focus=new,
    )

    # Verifica campos específicos do evento
    assert event.aggregate_id == aggregate_id
    assert event.previous_focus == previous
    assert event.new_focus == new

    # Campos herdados do DomainEvent
    assert event.id is not None
    assert event.occurred_at is not None
    assert event.event_type == "FocusLevelChanged"
