from uuid import UUID
from typing import List, Optional, Dict
from datetime import datetime

# Importações de Entidades
from brain.domain.entities.student import Student
from brain.domain.entities.performance_event import PerformanceEvent
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.study_plan import StudyPlan
from brain.domain.entities.error_event import ErrorEvent
from brain.domain.entities.cognitive_profile import CognitiveProfile

# Importações de Portas
from brain.application.ports.repositories import (
    StudentRepository,
    PerformanceRepository,
    KnowledgeRepository,
    StudyPlanRepository,
    CognitiveProfileRepository,
    ErrorEventRepository
)

class InMemoryStudentRepository(StudentRepository):
    def __init__(self):
        self.students: Dict[UUID, Student] = {}
    
    async def get_by_id(self, student_id: UUID) -> Optional[Student]:
        return self.students.get(student_id)
    
    async def save(self, student: Student) -> None:
        self.students[student.id] = student

class InMemoryPerformanceRepository(PerformanceRepository):
    def __init__(self):
        self.events: List[PerformanceEvent] = []
    
    async def get_recent_events(self, student_id: UUID, limit: int = 50) -> List[PerformanceEvent]:
        student_events = [e for e in self.events if e.student_id == student_id]
        if student_events and hasattr(student_events[0], 'timestamp'):
            student_events.sort(key=lambda e: e.timestamp)
        return student_events[-limit:]

    # Método genérico exigido pelo contrato
    async def get_history_for_student(self, student_id: UUID) -> List[PerformanceEvent]:
        return [e for e in self.events if e.student_id == student_id]

    # Método específico chamado pelo RecordReviewUseCase (Atenção aqui!)
    async def get_history(self, student_id: UUID, node_id: UUID) -> List[PerformanceEvent]:
        """Recupera histórico específico de um nó para cálculo de tendência."""
        return [
            e for e in self.events 
            if e.student_id == student_id and getattr(e, 'knowledge_node_id', None) == node_id
        ]
    
    async def save(self, event: PerformanceEvent) -> None:
        self.events.append(event)

class InMemoryKnowledgeRepository(KnowledgeRepository):
    def __init__(self):
        self.nodes: List[KnowledgeNode] = []
        self._nodes_by_id: Dict[UUID, KnowledgeNode] = {}
        self._nodes_by_subject: Dict[str, List[KnowledgeNode]] = {}
    
    async def get_full_graph(self) -> List[KnowledgeNode]:
        return self.nodes.copy()
    
    async def get_overdue_nodes(self, current_time: datetime) -> List[KnowledgeNode]:
        return [
            node for node in self.nodes 
            if hasattr(node, 'next_review_at') and node.next_review_at and node.next_review_at <= current_time
        ]

    async def get_by_id(self, node_id: UUID) -> Optional[KnowledgeNode]:
        return self._nodes_by_id.get(node_id)
    
    async def get_node_by_name(self, name: str) -> Optional[KnowledgeNode]:
        for node in self.nodes:
            if node.name == name:
                return node
        return None
        
    async def get_node_by_title(self, title: str) -> Optional[KnowledgeNode]:
        for node in self.nodes:
            if node.title == title:
                return node
        return None
        
    async def save(self, node: KnowledgeNode) -> None:
        """Upsert assíncrono."""
        # Atualiza dicionário principal
        self._nodes_by_id[node.id] = node
        
        # Atualiza lista linear (se existir, substitui; se não, adiciona)
        found = False
        for i, n in enumerate(self.nodes):
            if n.id == node.id:
                self.nodes[i] = node
                found = True
                break
        if not found:
            self.nodes.append(node)

        # Atualiza índice por subject
        subject = getattr(node, 'subject', 'general')
        if subject not in self._nodes_by_subject:
            self._nodes_by_subject[subject] = []
        
        # Remove versão antiga do subject list se existir e adiciona nova
        self._nodes_by_subject[subject] = [
            n for n in self._nodes_by_subject[subject] if n.id != node.id
        ]
        self._nodes_by_subject[subject].append(node)

    # Alias assíncrono para compatibilidade com 'add' se o contrato pedir
    add = save 
    
    async def update(self, node: KnowledgeNode) -> None:
        await self.save(node)

class InMemoryCognitiveProfileRepository(CognitiveProfileRepository):
    def __init__(self):
        self._profiles: Dict[UUID, CognitiveProfile] = {}

    async def get_by_student_id(self, student_id: UUID) -> Optional[CognitiveProfile]:
        return self._profiles.get(student_id)

    async def save(self, profile: CognitiveProfile) -> None:
        self._profiles[profile.student_id] = profile

class InMemoryStudyPlanRepository(StudyPlanRepository):
    def __init__(self):
        self.plans: Dict[UUID, StudyPlan] = {}
    
    async def save(self, study_plan: StudyPlan) -> None:
        self.plans[study_plan.id] = study_plan
    
    async def get_by_student_id(self, student_id: UUID) -> List[StudyPlan]:
        return [p for p in self.plans.values() if p.student_id == student_id]

class InMemoryErrorEventRepository(ErrorEventRepository):
    def __init__(self):
        self.errors: List[ErrorEvent] = []

    async def get_by_student_id(self, student_id: UUID) -> List[ErrorEvent]:
        return [e for e in self.errors if e.student_id == student_id]
    
    async def get_by_student_and_subject(self, student_id: UUID, subject: str) -> List[ErrorEvent]:
        # Implementação simplificada para mock
        return [e for e in self.errors if e.student_id == student_id]