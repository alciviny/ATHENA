import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from brain.application.use_cases.generate_study_plan import (
    GenerateStudyPlanUseCase,
    StudentNotFoundError,
    CognitiveProfileNotFoundError,
)
from brain.application.dto.study_plan_dto import StudyPlanOutputDTO
from brain.domain.entities.student import Student, StudentGoal
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.study_plan import StudyPlan

# Mock das dependências externas (repositórios)
@pytest.fixture
def mock_student_repo():
    return AsyncMock()

@pytest.fixture
def mock_performance_repo():
    return AsyncMock()

@pytest.fixture
def mock_knowledge_repo():
    return AsyncMock()

@pytest.fixture
def mock_study_plan_repo():
    return AsyncMock()

@pytest.fixture
def mock_cognitive_profile_repo():
    return AsyncMock()

@pytest.fixture
def mock_adaptive_rules():
    return [MagicMock()]

@pytest.fixture
def generate_study_plan_use_case(
    mock_student_repo,
    mock_performance_repo,
    mock_knowledge_repo,
    mock_study_plan_repo,
    mock_cognitive_profile_repo,
    mock_adaptive_rules,
):
    return GenerateStudyPlanUseCase(
        student_repo=mock_student_repo,
        performance_repo=mock_performance_repo,
        knowledge_repo=mock_knowledge_repo,
        study_plan_repo=mock_study_plan_repo,
        cognitive_profile_repo=mock_cognitive_profile_repo,
        adaptive_rules=mock_adaptive_rules,
    )

@pytest.mark.asyncio
async def test_generate_study_plan_success(generate_study_plan_use_case, mock_student_repo, mock_cognitive_profile_repo, mock_study_plan_repo):
    """
    Testa o caso de sucesso da geração de um plano de estudos.
    """
    student_id = uuid4()
    mock_student = Student(id=student_id, name="Test Student", goal=StudentGoal.POLICIA_FEDERAL)
    mock_profile = CognitiveProfile(
        id=uuid4(), 
        student_id=student_id,
        retention_rate=0.5,
        learning_speed=0.5,
        stress_sensitivity=0.5
    )
    mock_plan = StudyPlan(
        id=uuid4(), 
        student_id=student_id, 
        knowledge_nodes=[uuid4()],
        created_at=datetime.now(timezone.utc)
    )
    
    # Configura os retornos dos mocks dos repositórios
    mock_student_repo.get_by_id.return_value = mock_student
    mock_cognitive_profile_repo.get_by_student_id.return_value = mock_profile

    # Mock do StudyPlanGenerator para focar no teste do caso de uso
    with patch('brain.application.use_cases.generate_study_plan.StudyPlanGenerator') as MockGenerator:
        # Configura a instância mockada para retornar o plano mockado
        mock_generator_instance = MockGenerator.return_value
        mock_generator_instance.generate.return_value = mock_plan

        # --- Act ---
        result_dto = await generate_study_plan_use_case.execute(student_id)

        # --- Assert ---
        # Verifica se os repositórios foram chamados
        mock_student_repo.get_by_id.assert_awaited_once_with(student_id)
        mock_cognitive_profile_repo.get_by_student_id.assert_awaited_once_with(student_id)

        # Verifica se o gerador foi instanciado e usado
        MockGenerator.assert_called_once()
        mock_generator_instance.generate.assert_called_once()

        # Verifica se o plano foi salvo
        mock_study_plan_repo.save.assert_awaited_once_with(mock_plan)

        # Verifica se o DTO de saída está correto
        assert isinstance(result_dto, StudyPlanOutputDTO)
        assert result_dto.id == mock_plan.id
        assert result_dto.student_id == student_id
        assert len(result_dto.knowledge_nodes) == 1

@pytest.mark.asyncio
async def test_student_not_found(generate_study_plan_use_case, mock_student_repo):
    """
    Testa se a exceção StudentNotFoundError é levantada quando o aluno não é encontrado.
    """
    student_id = uuid4()
    mock_student_repo.get_by_id.return_value = None

    with pytest.raises(StudentNotFoundError):
        await generate_study_plan_use_case.execute(student_id)
        
    mock_student_repo.get_by_id.assert_awaited_once_with(student_id)

@pytest.mark.asyncio
async def test_cognitive_profile_not_found(generate_study_plan_use_case, mock_student_repo, mock_cognitive_profile_repo):
    """
    Testa se a exceção CognitiveProfileNotFoundError é levantada quando o perfil não é encontrado.
    """
    student_id = uuid4()
    mock_student = Student(id=student_id, name="Test Student", goal=StudentGoal.INSS)

    mock_student_repo.get_by_id.return_value = mock_student
    mock_cognitive_profile_repo.get_by_student_id.return_value = None

    with pytest.raises(CognitiveProfileNotFoundError):
        await generate_study_plan_use_case.execute(student_id)

    mock_student_repo.get_by_id.assert_awaited_once_with(student_id)
    mock_cognitive_profile_repo.get_by_student_id.assert_awaited_once_with(student_id)