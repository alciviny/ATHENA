import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime

from brain.application.services.memory_analysis_service import MemoryAnalysisService
from brain.domain.entities.student import Student, StudentGoal
from brain.domain.entities.performance_event import PerformanceEvent, PerformanceEventType, PerformanceMetric
from brain.domain.entities.knowledge_node import KnowledgeNode

# Fixture to set up the test data
@pytest.fixture
def setup_data():
    student_id = uuid4()
    student = Student(id=student_id, name="Test Student", goal=StudentGoal.INSS)
    node_1 = KnowledgeNode(id=uuid4(), name="Math", subject="Math")
    node_2 = KnowledgeNode(id=uuid4(), name="History", subject="History")
    history = [
        PerformanceEvent(
            id=uuid4(), student_id=student_id,
            event_type=PerformanceEventType.STUDY_SESSION,
            occurred_at=datetime.now(),
            topic=node_1.name,
            metric=PerformanceMetric.ACCURACY,
            value=0.9,
            baseline=0.9
        ),
        PerformanceEvent(
            id=uuid4(), student_id=student_id,
            event_type=PerformanceEventType.STUDY_SESSION,
            occurred_at=datetime.now(),
            topic=node_2.name,
            metric=PerformanceMetric.ACCURACY,
            value=0.7,
            baseline=0.7
        ),
        PerformanceEvent(
            id=uuid4(), student_id=student_id,
            event_type=PerformanceEventType.STUDY_SESSION,
            occurred_at=datetime.now(),
            topic=node_1.name,
            metric=PerformanceMetric.ACCURACY,
            value=0.95,
            baseline=0.95
        ),
    ]
    return student, history, node_1, node_2

async def test_get_student_memory_status(setup_data):
    student, history, node_1, node_2 = setup_data
    
    engine = MagicMock()
    # Mocking an async method requires an AsyncMock
    knowledge_repo = MagicMock()
    knowledge_repo.get_node_by_name = AsyncMock()

    service = MemoryAnalysisService(engine, knowledge_repo)
    
    # Configure mock return values
    def analyze_memory_side_effect(subject_history):
        topic = subject_history[0].topic
        if topic == "Math":
            return { "current_retention": 0.92, "stability_days": 15, "needs_review": False }
        elif topic == "History":
            return { "current_retention": 0.75, "stability_days": 3, "needs_review": True }
        return {}

    engine.analyze_memory_state.side_effect = analyze_memory_side_effect
    
    async def get_node_by_name_side_effect(name):
        if name == node_1.name:
            return node_1
        if name == node_2.name:
            return node_2
        return None
        
    knowledge_repo.get_node_by_name.side_effect = get_node_by_name_side_effect

    # Execute
    memory_report = await service.get_student_memory_status(student, history)

    # Assertions
    assert len(memory_report) == 2
    assert engine.analyze_memory_state.call_count == 2
    assert knowledge_repo.get_node_by_name.call_count == 2
    
    # Sort reports to have a predictable order for assertions
    memory_report.sort(key=lambda r: r['subject_name'])

    # Report for Subject 1 (History) - 'History' comes before 'Math'
    report_1 = memory_report[0]
    assert report_1["subject_name"] == "History"
    assert report_1["current_retention"] == 0.75
    assert report_1["stability_days"] == 3
    assert report_1["needs_review"] is True
    assert report_1["status"] == "Crítico - Revisar Agora"

    # Report for Subject 2 (Math)
    report_2 = memory_report[1]
    assert report_2["subject_name"] == "Math"
    assert report_2["current_retention"] == 0.92
    assert report_2["stability_days"] == 15
    assert report_2["needs_review"] is False
    assert report_2["status"] == "Consolidado"

