import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from brain.application.use_cases.analyze_student_performance import AnalyzeStudentPerformance
from brain.domain.entities.error_event import ErrorEvent, ErrorType

# Mock das dependências
@pytest.fixture
def mock_error_repo():
    return AsyncMock()

@pytest.fixture
def mock_ai_service():
    return AsyncMock()

@pytest.fixture
def analyze_performance_use_case(mock_error_repo, mock_ai_service):
    return AnalyzeStudentPerformance(
        error_event_repository=mock_error_repo,
        ai_service=mock_ai_service,
    )

@pytest.mark.asyncio
async def test_analysis_success_with_errors(analyze_performance_use_case, mock_error_repo, mock_ai_service):
    """
    Testa o caso de sucesso, onde erros são encontrados e a IA gera uma análise.
    """
    student_id = uuid4()
    subject = "Math"
    mock_errors = [ErrorEvent(
        id=uuid4(), 
        student_id=student_id, 
        error_type=ErrorType.CONTEUDO, 
        knowledge_node_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
        severity=0.5
    )]
    expected_analysis = "O aluno está com dificuldades em cálculos básicos."

    # Configura os mocks
    mock_error_repo.get_by_student_and_subject.return_value = mock_errors
    mock_ai_service.analyze_student_errors.return_value = expected_analysis

    # --- Act ---
    result = await analyze_performance_use_case.execute(student_id, subject)

    # --- Assert ---
    mock_error_repo.get_by_student_and_subject.assert_awaited_once_with(student_id, subject)
    mock_ai_service.analyze_student_errors.assert_awaited_once_with(mock_errors, subject)
    assert result == expected_analysis

@pytest.mark.asyncio
async def test_analysis_with_no_errors(analyze_performance_use_case, mock_error_repo, mock_ai_service):
    """
    Testa o caso onde não há erros, e o serviço de IA não deve ser chamado.
    """
    student_id = uuid4()
    subject = "History"
    
    # Configura o mock do repositório para não retornar erros
    mock_error_repo.get_by_student_and_subject.return_value = []

    # --- Act ---
    result = await analyze_performance_use_case.execute(student_id, subject)

    # --- Assert ---
    mock_error_repo.get_by_student_and_subject.assert_awaited_once_with(student_id, subject)
    mock_ai_service.analyze_student_errors.assert_not_awaited()
    assert result == f"Nenhuma análise a ser feita para '{subject}', pois não foram encontrados erros."