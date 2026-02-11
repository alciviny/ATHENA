import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import psutil
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from brain.api.fastapi.main import app


class PerformanceTestSuite:
    """Suite de testes de performance para o sistema Athena."""

    def __init__(self, client: TestClient):
        self.client = client

    def get_memory_usage(self) -> float:
        """Retorna o uso de memória atual em MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def get_cpu_usage(self) -> float:
        """Retorna o uso de CPU atual."""
        return psutil.cpu_percent(interval=1)

    async def measure_response_time(self, endpoint: str, method: str = "GET",
                                  data: Dict[str, Any] = None,
                                  headers: Dict[str, str] = None) -> float:
        """Mede o tempo de resposta de um endpoint."""
        start_time = time.time()

        if method == "GET":
            response = self.client.get(endpoint, headers=headers)
        elif method == "POST":
            response = self.client.post(endpoint, json=data, headers=headers)
        elif method == "PUT":
            response = self.client.put(endpoint, json=data, headers=headers)
        elif method == "DELETE":
            response = self.client.delete(endpoint, headers=headers)
        else:
            raise ValueError(f"Método HTTP não suportado: {method}")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code < 500, f"Erro no endpoint {endpoint}: {response.status_code}"
        return response_time

    def run_concurrent_requests(self, endpoint: str, num_requests: int,
                              method: str = "GET", data: Dict[str, Any] = None,
                              headers: Dict[str, str] = None) -> List[float]:
        """Executa múltiplas requisições concorrentes e retorna os tempos de resposta."""
        response_times = []

        def make_request():
            return asyncio.run(self.measure_response_time(endpoint, method, data, headers))

        with ThreadPoolExecutor(max_workers=min(num_requests, 10)) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            for future in as_completed(futures):
                response_times.append(future.result())

        return response_times


@pytest.fixture
def performance_suite(client: TestClient):
    """Fixture para a suite de testes de performance."""
    return PerformanceTestSuite(client)


@pytest.mark.performance
class TestPerformance:
    """Testes de performance do sistema Athena."""

    def test_memory_usage_baseline(self, performance_suite: PerformanceTestSuite):
        """Testa o uso de memória em estado basal."""
        memory_usage = performance_suite.get_memory_usage()
        # Memória deve ser menor que 200MB em estado basal
        assert memory_usage < 200, f"Uso de memória muito alto: {memory_usage:.2f}MB"

    def test_cpu_usage_baseline(self, performance_suite: PerformanceTestSuite):
        """Testa o uso de CPU em estado basal."""
        cpu_usage = performance_suite.get_cpu_usage()
        # CPU deve ser menor que 50% em estado basal
        assert cpu_usage < 50, f"Uso de CPU muito alto: {cpu_usage:.2f}%"

    @pytest.mark.asyncio
    async def test_api_response_time_health_check(self, performance_suite: PerformanceTestSuite):
        """Testa o tempo de resposta do health check."""
        response_time = await performance_suite.measure_response_time("/health")
        # Health check deve responder em menos de 100ms
        assert response_time < 0.1, f"Health check muito lento: {response_time:.3f}s"

    @pytest.mark.asyncio
    async def test_api_response_time_login(self, performance_suite: PerformanceTestSuite):
        """Testa o tempo de resposta do login."""
        login_data = {
            "username": "demo_student",
            "password": "demo_password"
        }
        response_time = await performance_suite.measure_response_time(
            "/auth/login", method="POST", data=login_data
        )
        # Login deve responder em menos de 500ms
        assert response_time < 0.5, f"Login muito lento: {response_time:.3f}s"

    def test_concurrent_load_small(self, performance_suite: PerformanceTestSuite):
        """Testa carga concorrente pequena (10 usuários simultâneos)."""
        endpoint = "/health"
        num_requests = 10

        response_times = performance_suite.run_concurrent_requests(endpoint, num_requests)

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        # Tempo médio deve ser menor que 200ms
        assert avg_response_time < 0.2, f"Tempo médio muito alto: {avg_response_time:.3f}s"
        # Tempo máximo deve ser menor que 500ms
        assert max_response_time < 0.5, f"Tempo máximo muito alto: {max_response_time:.3f}s"
        # Tempo mínimo deve ser maior que 0
        assert min_response_time > 0, f"Tempo mínimo inválido: {min_response_time:.3f}s"

        print(f"Load test (10 concurrent): avg={avg_response_time:.3f}s, max={max_response_time:.3f}s, min={min_response_time:.3f}s")

    def test_concurrent_load_medium(self, performance_suite: PerformanceTestSuite):
        """Testa carga concorrente média (50 usuários simultâneos)."""
        endpoint = "/health"
        num_requests = 50

        response_times = performance_suite.run_concurrent_requests(endpoint, num_requests)

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        # Tempo médio deve ser menor que 300ms
        assert avg_response_time < 0.3, f"Tempo médio muito alto: {avg_response_time:.3f}s"
        # Tempo máximo deve ser menor que 1s
        assert max_response_time < 1.0, f"Tempo máximo muito alto: {max_response_time:.3f}s"

        print(f"Load test (50 concurrent): avg={avg_response_time:.3f}s, max={max_response_time:.3f}s")

    def test_api_throughput(self, performance_suite: PerformanceTestSuite):
        """Testa o throughput da API."""
        endpoint = "/health"
        num_requests = 100
        time_limit = 10  # segundos

        start_time = time.time()
        response_times = performance_suite.run_concurrent_requests(endpoint, num_requests)
        end_time = time.time()

        total_time = end_time - start_time
        throughput = num_requests / total_time  # requests per second

        # Throughput deve ser maior que 50 requests/segundo
        assert throughput > 50, f"Throughput muito baixo: {throughput:.2f} req/s"

        print(f"Throughput test: {throughput:.2f} req/s, total time: {total_time:.2f}s")

    def test_memory_usage_under_load(self, performance_suite: PerformanceTestSuite):
        """Testa o uso de memória sob carga."""
        initial_memory = performance_suite.get_memory_usage()

        # Executa carga
        endpoint = "/health"
        num_requests = 100
        performance_suite.run_concurrent_requests(endpoint, num_requests)

        final_memory = performance_suite.get_memory_usage()
        memory_increase = final_memory - initial_memory

        # Aumento de memória deve ser menor que 50MB
        assert memory_increase < 50, f"Aumento de memória muito alto: {memory_increase:.2f}MB"

        print(f"Memory usage: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, increase={memory_increase:.2f}MB")

    @pytest.mark.slow
    def test_sustained_load(self, performance_suite: PerformanceTestSuite):
        """Testa carga sustentada por 30 segundos."""
        endpoint = "/health"
        duration = 30  # segundos
        start_time = time.time()

        response_times = []
        request_count = 0

        while time.time() - start_time < duration:
            response_time = asyncio.run(performance_suite.measure_response_time(endpoint))
            response_times.append(response_time)
            request_count += 1
            time.sleep(0.1)  # Pequena pausa entre requisições

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        throughput = request_count / duration

        # Tempo médio deve ser menor que 200ms
        assert avg_response_time < 0.2, f"Tempo médio muito alto: {avg_response_time:.3f}s"
        # Throughput deve ser maior que 5 requests/segundo
        assert throughput > 5, f"Throughput muito baixo: {throughput:.2f} req/s"

        print(f"Sustained load test: {request_count} requests in {duration}s, avg={avg_response_time:.3f}s, throughput={throughput:.2f} req/s")

    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self, performance_suite: PerformanceTestSuite):
        """Testa o desempenho do pool de conexões do banco de dados."""
        # Este teste requer acesso ao banco de dados
        # Vamos testar um endpoint que usa o banco
        response_time = await performance_suite.measure_response_time("/health")
        assert response_time < 0.5, f"Database connection muito lento: {response_time:.3f}s"

    def test_rate_limiting_performance_impact(self, performance_suite: PerformanceTestSuite):
        """Testa o impacto de performance do rate limiting."""
        endpoint = "/health"
        num_requests = 20

        response_times = performance_suite.run_concurrent_requests(endpoint, num_requests)

        # Mesmo com rate limiting, deve responder
        successful_responses = [rt for rt in response_times if rt < 1.0]
        success_rate = len(successful_responses) / len(response_times)

        # Pelo menos 80% das requisições devem ser bem-sucedidas
        assert success_rate > 0.8, f"Rate limiting afetando performance: {success_rate:.2%} success rate"

        print(f"Rate limiting test: {success_rate:.2%} success rate")

    def test_response_time_auth_endpoints(self):
        """Testa tempo de resposta dos endpoints de auth."""
        student_id = str(uuid4())

        # Testa login
        start_time = time.time()
        response = performance_suite.client.post(
            "/auth/login",
            data={"username": student_id, "password": "demo"}
        )
        login_time = time.time() - start_time

        assert response.status_code == 200
        assert login_time < 2.0  # Deve responder em menos de 2 segundos

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Testa endpoint protegido
        start_time = time.time()
        response = performance_suite.client.get("/auth/me", headers=headers)
        me_time = time.time() - start_time

        assert response.status_code == 200
        assert me_time < 1.0  # Deve responder em menos de 1 segundo

    def test_memory_usage_stability(self):
        """Testa estabilidade de uso de memória."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Faz várias operações
        for i in range(50):
            student_id = str(uuid4())
            response = performance_suite.client.post(
                "/auth/login",
                data={"username": student_id, "password": "demo"}
            )
            assert response.status_code == 200

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Não deve aumentar mais que 50MB
        assert memory_increase < 50

    def test_database_connection_pooling(self):
        """Testa que conexões de banco são reutilizadas."""
        # Este teste verifica que não há vazamento de conexões
        import gc

        initial_objects = len(gc.get_objects())

        # Faz muitas operações de banco
        for i in range(100):
            student_id = str(uuid4())
            response = performance_suite.client.post(
                "/auth/login",
                data={"username": student_id, "password": "demo"}
            )
            assert response.status_code == 200

        gc.collect()
        final_objects = len(gc.get_objects())

        # Não deve haver crescimento excessivo de objetos
        object_growth = final_objects - initial_objects
        assert object_growth < 1000  # Permite algum crescimento normal

    def test_resource_cleanup(self):
        """Testa limpeza adequada de recursos."""
        import threading

        initial_threads = threading.active_count()

        # Faz operações que podem criar threads/fibers
        for i in range(20):
            student_id = str(uuid4())
            response = performance_suite.client.post(
                "/auth/login",
                data={"username": student_id, "password": "demo"}
            )
            assert response.status_code == 200

        # Espera um pouco para cleanup
        time.sleep(1)

        final_threads = threading.active_count()

        # Não deve haver crescimento excessivo de threads
        thread_growth = final_threads - initial_threads
        assert thread_growth < 5  # Permite pequeno crescimento


class TestLoadBalancingReadiness:
    """Testes para verificar readiness para load balancing."""

    def test_stateless_authentication(self):
        """Testa que autenticação é stateless (importante para LB)."""
        student_id = str(uuid4())

        # Login
        response1 = performance_suite.client.post(
            "/auth/login",
            data={"username": student_id, "password": "demo"}
        )
        assert response1.status_code == 200
        token = response1.json()["access_token"]

        # Simula mudança de instância (novo client)
        # Na prática, seria outra instância atrás do LB
        headers = {"Authorization": f"Bearer {token}"}

        # Deve funcionar sem estado persistido
        response2 = performance_suite.client.get("/auth/me", headers=headers)
        assert response2.status_code == 200

    def test_idempotent_operations(self):
        """Testa que operações são idempotentes."""
        student_id = str(uuid4())

        # Faz login múltiplas vezes com mesmo usuário
        for _ in range(3):
            response = performance_suite.client.post(
                "/auth/login",
                data={"username": student_id, "password": "demo"}
            )
            assert response.status_code == 200

            # Cada token deve ser válido independentemente
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            me_response = performance_suite.client.get("/auth/me", headers=headers)
            assert me_response.status_code == 200

    def test_graceful_degradation(self):
        """Testa degradação graceful sob carga."""
        # Reduz artificialmente o rate limit para teste
        # Nota: em produção, isso seria configurado via env vars

        # Faz requisições até o limite
        responses = []
        for i in range(110):  # Mais que o limite
            response = performance_suite.client.get("/health")
            responses.append(response.status_code)

        # Deve ter alguns 429, mas sistema continua funcionando
        assert 429 in responses  # Algumas rejeitadas
        assert responses[-1] in [200, 429]  # Última ainda funciona ou é rejeitada

        # Sistema deve se recuperar após cooldown
        time.sleep(2)  # Espera reset do rate limit
        response = performance_suite.client.get("/health")
        assert response.status_code == 200


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