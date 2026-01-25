from fastapi import APIRouter, Depends, Query, Path, status, HTTPException
from uuid import UUID
from pydantic import BaseModel
from brain.api.fastapi.dependencies import (
    get_analyze_student_performance_use_case,
    get_record_review_use_case,
)
from brain.application.use_cases.analyze_student_performance import (
    AnalyzeStudentPerformance,
)
from brain.application.use_cases.record_review import RecordReviewUseCase

router = APIRouter(tags=["Student Performance"])

# DTO para recebimento de performance
class performance_event_schema(BaseModel):
    node_id: str
    success: bool
    response_time_seconds: float

@router.post(
    "/{student_id}/record",
    status_code=status.HTTP_200_OK,
    summary="Record student performance event",
)
async def record_performance(
    student_id: UUID,
    event: performance_event_schema,
    use_case: RecordReviewUseCase = Depends(get_record_review_use_case),
):
    """
    Recebe um evento de performance (acerto/erro) e dispara 
    a atualização automática do grafo de conhecimento.
    """
    try:
        result = await use_case.execute(
            student_id=student_id, 
            node_id=event.node_id,
            success=event.success,
            response_time_seconds=event.response_time_seconds
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/analysis/{student_id}",
    status_code=status.HTTP_200_OK,
    summary="Analyze student performance by subject",
)
async def analyze_performance(
    student_id: UUID = Path(..., description="UUID do estudante"),
    subject: str = Query(..., examples=["Matemática"]),
    use_case: AnalyzeStudentPerformance = Depends(get_analyze_student_performance_use_case),
):
    try:
        analysis = await use_case.execute(student_id=student_id, subject=subject)
        return {
            "student_id": student_id,
            "subject": subject,
            "analysis": analysis,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred during analysis.")
