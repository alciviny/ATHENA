from uuid import UUID
from fastapi import APIRouter, Depends
from brain.api.fastapi.dependencies import get_roi_analysis_service
from brain.application.services.roi_analysis_service import ROIAnalysisService
from brain.application.dto.graph_dto import KnowledgeGraphDTO

router = APIRouter(prefix="/students", tags=["ROI"])

@router.get("/{student_id}/graph", response_model=KnowledgeGraphDTO)
async def get_knowledge_graph_endpoint(
    student_id: UUID,
    service: ROIAnalysisService = Depends(get_roi_analysis_service),
):
    """
    Returns the student's full knowledge graph, including nodes with ROI scores
    and the dependency links between them.
    """
    return await service.get_knowledge_graph(student_id)
