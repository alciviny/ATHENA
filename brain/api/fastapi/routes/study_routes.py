from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# ... imports existentes ...

router = APIRouter()

class ReviewSchema(BaseModel):
    student_id: UUID
    success: bool
    response_time_seconds: float = 0.0
    grade: Optional[int] = None  # Campo novo

# ... rota generate-plan ...

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
            explicit_grade=review_data.grade # Passando o valor
        )
        return updated_node
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log real error here in production
        print(f"Error processing review: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
