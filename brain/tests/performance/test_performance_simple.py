import time
import psutil
import pytest
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import uuid4

from brain.api.fastapi.main import app


@pytest.fixture
def client():
    """Fixture para o TestClient."""
    return TestClient(app)


@pytest.mark.performance
class TestPerformance:
    """Testes de performance do sistema Athena."""

    def test_memory_usage_baseline(self):
        """Testa o uso de memória em estado basal."""
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
        # Memória deve ser menor que 500MB em estado basal (ajustado para aplicação real)
        assert memory_usage < 500, f"Uso de memória muito alto: {memory_usage:.2f}MB"
        print(f"✓ Memory usage: {memory_usage:.2f}MB")

    def test_cpu_usage_baseline(self):
        """Testa o uso de CPU em estado basal."""
        cpu_usage = psutil.cpu_percent(interval=1)
        # CPU deve ser menor que 50% em estado basal
        assert cpu_usage < 50, f"Uso de CPU muito alto: {cpu_usage:.2f}%"
        print(f"✓ CPU usage: {cpu_usage:.2f}%")

    def test_api_response_time_health_check(self, client: TestClient):
        """Testa o tempo de resposta do health check."""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        # Health check deve responder em menos de 100ms
        assert response_time < 0.1, f"Health check muito lento: {response_time:.3f}s"
        print(f"✓ Health check response time: {response_time:.3f}s")

    def test_api_response_time_login(self, client: TestClient):
        """Testa o tempo de resposta do login."""
        login_data = {
            "username": "demo_student",
            "password": "demo_password"
        }
        start_time = time.time()
        response = client.post("/auth/login", json=login_data)
        end_time = time.time()
        response_time = end_time - start_time

        # Login deve responder em menos de 500ms
        assert response_time < 0.5, f"Login muito lento: {response_time:.3f}s"
        print(f"✓ Login response time: {response_time:.3f}s")

    def test_concurrent_load_small(self, client: TestClient):
        """Testa carga concorrente pequena (10 usuários simultâneos)."""
        def make_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            return response.status_code == 200, end_time - start_time

        # Executa 10 requisições concorrentes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]

        successful_requests = sum(1 for success, _ in results if success)
        response_times = [duration for _, duration in results]

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        # Pelo menos 80% devem ser bem-sucedidas
        success_rate = successful_requests / len(results)
        assert success_rate >= 0.8, f"Taxa de sucesso muito baixa: {success_rate:.2%}"

        # Tempo médio deve ser menor que 200ms
        assert avg_response_time < 0.2, f"Tempo médio muito alto: {avg_response_time:.3f}s"
        # Tempo máximo deve ser menor que 500ms
        assert max_response_time < 0.5, f"Tempo máximo muito alto: {max_response_time:.3f}s"

        print(f"✓ Load test (10 concurrent): avg={avg_response_time:.3f}s, max={max_response_time:.3f}s, success={success_rate:.2%}")

    def test_api_throughput(self, client: TestClient):
        """Testa o throughput da API."""
        def single_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            return response.status_code == 200, end_time - start_time

        # Executa 100 requisições sequenciais
        results = []
        for _ in range(100):
            results.append(single_request())

        successful_requests = sum(1 for success, _ in results if success)
        response_times = [duration for _, duration in results]
        avg_response_time = sum(response_times) / len(response_times)

        assert successful_requests == 100  # Todas devem ser bem-sucedidas
        assert avg_response_time < 0.5  # Tempo médio < 500ms

        print(f"✓ Throughput test: {successful_requests}/100 successful, avg={avg_response_time:.3f}s")

    def test_memory_usage_under_load(self, client: TestClient):
        """Testa o uso de memória sob carga."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Executa carga
        for i in range(100):
            response = client.get("/health")
            assert response.status_code == 200

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        # Aumento de memória deve ser menor que 50MB
        assert memory_increase < 50, f"Aumento de memória muito alto: {memory_increase:.2f}MB"

        print(f"✓ Memory usage under load: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, increase={memory_increase:.2f}MB")

    def test_rate_limiting_performance_impact(self, client: TestClient):
        """Testa o impacto de performance do rate limiting."""
        # Faz requisições até o limite
        responses = []
        for i in range(20):  # Mais que o limite
            response = client.get("/health")
            responses.append(response.status_code)

        # Deve ter alguns 429, mas sistema continua funcionando
        assert 429 in responses  # Algumas rejeitadas
        assert responses[-1] in [200, 429]  # Última ainda funciona ou é rejeitada

        # Sistema deve se recuperar após cooldown
        time.sleep(2)  # Espera reset do rate limit
        response = client.get("/health")
        assert response.status_code == 200

        rejected_count = responses.count(429)
        print(f"✓ Rate limiting test: {rejected_count}/{len(responses)} requests rejected")


class TestLoadBalancingReadiness:
    """Testes para verificar readiness para load balancing."""

    def test_stateless_authentication(self, client: TestClient):
        """Testa que autenticação é stateless (importante para LB)."""
        student_id = str(uuid4())

        # Login
        response1 = client.post(
            "/auth/login",
            json={"username": student_id, "password": "demo"}
        )
        assert response1.status_code == 200
        token = response1.json()["access_token"]

        # Simula mudança de instância (novo client)
        # Na prática, seria outra instância atrás do LB
        headers = {"Authorization": f"Bearer {token}"}

        # Deve funcionar sem estado persistido
        response2 = client.get("/auth/me", headers=headers)
        assert response2.status_code == 200

        print("✓ Stateless authentication test passed")

    def test_idempotent_operations(self, client: TestClient):
        """Testa que operações são idempotentes."""
        student_id = str(uuid4())

        # Faz login múltiplas vezes com mesmo usuário
        for i in range(3):
            response = client.post(
                "/auth/login",
                json={"username": student_id, "password": "demo"}
            )
            assert response.status_code == 200

            # Cada token deve ser válido independentemente
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            me_response = client.get("/auth/me", headers=headers)
            assert me_response.status_code == 200

        print("✓ Idempotent operations test passed")

    def test_graceful_degradation(self, client: TestClient):
        """Testa degradação graceful sob carga."""
        # Faz requisições até o limite
        responses = []
        for i in range(110):  # Mais que o limite
            response = client.get("/health")
            responses.append(response.status_code)

        # Deve ter alguns 429, mas sistema continua funcionando
        assert 429 in responses  # Algumas rejeitadas
        assert responses[-1] in [200, 429]  # Última ainda funciona ou é rejeitada

        # Sistema deve se recuperar após cooldown
        time.sleep(2)  # Espera reset do rate limit
        response = client.get("/health")
        assert response.status_code == 200

        rejected_count = responses.count(429)
        print(f"✓ Graceful degradation test: {rejected_count}/110 requests rejected, system recovered")


# Testes de benchmark para comparar performance
@pytest.mark.benchmark
class TestBenchmark:
    """Testes de benchmark para medir performance absoluta."""

    def test_health_endpoint_benchmark(self, benchmark, client: TestClient):
        """Benchmark do endpoint de health check."""
        def run_health_check():
            response = client.get("/health")
            assert response.status_code == 200

        benchmark(run_health_check)

    def test_login_endpoint_benchmark(self, benchmark, client: TestClient):
        """Benchmark do endpoint de login."""
        login_data = {
            "username": "demo_student",
            "password": "demo_password"
        }

        def run_login():
            response = client.post("/auth/login", json=login_data)
            assert response.status_code == 200

        benchmark(run_login)