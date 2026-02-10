import logging
import asyncio
import json
import time
from typing import List, Dict, Any

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import BaseModel, Field

from brain.application.ports.ai_service import AIService
from brain.domain.entities.error_event import ErrorEvent
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.exceptions import (
    AIServiceError,
    AIQuotaExceededError,
    AITimeoutError,
    AIInvalidResponseError,
    AIModelNotFoundError
)
from brain.infrastructure.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from brain.infrastructure.logging import get_logger

logger = get_logger(__name__)


class FlashcardOutput(BaseModel):
    pergunta: str = Field(..., description="Enunciado da questão")
    opcoes: List[str] = Field(..., description="Lista de 4 alternativas", min_items=4, max_items=4)
    correta_index: int = Field(..., description="Índice da alternativa correta (0-3)", ge=0, le=3)
    explicacao: str = Field(..., description="Explicação curta da resposta correta")


class ScenarioOutput(BaseModel):
    scenario_text: str = Field(..., description="Texto do cenário prático proposto.")
    expected_outcome: str = Field(..., description="Resultado ou solução esperada para o cenário.")
    difficulty_adjusted: float = Field(..., description="Nível de dificuldade ajustado pelo LLM (0.0 a 1.0).", ge=0.0, le=1.0)


class GeminiService(AIService):
    def __init__(self, api_key: str, model: str = "models/gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Circuit breaker para proteção contra falhas
        self.circuit_breaker = CircuitBreaker(
            name="gemini",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout=60
            )
        )
        
        logger.info(
            "GeminiService inicializado",
            model=self.model_name,
            circuit_breaker="enabled"
        )

    async def _retry_operation(self, func, operation_name: str, *args, **kwargs):
        """
        Executa com retries e backoff agressivo para erro 429.
        Protegido por circuit breaker.
        """
        retries = 3
        base_delay = 5

        logger.info("Iniciando operação", operation=operation_name)

        for attempt in range(retries):
            try:
                start_time = time.time()

                # Executa a função protegida pelo circuit breaker
                result = await self.circuit_breaker.call(func, *args, **kwargs)

                elapsed = time.time() - start_time
                logger.info(
                    "Operação bem-sucedida",
                    operation=operation_name,
                    attempt=attempt + 1,
                    duration_seconds=round(elapsed, 2)
                )
                return result

            except google_exceptions.ResourceExhausted as e:
                # Cota excedida - erro 429
                wait_time = 65 + (20 * attempt)
                logger.warning(
                    "Cota de API excedida",
                    operation=operation_name,
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                    error=str(e)
                )
                
                if attempt == retries - 1:
                    raise AIQuotaExceededError(
                        f"Cota do Gemini excedida após {retries} tentativas",
                        provider="gemini",
                        retry_after=wait_time
                    )
                
                await asyncio.sleep(wait_time)

            except google_exceptions.NotFound as e:
                logger.error(
                    "Modelo não encontrado",
                    operation=operation_name,
                    model=self.model_name,
                    error=str(e)
                )
                raise AIModelNotFoundError(
                    f"Modelo {self.model_name} não existe",
                    provider="gemini"
                )

            except Exception as e:
                # Erros genéricos (rede, timeout)
                if "404" in str(e) or "not found" in str(e).lower():
                    raise AIModelNotFoundError(
                        f"Modelo {self.model_name} não encontrado",
                        provider="gemini"
                    )

                wait_time = base_delay * (2 ** attempt)
                logger.error(
                    "Erro na operação",
                    operation=operation_name,
                    attempt=attempt + 1,
                    error_type=e.__class__.__name__,
                    error=str(e)
                )
                
                if attempt < retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise AIServiceError(
                        f"Falha após {retries} tentativas na operação: {operation_name}",
                        provider="gemini"
                    )

        logger.critical("Falha total na operação", operation=operation_name)
        raise AIServiceError(
            f"Falha após múltiplas tentativas na operação: {operation_name}",
            provider="gemini"
        )

    async def generate_embedding(self, text: str) -> List[float]:
        async def _call_embed():
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']

        try:
            return await self._retry_operation(_call_embed, "Embedding")
        except Exception as e:
            logger.error("Erro ao gerar embedding", error=str(e), error_type=e.__class__.__name__)
            return []

    async def analyze_student_errors(self, errors: List[ErrorEvent], subject: str) -> str:
        if not errors: return "Sem dados."
        prompt = f"Analise erros em {subject}: {errors}"

        async def _call_analyze():
            resp = await asyncio.to_thread(self.model.generate_content, prompt)
            return resp.text

        try:
            return await self._retry_operation(_call_analyze, "Analyze Errors")
        except Exception as e:
            logger.error(
                "Erro ao analisar erros do estudante",
                subject=subject,
                error_count=len(errors),
                error=str(e)
            )
            return "Erro na análise."

    async def generate_flashcard(self, topic: str, difficulty: int, context: str = "") -> Dict[str, Any]:
        prompt = f"""
        Gere JSON para flashcard de "{topic}" (Dif: {difficulty}/5).
        Contexto: {context[:500]}...
        Schema: {{pergunta, opcoes[], correta_index, explicacao}}
        """

        async def _call_generate():
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            text = response.text
            return FlashcardOutput.model_validate_json(text).model_dump()

        try:
            return await self._retry_operation(_call_generate, f"Card: {topic}")
        except Exception as e:
            logger.error(
                "Erro ao gerar flashcard",
                topic=topic,
                difficulty=difficulty,
                error=str(e)
            )
            raise

    async def generate_scenario(self, node: KnowledgeNode, stress_level: float) -> Dict[str, Any]:
        prompt = f"""
        You are an expert Mentor in '{node.subject}'.
        The student is reviewing the concept: '{node.name}'.
        Context data: {node.content}.

        Task: Create a practical, high-stakes scenario where this concept is the key to the solution.
        - If the subject is technical (Code, Math), provide a broken snippet or formula.
        - If the subject is abstract (Philosophy, Law), present a moral dilemma or a complex case study.
        - If the subject is visual (Anatomy, Geography), describe a scene or map.

        Stress Level is {stress_level} (0.0 to 1.0).
        - High stress: make the scenario ambiguous, with time pressure and red herrings.
        - Low stress: make it a clear, textbook example.
        
        Output MUST be a JSON object matching this Pydantic schema:
        {{
            "scenario_text": "str",
            "expected_outcome": "str",
            "difficulty_adjusted": "float"
        }}
        """

        async def _call_generate():
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            # O Gemini com `application/json` já retorna um objeto JSON, sem ```json
            return ScenarioOutput.model_validate_json(response.text).model_dump()

        try:
            return await self._retry_operation(_call_generate, f"Scenario: {node.name}")
        except Exception as e:
            logger.error(
                "Erro ao gerar cenário",
                node_id=str(node.id),
                node_name=node.name,
                stress_level=stress_level,
                error=str(e)
            )
            raise