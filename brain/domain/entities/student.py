from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import datetime


@dataclass(frozen=True)
class Student:
    """
    Entidade de domínio que representa um aluno do sistema.
    Atua como Aggregate Root.
    """
    id: UUID
    name: str
    email: str
    password_hash: str
    goal: str
    is_active: bool = True
    created_at: datetime = None
    last_login_at: Optional[datetime] = None
    cognitive_profile_id: Optional[UUID] = None

    def __post_init__(self):
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.utcnow())

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

    def is_authenticated(self) -> bool:
        """
        Verifica se o aluno está ativo e pode se autenticar.
        """
        return self.is_active

    def update_last_login(self) -> 'Student':
        """
        Atualiza a data do último login.
        """
        return Student(
            id=self.id,
            name=self.name,
            email=self.email,
            password_hash=self.password_hash,
            goal=self.goal,
            is_active=self.is_active,
            created_at=self.created_at,
            last_login_at=datetime.utcnow(),
            cognitive_profile_id=self.cognitive_profile_id
        )
