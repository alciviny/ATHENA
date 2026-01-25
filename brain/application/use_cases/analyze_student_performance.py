from typing import List
from uuid import UUID
from brain.application.ports.ai_service import AIService
from brain.application.ports.repositories import ErrorEventRepository
from brain.domain.entities.error_event import ErrorEvent


class AnalyzeStudentPerformance:
    """
    Use case to analyze a student's performance based on their errors in a specific subject.
    """

    def __init__(
        self,
        error_event_repository: ErrorEventRepository,
        ai_service: AIService,
    ):
        self.error_event_repository = error_event_repository
        self.ai_service = ai_service

    async def execute(self, student_id: UUID, subject: str) -> str:
        """
        Executes the performance analysis for a given subject.
        """
        errors: List[ErrorEvent] = await self.error_event_repository.get_by_student_and_subject(
            student_id,
            subject
        )
        
        if not errors:
            return f"Nenhuma análise a ser feita para '{subject}', pois não foram encontrados erros."

        analysis = await self.ai_service.analyze_student_errors(errors, subject)
        return analysis