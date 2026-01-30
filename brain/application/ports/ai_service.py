from abc import ABC, abstractmethod
from typing import List, Dict, Any
from brain.domain.entities.error_event import ErrorEvent

class AIService(ABC):
    """
    Porta para serviços de IA Generativa.
    """

    @abstractmethod
    async def analyze_student_errors(
        self,
        errors: List[ErrorEvent],
        subject: str,
    ) -> str:
        """Analisa padrões de erro."""
        pass

    @abstractmethod
    async def generate_flashcard(
        self,
        topic: str,
        difficulty: int,
        context: str = "",
    ) -> Dict[str, Any]:
        """Gera flashcard."""
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Gera representação vetorial."""
        pass