from abc import ABC, abstractmethod
from typing import List

from brain.domain.entities.error_event import ErrorEvent


class AIService(ABC):
    """
    Porta para serviços de Inteligência Artificial.

    Define a interface para analisar qualitativamente os erros de um aluno,
    abstraindo a implementação concreta (OpenAI, Gemini, etc.).
    """

    @abstractmethod
    def analyze_student_errors(
        self,
        errors: List[ErrorEvent],
        subject: str,
    ) -> str:
        """
        Analisa uma lista de erros e retorna uma análise qualitativa.

        :param errors: Lista de eventos de erro do aluno.
        :param subject: Matéria em foco para a análise.
        :return: Uma string com a análise e sugestões.
        """
        pass