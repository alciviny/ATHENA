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

logger = logging.getLogger(__name__)

class FlashcardOutput(BaseModel):
    pergunta: str = Field(..., description="Enunciado da questão")
    opcoes: List[str] = Field(..., description="Lista de 4 alternativas", min_items=4, max_items=4)
    correta_index: int = Field(..., description="Índice da alternativa correta (0-3)", ge=0, le=3)
    explicacao: str = Field(..., description="Explicação curta da resposta correta")

class GeminiService(AIService):
    # MUDANÇA: 'gemini-1.5-flash' é o oficial estável para Free Tier.
    def __init__(self, api_key: str, model: str = "models/gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model_name=model)
        logger.info(f"[GEMINI-PROBE] GeminiService inicializado com modelo ESTÁVEL: {self.model_name}")

    async def _retry_operation(self, func, operation_name: str, *args, **kwargs):
        """
        Executa com retries e backoff agressivo para erro 429.
        """
        retries = 3
        base_delay = 5  

        logger.info(f"[GEMINI-PROBE] 🚀 Iniciando: '{operation_name}'")

        for attempt in range(retries):
            try:
                start_time = time.time()
                
                # Executa a função
                result = await func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                logger.info(f"[GEMINI-PROBE] ✅ SUCESSO na tentativa {attempt+1}! ({elapsed:.2f}s)")
                return result

            except google_exceptions.ResourceExhausted as e:
                # Se der cota, espera 65s (para garantir o reset de 1 minuto da janela do Google)
                wait_time = 65 + (20 * attempt)
                logger.error(f"[GEMINI-PROBE] 🛑 COTA (429) na tentativa {attempt+1}.")
                logger.warning(f"[GEMINI-PROBE] ⏳ DORMINDO {wait_time}s para resetar a janela...")
                await asyncio.sleep(wait_time)
                logger.info("[GEMINI-PROBE] ⏰ Acordando...")

            except Exception as e:
                # Erros genéricos (rede, timeout)
                if "404" in str(e) or "not found" in str(e).lower():
                    logger.critical(f"[GEMINI-PROBE] 💀 MODELO NÃO EXISTE: {e}")
                    raise e
                
                wait_time = base_delay * (2 ** attempt)
                logger.error(f"[GEMINI-PROBE] 💥 Erro na tentativa {attempt+1}: {e}")
                await asyncio.sleep(wait_time)

        logger.critical(f"[GEMINI-PROBE] 💀 FALHA TOTAL em '{operation_name}'.")
        raise Exception("Falha após múltiplas tentativas.")

    async def generate_embedding(self, text: str) -> List[float]:
        async def _call_embed():
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']

        try:
            return await self._retry_operation(_call_embed, f"Embedding")
        except:
            return []

    async def analyze_student_errors(self, errors: List[ErrorEvent], subject: str) -> str:
        if not errors: return "Sem dados."
        prompt = f"Analise erros em {subject}: {errors}"
        
        async def _call_analyze():
            resp = await asyncio.to_thread(self.model.generate_content, prompt)
            return resp.text

        try:
            return await self._retry_operation(_call_analyze, "Analyze Errors")
        except: 
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
            clean_text = text.replace("```json", "").replace("```", "").strip()
            return FlashcardOutput.model_validate_json(clean_text).model_dump()

        try:
            return await self._retry_operation(_call_generate, f"Card: {topic}")
        except Exception as e:
            # O UseCase já tem fallback, então aqui só relançamos
            raise e