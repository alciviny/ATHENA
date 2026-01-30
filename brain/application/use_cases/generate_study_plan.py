import sys
import asyncio
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
        print("--- GenerateStudyPlanUseCase: START ---")
        try:
            # 1. Recuperar dados
            student = await self.student_repo.get_by_id(student_id)
            if not student:
                raise StudentNotFoundError(f"Estudante {student_id} não encontrado.")

            cognitive_profile = await self.cognitive_profile_repo.get_by_student_id(student.id)
            if not cognitive_profile:
                from brain.domain.entities.cognitive_profile import CognitiveProfile
                cognitive_profile = CognitiveProfile(student_id=student.id)
                await self.cognitive_profile_repo.save(cognitive_profile)

            recent_events = await self.performance_repo.get_recent_events(student_id)
            all_nodes = await self.knowledge_repo.get_full_graph()

            # 2. Gerar estrutura
            generator = StudyPlanGenerator(
                knowledge_graph=all_nodes,
                adaptive_rules=self.adaptive_rules
            )

            study_plan = generator.generate(
                student=student,
                cognitive_profile=cognitive_profile,
                performance_events=recent_events
            )
            print(f"Plan structure created with {len(study_plan.knowledge_nodes)} nodes.")

            # 3. Gerar conteúdo (Flashcards)
            generated_contents = []
            
            for i, node in enumerate(study_plan.knowledge_nodes):
                print(f"[{i+1}/{len(study_plan.knowledge_nodes)}] Generating AI content for: {node.name}")
                
                # A. Busca Contexto (RAG) - Com tratamento de erro silencioso
                rag_context = ""
                try:
                    rag_context = await self.vector_repo.search_context(query=node.name, limit=1)
                except Exception as e:
                    print(f"   [WARN] RAG Ignored: {e}")
                
                final_context = rag_context if rag_context else f"Conceitos fundamentais de {node.name}"

                # B. Gera Card (AI) - Com Fallback Imediato
                try:
                    card = await self.ai_service.generate_flashcard(
                        topic=node.name,
                        difficulty=int(node.difficulty * 5),
                        context=final_context
                    )
                    generated_contents.append(card)
                    print("   -> Success")
                except Exception as e:
                    print(f"   [ERROR] AI Failed (Using Fallback): {e}")
                    # Fallback para o usuário não ficar sem nada
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

                # C. PAUSA DE SEGURANÇA (5s)
                # Só pausa se não for o último item
                if i < len(study_plan.knowledge_nodes) - 1:
                    print("   Waiting 5s...")
                    await asyncio.sleep(5)

            # 4. Salvar
            print("Step 5: Saving study plan...")
            await self.study_plan_repo.save(study_plan)

            # 5. Formatar DTO
            print("Step 6: Formatting DTO...")
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
                # Garante que seja string, não importa o que venha do domínio
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
                    focus_level=f_level_str, # Agora é string!
                    method="pomodoro"
                )
                sessions_dto.append(session)

            return StudyPlanDTO(
                id=str(study_plan.id),
                student_id=str(student.id),
                goals=["Plano Adaptativo"],
                created_at=study_plan.created_at,
                sessions=sessions_dto,
                status="created"
            )

        except Exception as e:
            print(f"!!! CRITICAL ERROR: {e}", file=sys.stderr)
            # Re-lança para o FastAPI pegar o 500 se for algo muito grave
            raise e