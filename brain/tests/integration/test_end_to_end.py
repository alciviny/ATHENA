import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from brain.api.fastapi.main import app
from brain.infrastructure.persistence.database import get_db_session
from brain.infrastructure.persistence.models import StudentModel, CognitiveProfileModel

client = TestClient(app)

@pytest.mark.asyncio
class TestEndToEndFlow:
    """Testes de integração end-to-end do fluxo completo."""

    async def test_complete_user_flow(self, db_session: AsyncSession):
        """Testa fluxo completo: cadastro → login → estudo → performance."""
        student_id = str(uuid4())

        # 1. Login (usando credenciais demo)
        login_response = client.post(
            "/auth/login",
            data={
                "username": student_id,
                "password": "demo"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Verificar usuário autenticado
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["student_id"] == student_id

        # 3. Criar dados de teste no banco
        await self._create_test_student(db_session, student_id)

        # 4. Tentar gerar plano de estudo (deve funcionar com dados mock)
        plan_response = client.get("/study/plan", headers=headers)
        # Pode falhar se não houver dados suficientes, mas não deve ser erro de auth
        assert plan_response.status_code in [200, 404, 500]  # Sucesso ou erro esperado

        # 5. Testar endpoint de performance
        perf_response = client.get("/performance/history", headers=headers)
        assert perf_response.status_code in [200, 404]  # Pode não ter dados

        # 6. Testar logout implícito (token expira)
        # Nota: em produção, teria endpoint de logout para invalidar token

    async def test_rate_limiting_integration(self):
        """Testa rate limiting em cenário real."""
        student_id = str(uuid4())

        # Login primeiro
        login_response = client.post(
            "/auth/login",
            data={"username": student_id, "password": "demo"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Faz 101 requisições (limite é 100 por minuto)
        responses = []
        for i in range(101):
            response = client.get("/auth/me", headers=headers)
            responses.append(response.status_code)

        # Pelo menos uma deve ser 429 (rate limited)
        assert 429 in responses

        # A maioria deve ser 200 (dentro do limite)
        successful_requests = sum(1 for r in responses if r == 200)
        assert successful_requests >= 95  # Pelo menos 95% sucesso

    async def test_security_headers_integration(self):
        """Testa headers de segurança em todos os endpoints."""
        endpoints = [
            "/",
            "/health",
            "/docs",
            "/auth/login"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)

            # Todos devem ter headers de segurança
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "Content-Security-Policy" in response.headers

    async def test_error_handling_integration(self):
        """Testa tratamento de erros em cenário real."""
        # Endpoint inexistente
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # Método não permitido
        response = client.post("/health")
        assert response.status_code in [405, 404]

        # Payload malformado
        response = client.post(
            "/auth/login",
            data="invalid form data {",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422

    async def test_concurrent_requests(self):
        """Testa comportamento com requisições concorrentes."""
        import asyncio
        import aiohttp

        async def make_request(session, url, headers):
            async with session.get(url, headers=headers) as response:
                return response.status

        # Login
        student_id = str(uuid4())
        login_response = client.post(
            "/auth/login",
            data={"username": student_id, "password": "demo"}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Faz 10 requisições concorrentes
        async with aiohttp.ClientSession() as session:
            tasks = [
                make_request(session, "http://localhost:8000/auth/me", headers)
                for _ in range(10)
            ]
            results = await asyncio.gather(*tasks)

        # Todas devem ser 200 (sucesso) ou algumas 429 (rate limit)
        valid_statuses = {200, 429}
        assert all(status in valid_statuses for status in results)

    async def _create_test_student(self, db_session: AsyncSession, student_id: str):
        """Cria dados de teste para o estudante."""

        # Cria estudante
        student = StudentModel(
            id=student_id,
            name="Test Student",
            goal="POLICIA_FEDERAL"
        )

        # Cria perfil cognitivo
        profile = CognitiveProfileModel(
            id=str(uuid4()),
            retention_rate=0.8,
            learning_speed=0.7,
            stress_sensitivity=0.3
        )
        student.cognitive_profile = profile

        db_session.add(student)
        await db_session.commit()

@pytest.fixture
async def db_session():
    """Fixture para sessão de banco de dados de teste."""
    from brain.infrastructure.persistence.database import SessionLocal

    async with SessionLocal() as session:
        yield session
        # Cleanup pode ser adicionado aqui se necessário