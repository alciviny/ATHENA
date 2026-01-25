from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from brain.api.fastapi.dependencies import get_student_repository, get_roi_analysis_service, get_performance_repository
from brain.application.services.roi_analysis_service import ROIAnalysisService
from brain.application.ports.repositories import StudentRepository, PerformanceRepository

router = APIRouter(prefix="/students", tags=["ROI"])

@router.get("/{student_id}/roi-report")
async def get_roi_report(
    student_id: UUID,
    student_repo: StudentRepository = Depends(get_student_repository),
    performance_repo: PerformanceRepository = Depends(get_performance_repository),
    service: ROIAnalysisService = Depends(get_roi_analysis_service),
):
    student = await student_repo.get_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    history = await performance_repo.get_history_for_student(student_id)
    return service.analyze(student, history)
