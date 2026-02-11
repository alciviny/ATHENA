import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import HTTPException

from brain.api.fastapi.main import app
from brain.api.fastapi.auth.security import (
    create_access_token,
    verify_token,
    authenticate_student,
    get_password_hash,
    verify_password
)

client = TestClient(app)

class TestAuthentication:
    """Testes de autenticação e segurança."""

    def test_password_hashing(self):
        """Testa hash e verificação de senha."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_create_access_token(self):
        """Testa criação de token JWT."""
        student_id = str(uuid4())
        token = create_access_token(data={"sub": student_id})

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Testa verificação de token válido."""
        student_id = str(uuid4())
        token = create_access_token(data={"sub": student_id})

        token_data = verify_token(token)
        assert str(token_data.student_id) == student_id

    def test_verify_invalid_token(self):
        """Testa verificação de token inválido."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid_token")

        assert exc_info.value.status_code == 401

    def test_authenticate_student_success(self):
        """Testa autenticação bem-sucedida."""
        student_id = str(uuid4())
        password = "demo"

        result = authenticate_student(student_id, password)
        assert result is not None
        assert str(result) == student_id

    def test_authenticate_student_failure(self):
        """Testa autenticação falhada."""
        result = authenticate_student("invalid_id", "wrong_password")
        assert result is None

    def test_login_endpoint_success(self):
        """Testa endpoint de login com credenciais válidas."""
        student_id = str(uuid4())

        response = client.post(
            "/auth/login",
            data={
                "username": student_id,
                "password": "demo"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_endpoint_failure(self):
        """Testa endpoint de login com credenciais inválidas."""
        response = client.post(
            "/auth/login",
            data={
                "username": "invalid_id",
                "password": "wrong_password"
            }
        )

        assert response.status_code == 401

    def test_protected_endpoint_without_token(self):
        """Testa acesso a endpoint protegido sem token."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self):
        """Testa acesso a endpoint protegido com token válido."""
        # Primeiro faz login
        student_id = str(uuid4())
        login_response = client.post(
            "/auth/login",
            data={
                "username": student_id,
                "password": "demo"
            }
        )
        token = login_response.json()["access_token"]

        # Depois acessa endpoint protegido
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == student_id

    def test_refresh_token(self):
        """Testa refresh de token."""
        # Primeiro faz login
        student_id = str(uuid4())
        login_response = client.post(
            "/auth/login",
            data={
                "username": student_id,
                "password": "demo"
            }
        )
        token = login_response.json()["access_token"]

        # Faz refresh
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verifica que o novo token funciona
        new_token = data["access_token"]
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert response.status_code == 200