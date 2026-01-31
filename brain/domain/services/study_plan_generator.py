from typing import List, Dict
from brain.domain.entities.student import Student
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.performance_event import PerformanceEvent
from brain.domain.entities.study_plan import StudyPlan, StudyFocusLevel
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.infrastructure.persistence.models import KnowledgeNodeModel as KnowledgeNodeData
from brain.domain.services.graph_validator import KnowledgeGraphValidator, GraphValidationError
from brain.application.services.roi_analysis_service import ROIAnalysisService
from brain.application.services.memory_analysis_service import MemoryAnalysisService
from uuid import uuid4, UUID as UUIDType
from datetime import datetime, timezone

class StudyPlanGenerator:
    """
    Generates an adaptive study plan using topological sorting to ensure logical
    prerequisite order before applying strategic prioritization.
    """
    def __init__(
        self,
        knowledge_graph_data: List[KnowledgeNodeData] = None,
        knowledge_graph: List[KnowledgeNodeData] = None,
        roi_service: ROIAnalysisService = None,
        memory_service: MemoryAnalysisService = None,
        adaptive_rules: List = None,
    ):
        # Recebe os nós do banco de dados (camada de persistência)
        # Suporte compatível com o argumento `knowledge_graph` usado pelos testes
        if knowledge_graph is not None:
            self.knowledge_graph_data = knowledge_graph
        else:
            self.knowledge_graph_data = knowledge_graph_data or []
        self.node_data_map = {str(node.id): node for node in self.knowledge_graph_data}
        self.roi_service = roi_service or ROIAnalysisService()
        self.memory_service = memory_service or MemoryAnalysisService()
        self.adaptive_rules = adaptive_rules or []

    def _calculate_proficiencies(self, performance_events: List[PerformanceEvent]) -> Dict[str, float]:
        # Implementação simplificada para os testes: mapeia tópicos para um score 0-1
        proficiencies: Dict[str, float] = {}
        for ev in performance_events:
            try:
                # Usa topic como chave quando não houver node_id explícito
                key = str(getattr(ev, "node_id", getattr(ev, "topic", "")))
                # Normaliza event.value se estiver na escala 0-1 ou 0-100
                val = getattr(ev, "value", 0.0)
                if val > 1.0:
                    val = val / 100.0
                proficiencies[key] = max(0.0, min(1.0, val))
            except Exception:
                continue
        return proficiencies

    def _build_plan(self, student_id: str, recommended_nodes: List[KnowledgeNodeData], focus_level: StudyFocusLevel = None) -> StudyPlan:
        student_uuid = student_id if isinstance(student_id, UUIDType) else UUIDType(student_id)
        plan = StudyPlan(
            id=uuid4(),
            student_id=student_uuid,
            created_at=datetime.now(timezone.utc),
            knowledge_nodes=recommended_nodes,
            focus_level=focus_level or StudyFocusLevel.REVIEW,
        )
        return plan

    def generate(
        self, 
        student: Student, 
        cognitive_profile: CognitiveProfile, 
        performance_events: List[PerformanceEvent],
        node_scores: Dict[str, float] = None
    ) -> StudyPlan:
        """
        Gera um plano de estudo adaptativo.
        
        Args:
            student: Entidade Student
            cognitive_profile: Perfil cognitivo com focus_level
            performance_events: Lista de eventos recentes
            node_scores: Dicionário {node_id: score} para priorização customizada
        """
        # 1. Converter modelos de persistência em entidades de domínio para validação
        domain_node_map: Dict[str, KnowledgeNode] = {}
        for n in self.knowledge_graph_data:
            node_id = str(getattr(n, "id", n))
            if isinstance(n, KnowledgeNode):
                # Já é uma entidade de domínio
                domain_node_map[node_id] = n
            else:
                domain_node_map[node_id] = KnowledgeNode(
                    id=node_id,
                    name=getattr(n, "name", getattr(n, "title", "")),
                    subject=getattr(n, "subject", ""),
                )

        for node_data in self.knowledge_graph_data:
            node_id = str(getattr(node_data, "id", node_data))
            domain_node = domain_node_map[node_id]
            # Assumindo que node_data.dependencies possa existir (em models)
            deps = getattr(node_data, "dependencies", []) or []
            resolved_deps = []
            for dep in deps:
                dep_id = str(getattr(dep, "id", dep))
                if dep_id in domain_node_map:
                    resolved_deps.append(domain_node_map[dep_id])
            # Atribui dinamicamente (compatível com dataclasses simples)
            setattr(domain_node, "dependencies", resolved_deps)
        
        # 2. Validar e obter a ordem lógica global a partir das entidades de domínio
        try:
            ordered_domain_nodes = KnowledgeGraphValidator.get_topological_order(list(domain_node_map.values()))
        except GraphValidationError:
            # Em produção, um ciclo não deveria existir, mas como fallback, usa a lista sem ordem
            ordered_domain_nodes = list(domain_node_map.values())

        # Mapeia a ordem de volta para os objetos de dados (que têm todos os atributos)
        ordered_nodes_data = [self.node_data_map.get(str(node.id)) for node in ordered_domain_nodes]
        # Filtra eventuais nós não mapeados (defensivo para dados mistos)
        ordered_nodes_data = [n for n in ordered_nodes_data if n is not None]

        # 3. Calcular proficiências
        proficiencies = self._calculate_proficiencies(performance_events)

        # 4. Identificar nós elegíveis na ordem correta
        eligible_nodes: List[KnowledgeNodeData] = []
        for node in ordered_nodes_data:
            # Um nó só é elegível se todos os seus pré-requisitos foram dominados
            is_ready = all(proficiencies.get(str(dep.id), 0) >= 0.7 for dep in node.dependencies)
            is_mastered = proficiencies.get(str(node.id), 0) >= 0.9

            if is_ready and not is_mastered:
                eligible_nodes.append(node)

        # 5. Aplicar regras adaptativas, se fornecidas
        # Construir contexto inicial para regras
        weak_metrics = [e.metric for e in performance_events if e.value < getattr(e, "baseline", 1.0)]
        ctx = {
            "target_nodes": eligible_nodes,
            "weak_metrics": weak_metrics,
            "cognitive_profile": cognitive_profile,
            "performance_events": performance_events,
        }

        for rule in self.adaptive_rules:
            try:
                if hasattr(rule, "apply"):
                    rule.apply(ctx)
                else:
                    # Caso recebam a classe/funcionalidade diretamente
                    rule(ctx)
            except Exception:
                continue

        # Atualiza eligible_nodes de acordo com possíveis modificações feitas pelas regras
        eligible_nodes = ctx.get("target_nodes", eligible_nodes)

        # 5. Calcular scores de priorização usando node_scores ou ROI padrão
        scored_nodes = []
        for node in eligible_nodes:
            node_id_str = str(node.id)
            
            # Se node_scores foi fornecido, usar aquele valor
            if node_scores and node_id_str in node_scores:
                custom_score = node_scores[node_id_str]
            else:
                custom_score = None
            
            # Calcular retention_probability usando MemoryAnalysisService
            last_review = getattr(node, "last_review", getattr(node, "last_reviewed_at", None))
            if last_review:
                retention_probability = self.memory_service.calculate_retention_probability(
                    last_review, 
                    getattr(node, "stability", 0.0)
                )
            else:
                retention_probability = 0.0  # Nó novo ainda não tem retenção
            
            # Fórmula: roi_score * (1 - retention_probability)
            if custom_score is not None:
                priority = custom_score * (1.0 - retention_probability)
            else:
                roi_score = self.roi_service.calculate_priority_score(
                    node, 
                    proficiencies.get(node_id_str, 0.0)
                )
                priority = roi_score * (1.0 - retention_probability)
            
            scored_nodes.append((node, priority))

        # 6. Ordenar por prioridade decrescente
        scored_nodes.sort(key=lambda x: x[1], reverse=True)

        # 7. Aplicar restrição baseada em focus_level
        focus_level = cognitive_profile.focus_level
        
        if focus_level == "RECOVERY":
            # Em RECOVERY, apenas revisão: máximo 3 nós com retenção < 0.7
            review_nodes = []
            for node, priority in scored_nodes:
                if node.last_review:
                    retention = self.memory_service.calculate_retention_probability(
                        node.last_review,
                        node.stability
                    )
                    if retention < 0.7:
                        review_nodes.append(node)
                        if len(review_nodes) >= 3:
                            break
            selected_nodes = review_nodes
        else:
            # DEEP_WORK: modo normal, selecionar top 5
            selected_nodes = [node for node, _ in scored_nodes[:5]]

        # Determinar foco final do plano (prioriza alterações das regras)
        plan_focus = ctx.get("focus_level") if ctx.get("focus_level") else None
        if not plan_focus:
            if not performance_events or len(weak_metrics) == 0:
                plan_focus = StudyFocusLevel.NEW_CONTENT
            elif cognitive_profile.focus_level == "RECOVERY":
                plan_focus = StudyFocusLevel.REVIEW
            else:
                plan_focus = StudyFocusLevel.REVIEW

        # 8. Construir o plano com os nós selecionados
        return self._build_plan(str(student.id), selected_nodes, focus_level=plan_focus)