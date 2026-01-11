from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from brain.domain.entities.student import Student
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.PerformanceEvent import PerformanceEvent
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.StudyPlan import StudyPlan

class StudentRepository(ABC):
    @abstractmethod
    def get_by_id(self, student_id: UUID) -> Optional[Student]:
        pass

class PerformanceRepository(ABC):
    @abstractmethod
    def get_recent_events(self, student_id: UUID, limit: int = 50) -> List[PerformanceEvent]:
        pass

class KnowledgeRepository(ABC):
    @abstractmethod
    def get_full_graph(self) -> List[KnowledgeNode]:
        pass

class StudyPlanRepository(ABC):
    @abstractmethod
    def save(self, study_plan: StudyPlan) -> None:
        pass