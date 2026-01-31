from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from enum import Enum


class StudyPlanType(str, Enum):
    LEARNING = "learning"
    REVISION = "revision"
    EXAM = "exam"


class StudyItemDTO(BaseModel):
    id: str
    type: str
    content: Dict[str, Any]
    topic_roi: str # Explicação estratégica para o aluno
    estimated_time_minutes: int
    status: str


class StudySessionDTO(BaseModel):
    id: str
    topic: str
    start_time: datetime
    duration_minutes: int
    items: List[StudyItemDTO]
    # MUDANÇA CRÍTICA: De 'int' para 'str' para aceitar o Enum convertido
    focus_level: str 
    method: str = "pomodoro"


class StudyPlanDTO(BaseModel):
    id: str
    student_id: str
    goals: List[str]
    created_at: datetime
    sessions: List[StudySessionDTO]
    status: str
    # Novo campo: tipo do plano (EXAM para simuladores)
    plan_type: Optional[StudyPlanType] = StudyPlanType.LEARNING
    # Tempo limite global para sessões do tipo EXAM (em segundos)
    time_limit_seconds: Optional[int] = None


# Compatibilidade com testes antigos: DTO de saída simplificado
class StudyPlanOutputDTO(BaseModel):
    id: UUID
    student_id: UUID
    knowledge_nodes: List[UUID]
    created_at: datetime
    estimated_duration_minutes: int
    focus_level: str
    # Flashcards gerados para cada nó (opcional)
    flashcards: Optional[List[Dict[str, Any]]] = None
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }