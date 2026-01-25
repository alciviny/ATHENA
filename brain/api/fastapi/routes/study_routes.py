from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from brain.application.use_cases.generate_study_plan import (
    GenerateStudyPlanUseCase,
    StudentNotFoundError,
    CognitiveProfileNotFoundError,
)
from brain.application.use_cases.record_review import RecordReviewUseCase
from brain.api.fastapi.dependencies import (
    get_generate_study_plan_use_case,
    get_record_review_use_case,
)
from pydantic import BaseModel


router = APIRouter()

class ReviewSchema(BaseModel):
    student_id: UUID
    success: bool
    response_time_seconds: float = 0.0

@router.post("/generate-plan/{student_id}")
async def generate_plan(
    student_id: UUID, 
    use_case: GenerateStudyPlanUseCase = Depends(get_generate_study_plan_use_case)
):
    try:
        study_plan = await use_case.execute(student_id)
        return study_plan
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CognitiveProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.post("/review/{node_id}")
async def record_review(
    node_id: UUID, 
    review_data: ReviewSchema,
    use_case: RecordReviewUseCase = Depends(get_record_review_use_case)
):
    try:
        updated_node = await use_case.execute(
            student_id=review_data.student_id,
            node_id=str(node_id),
            success=review_data.success,
            response_time_seconds=review_data.response_time_seconds,
        )
        return updated_node
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
