import logging
from typing import List, Dict, Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from brain.application.ports.ai_service import AIService
from brain.domain.entities.error_event import ErrorEvent

logger = logging.getLogger(__name__)


# ---------- Validação Estrutural (JSON Mode) ----------

class FlashcardOutput(BaseModel):
    pergunta: str = Field(..., description="Enunciado da questão")
    opcoes: List[str] = Field(
        ..., description="Lista de 4 alternativas", min_items=4, max_items=4
    )
    correta_index: int = Field(
        ..., description="Índice da alternativa correta (0-3)", ge=0, le=3
    )
    explicacao: str = Field(..., description="Explicação curta da resposta correta")


# ---------- Implementação Real ----------

class OpenAIService(AIService):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def analyze_student_errors(
        self,
        errors: List[ErrorEvent],
        subject: str,
    ) -> str:
        if not errors:
            return "Sem erros suficientes para análise."

        errors_desc = "\n".join(
            f"- Tópico: {e.topic} (Severidade: {e.severity})"
            for e in errors
        )

        prompt = f"""
Você é um tutor pedagógico especialista.

O aluno cometeu os seguintes erros em {subject}:
{errors_desc}

Analise a causa raiz desses erros e proponha um plano de correção prático.
Seja claro, objetivo e encorajador.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            return response.choices[0].message.content or ""

        except Exception as exc:
            logger.error(f"Erro na OpenAI (analyze_student_errors): {exc}")
            return "Não foi possível gerar a análise no momento."

    async def generate_flashcard(
        self,
        topic: str,
        difficulty: int,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        Gera uma questão com GARANTIA de JSON válido usando Pydantic.
        """

        context_prompt = (
            f"Use EXCLUSIVAMENTE o seguinte contexto como base:\n{context}"
            if context
            else "Use conhecimento acadêmico consolidado."
        )

        prompt = f"""
Crie uma questão de múltipla escolha sobre o tópico: "{topic}"

Nível de dificuldade: {difficulty}/5

{context_prompt}

Retorne APENAS um JSON com os campos:
pergunta, opcoes, correta_index, explicacao
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um gerador de questões educacionais. "
                            "Sempre responda exclusivamente em JSON válido."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            content = response.choices[0].message.content
            flashcard = FlashcardOutput.model_validate_json(content)

            return flashcard.model_dump()

        except Exception as exc:
            logger.error(f"Erro ao gerar flashcard: {exc}")

            return {
                "pergunta": "Erro ao gerar questão.",
                "opcoes": ["-", "-", "-", "-"],
                "correta_index": 0,
                "explicacao": "Falha ao comunicar com o serviço de IA.",
            }
