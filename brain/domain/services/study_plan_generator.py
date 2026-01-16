from datetime import datetime, timezone
from typing import List, Dict
from uuid import uuid4

from brain.domain.entities.student import Student
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.PerformanceEvent import (
    PerformanceEvent,
    PerformanceMetric,
)
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.StudyPlan import StudyPlan, StudyFocusLevel
from brain.domain.policies.adaptive_rule import AdaptiveRule


class StudyPlanGenerator:
    """
    Domain Service responsável por gerar planos de estudo adaptativos.

    Atua como orquestrador entre:
    - Perfil cognitivo
    - Eventos de performance
    - Grafo de conhecimento
    - Regras adaptativas
    """

    BASE_TIME_PER_NODE_MINUTES = 25

    def __init__(
        self,
        knowledge_graph: List[KnowledgeNode],
        adaptive_rules: List[AdaptiveRule],
    ) -> None:
        self.knowledge_graph = knowledge_graph
        self.adaptive_rules = adaptive_rules

    # =========================
    # Public API
    # =========================

    def generate(
        self,
        student: Student,
        cognitive_profile: CognitiveProfile,
        performance_events: List[PerformanceEvent],
    ) -> StudyPlan:
        """
        Gera um plano de estudo adaptativo para o aluno.
        """

        # 1. Detectar métricas fracas
        weak_metrics = self._detect_weak_metrics(performance_events)

        # 2. Selecionar nós relevantes do grafo
        target_nodes = self._select_relevant_nodes(weak_metrics)

        # 3. Determinar foco inicial do plano
        focus_level = self._determine_focus(weak_metrics)

        # 4. Montar contexto adaptativo
        context: Dict[str, object] = {
            "student": student,
            "cognitive_profile": cognitive_profile,
            "performance_events": performance_events,
            "weak_metrics": weak_metrics,
            "target_nodes": target_nodes,
            "focus_level": focus_level,
        }

        # 5. Aplicar regras adaptativas (podem alterar o contexto)
        for rule in self.adaptive_rules:
            rule.apply(context)

        # 6. Estimar duração
        estimated_duration = self._estimate_duration(context["target_nodes"])

        # 7. Criar StudyPlan
        return StudyPlan(
            id=uuid4(),
            student_id=student.id,
            created_at=datetime.now(timezone.utc),
            knowledge_nodes=[node.id for node in context["target_nodes"]],
            estimated_duration_minutes=estimated_duration,
            focus_level=context["focus_level"],
        )

    # =========================
    # Private helpers
    # =========================

    def _detect_weak_metrics(
        self,
        events: List[PerformanceEvent],
    ) -> List[PerformanceMetric]:
        """
        Identifica métricas onde o desempenho ficou abaixo do baseline.
        """
        weak_metrics = {
            event.metric
            for event in events
            if event.is_negative()
        }
        return list(weak_metrics)

    def _select_relevant_nodes(
        self,
        weak_metrics: List[PerformanceMetric],
    ) -> List[KnowledgeNode]:
        """
        Seleciona nós do grafo relacionados às métricas fracas, garantindo
        que todas as dependências sejam incluídas.
        """
        if not weak_metrics:
            return self.knowledge_graph

        primary_targets: List[KnowledgeNode] = []
        for node in self.knowledge_graph:
            if (PerformanceMetric.ACCURACY in weak_metrics and node.is_high_difficulty()) or \
               (PerformanceMetric.RETENTION in weak_metrics and node.is_high_impact()):
                primary_targets.append(node)

        # Usar um dicionário para garantir nós únicos e acesso rápido
        full_plan_nodes: Dict[UUID, KnowledgeNode] = {node.id: node for node in primary_targets}

        # Adicionar todas as dependências recursivamente
        for node in primary_targets:
            self._get_all_dependencies(node, full_plan_nodes)
            
        # Ordenar o plano de estudo: primeiro as dependências
        # Esta é uma ordenação topológica simples
        sorted_nodes = sorted(
            list(full_plan_nodes.values()),
            key=lambda n: len(n.dependencies)
        )

        return sorted_nodes

    def _get_all_dependencies(
        self,
        node: KnowledgeNode,
        plan_nodes: Dict[UUID, KnowledgeNode],
    ) -> None:
        """
        Adiciona recursivamente as dependências de um nó ao plano.
        """
        
        # Criar um mapa do grafo para acesso rápido
        graph_map = {n.id: n for n in self.knowledge_graph}

        for dep_id in node.dependencies:
            if dep_id not in plan_nodes:
                dependency_node = graph_map.get(dep_id)
                if dependency_node:
                    plan_nodes[dep_id] = dependency_node
                    self._get_all_dependencies(dependency_node, plan_nodes)

    def _determine_focus(
        self,
        weak_metrics: List[PerformanceMetric],
    ) -> StudyFocusLevel:
        """
        Decide o foco do plano com base nas fragilidades detectadas.
        """
        if not weak_metrics:
            return StudyFocusLevel.NEW_CONTENT

        if len(weak_metrics) >= 2:
            return StudyFocusLevel.REVIEW

        return StudyFocusLevel.REINFORCEMENT

    def _estimate_duration(
        self,
        nodes: List[KnowledgeNode],
    ) -> int:
        """
        Estima o tempo total do plano com base nos nós selecionados.
        """
        return len(nodes) * self.BASE_TIME_PER_NODE_MINUTES
