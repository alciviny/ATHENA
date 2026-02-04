from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from brain.api.fastapi.dependencies import (
    get_generate_study_plan_use_case,
    get_record_review_use_case,
    get_start_exam_simulator_use_case,
    get_validate_feynman_explanation_use_case,
)
# --- CORREÇÃO: Importamos o DTO correto (criado no passo anterior) ---
from brain.application.dto.study_plan_dto import StudyPlanDTO, StudyPlanOutputDTO
from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase
from brain.application.use_cases.record_review import RecordReviewUseCase
from brain.application.use_cases.start_exam_simulator import StartExamSimulatorUseCase
from brain.application.use_cases.validate_feynman_explanation import ValidateFeynmanExplanation
from brain.domain.entities.error_event import ErrorRootCause

router = APIRouter()


class FeynmanValidationSchema(BaseModel):
    student_id: UUID
    node_id: UUID
    explanation: str


# --- CORREÇÃO: Atualizamos o response_model para StudyPlanDTO ---
@router.post("/generate-plan/{student_id}", response_model=StudyPlanOutputDTO)
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



@router.post("/study/start-simulator/{student_id}", response_model=StudyPlanOutputDTO)
async def start_exam_simulator(
    student_id: UUID,
    num_questions: Optional[int] = 20,
    time_limit_seconds: Optional[int] = 3600,
    stress_level: Optional[float] = 1.0,
    use_case: StartExamSimulatorUseCase = Depends(get_start_exam_simulator_use_case),
):
    try:
        plan = await use_case.execute(student_id=student_id, num_questions=num_questions, time_limit_seconds=time_limit_seconds, stress_level=stress_level)
        return plan
    except Exception as e:
        print(f"Error starting simulator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ReviewSchema(BaseModel):
    student_id: UUID
    success: bool
    response_time_seconds: float = 0.0
    grade: Optional[int] = None
    root_cause: Optional[ErrorRootCause] = None


@router.post("/review/{node_id}")
async def record_review(
    node_id: str,
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
            root_cause=review_data.root_cause,
        )
        return updated_node
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error processing review: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.post("/feynman/validate")
async def validate_feynman_explanation(
    validation_data: FeynmanValidationSchema,
    use_case: ValidateFeynmanExplanation = Depends(get_validate_feynman_explanation_use_case),
):
    """
    Validates a student's explanation for a given knowledge node using the Feynman technique.
    """
    try:
        result = await use_case.execute(
            student_id=validation_data.student_id,
            node_id=validation_data.node_id,
            explanation=validation_data.explanation,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Log the exception for debugging
        print(f"Unexpected error during Feynman validation: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during validation.")