from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class StudyItemDTO(BaseModel):
    id: str
    type: str
    content: Dict[str, Any]
    estimated_time_minutes: int
    difficulty: float
    status: str = "pending"

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