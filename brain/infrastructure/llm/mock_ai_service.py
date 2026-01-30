import time
import logging
import asyncio
from typing import List, Dict, Any

from brain.application.ports.ai_service import AIService
from brain.domain.entities.error_event import ErrorEvent

logger = logging.getLogger(__name__)


class MockAIService(AIService):
    """
    Implementação Mock do serviço de IA para fins de desenvolvimento e teste.

    Simula o comportamento de um LLM, retornando uma análise pré-definida
    após um delay configurável.
    """

    def __init__(self, delay_seconds: float = 1.0) -> None:
        """
        :param delay_seconds: Tempo de espera (em segundos) para simular latência.
                              Use 0 em testes rápidos.
        """
        self.delay_seconds = delay_seconds

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Simula a geração de um embedding. Retorna um vetor fixo de 768 dimensões.
        """
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)
        
        return [0.1] * 768

    async def generate_flashcard(
        self, topic: str, difficulty: int, context: str
    ) -> Dict[str, Any]:
        """
        Simula a geração de um flashcard, retornando um exemplo fixo.
        """
        logger.info(f"Mock AI Service: Gerando flashcard para o tópico '{topic}'.")

        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        # Resposta determinística para testes
        flashcard = {
            "pergunta": f"Qual é o conceito fundamental de '{topic}'?",
            "opcoes": [
                f"Opção A sobre {topic}",
                f"Opção B sobre {topic}",
                f"Opção C sobre {topic}",
                f"Opção D sobre {topic}",
            ],
            "correta_index": 0,
            "explicacao": f"Esta é uma explicação detalhada sobre por que a Opção A é a resposta correta para a pergunta sobre '{topic}'. A dificuldade foi {difficulty}.",
        }

        logger.info(f"Mock AI Service: Flashcard para '{topic}' gerado.")
        return flashcard

    async def analyze_student_errors(
        self,
        errors: List[ErrorEvent],
        subject: str,
    ) -> str:
        """
        Simula a análise de erros, retornando uma resposta determinística.
        """
        logger.info(
            "Mock AI Service: Analisando %s erros na matéria '%s'",
            len(errors),
            subject,
        )

        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if not errors:
            logger.info("Mock AI Service: Nenhum erro encontrado para análise.")
            return "Nenhum erro encontrado para análise."

        # Usa sorted para garantir determinismo em testes
        error_topics = sorted({error.topic for error in errors})

        analysis = (
            f"Análise simulada para a matéria '{subject}':\n"
            f"O aluno parece ter dificuldade consistente nos seguintes tópicos: "
            f"{', '.join(error_topics)}.\n"
            "Sugestão: Revisar os conceitos fundamentais de cada um desses assuntos, "
            "com foco em exercícios práticos de múltipla escolha para fortalecer "
            "o reconhecimento de padrões."
        )

        logger.info("Mock AI Service: Análise concluída com sucesso.")
        return analysis
