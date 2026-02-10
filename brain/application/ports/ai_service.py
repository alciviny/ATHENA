from abc import ABC, abstractmethod
from typing import Dict, Any, List

# Se precisares importar KnowledgeNode para tipagem, usa TYPE_CHECKING para evitar ciclo
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from brain.domain.entities.knowledge_node import KnowledgeNode

class AIService(ABC):
    """
    Porta (Interface) para serviços de Inteligência Artificial.
    """

    @abstractmethod
    async def validate_feynman_explanation(
        self,
        node_content: Dict[str, Any],
        explanation: str,
        subject: str,
        difficulty: float,
    ) -> Dict[str, Any]:
        """
        Avalia a explicação de um conceito feita pelo aluno (Técnica Feynman).
        """
        pass

    @abstractmethod
    async def generate_scenario(
        self, 
        node: "KnowledgeNode", 
        stress_level: float
    ) -> Dict[str, Any]:
        """
        Gera um cenário prático (Prediction-Based Learning) baseado no nó.
        
        Returns:
            Dict com chaves: 'scenario_text', 'expected_outcome', 'difficulty_adjusted'.
        """
        pass

    @abstractmethod
    async def generate_flashcard(
        self,
        topic: str,
        difficulty: int,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Gera um flashcard de múltipla escolha para um tópico.
        
        Returns:
            Dict com chaves: 'pergunta', 'opcoes', 'correta_index', 'explicacao'.
        """
        pass

    @abstractmethod
    async def analyze_student_errors(
        self,
        errors: list,
        subject: str,
    ) -> str:
        """
        Analisa os erros do aluno em uma matéria e retorna um texto de análise.
        """
        pass

    @abstractmethod
    async def generate_embedding(
        self,
        text: str
    ) -> List[float]:
        """
        Gera um vetor de embedding para o texto fornecido.
        
        Returns:
            Lista de floats representando o embedding do texto.
        """
        pass