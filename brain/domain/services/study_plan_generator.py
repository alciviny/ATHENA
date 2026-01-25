from datetime import datetime, timezone
from typing import List, Dict
from uuid import uuid4, UUID

from brain.domain.entities.student import Student
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.performance_event import (
    PerformanceEvent,
    PerformanceMetric,
)
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.entities.study_plan import StudyPlan as StudyPlanEntity, StudyFocusLevel
from brain.domain.policies.adaptive_rule import AdaptiveRule


HIGH_DIFFICULTY_THRESHOLD = 0.7
LOW_STABILITY_THRESHOLD = 10.0


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
    ) -> StudyPlanEntity:
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
        return StudyPlanEntity(
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
        Seleciona nós do grafo relacionados às métricas fracas.
        O conceito de dependências foi removido.
        """
        if not weak_metrics:
            return self.knowledge_graph

        primary_targets: List[KnowledgeNode] = []
        for node in self.knowledge_graph:
            if (PerformanceMetric.ACCURACY in weak_metrics and node.difficulty >= HIGH_DIFFICULTY_THRESHOLD) or \
               (PerformanceMetric.RETENTION in weak_metrics and node.stability < LOW_STABILITY_THRESHOLD):
                primary_targets.append(node)
        
        return primary_targets

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
