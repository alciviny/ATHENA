import sys
import asyncio
import logging
from uuid import UUID, uuid4
from typing import List
from datetime import datetime, timezone

from brain.domain.services.study_plan_generator import StudyPlanGenerator
from brain.domain.policies.adaptive_rule import AdaptiveRule
from brain.application.ports.repositories import (
    StudentRepository,
    PerformanceRepository,
    KnowledgeRepository,
    StudyPlanRepository,
    CognitiveProfileRepository,
    KnowledgeVectorRepository,
)
from brain.application.ports.ai_service import AIService
from brain.application.dto.study_plan_dto import StudyPlanDTO, StudySessionDTO, StudyItemDTO

# Configuração do Logger
logger = logging.getLogger(__name__)

class StudentNotFoundError(Exception):
    pass

class GenerateStudyPlanUseCase:
    def __init__(
        self,
        student_repo: StudentRepository,
        performance_repo: PerformanceRepository,
        knowledge_repo: KnowledgeRepository,
        study_plan_repo: StudyPlanRepository,
        cognitive_profile_repo: CognitiveProfileRepository,
        vector_repo: KnowledgeVectorRepository,
        ai_service: AIService,
        adaptive_rules: List[AdaptiveRule]
    ):
        self.student_repo = student_repo
        self.performance_repo = performance_repo
        self.knowledge_repo = knowledge_repo
        self.study_plan_repo = study_plan_repo
        self.cognitive_profile_repo = cognitive_profile_repo
        self.vector_repo = vector_repo
        self.ai_service = ai_service
        self.adaptive_rules = adaptive_rules

    async def execute(self, student_id: UUID) -> StudyPlanDTO:
        logger.info("--- [PLAN-FLOW] 🏁 GenerateStudyPlanUseCase: INICIADO ---")
        
        try:
            # 1. Recuperar dados
            student = await self.student_repo.get_by_id(student_id)
            if not student:
                raise StudentNotFoundError(f"Estudante {student_id} não encontrado.")

            cognitive_profile = await self.cognitive_profile_repo.get_by_student_id(student.id)
            if not cognitive_profile:
                # Lazy creation do perfil cognitivo se não existir
                from brain.domain.entities.cognitive_profile import CognitiveProfile
                cognitive_profile = CognitiveProfile(student_id=student.id)
                await self.cognitive_profile_repo.save(cognitive_profile)
                logger.info(f"[PLAN-FLOW] Novo perfil cognitivo criado para {student_id}")

            recent_events = await self.performance_repo.get_recent_events(student_id)
            all_nodes = await self.knowledge_repo.get_full_graph()

            # 2. Gerar estrutura (Otimização do grafo)
            generator = StudyPlanGenerator(
                knowledge_graph=all_nodes,
                adaptive_rules=self.adaptive_rules
            )

            study_plan = generator.generate(
                student=student,
                cognitive_profile=cognitive_profile,
                performance_events=recent_events
            )
            
            total_nodes = len(study_plan.knowledge_nodes)
            logger.info(f"[PLAN-FLOW] Estrutura do plano criada com {total_nodes} nós.")

            # 3. Gerar conteúdo (Flashcards)
            generated_contents = []
            
            for i, node in enumerate(study_plan.knowledge_nodes):
                logger.info(f"--- [PLAN-FLOW] Processando Nó {i+1}/{total_nodes}: '{node.name}' ---")
                
                # A. Busca Contexto (RAG)
                rag_context = ""
                try:
                    # Tenta buscar contexto, mas não falha o processo se der erro no vetor
                    rag_context = await self.vector_repo.search_context(query=node.name, limit=1)
                except Exception as e:
                    logger.warning(f"[PLAN-FLOW] ⚠️ RAG Ignorado para '{node.name}': {e}")
                
                final_context = rag_context if rag_context else f"Conceitos fundamentais de {node.name}"

                # B. Gera Card (AI) - Com Retry Interno do Service e Fallback aqui
                try:
                    card = await self.ai_service.generate_flashcard(
                        topic=node.name,
                        difficulty=int(node.difficulty * 5),
                        context=final_context
                    )
                    generated_contents.append(card)
                    logger.info(f"[PLAN-FLOW] ✅ Conteúdo gerado com sucesso para '{node.name}'")
                
                except Exception as e:
                    logger.error(f"[PLAN-FLOW] ❌ FALHA CRÍTICA NA IA para '{node.name}': {e}")
                    # Fallback de emergência: Cria um card manual para o usuário não ficar travado
                    generated_contents.append({
                        "pergunta": f"Pratique os conceitos de: {node.name}",
                        "opcoes": [
                            "Revisar Documentação Oficial",
                            "Fazer Exercício Prático",
                            "Ver Vídeo Aula",
                            "Ler Anotações"
                        ],
                        "correta_index": 0,
                        "explicacao": "A IA estava indisponível temporariamente, mas este tópico é crucial para seu plano."
                    })

                # C. PAUSA DE SEGURANÇA (Rate Limit Prevention)
                # Pausa entre nós para evitar "429 Resource Exhausted" do Google
                if i < total_nodes - 1:
                    logger.info("[PLAN-FLOW] 🛌 Descansando 5s para poupar cota da API...")
                    await asyncio.sleep(5)

            # 4. Salvar
            logger.info("[PLAN-FLOW] Salvando plano de estudos no banco...")
            await self.study_plan_repo.save(study_plan)

            # 5. Formatar DTO
            logger.info("[PLAN-FLOW] Formatando resposta (DTO)...")
            sessions_dto = []
            for i, node in enumerate(study_plan.knowledge_nodes):
                content = generated_contents[i]
                
                item = StudyItemDTO(
                    id=str(node.id),
                    type="flashcard",
                    content={
                        "front": content.get("pergunta", "Questão"),
                        "options": content.get("opcoes", []),
                        "correct_index": content.get("correta_index", 0),
                        "back": content.get("explicacao", "")
                    },
                    estimated_time_minutes=5,
                    difficulty=node.difficulty,
                    status="pending"
                )

                # CORREÇÃO CRÍTICA DO ENUM
                # Converte enum para string seguramente
                f_level = study_plan.focus_level
                if hasattr(f_level, 'value'):
                    f_level_str = f_level.value
                else:
                    f_level_str = str(f_level)

                session = StudySessionDTO(
                    id=str(uuid4()),
                    topic=node.name,
                    start_time=datetime.now(timezone.utc),
                    duration_minutes=15,
                    items=[item],
                    focus_level=f_level_str,
                    method="pomodoro"
                )
                sessions_dto.append(session)

            logger.info("[PLAN-FLOW] 🎉 Plano gerado e entregue com sucesso!")
            
            return StudyPlanDTO(
                id=str(study_plan.id),
                student_id=str(student.id),
                goals=["Plano Adaptativo"],
                created_at=study_plan.created_at,
                sessions=sessions_dto,
                status="created"
            )

        except Exception as e:
            logger.critical(f"[PLAN-FLOW] 💀 CRITICAL ERROR: {e}", exc_info=True)
            raise e