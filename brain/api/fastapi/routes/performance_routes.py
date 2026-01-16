from fastapi import APIRouter, Depends, Query, Path, status

from brain.api.fastapi.dependencies import (
    get_analyze_student_performance_use_case,
)
from brain.application.use_cases.analyze_student_performance import (
    AnalyzeStudentPerformance,
)

router = APIRouter(tags=["Student Performance"])


@router.get(
    "/performance/analysis/{student_id}",
    status_code=status.HTTP_200_OK,
    summary="Analyze student performance by subject",
    description="Analyzes a student's performance in a specific subject based on recorded errors.",
)
async def analyze_performance(
    student_id: str = Path(
        ...,
        description="Unique identifier of the student",
        example="student-123",
    ),
    subject: str = Query(
        ...,
        description="Subject to be analyzed",
        example="Matemática",
    ),
    use_case: AnalyzeStudentPerformance = Depends(
        get_analyze_student_performance_use_case
    ),
):
    """
    Orchestrates the performance analysis request by delegating
    the business logic to the AnalyzeStudentPerformance use case.
    """
    analysis = use_case.execute(student_id=student_id, subject=subject)

    return {
        "student_id": student_id,
        "subject": subject,
        "analysis": analysis,
    }
