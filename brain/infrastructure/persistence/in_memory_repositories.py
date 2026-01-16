from uuid import UUID
from typing import List, Optional, Dict
from datetime import datetime
from brain.domain.entities.student import Student
from brain.domain.entities.PerformanceEvent import PerformanceEvent
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.StudyPlan import StudyPlan
from brain.domain.entities.error_event import ErrorEvent
from brain.application.ports.repositories import (
    StudentRepository,
    PerformanceRepository,
    KnowledgeRepository,
    StudyPlanRepository,
    ErrorEventRepository
)


class InMemoryStudentRepository(StudentRepository):
    def __init__(self):
        self.students: Dict[UUID, Student] = {}
    
    def get_by_id(self, student_id: UUID) -> Optional[Student]:
        return self.students.get(student_id)
    
    def save(self, student: Student) -> None:
        self.students[student.id] = student
    
    def delete(self, student_id: UUID) -> bool:
        """Remove a student from the repository."""
        if student_id in self.students:
            del self.students[student_id]
            return True
        return False
    
    def get_all(self) -> List[Student]:
        """Get all students."""
        return list(self.students.values())


class InMemoryPerformanceRepository(PerformanceRepository):
    def __init__(self):
        self.events: List[PerformanceEvent] = []
    
    def get_recent_events(self, student_id: UUID, limit: int = 50) -> List[PerformanceEvent]:
        """
        Get the most recent performance events for a student.
        Returns events sorted by timestamp (most recent last).
        """
        student_events = [e for e in self.events if e.student_id == student_id]
        # Sort by timestamp if available, otherwise maintain insertion order
        if student_events and hasattr(student_events[0], 'timestamp'):
            student_events.sort(key=lambda e: e.timestamp)
        return student_events[-limit:] if len(student_events) > limit else student_events
    
    def add_event(self, event: PerformanceEvent) -> None:
        self.events.append(event)
    
    def get_events_by_topic(self, student_id: UUID, topic: str) -> List[PerformanceEvent]:
        """Get all events for a specific topic and student."""
        return [
            e for e in self.events 
            if e.student_id == student_id and hasattr(e, 'topic') and e.topic == topic
        ]
    
    def clear_events(self, student_id: Optional[UUID] = None) -> None:
        """Clear events for a specific student or all events if no student_id provided."""
        if student_id:
            self.events = [e for e in self.events if e.student_id != student_id]
        else:
            self.events.clear()


class InMemoryKnowledgeRepository(KnowledgeRepository):
    def __init__(self):
        self.nodes: List[KnowledgeNode] = []
        self._nodes_by_id: Dict[UUID, KnowledgeNode] = {}
        self._nodes_by_subject: Dict[str, List[KnowledgeNode]] = {}
    
    def get_full_graph(self) -> List[KnowledgeNode]:
        """Get all knowledge nodes in the graph."""
        return self.nodes.copy()  # Return a copy to prevent external modifications
    
    def set_graph(self, nodes: List[KnowledgeNode]) -> None:
        """Replace the entire knowledge graph."""
        self.nodes = nodes.copy()
        self._nodes_by_id = {node.id: node for node in self.nodes}
        self._nodes_by_subject = {}
        for node in self.nodes:
            if node.subject not in self._nodes_by_subject:
                self._nodes_by_subject[node.subject] = []
            self._nodes_by_subject[node.subject].append(node)
    
    def get_node_by_id(self, node_id: UUID) -> Optional[KnowledgeNode]:
        """Get a specific knowledge node by its ID."""
        return self._nodes_by_id.get(node_id)
        
    def add_node(self, node: KnowledgeNode) -> None:
        """Add a single knowledge node to the graph."""
        if node.id not in self._nodes_by_id:
            self.nodes.append(node)
            self._nodes_by_id[node.id] = node
            if node.subject not in self._nodes_by_subject:
                self._nodes_by_subject[node.subject] = []
            self._nodes_by_subject[node.subject].append(node)

    def update_node(self, node: KnowledgeNode) -> bool:
        """Update an existing knowledge node."""
        if node.id in self._nodes_by_id:
            # Find and update in the main list
            for i, existing_node in enumerate(self.nodes):
                if existing_node.id == node.id:
                    self.nodes[i] = node
                    break
            # Update in the subject dictionary
            subject_nodes = self._nodes_by_subject.get(node.subject, [])
            for i, existing_node in enumerate(subject_nodes):
                if existing_node.id == node.id:
                    subject_nodes[i] = node
                    break
            self._nodes_by_id[node.id] = node
            return True
        return False

    def get_nodes_by_subject(self, subject: str) -> List[KnowledgeNode]:
        return self._nodes_by_subject.get(subject, [])


class InMemoryErrorEventRepository(ErrorEventRepository):
    def __init__(self, knowledge_repo: InMemoryKnowledgeRepository):
        self.errors: List[ErrorEvent] = []
        self.knowledge_repo = knowledge_repo

    def get_by_student_id(self, student_id: UUID) -> List[ErrorEvent]:
        return [error for error in self.errors if error.student_id == student_id]

    def get_by_student_and_subject(self, student_id: UUID, subject: str) -> List[ErrorEvent]:
        subject_nodes = self.knowledge_repo.get_nodes_by_subject(subject)
        subject_node_ids = {node.id for node in subject_nodes}
        
        return [
            error for error in self.errors 
            if error.student_id == student_id and error.knowledge_node_id in subject_node_ids
        ]
        
    def add_error(self, error: ErrorEvent):
        self.errors.append(error)


class InMemoryStudyPlanRepository(StudyPlanRepository):
    def __init__(self, verbose: bool = True):
        self.plans: Dict[UUID, StudyPlan] = {}
        self.verbose = verbose
    
    def save(self, study_plan: StudyPlan) -> None:
        self.plans[study_plan.id] = study_plan
        if self.verbose:
            print(f"[Infra] Plano de estudo {study_plan.id} salvo com sucesso para o aluno {study_plan.student_id}")
    
    def get_by_id(self, plan_id: UUID) -> Optional[StudyPlan]:
        return self.plans.get(plan_id)
    
    def get_by_student_id(self, student_id: UUID) -> List[StudyPlan]:
        """Get all study plans for a specific student."""
        return [plan for plan in self.plans.values() if plan.student_id == student_id]
    
    def get_active_plan(self, student_id: UUID) -> Optional[StudyPlan]:
        """Get the most recent or active study plan for a student."""
        student_plans = self.get_by_student_id(student_id)
        if not student_plans:
            return None
        # Return the most recently created plan
        if hasattr(student_plans[0], 'created_at'):
            return max(student_plans, key=lambda p: p.created_at)
        return student_plans[-1]
    
    def delete(self, plan_id: UUID) -> bool:
        """Delete a study plan."""
        if plan_id in self.plans:
            del self.plans[plan_id]
            return True
        return False
    
    def get_all(self) -> List[StudyPlan]:
        """Get all study plans."""
        return list(self.plans.values())
