from dataclasses import dataclass, field
from typing import List
from uuid import UUID


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Garante que um valor esteja dentro de um intervalo seguro.
    """
    return max(min_value, min(max_value, value))


@dataclass
class KnowledgeNode:
    """
    Nó do Grafo de Conhecimento.

    Representa um tópico, assunto ou conceito cobrado em prova,
    incluindo sua importância, dificuldade percebida e dependências.
    """
    id: UUID
    name: str
    subject: str

    # Métricas normalizadas (0.0 - 1.0)
    weight_in_exam: float      # impacto na nota final
    difficulty: float          # dificuldade percebida pelo aluno médio

    # Dependências (outros KnowledgeNodes)
    dependencies: List[UUID] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Normaliza automaticamente os valores críticos.
        """
        self.weight_in_exam = _clamp(self.weight_in_exam)
        self.difficulty = _clamp(self.difficulty)

    # ==============================
    # Domain Rules
    # ==============================

    def is_high_impact(self, threshold: float = 0.7) -> bool:
        """
        Indica se o nó possui alto impacto na prova.
        """
        return self.weight_in_exam >= threshold

    def is_high_difficulty(self, threshold: float = 0.7) -> bool:
        """
        Indica se o nó é considerado difícil.
        """
        return self.difficulty >= threshold

    def is_foundational(self) -> bool:
        """
        Um nó fundacional não depende de outros conhecimentos.
        """
        return len(self.dependencies) == 0

    # ==============================
    # Graph Semantics
    # ==============================

    def can_be_studied_after(self, completed_nodes: List[UUID]) -> bool:
        """
        Verifica se todas as dependências deste nó já foram concluídas.
        """
        return all(dep in completed_nodes for dep in self.dependencies)
