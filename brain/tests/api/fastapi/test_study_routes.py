import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from brain.api.fastapi.main import app
from brain.application.use_cases.generate_study_plan import GenerateStudyPlanUseCase
from brain.application.dto.study_plan_dto import StudyPlanOutputDTO
from brain.api.fastapi.dependencies import get_generate_study_plan_use_case
from brain.domain.entities.study_plan import StudyFocusLevel

# O TestClient atua como um 'navegador' para nossos testes, 
# permitindo fazer requisições HTTP à nossa aplicação.
client = TestClient(app)

def test_generate_study_plan_success():
    """
    Testa o sucesso da rota de geração de plano de estudos (POST /study/generate-plan/{student_id})
    """
    # --- Arrange (Preparação) ---
    student_id = uuid4()
    plan_id = uuid4()

    # 1. Crie o DTO de saída esperado, que o nosso dublê (mock) irá retornar.
    expected_dto = StudyPlanOutputDTO(
        id=plan_id,
        student_id=student_id,
        knowledge_nodes=[uuid4(), uuid4()],
        created_at=datetime.fromisoformat("2026-01-26T12:00:00+00:00"),
        estimated_duration_minutes=120,
        focus_level=StudyFocusLevel.REINFORCEMENT.value
    )

    # 2. Crie o dublê (mock) para o caso de uso.
    use_case_mock = AsyncMock(spec=GenerateStudyPlanUseCase)
    use_case_mock.execute.return_value = expected_dto

    # 3. Substitua a dependência real (a função get_use_case) pelo nosso dublê.
    app.dependency_overrides[get_generate_study_plan_use_case] = lambda: use_case_mock
    
    # --- Act (Ação) ---
    # 4. Faça a requisição HTTP para o endpoint correto.
    response = client.post(f"/study/generate-plan/{student_id}")

    # Limpa o override para não afetar outros testes
    app.dependency_overrides.clear()

    # 5. Verifique se a resposta da API está correta.
    assert response.status_code == 200, response.text # Rota retorna 200 OK por padrão
    
    # Como o DTO não é um modelo Pydantic, criamos o dicionário esperado manualmente
    # para corresponder ao formato JSON da resposta da API.
    expected_json = {
        "id": str(expected_dto.id),
        "student_id": str(expected_dto.student_id),
        "created_at": expected_dto.created_at.isoformat(),
        "knowledge_nodes": [str(kn) for kn in expected_dto.knowledge_nodes],
        "estimated_duration_minutes": expected_dto.estimated_duration_minutes,
        "focus_level": expected_dto.focus_level,
    }
    assert response.json() == expected_json

    # 6. Verifique se o nosso dublê foi chamado corretamente.
    use_case_mock.execute.assert_awaited_once_with(student_id)

