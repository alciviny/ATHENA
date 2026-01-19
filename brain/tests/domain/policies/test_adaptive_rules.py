from brain.domain.entities.study_plan import StudyFocusLevel
from brain.domain.entities.performance_event import PerformanceMetric

from brain.domain.policies.rules.low_accuracy_high_difficulty import (
    LowAccuracyHighDifficultyRule,
)

from brain.tests.domain.fakes import fake_knowledge_node


def test_low_accuracy_high_difficulty_rule_applies_correctly():
    high_difficulty_node = fake_knowledge_node(difficulty=8.0)
    low_difficulty_node = fake_knowledge_node(difficulty=3.0)

    context = {
        "weak_metrics": [PerformanceMetric.ACCURACY],
        "target_nodes": [
            high_difficulty_node,
            low_difficulty_node,
        ],
        "focus_level": StudyFocusLevel.NEW_CONTENT,
    }

    # Act — avalia condição
    should_apply = LowAccuracyHighDifficultyRule.should_apply(context)

    assert should_apply is True

    # Act — aplica regra
    LowAccuracyHighDifficultyRule.apply(context)

    # Assert — foco forçado para revisão
    assert context["focus_level"] == StudyFocusLevel.REVIEW

    # Assert — apenas nós de alta dificuldade permanecem
    assert context["target_nodes"] == [high_difficulty_node]
