from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from enum import Enum


class StudentGoal(str, Enum):
    """
    Objetivo principal do aluno.
    Pode ser expandido conforme novos concursos forem adicionados.
    """
    POLICIA_FEDERAL = "Polícia Federal"
    INSS = "INSS"
    RECEITA_FEDERAL = "Receita Federal"
    TRF = "TRF"


@dataclass(frozen=True)
class Student:
    """
    Entidade de domínio que representa um aluno do sistema.
    Atua como Aggregate Root.
    """
    id: UUID
    name: str
    goal: StudentGoal
    cognitive_profile_id: Optional[UUID] = None

    def has_cognitive_profile(self) -> bool:
        """
        Indica se o aluno já possui um perfil cognitivo associado.
        """
        return self.cognitive_profile_id is not None

    def requires_diagnostic(self) -> bool:
        """
        Regra de domínio explícita:
        Se não há perfil cognitivo, o aluno precisa passar por diagnóstico.
        """
        return not self.has_cognitive_profile()
