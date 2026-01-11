from brain.domain.services.study_plan_generator import StudyPlanGenerator
from brain.domain.entities.StudyPlan import StudyFocusLevel
from brain.domain.entities.PerformanceEvent import PerformanceMetric

from brain.domain.policies.rules.low_accuracy_high_difficulty import (
    LowAccuracyHighDifficultyRule,
)
from brain.domain.policies.rules.retention_drop_rule import RetentionDropRule
from brain.domain.policies.rules.overload_prevention_rule import (
    OverloadPreventionRule,
    MAX_NODES,
)

from brain.tests.domain.fakes import (
    fake_student,
    fake_cognitive_profile,
    fake_performance_event,
    fake_knowledge_node,
)


def test_generates_new_content_plan_when_no_weak_metrics():
    generator = StudyPlanGenerator(
        knowledge_graph=[
            fake_knowledge_node(),
            fake_knowledge_node(),
        ],
        adaptive_rules=[],
    )

    plan = generator.generate(
        student=fake_student(),
        cognitive_profile=fake_cognitive_profile(),
        performance_events=[],
    )

    assert plan.focus_level == StudyFocusLevel.NEW_CONTENT
    assert len(plan.knowledge_nodes) > 0


def test_low_accuracy_high_difficulty_forces_review_and_filters_nodes():
    generator = StudyPlanGenerator(
        knowledge_graph=[
            fake_knowledge_node(difficulty=0.8),
            fake_knowledge_node(difficulty=0.3),
        ],
        adaptive_rules=[LowAccuracyHighDifficultyRule],
    )

    plan = generator.generate(
        student=fake_student(),
        cognitive_profile=fake_cognitive_profile(),
        performance_events=[
            fake_performance_event(metric=PerformanceMetric.ACCURACY)
        ],
    )

    assert plan.focus_level == StudyFocusLevel.REVIEW
    assert len(plan.knowledge_nodes) == 1


def test_retention_drop_prioritizes_high_impact_nodes():
    generator = StudyPlanGenerator(
        knowledge_graph=[
            fake_knowledge_node(weight_in_exam=0.8),
            fake_knowledge_node(weight_in_exam=0.3),
        ],
        adaptive_rules=[RetentionDropRule],
    )

    plan = generator.generate(
        student=fake_student(),
        cognitive_profile=fake_cognitive_profile(),
        performance_events=[
            fake_performance_event(metric=PerformanceMetric.RETENTION)
        ],
    )

    assert plan.focus_level == StudyFocusLevel.REVIEW
    assert len(plan.knowledge_nodes) == 1


def test_overload_prevention_limits_number_of_nodes():
    generator = StudyPlanGenerator(
        knowledge_graph=[
            fake_knowledge_node(weight_in_exam=0.8) for _ in range(10)
        ],
        adaptive_rules=[OverloadPreventionRule],
    )

    plan = generator.generate(
        student=fake_student(),
        cognitive_profile=fake_cognitive_profile(),
        performance_events=[],
    )

    assert len(plan.knowledge_nodes) <= MAX_NODES
