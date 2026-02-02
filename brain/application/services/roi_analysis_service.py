from typing import List, Dict, Optional
from uuid import UUID
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.value_objects.roi_status import ROIStatus
from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository


class ROIAnalysisService:
    def __init__(self, knowledge_repo: KnowledgeRepository, performance_repo: PerformanceRepository):
        self.knowledge_repo = knowledge_repo
        self.performance_repo = performance_repo

    def calculate_priority_score(self, node: KnowledgeNode, current_proficiency: float) -> float:
        """
        Calcula o Score de Prioridade (0.0 a 1.0).
        Fórmula: (Importância * (1 - Proficiência)) / (Dificuldade + Suporte)
        """
        if current_proficiency >= 0.9: # Domínio completo
            return 0.0
            
        # Potencial de ganho: Quanto falta para dominar o que é importante
        importance_weight = getattr(node, "importance_weight", getattr(node, "weight_in_exam", 1.0))
        gap_opportunity = importance_weight * (1.0 - current_proficiency)
        
        # ROI: Ganho ajustado pelo esforço (Dificuldade). 
        # Tópicos fáceis com alto gap têm o maior ROI.
        roi_score = gap_opportunity / (node.difficulty + 0.1)
        
        return min(roi_score, 1.0)

    def get_roi_label(self, score: float) -> str:
        if score > 0.7: return "ALTO IMPACTO: Ganho Rápido"
        if score > 0.4: return "ESTRATÉGICO: Reforço Necessário"
        return "MANUTENÇÃO: Ajuste Fino"

    async def get_knowledge_graph(self, student_id: UUID) -> Dict:
        """
        Gera uma representação completa do grafo de conhecimento com scores de ROI.
        """
        all_nodes = await self.knowledge_repo.get_full_graph()
        
        # TODO: Implementar uma forma real de buscar a proficiência do aluno por nó.
        # Por enquanto, usaremos um valor fixo para demonstração.
        student_proficiency_map = {node.id: 0.5 for node in all_nodes}
        
        graph_nodes = []
        for node in all_nodes:
            proficiency = student_proficiency_map.get(node.id, 0.1) # Default 0.1 se não encontrado
            roi_score = self.calculate_priority_score(node, proficiency)
            status = self.get_roi_label(roi_score)
            
            graph_nodes.append({
                "id": node.id,
                "name": node.name,
                "roi_score": roi_score,
                "status": status,
                "weight": node.weight_in_exam,
                "difficulty": node.difficulty,
                "stability": node.stability,
            })

        links = []
        for node in all_nodes:
            if not node.dependency_ids:
                continue
            for dep_id in node.dependency_ids:
                links.append({"source": dep_id, "target": node.id})

        return {"nodes": graph_nodes, "links": links}


    def analyze(self, student: object, history: List[object]) -> List[dict]:
        """
        Gera um relatório por matéria baseado no engine configurado.
        (Este método permanece para compatibilidade, mas a lógica principal do grafo está acima)
        """
        # Esta implementação antiga pode ser mantida, removida ou refatorada
        # dependendo se a análise por matéria ainda é necessária.
        # Por enquanto, retornaremos uma lista vazia para focar no novo método.
        return []