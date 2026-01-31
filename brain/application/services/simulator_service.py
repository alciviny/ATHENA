from typing import List, Optional
from uuid import UUID
from datetime import datetime

from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository
from brain.domain.entities.knowledge_node import KnowledgeNode


class SimulatorService:
    """
    Serviço responsável por gerar listas de questões para simuladores.

    Seleciona nós com proficiência média (0.5-0.7) — zonas de incerteza —
    e aplica um `stress_level` que reduz o tempo estimado por questão
    conforme o aluno avança.
    """
    def __init__(self, knowledge_repo: KnowledgeRepository, performance_repo: PerformanceRepository):
        self.knowledge_repo = knowledge_repo
        self.performance_repo = performance_repo

    async def generate_simulation(
        self,
        student_id: UUID,
        num_questions: int = 20,
        stress_level: float = 1.0,
        min_time_sec: int = 20,
    ) -> List[KnowledgeNode]:
        """
        Gera uma lista de `num_questions` KnowledgeNode selecionados prioritariamente
        por proficiências entre 0.5 e 0.7.

        stress_level: valor >=0.0. Quanto maior, maior a redução de tempo ao longo da prova.
        """
        all_nodes = await self.knowledge_repo.get_full_graph()
        recent_events = await self.performance_repo.get_recent_events(student_id, limit=200)

        # Construir mapa de proficiências (0.0-1.0)
        perf_map = {}
        # Usar evento mais recente por node (se houver)
        for ev in sorted(recent_events, key=lambda e: getattr(e, 'occurred_at', datetime.min)):
            # Alguns repositórios usam node_id; tentamos acomodar ambos
            node_key = str(getattr(ev, 'node_id', getattr(ev, 'topic', '')))
            try:
                perf_map[node_key] = ev.value if hasattr(ev, 'value') else 0.0
            except Exception:
                perf_map[node_key] = 0.0

        # Filtrar nós com proficiência média (0.5 - 0.7)
        candidates = []
        for node in all_nodes:
            prof = perf_map.get(str(getattr(node, 'id', '')), 0.0)
            # Normalizar para 0-1 caso value esteja em 0-100
            if prof > 1.0:
                prof = prof / 100.0
            if 0.5 <= prof <= 0.7:
                candidates.append((node, prof))

        # Se não tivermos candidatos suficientes, relaxar critérios pegando os mais próximos
        if len(candidates) < num_questions:
            # Sort por distância à zona alvo (0.6)
            extras = []
            for node in all_nodes:
                prof = perf_map.get(str(getattr(node, 'id', '')), 0.0)
                if prof > 1.0:
                    prof = prof / 100.0
                dist = abs(prof - 0.6)
                extras.append((node, prof, dist))
            extras.sort(key=lambda x: x[2])
            # Merge mantendo candidatos primeiro
            merged = [c[0] for c in candidates]
            for node, prof, _ in extras:
                if node not in merged:
                    merged.append(node)
                if len(merged) >= num_questions:
                    break
            selected = merged[:num_questions]
        else:
            # Ordernar candidatos por weight/dificuldade (priorizar maior weight)
            candidates.sort(key=lambda x: (getattr(x[0], 'weight', 1.0), -getattr(x[0], 'difficulty', 5.0)), reverse=True)
            selected = [n for n, _ in candidates[:num_questions]]

        # Aplicar redução de tempo estimado por questão conforme stress_level e progresso
        total = len(selected)
        for idx, node in enumerate(selected):
            base_time = getattr(node, 'estimated_study_time', 60) if hasattr(node, 'estimated_study_time') else 60
            progress = idx / max(1, total - 1) if total > 1 else 0.0
            # Redução proporcional ao progresso e stress_level
            reduction_factor = 1.0 - (progress * 0.5 * float(stress_level))
            reduction_factor = max(0.5, reduction_factor)  # nunca reduzir mais que 50%
            estimated_seconds = max(min_time_sec, int(base_time * reduction_factor))
            setattr(node, 'estimated_time_seconds', estimated_seconds)

        return selected
