import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4, UUID
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

# Definição mínima do KnowledgeNode para o teste funcionar de forma autônoma
class KnowledgeNode(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    content: Dict[str, Any] = {}
    subject: Optional[str] = None
    difficulty: float = 5.0
    metadata: Dict[str, Any] = {}

# Importações reais do projeto
from brain.application.ports.ai_service import AIService
from brain.application.services.simulator_service import SimulatorService
from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository


# 1. Mock AIService
class MockAIService(AIService):
    def __init__(self, fake_scenario: Dict[str, Any]):
        self.fake_scenario = fake_scenario

    async def generate_scenario(self, node: KnowledgeNode, stress_level: float) -> Dict[str, Any]:
        """Retorna um cenário fixo para o teste."""
        return self.fake_scenario

    async def validate_feynman_explanation(self, **kwargs) -> Dict[str, Any]:
        """Não é necessário para este teste."""
        return {}


# 2. Classe de Teste Principal
class TestSimulatorLogic(unittest.TestCase):

    def test_simulation_transforms_node_correctly(self):
        """
        Testa se o SimulatorService transforma corretamente um nó
        após receber uma resposta bem-sucedida do MockAIService.
        """
        # Executa o teste assíncrono
        asyncio.run(self.run_async_test())

    async def run_async_test(self):
        # -- ARRANGE (Preparação) --
        student_id = uuid4()
        node_id = uuid4()
        
        # O nó original antes de qualquer transformação
        original_node = KnowledgeNode(
            id=node_id,
            name="Qual a complexidade do algoritmo Bubble Sort?",
            content={"type": "flashcard"},
            subject="Algoritmos"
        )

        # A resposta que esperamos do serviço de IA
        fake_scenario_response = {
            "scenario_text": "Um junior na sua equipe submeteu um código que usa Bubble Sort para ordenar 1 milhão de itens. Qual será a consequência?",
            "expected_outcome": "O sistema ficará extremamente lento ou travará devido à complexidade O(n^2)",
            "difficulty_adjusted": 7.5
        }

        # Mock dos repositórios para isolar o serviço
        mock_knowledge_repo = MagicMock(spec=KnowledgeRepository)
        mock_knowledge_repo.get_full_graph = AsyncMock(return_value=[original_node]) # Retorna nosso nó de teste
        
        mock_performance_repo = MagicMock(spec=PerformanceRepository)
        mock_performance_repo.get_recent_events = AsyncMock(return_value=[]) # Sem histórico de performance

        # Mock do serviço de IA que retorna nosso cenário falso
        mock_ai_service = MockAIService(fake_scenario=fake_scenario_response)

        # Instancia o serviço real com todos os mocks
        simulator = SimulatorService(
            knowledge_repo=mock_knowledge_repo,
            performance_repo=mock_performance_repo,
            ai_service=mock_ai_service
        )

        # -- ACT (Ação) --
        # Chama o método que queremos testar
        final_nodes = await simulator.generate_simulation(student_id=student_id, num_questions=1)

        # -- ASSERT (Verificação) --
        self.assertEqual(len(final_nodes), 1, "A lista final deveria conter um nó.")
        
        transformed_node = final_nodes[0]

        # 1. Verifica se o texto da pergunta (node.name) foi atualizado para o cenário
        self.assertEqual(transformed_node.name, fake_scenario_response["scenario_text"])

        # 2. Verifica se o conteúdo (content) foi enriquecido com os metadados do cenário
        self.assertTrue(transformed_node.content.get("is_scenario"), "A flag 'is_scenario' deveria ser True.")
        self.assertEqual(transformed_node.content.get("expected_outcome"), fake_scenario_response["expected_outcome"])

        # 3. Verifica se a dificuldade foi ajustada dinamicamente
        self.assertEqual(transformed_node.difficulty, fake_scenario_response["difficulty_adjusted"])
        
        print("\n✅ Teste de Lógica do Cenário passou com sucesso!")


if __name__ == "__main__":
    # Para rodar o teste, execute: python test_scenario_logic.py
    unittest.main()
