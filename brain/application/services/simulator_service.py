from typing import List
from uuid import UUID
from datetime import datetime
import logging
import asyncio

from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository
from brain.application.ports.ai_service import AIService
from brain.domain.entities.knowledge_node import KnowledgeNode

logger = logging.getLogger(__name__)

class SimulatorService:
    """
    Serviço responsável por gerar simuladores com cenários práticos (Prediction-Based).
    """
    def __init__(
        self, 
        knowledge_repo: KnowledgeRepository, 
        performance_repo: PerformanceRepository,
        ai_service: AIService  # Injeção nova
    ):
        self.knowledge_repo = knowledge_repo
        self.performance_repo = performance_repo
        self.ai_service = ai_service

    async def generate_simulation(
        self,
        student_id: UUID,
        num_questions: int = 20,
        stress_level: float = 1.0,
        min_time_sec: int = 20,
    ) -> List[KnowledgeNode]:
        """
        Gera uma lista de KnowledgeNodes transformados em Cenários de Previsão.
        """
        # 1. Seleção dos Nós (Lógica original mantida: zona de proficiência 0.5-0.7)
        all_nodes = await self.knowledge_repo.get_full_graph()
        recent_events = await self.performance_repo.get_recent_events(student_id, limit=200)

        perf_map = {}
        for ev in sorted(recent_events, key=lambda e: getattr(e, 'occurred_at', datetime.min)):
            node_key = str(getattr(ev, 'node_id', getattr(ev, 'topic', '')))
            try:
                perf_map[node_key] = ev.value if hasattr(ev, 'value') else 0.0
            except Exception:
                perf_map[node_key] = 0.0

        candidates = []
        for node in all_nodes:
            prof = perf_map.get(str(getattr(node, 'id', '')), 0.0)
            if prof > 1.0: prof = prof / 100.0
            if 0.5 <= prof <= 0.7:
                candidates.append((node, prof))

        if len(candidates) < num_questions:
            # Fallback selection logic
            extras = []
            for node in all_nodes:
                prof = perf_map.get(str(getattr(node, 'id', '')), 0.0)
                if prof > 1.0: prof = prof / 100.0
                dist = abs(prof - 0.6)
                extras.append((node, prof, dist))
            extras.sort(key=lambda x: x[2])
            
            merged = [c[0] for c in candidates]
            merged_ids = {c.id for c in merged}
            for node, prof, _ in extras:
                if node.id not in merged_ids:
                    merged.append(node)
                    merged_ids.add(node.id)
                if len(merged) >= num_questions:
                    break
            selected = merged[:num_questions]
        else:
            candidates.sort(key=lambda x: (getattr(x[0], 'weight', 1.0), -getattr(x[0], 'difficulty', 5.0)), reverse=True)
            selected = [n for n, _ in candidates[:num_questions]]

        # 2. Transformação em Cenários (NOVO)
        logger.info(f"Gerando cenários para {len(selected)} nós com Stress Level {stress_level}...")
        
        tasks = [
            self._transform_node_into_scenario(node, stress_level, min_time_sec, idx, len(selected))
            for idx, node in enumerate(selected)
        ]
        final_nodes = await asyncio.gather(*tasks)

        return [node for node in final_nodes if node is not None]

    async def _transform_node_into_scenario(
        self, 
        node: KnowledgeNode, 
        stress_level: float, 
        min_time_sec: int, 
        idx: int, 
        total: int
    ) -> KnowledgeNode:
        try:
            # Chamada ao Groq para gerar o cenário
            scenario_data = await self.ai_service.generate_scenario(node, stress_level)
            
            # Transformação em Runtime (não salva no DB)
            # Substituímos o 'front' (pergunta) pelo cenário e guardamos a resposta no metadata
            node.name = scenario_data.get("scenario_text", node.name) # Usa 'name' como o campo da pergunta
            
            # Ajuste de dificuldade dinâmica
            node.difficulty = float(scenario_data.get("difficulty_adjusted", node.difficulty))
            
            # Metadata oculto para validação futura — usa atributo separado
            # para não sobrescrever o content (str) do nó
            if not hasattr(node, 'scenario_data'):
                node.scenario_data = {}
            
            node.scenario_data["expected_outcome"] = scenario_data.get("expected_outcome", "")
            node.scenario_data["is_scenario"] = True
            
            # Ajuste de tempo baseado no stress
            base_time = getattr(node, 'estimated_study_time', 60) or 60
            progress = idx / max(1, total - 1) if total > 1 else 0.0
            reduction_factor = max(0.4, 1.0 - (progress * 0.6 * float(stress_level))) # Mais agressivo
            
            if not hasattr(node, 'metadata'):
                node.metadata = {}
            node.metadata['estimated_time_seconds'] = max(min_time_sec, int(base_time * reduction_factor))
            
            return node
            
        except Exception as e:
            logger.error(f"Falha ao gerar cenário para o nó {node.id}: {e}")
            # Fallback: Mantém o nó original como flashcard simples
            return node