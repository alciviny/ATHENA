from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from brain.api.fastapi.dependencies import (
    get_generate_study_plan_use_case,
    get_record_review_use_case,
)
# --- CORREÇÃO: Importamos o DTO correto (criado no passo anterior) ---
from brain.application.dto.study_plan_dto import StudyPlanDTO
from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase
from brain.application.use_cases.record_review import RecordReviewUseCase

router = APIRouter()


# --- CORREÇÃO: Atualizamos o response_model para StudyPlanDTO ---
@router.post("/generate-plan/{student_id}", response_model=StudyPlanDTO)
async def generate_study_plan(
    student_id: UUID,
    use_case: GenerateStudyPlanUseCase = Depends(get_generate_study_plan_use_case),
):
    """
    Generates a new adaptive study plan for a given student.
    """
    try:
        study_plan = await use_case.execute(student_id)
        return study_plan
    except Exception as e:
        # Log detalhado do erro para debug
        print(f"Error generating plan: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


class ReviewSchema(BaseModel):
    student_id: UUID
    success: bool
    response_time_seconds: float = 0.0
    grade: Optional[int] = None


@router.post("/review/{node_id}")
async def record_review(
    node_id: UUID,
    review_data: ReviewSchema,
    use_case: RecordReviewUseCase = Depends(get_record_review_use_case),
):
    """
    Records the result of a student's review of a knowledge node.
    """
    try:
        updated_node = await use_case.execute(
            student_id=review_data.student_id,
            node_id=str(node_id),
            success=review_data.success,
            response_time_seconds=review_data.response_time_seconds,
            explicit_grade=review_data.grade,
        )
        return updated_node
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error processing review: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")