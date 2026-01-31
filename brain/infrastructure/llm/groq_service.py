import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional

from groq import AsyncGroq
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError

from brain.application.ports.ai_service import AIService
from brain.domain.entities.error_event import ErrorEvent

# ============================================================
# LOGGING CONFIG (Docker-friendly)
# ============================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("groq_service")


# ============================================================
# MODELOS
# ============================================================

class FlashcardOutput(BaseModel):
    pergunta: str = Field(..., description="Enunciado da questão")
    opcoes: List[str] = Field(..., min_items=4, max_items=4)
    correta_index: int = Field(..., ge=0, le=3)
    explicacao: str


# ============================================================
# SERVIÇO
# ============================================================

class GroqService(AIService):
    """
    Serviço Híbrido:
    - Geração de texto: Groq (LLaMA 3.x)
    - Embeddings: Google Gemini
    """

    def __init__(
        self,
        groq_api_key: str,
        gemini_api_key: Optional[str],
        model: str = "llama-3.3-70b-versatile",
        max_retries: int = 2,
    ):
        self.client = AsyncGroq(api_key=groq_api_key)
        self.model = model
        self.max_retries = max_retries

        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)

        self.embedding_model = "models/text-embedding-004"

        logger.info(
            "[INIT] Serviço Groq híbrido iniciado | "
            f"Model={self.model} | Embeddings=Gemini | Retries={self.max_retries}"
        )

    # ========================================================
    # FLASHCARD
    # ========================================================

    async def generate_flashcard(
        self,
        topic: str,
        difficulty: int,
        context: str = "",
    ) -> Dict[str, Any]:

        temperature = 0.2 if difficulty <= 2 else 0.5

        prompt = f"""
Você é um professor especialista.

Crie UM flashcard sobre:
Tema: "{topic}"
Dificuldade: {difficulty}/5

Contexto:
{context[:800]}

RETORNE EXCLUSIVAMENTE JSON VÁLIDO no formato:

{{
  "pergunta": "...",
  "opcoes": ["A", "B", "C", "D"],
  "correta_index": 0,
  "explicacao": "..."
}}
"""

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"[FLASHCARD] Gerando | Topic='{topic}' | "
                    f"Difficulty={difficulty} | Attempt={attempt}"
                )

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Você responde APENAS com JSON válido. "
                                "Sem markdown, sem comentários, sem texto extra."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                )

                content = response.choices[0].message.content

                flashcard = FlashcardOutput.model_validate_json(content)

                logger.info(
                    "[FLASHCARD] Sucesso | "
                    f"Pergunta='{flashcard.pergunta[:60]}...'"
                )

                return flashcard.model_dump()

            except ValidationError as ve:
                logger.error(
                    "[FLASHCARD-VALIDATION] JSON inválido retornado pelo modelo",
                    exc_info=ve,
                )
                logger.debug(f"[FLASHCARD-RAW] {content}")

            except Exception as e:
                logger.error(
                    "[FLASHCARD-ERROR] Falha ao gerar flashcard",
                    exc_info=e,
                )

            await asyncio.sleep(0.5)

        logger.critical(
            f"[FLASHCARD] Falha definitiva após {self.max_retries} tentativas"
        )
        raise RuntimeError("Não foi possível gerar flashcard válido")

    # ========================================================
    # ANÁLISE DE ERROS DO ALUNO
    # ========================================================

    async def analyze_student_errors(
        self,
        errors: List[ErrorEvent],
        subject: str,
    ) -> str:

        if not errors:
            logger.warning("[ANALYSIS] Sem erros fornecidos")
            return "Sem dados suficientes para análise."

        errors_payload = [e.model_dump() for e in errors]

        prompt = (
            f"Analise os erros recentes do aluno na disciplina {subject}.\n\n"
            f"Erros:\n{json.dumps(errors_payload, ensure_ascii=False)}\n\n"
            "Sugira estratégias pedagógicas claras e objetivas."
        )

        try:
            logger.info(
                f"[ANALYSIS] Iniciando análise | Subject={subject} | "
                f"Errors={len(errors)}"
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            result = response.choices[0].message.content

            logger.info("[ANALYSIS] Análise concluída com sucesso")

            return result

        except Exception as e:
            logger.error(
                "[ANALYSIS-ERROR] Falha na análise de erros",
                exc_info=e,
            )
            return "Não foi possível analisar os erros no momento."

    # ========================================================
    # EMBEDDINGS
    # ========================================================

    async def generate_embedding(self, text: str) -> List[float]:
        if not text.strip():
            logger.warning("[EMBEDDING] Texto vazio recebido")
            return []

        try:
            logger.info(
                f"[EMBEDDING] Gerando embedding | Size={len(text)} chars"
            )

            result = await asyncio.to_thread(
                genai.embed_content,
                model=self.embedding_model,
                content=text,
                task_type="retrieval_query",
            )

            embedding = result["embedding"]

            logger.info(
                f"[EMBEDDING] Sucesso | Dim={len(embedding)}"
            )

            return embedding

        except Exception as e:
            logger.critical(
                "[EMBEDDING-ERROR] Falha ao gerar embedding",
                exc_info=e,
            )
            raise RuntimeError("Embedding indisponível")
