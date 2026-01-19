from typing import List, Dict
from uuid import UUID
from brain.application.ports.repositories import KnowledgeRepository
from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.domain.entities.student import Student
from brain.domain.entities.performance_event import PerformanceEvent

class MemoryAnalysisService:
    def __init__(self, engine: IntelligenceEngine, knowledge_repo: KnowledgeRepository):
        self.engine = engine
        self.knowledge_repo = knowledge_repo

    def get_student_memory_status(self, student: Student, history: List[PerformanceEvent]) -> List[Dict]:
        memory_report: List[Dict] = []
        
        topics = set(event.topic for event in history)
        
        for topic in topics:
            subject_history = self._filter_subject_history(history, topic)
            state = self.engine.analyze_memory_state(subject_history)
            
            node = self.knowledge_repo.get_node_by_title(topic)
            subject_name = node.title if node else "Unknown Subject"
            
            memory_report.append({
                "subject_id": str(topic), # Using topic as a unique identifier for reporting
                "subject_name": subject_name,
                "current_retention": state["current_retention"],
                "stability_days": state["stability_days"],
                "needs_review": state["needs_review"],
                "status": self._get_status_label(state["current_retention"], state["needs_review"]),
            })
        return memory_report

    def _filter_subject_history(self, history: List[PerformanceEvent], topic: str) -> List[PerformanceEvent]:
        return [event for event in history if event.topic == topic]

    def _get_status_label(self, retention: float, needs_review: bool) -> str:
        if needs_review:
            return "Crítico - Revisar Agora"
        if retention >= 0.90:
            return "Consolidado"
        if retention >= 0.80:
            return "Risco Moderado"
        return "Atenção"
