from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from brain.api.fastapi.dependencies import get_student_repository, get_memory_analysis_service, get_performance_repository
from brain.application.services.memory_analysis_service import MemoryAnalysisService
from brain.application.ports.repositories import StudentRepository, PerformanceRepository


router = APIRouter(prefix="/students", tags=["Memory"])

@router.get("/{student_id}/memory-status")
async def get_memory_status(
    student_id: UUID,
    student_repo: StudentRepository = Depends(get_student_repository),
    performance_repo: PerformanceRepository = Depends(get_performance_repository),
    service: MemoryAnalysisService = Depends(get_memory_analysis_service),
):
    student = await student_repo.get_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    history = await performance_repo.get_history_for_student(student_id)
    return await service.get_student_memory_status(student, history)
