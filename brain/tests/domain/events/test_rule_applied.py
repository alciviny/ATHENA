import pytest
from uuid import UUID

from brain.domain.events.rule_applied import RuleApplied


def test_rule_applied_creation():
    changes = {"focus_level": "REVIEW", "target_nodes": [1, 2]}
    aggregate_id = UUID("00000000-0000-0000-0000-000000000001")

    event = RuleApplied(
        aggregate_id=aggregate_id,
        rule_name="Low Accuracy High Difficulty",
        rule_description="Revisa nós difíceis quando acurácia está baixa",
        changes=changes,
    )

    # Verifica campos essenciais
    assert event.aggregate_id == aggregate_id
    assert event.rule_name == "Low Accuracy High Difficulty"
    assert event.rule_description.startswith("Revisa nós difíceis")
    assert event.changes == changes

    # Campos herdados do DomainEvent
    assert event.id is not None
    assert event.occurred_at is not None
    assert event.event_type == "RuleApplied"
