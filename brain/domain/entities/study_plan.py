from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID
from enum import Enum

from brain.domain.entities.knowledge_node import KnowledgeNode


class StudyFocusLevel(str, Enum):
    """
    Estratégia principal do plano de estudo.
    """
    REVIEW = "review"
    NEW_CONTENT = "new_content"
    REINFORCEMENT = "reinforcement"


@dataclass(frozen=True)
class StudyPlan:
    """
    Plano de estudo gerado de forma adaptativa para o aluno.

    Consolida decisões baseadas no perfil cognitivo, histórico de erros
    e grafo de conhecimento.
    """
    id: UUID
    student_id: UUID
    created_at: datetime

    # Conteúdos selecionados do grafo
    knowledge_nodes: List[KnowledgeNode] = field(default_factory=list)

    # Duração estimada total do plano
    estimated_duration_minutes: int = 0

    focus_level: StudyFocusLevel = StudyFocusLevel.REVIEW

    # ==============================
    # Domain Semantics
    # ==============================

    def is_review_plan(self) -> bool:
        """
        Indica se o plano é focado em revisão.
        """
        return self.focus_level == StudyFocusLevel.REVIEW

    def is_new_content_plan(self) -> bool:
        """
        Indica se o plano introduz novos conteúdos.
        """
        return self.focus_level == StudyFocusLevel.NEW_CONTENT

    def is_reinforcement_plan(self) -> bool:
        """
        Indica se o plano é focado em reforço.
        """
        return self.focus_level == StudyFocusLevel.REINFORCEMENT

    def estimated_duration_hours(self) -> float:
        """
        Retorna a duração estimada do plano em horas.
        """
        return self.estimated_duration_minutes / 60.0
