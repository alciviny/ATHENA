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
    def __init__(self, api_key: str, model: str = "models/gemini-1.5-flash"):
        # FORÇANDO O FLASH: Mesmo que venha outro valor, o default é o Flash.
        # Se você estiver passando "models/gemini-pro-latest" pelo settings.py, mude lá também!
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model_name=model)
        logger.info(f"GeminiService inicializado com modelo: {self.model_name}")

    async def _retry_operation(self, func, *args, **kwargs):
        """Tenta executar uma operação com backoff exponencial em caso de erro 429."""
        retries = 5 # Aumentei para 5 tentativas
        base_delay = 5 # Começa esperando 5 segundos (mais conservador)
        
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except google_exceptions.ResourceExhausted:
                wait_time = base_delay * (2 ** attempt)
                logger.warning(f"Cota excedida (429). Tentativa {attempt+1}/{retries}. Aguardando {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Erro não relacionado a cota: {e}")
                raise e
        
        raise Exception("Falha após múltiplas tentativas devido a limite de cota.")

    async def generate_embedding(self, text: str) -> List[float]:
        async def _call_embed():
            # Embeddings também sofrem rate limit, protegemos aqui
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']

        try:
            return await self._retry_operation(_call_embed)
        except Exception as e:
            logger.error(f"Erro fatal no embedding: {e}")
            return []

    async def analyze_student_errors(self, errors: List[ErrorEvent], subject: str) -> str:
        if not errors:
            return "Sem erros suficientes para análise."

        errors_desc = "\n".join(f"- Tópico: {e.topic} (Severidade: {e.severity})" for e in errors)
        prompt = f"Analise erros em {subject}:\n{errors_desc}\nProponha correção."

        async def _call_analyze():
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text

        try:
            return await self._retry_operation(_call_analyze)
        except:
            return "Análise indisponível."

    async def generate_flashcard(self, topic: str, difficulty: int, context: str = "") -> Dict[str, Any]:
        context_prompt = (
            f"Contexto:\n{context}" if context else "Use conhecimento acadêmico."
        )

        prompt = f"""
        Crie questão múltipla escolha sobre "{topic}" (Dif: {difficulty}/5).
        {context_prompt}
        JSON OBRIGATÓRIO:
        {{
          "pergunta": "...",
          "opcoes": ["...", "...", "...", "..."],
          "correta_index": 0,
          "explicacao": "..."
        }}
        """

        async def _call_generate():
            resp = await asyncio.to_thread(self.model.generate_content, prompt)
            content = resp.text
            # Limpeza robusta do JSON
            json_str = content.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            return FlashcardOutput.model_validate_json(json_str.strip()).model_dump()

        try:
            return await self._retry_operation(_call_generate)
        except Exception as exc:
            logger.error(f"Erro flashcard: {exc}")
            return {
                "pergunta": f"Erro ao gerar: {topic}",
                "opcoes": ["Tente novamente", "Erro na IA", "Verifique logs", "Wait"],
                "correta_index": 0,
                "explicacao": "Falha na comunicação com a IA."
            }