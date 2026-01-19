import unittest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime

from brain.application.services.memory_analysis_service import MemoryAnalysisService
from brain.domain.entities.student import Student, StudentGoal
from brain.domain.entities.performance_event import PerformanceEvent, PerformanceEventType, PerformanceMetric
from brain.domain.entities.knowledge_node import KnowledgeNode

class TestMemoryAnalysisService(unittest.TestCase):

    def setUp(self):
        self.engine = MagicMock()
        self.knowledge_repo = MagicMock()
        self.service = MemoryAnalysisService(self.engine, self.knowledge_repo)

        # Entities
        self.student_id = uuid4()
        self.student = Student(
            id=self.student_id,
            name="Test Student",
            goal=StudentGoal.INSS # Use a valid goal
        )
        
        self.node_1 = KnowledgeNode(id=uuid4(), title="Math")
        self.node_2 = KnowledgeNode(id=uuid4(), title="History")

        # Mock Performance History
        self.history = [
            PerformanceEvent(
                id=uuid4(), student_id=self.student_id,
                event_type=PerformanceEventType.STUDY_SESSION,
                occurred_at=datetime.now(),
                topic=self.node_1.title,
                metric=PerformanceMetric.ACCURACY,
                value=0.9,
                baseline=0.9
            ),
            PerformanceEvent(
                id=uuid4(), student_id=self.student_id,
                event_type=PerformanceEventType.STUDY_SESSION,
                occurred_at=datetime.now(),
                topic=self.node_2.title,
                metric=PerformanceMetric.ACCURACY,
                value=0.7,
                baseline=0.7
            ),
             PerformanceEvent(
                id=uuid4(), student_id=self.student_id,
                event_type=PerformanceEventType.STUDY_SESSION,
                occurred_at=datetime.now(),
                topic=self.node_1.title,
                metric=PerformanceMetric.ACCURACY,
                value=0.95,
                baseline=0.95
            ),
        ]

    def test_get_student_memory_status(self):
        # Configure mock return values
        self.engine.analyze_memory_state.side_effect = [
            # State for first subject analyzed
            { "current_retention": 0.92, "stability_days": 15, "needs_review": False },
            # State for second subject analyzed
            { "current_retention": 0.75, "stability_days": 3, "needs_review": True }
        ]
        
        def get_node_by_title_side_effect(title):
            if title == self.node_1.title:
                return self.node_1
            if title == self.node_2.title:
                return self.node_2
            return None
            
        self.knowledge_repo.get_node_by_title.side_effect = get_node_by_title_side_effect

        # Execute
        memory_report = self.service.get_student_memory_status(self.student, self.history)

        # Assertions
        self.assertEqual(len(memory_report), 2)
        self.assertEqual(self.engine.analyze_memory_state.call_count, 2)
        self.assertEqual(self.knowledge_repo.get_node_by_title.call_count, 2)
        
        # Sort reports to have a predictable order for assertions
        # because the order of processing from a set is not guaranteed.
        memory_report.sort(key=lambda r: r['subject_name'])

        # Report for Subject 1 (History) - assuming 'H' comes before 'M'
        report_1 = memory_report[0]
        self.assertEqual(report_1["subject_name"], "History")
        self.assertEqual(report_1["current_retention"], 0.75)
        self.assertEqual(report_1["stability_days"], 3)
        self.assertTrue(report_1["needs_review"])
        self.assertEqual(report_1["status"], "Crítico - Revisar Agora")

        # Report for Subject 2 (Math)
        report_2 = memory_report[1]
        self.assertEqual(report_2["subject_name"], "Math")
        self.assertEqual(report_2["current_retention"], 0.92)
        self.assertEqual(report_2["stability_days"], 15)
        self.assertFalse(report_2["needs_review"])
        self.assertEqual(report_2["status"], "Consolidado")


if __name__ == '__main__':
    unittest.main()
