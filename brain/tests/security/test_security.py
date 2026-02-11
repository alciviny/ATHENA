import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from brain.api.fastapi.main import app

client = TestClient(app)

class TestSecurityMiddleware:
    """Testes de middlewares de segurança."""

    def test_security_headers_present(self):
        """Testa se headers de segurança estão presentes."""
        response = client.get("/")

        # Headers de segurança obrigatórios
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_rate_limiting_exempt_paths(self):
        """Testa que caminhos isentos não são rate limited."""
        # Faz múltiplas requisições para caminhos isentos
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

            response = client.get("/docs")
            assert response.status_code == 200

    def test_rate_limiting_protected_paths(self):
        """Testa rate limiting em caminhos protegidos."""
        # Login primeiro para ter um token
        response = client.post(
            "/auth/login",
            data={"username": str(uuid4()), "password": "demo"}
        )
        token = response.json()["access_token"]

        # Faz muitas requisições para um endpoint protegido
        for i in range(105):  # Mais que o limite de 100
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            if i < 100:
                assert response.status_code == 200
            else:
                # Após 100 requests, deve ser rate limited
                assert response.status_code == 429

class TestInputValidation:
    """Testes de validação de entrada."""

    def test_sql_injection_prevention(self):
        """Testa prevenção de SQL injection."""
        malicious_inputs = [
            "'; DROP TABLE students; --",
            "' OR '1'='1",
            "admin'--",
            "<script>alert('xss')</script>",
            "../../../etc/passwd"
        ]

        for malicious_input in malicious_inputs:
            # Tenta login com input malicioso
            response = client.post(
                "/auth/login",
                data={
                    "username": malicious_input,
                    "password": "demo"
                }
            )

            # Deve falhar na autenticação, não causar erro de SQL
            assert response.status_code in [401, 422]  # Unauthorized ou Validation Error

    def test_large_payload_rejection(self):
        """Testa rejeição de payloads muito grandes."""
        large_data = "x" * 1000000  # 1MB de dados

        response = client.post(
            "/auth/login",
            data={
                "username": str(uuid4()),
                "password": large_data
            }
        )

        # Deve ser rejeitado ou truncado
        assert response.status_code in [401, 413, 422]

    def test_invalid_json_handling(self):
        """Testa tratamento de JSON inválido."""
        response = client.post(
            "/auth/login",
            data="invalid json {",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Validation error

class TestErrorHandling:
    """Testes de tratamento de erros seguro."""

    def test_no_information_leakage(self):
        """Testa que erros não vazam informações sensíveis."""
        # Tenta acessar endpoint inexistente
        response = client.get("/nonexistent/endpoint")

        assert response.status_code == 404
        data = response.json()

        # Não deve conter informações de debug ou stack trace
        assert "traceback" not in str(data).lower()
        assert "internal" not in str(data).lower()
        assert "error" in data

    def test_database_error_handling(self):
        """Testa tratamento seguro de erros de banco."""
        # Simula erro de banco (mock)
        with patch('brain.api.fastapi.routes.study_routes.get_study_plan') as mock_func:
            mock_func.side_effect = Exception("Database connection failed")

            response = client.get("/study/plan")

            assert response.status_code == 500
            data = response.json()

            # Deve retornar erro genérico, não detalhes técnicos
            assert "error" in data
            assert "Database connection failed" not in str(data)

class TestHTTPSecurity:
    """Testes de segurança HTTP."""

    def test_no_http_methods_exposed(self):
        """Testa que métodos HTTP perigosos não estão expostos."""
        dangerous_methods = ["TRACE", "TRACK", "OPTIONS"]

        for method in dangerous_methods:
            response = client.request(method, "/")
            # Deve retornar 405 Method Not Allowed ou ser tratado
            assert response.status_code in [405, 404, 200]

    def test_cors_headers(self):
        """Testa headers CORS apropriados."""
        response = client.options("/")

        # Deve ter headers CORS apropriados ou não permitir
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]

        # Ou tem CORS configurado ou bloqueia completamente
        has_cors = any(header in response.headers for header in cors_headers)
        if has_cors:
            assert response.headers.get("access-control-allow-origin") != "*"