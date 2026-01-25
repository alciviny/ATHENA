from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from brain.domain.entities.student import Student
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.PerformanceEvent import PerformanceEvent
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.study_plan import StudyPlan
from brain.domain.entities.error_event import ErrorEvent

class StudentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, student_id: UUID) -> Optional[Student]:
        pass

class PerformanceRepository(ABC):
    @abstractmethod
    async def get_recent_events(self, student_id: UUID, limit: int = 50) -> List[PerformanceEvent]:
        pass

    @abstractmethod
    async def get_history_for_student(self, student_id: UUID) -> List[PerformanceEvent]:
        pass

    @abstractmethod
    async def get_history(self, student_id: UUID, node_id: UUID) -> List[PerformanceEvent]:
        pass

    @abstractmethod
    async def save(self, event: PerformanceEvent) -> None:
        pass

class KnowledgeRepository(ABC):
    @abstractmethod
    async def get_full_graph(self) -> List[KnowledgeNode]:
        pass

    @abstractmethod
    async def get_overdue_nodes(self, current_time: datetime) -> List[KnowledgeNode]:
        pass

    @abstractmethod
    async def get_node_by_name(self, name: str) -> Optional[KnowledgeNode]:
        pass

    @abstractmethod
    async def get_by_id(self, node_id: UUID) -> Optional[KnowledgeNode]:
        pass
    
    @abstractmethod
    async def update(self, node: KnowledgeNode) -> None:
        pass
    
    @abstractmethod
    async def save(self, node: KnowledgeNode) -> None:
        pass

class StudyPlanRepository(ABC):
    @abstractmethod
    async def save(self, study_plan: StudyPlan) -> None:
        pass

class CognitiveProfileRepository(ABC):
    @abstractmethod
    async def get_by_student_id(self, student_id: UUID) -> Optional[CognitiveProfile]:
        pass
        
    @abstractmethod
    async def save(self, profile: CognitiveProfile) -> None:
        pass

class ErrorEventRepository(ABC):
    @abstractmethod
    async def get_by_student_id(self, student_id: UUID) -> List[ErrorEvent]:
        pass
    
    @abstractmethod
    async def get_by_student_and_subject(self, student_id: UUID, subject: str) -> List[ErrorEvent]:
        pass


class KnowledgeVectorRepository(ABC):
    """
    Porta de acesso ao mecanismo de busca vetorial (Qdrant, Pinecone, etc).

    Responsável exclusivamente por operações de similaridade semântica.
    Nenhuma regra de negócio deve viver aqui.
    """
    @abstractmethod
    async def find_semantically_related(
        self,
        reference_node_id: UUID,
        *,
        limit: int = 5
    ) -> List[UUID]:
        """
        Retorna IDs de nós semanticamente próximos ao nó de referência.

        Args:
            reference_node_id: ID do nó base no espaço vetorial.
            limit: Número máximo de vizinhos retornados.

        Returns:
            Lista de UUIDs de nós semanticamente relacionados.
        """
        raise NotImplementedError