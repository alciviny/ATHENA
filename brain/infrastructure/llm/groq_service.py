import json
import logging
from typing import Dict, Any, List
from groq import AsyncGroq

from brain.application.ports.ai_service import AIService
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.config.settings import settings
from brain.domain.exceptions import AIServiceError, AIInvalidResponseError
from brain.infrastructure.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from brain.infrastructure.logging import get_logger

logger = get_logger(__name__)

class GroqService(AIService):
    """
    Implementação do serviço de IA usando a API da Groq.
    Focado em alta velocidade e inferência "Universal".
    """

    def __init__(self):
        api_key = settings.GROQ_API_KEY
        if not api_key:
            logger.warning("GROQ_API_KEY não configurada")
        
        self.client = AsyncGroq(api_key=api_key)
        # Modelo atualizado - llama3-70b-8192 foi descontinuado
        self.model = "llama-3.3-70b-versatile"
        
        # Circuit breaker para proteção
        self.circuit_breaker = CircuitBreaker(
            name="groq",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout=60
            )
        )
        
        logger.info(
            "GroqService inicializado",
            model=self.model,
            circuit_breaker="enabled"
        ) 

    async def validate_feynman_explanation(
        self,
        node_content: Dict[str, Any],
        explanation: str,
        subject: str,
        difficulty: float,
    ) -> Dict[str, Any]:
        """
        Valida uma explicação usando o modelo da Groq.
        """
        system_prompt = (
            f"Você é um especialista em {subject}. "
            "Sua tarefa é avaliar a explicação de um estudante sobre um conceito técnico.\n"
            "Retorne APENAS um JSON com o seguinte formato:\n"
            "{\n"
            '  "score": <float entre 0.0 e 1.0>,\n'
            '  "feedback": "<texto curto e direto sobre a qualidade da explicação>",\n'
            '  "missing_concepts": ["<conceito1>", "<conceito2>"]\n'
            "}"
        )

        user_prompt = (
            f"Conceito Original: {node_content}\n"
            f"Explicação do Estudante: {explanation}\n"
        )

        return await self._call_groq_json(system_prompt, user_prompt)

    async def generate_scenario(self, node: KnowledgeNode, stress_level: float) -> Dict[str, Any]:
        """
        Gera um cenário prático universal usando o prompt "Camaleão".
        """
        subject = node.subject if node.subject else "General Knowledge"
        
        system_prompt = (
            f"You are an expert Mentor in '{subject}'. "
            "Your goal is to test the student's intuition and prediction skills.\n"
            "Return ONLY a JSON object with this format:\n"
            "{\n"
            '  "scenario_text": "<The problem description/scenario>",\n'
            '  "expected_outcome": "<The logical consequence or correct prediction>",\n'
            '  "difficulty_adjusted": <float 1.0-10.0>\n'
            "}"
        )

        user_prompt = (
            f"Topic: {node.name}\n"
            f"Context Data: {node.content}\n"
            f"Stress Level: {stress_level} (0.0=Textbook, 1.0=Chaos/Ambiguous)\n\n"
            "Task: Create a practical, high-stakes scenario where this concept is the key.\n"
            "- If Technical (Code/Math): Provide a broken snippet or formula.\n"
            "- If Abstract (Philosophy/Law): Present a moral dilemma or case study.\n"
            "- If Visual (Trading/Geo): Describe a market setup or map scene.\n"
            "Ask the student to PREDICT the outcome."
        )

        return await self._call_groq_json(system_prompt, user_prompt)

    async def generate_flashcard(self, topic: str, difficulty: int, context: str = "") -> Dict[str, Any]:
        """
        Gera um flashcard de múltipla escolha usando o modelo da Groq.
        """
        system_prompt = (
            "You are an expert educator creating multiple-choice questions.\n"
            "Return ONLY a JSON object with this exact format:\n"
            "{\n"
            '  "pergunta": "<The question text>",\n'
            '  "opcoes": ["<option1>", "<option2>", "<option3>", "<option4>"],\n'
            '  "correta_index": <index of correct answer 0-3>,\n'
            '  "explicacao": "<Brief explanation of the correct answer>"\n'
            "}"
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Difficulty: {difficulty}/5\n"
            f"Context: {context[:500]}...\n\n"
            "Task: Create a well-crafted multiple-choice question that tests understanding of this topic.\n"
            "- Make the question clear and specific\n"
            "- Provide 4 plausible options\n"
            "- Only one option should be correct\n"
            "- Include a brief explanation of why the correct answer is right"
        )

        return await self._call_groq_json(system_prompt, user_prompt)

    async def analyze_student_errors(self, errors: list, subject: str) -> str:
        """
        Analisa os erros do aluno usando o modelo da Groq.
        """
        if not errors:
            return f"Nenhum erro encontrado para análise na matéria '{subject}'."

        errors_summary = []
        for e in errors:
            error_type = getattr(e, 'error_type', 'desconhecido')
            severity = getattr(e, 'severity', 0.0)
            errors_summary.append(f"- Tipo: {error_type}, Severidade: {severity:.1f}")

        errors_text = "\n".join(errors_summary[:20])  # Limita a 20 erros

        system_prompt = (
            f"Você é um tutor especialista em {subject}. "
            "Analise os erros do aluno e forneça uma análise concisa com:\n"
            "1. Padrões identificados nos erros\n"
            "2. Pontos fracos principais\n"
            "3. Sugestões práticas de estudo\n"
            "Responda em português, de forma direta e objetiva."
        )

        user_prompt = (
            f"Matéria: {subject}\n"
            f"Total de erros: {len(errors)}\n"
            f"Detalhamento:\n{errors_text}"
        )

        try:
            result = await self._call_groq_json(system_prompt, user_prompt)
            # Se veio JSON, extraímos o texto
            if isinstance(result, dict):
                return result.get("analysis", result.get("feedback", json.dumps(result, ensure_ascii=False)))
            return str(result)
        except Exception as e:
            logger.error("Erro ao analisar erros do estudante", error=str(e))
            return f"Não foi possível analisar os erros em '{subject}' neste momento."

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Groq não oferece API de embeddings nativa.
        Retorna lista vazia - o código chamador deve lidar com isso.
        """
        logger.debug(
            "GroqService não suporta embeddings nativamente",
            text_length=len(text)
        )
        return []

    async def _call_groq_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Helper para chamadas JSON seguras com circuit breaker."""
        
        async def _make_call():
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model,
                temperature=0.4,
                response_format={"type": "json_object"},
            )

            response_content = chat_completion.choices[0].message.content
            if not response_content:
                raise AIInvalidResponseError(
                    "Resposta vazia da Groq API",
                    provider="groq"
                )

            return json.loads(response_content)
        
        try:
            return await self.circuit_breaker.call(_make_call)
        except json.JSONDecodeError as e:
            logger.error(
                "Erro ao parsear JSON da resposta",
                error=str(e),
                provider="groq"
            )
            raise AIInvalidResponseError(
                "Resposta da Groq não é um JSON válido",
                provider="groq"
            )
        except Exception as e:
            logger.error(
                "Erro ao chamar Groq API",
                error=str(e),
                error_type=e.__class__.__name__
            )
            # Fallback genérico para não quebrar o fluxo
            return {
                "scenario_text": "Error generating AI scenario. Review the concept conventionally.",
                "expected_outcome": "N/A",
                "difficulty_adjusted": 5.0,
                "score": 0.0,
                "feedback": "Service Error",
                "missing_concepts": []
            }