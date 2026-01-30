import logging
import asyncio
import json
from typing import List, Dict, Any

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import BaseModel, Field

from brain.application.ports.ai_service import AIService
from brain.domain.entities.error_event import ErrorEvent

logger = logging.getLogger(__name__)

class FlashcardOutput(BaseModel):
    pergunta: str = Field(..., description="Enunciado da questão")
    opcoes: List[str] = Field(..., description="Lista de 4 alternativas", min_items=4, max_items=4)
    correta_index: int = Field(..., description="Índice da alternativa correta (0-3)", ge=0, le=3)
    explicacao: str = Field(..., description="Explicação curta da resposta correta")

class GeminiService(AIService):
    # ATUALIZADO: Default para 2.0 Flash
    def __init__(self, api_key: str, model: str = "models/gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model_name=model)
        logger.info(f"GeminiService inicializado com modelo: {self.model_name}")

    async def _retry_operation(self, func, *args, **kwargs):
        retries = 3
        base_delay = 2
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except google_exceptions.ResourceExhausted:
                wait_time = base_delay * (2 ** attempt)
                logger.warning(f"Cota (429). Tentativa {attempt+1}/{retries}. Aguardando {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                # Se o modelo não existir (404), não adianta tentar de novo
                if "404" in str(e) or "not found" in str(e).lower():
                    logger.critical(f"MODELO NÃO ENCONTRADO: {e}")
                    raise e
                raise e
        raise Exception("Falha após múltiplas tentativas.")

    async def generate_embedding(self, text: str) -> List[float]:
        async def _call_embed():
            # ATUALIZADO: Usando text-embedding-004 que está na sua lista
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']

        try:
            return await self._retry_operation(_call_embed)
        except Exception as e:
            logger.error(f"Erro embedding: {e}")
            return []

    async def analyze_student_errors(self, errors: List[ErrorEvent], subject: str) -> str:
        if not errors: return "Sem dados."
        prompt = f"Analise erros em {subject}: {errors}"
        try:
            resp = await self._retry_operation(lambda: asyncio.to_thread(self.model.generate_content, prompt)) # Lambda fix
            # Nota: Versões novas da lib podem retornar corrotina direto, mas to_thread é seguro
            # Se der erro de 'await', remova o to_thread no futuro.
            if asyncio.iscoroutine(resp): resp = await resp
            return resp.text
        except: return "Erro na análise."

    async def generate_flashcard(self, topic: str, difficulty: int, context: str = "") -> Dict[str, Any]:
        prompt = f"""
        Gere JSON para flashcard de "{topic}" (Dif: {difficulty}/5).
        Contexto: {context[:500]}...
        Schema: {{pergunta, opcoes[], correta_index, explicacao}}
        """

        async def _call_generate():
            # Chamada direta para garantir compatibilidade
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            text = response.text
            # Limpeza JSON
            clean_text = text.replace("```json", "").replace("```", "").strip()
            return FlashcardOutput.model_validate_json(clean_text).model_dump()

        try:
            return await self._retry_operation(_call_generate)
        except Exception as e:
            logger.error(f"Erro Card: {e}")
            return {
                "pergunta": f"Erro: {topic}",
                "opcoes": ["-", "-", "-", "-"],
                "correta_index": 0,
                "explicacao": "Falha na IA."
            }