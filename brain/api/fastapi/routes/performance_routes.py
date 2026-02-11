from fastapi import APIRouter, Depends, Query, Path, status, HTTPException
from uuid import UUID
from pydantic import BaseModel
from brain.api.fastapi.dependencies import (
    get_analyze_student_performance_use_case,
    get_record_review_use_case,
    get_performance_repository,
    get_knowledge_repository,
)
from brain.application.use_cases.analyze_student_performance import (
    AnalyzeStudentPerformance,
)
from brain.application.use_cases.record_review import RecordReviewUseCase
from brain.application.ports.repositories import PerformanceRepository, KnowledgeRepository

from statistics import mean

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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na análise: {type(e).__name__}: {str(e)}")


@router.get(
    "/subjects/{student_id}",
    status_code=status.HTTP_200_OK,
    summary="List available subjects for a student",
)
async def get_student_subjects(
    student_id: UUID,
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repository),
    performance_repo: PerformanceRepository = Depends(get_performance_repository),
):
    """Get all unique subjects that a student has interacted with (has performance events)."""
    try:
        # Get all performance events for the student
        performance_events = await performance_repo.get_history_for_student(student_id)
        
        # Extract unique node_ids from performance events
        node_ids = set()
        for event in performance_events:
            if hasattr(event, 'node_id') and event.node_id:
                node_ids.add(event.node_id)
        
        # Get knowledge nodes for these IDs
        subjects = set()
        for node_id in node_ids:
            try:
                node = await knowledge_repo.get_by_id(node_id)
                if node and node.subject:
                    subjects.add(node.subject)
            except:
                continue  # Skip if node not found
        
        subjects_list = sorted(list(subjects))
        
        return {
            "student_id": student_id,
            "subjects": subjects_list,
            "total_subjects": len(subjects_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar matérias: {e}")
