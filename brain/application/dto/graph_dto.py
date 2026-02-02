from pydantic import BaseModel, Field
from uuid import UUID
from typing import List

class GraphNodeDTO(BaseModel):
    id: UUID
    name: str
    roi_score: float = Field(..., description="Normalized ROI score between 0.0 and 1.0")
    status: str
    weight: float = Field(..., description="Importance weight in exams")
    difficulty: float
    stability: float

    class Config:
        orm_mode = True

class GraphLinkDTO(BaseModel):
    source: UUID
    target: UUID

    class Config:
        orm_mode = True

class KnowledgeGraphDTO(BaseModel):
    nodes: List[GraphNodeDTO]
    links: List[GraphLinkDTO]
