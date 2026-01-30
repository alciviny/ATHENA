from abc import ABC, abstractmethod
from typing import List, Dict, Any

from brain.domain.entities.error_event import ErrorEvent


class AIService(ABC):
    """
    Porta para serviços de IA Generativa.
    Responsável por Análise (Crítica) e Geração (Criativa).
    """

    @abstractmethod
    async def analyze_student_errors(
        self,
        errors: List[ErrorEvent],
        subject: str,
    ) -> str:
        """
        Analisa padrões de erro do aluno e sugere plano de correção.
        """
        pass

    @abstractmethod
    async def generate_flashcard(
        self,
        topic: str,
        difficulty: int,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Gera uma questão de estudo (Flashcard) baseada em um tópico.

        :param topic: O assunto (ex: "Cinemática").
        :param difficulty: Nível de 1 a 5.
        :param context: Texto de referência (RAG) para evitar alucinação.
        :return: Um dicionário com:
            - pergunta: str
            - opcoes: List[str]
            - correta_index: int
            - explicacao: str
        """
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Gera o vetor (embedding) para um texto.
        """
        pass
