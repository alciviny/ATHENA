from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from brain.api.fastapi.dependencies import get_student_repository, get_memory_analysis_service
from brain.application.services.memory_analysis_service import MemoryAnalysisService

router = APIRouter(prefix="/students", tags=["Memory"])

@router.get("/{student_id}/memory-status")
async def get_memory_status(
    student_id: UUID,
    repo=Depends(get_student_repository),
    service: MemoryAnalysisService = Depends(get_memory_analysis_service),
):
    student = await repo.get_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    history = await repo.get_performance_history(student_id)
    return await service.get_student_memory_status(student, history)
