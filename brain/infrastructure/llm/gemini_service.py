import logging
import json
from typing import List, Dict, Any

import google.generativeai as genai
from pydantic import BaseModel, Field

from brain.application.ports.ai_service import AIService
from brain.domain.entities.error_event import ErrorEvent

logger = logging.getLogger(__name__)


class FlashcardOutput(BaseModel):
    pergunta: str = Field(..., description="Enunciado da questão")
    opcoes: List[str] = Field(
        ..., description="Lista de 4 alternativas", min_items=4, max_items=4
    )
    correta_index: int = Field(
        ..., description="Índice da alternativa correta (0-3)", ge=0, le=3
    )
    explicacao: str = Field(..., description="Explicação curta da resposta correta")


class GeminiService(AIService):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

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
            # O SDK do Gemini (geralmente) suporta chamadas síncronas que podem ser "envolvidas"
            # mas para manter a simplicidade e seguindo o padrão da interface:
            response = self.model.generate_content(prompt)
            return response.text

        except Exception as exc:
            logger.error(f"Erro no Gemini (analyze_student_errors): {exc}")
            return "Não foi possível gerar a análise no momento."

    async def generate_flashcard(
        self,
        topic: str,
        difficulty: int,
        context: str = "",
    ) -> Dict[str, Any]:
        context_prompt = (
            f"Use EXCLUSIVAMENTE o seguinte contexto como base:\n{context}"
            if context
            else "Use conhecimento acadêmico consolidado."
        )

        prompt = f"""
Você é um gerador de questões educacionais.
Crie uma questão de múltipla escolha sobre o tópico: "{topic}"

Nível de dificuldade: {difficulty}/5

{context_prompt}

Retorne um JSON com os campos:
pergunta, opcoes, correta_index, explicacao
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            content = response.text
            flashcard = FlashcardOutput.model_validate_json(content)

            return flashcard.model_dump()

        except Exception as exc:
            logger.error(f"Erro ao gerar flashcard com Gemini: {exc}")

            return {
                "pergunta": "Erro ao gerar questão.",
                "opcoes": ["-", "-", "-", "-"],
                "correta_index": 0,
                "explicacao": "Falha ao comunicar com o serviço de IA.",
            }
