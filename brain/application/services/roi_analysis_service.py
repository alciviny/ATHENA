from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, timezone
import math
from brain.domain.entities.knowledge_node import KnowledgeNode
from brain.domain.value_objects.roi_status import ROIStatus
from brain.application.ports.repositories import KnowledgeRepository, PerformanceRepository
from brain.domain.services.intelligence_engine import IntelligenceEngine


class ROIAnalysisService:
    def __init__(self, knowledge_repo: KnowledgeRepository, performance_repo: PerformanceRepository,
                 intelligence_engine: Optional[IntelligenceEngine] = None):
        self.knowledge_repo = knowledge_repo
        self.performance_repo = performance_repo
        self.intelligence_engine = intelligence_engine or IntelligenceEngine()

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
        Calcula proficiência real baseada na curva de esquecimento R = e^(-t/S).
        """
        all_nodes = await self.knowledge_repo.get_full_graph()
        
        # Calcular proficiência real para cada nó usando a fórmula de retenção
        now = datetime.now(timezone.utc)
        student_proficiency_map = {}
        for node in all_nodes:
            if node.last_reviewed_at and node.stability > 0:
                # Curva de esquecimento: R = e^(-t/S)
                last_review = node.last_reviewed_at
                if last_review.tzinfo is None:
                    last_review = last_review.replace(tzinfo=timezone.utc)
                elapsed_days = max(0, (now - last_review).total_seconds() / 86400.0)
                stability = max(0.1, node.stability)
                retention = math.exp(-elapsed_days / stability)
                student_proficiency_map[node.id] = retention
            elif node.reps > 0:
                # Já revisou mas sem dados de timing — usar fator baseado em reps/lapses
                success_ratio = max(0.1, 1.0 - (node.lapses / max(1, node.reps)))
                student_proficiency_map[node.id] = success_ratio * 0.7
            else:
                # Nunca revisou
                student_proficiency_map[node.id] = 0.0
        
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
        Gera relatório detalhado de análise por matéria com métricas avançadas.

        Usa o IntelligenceEngine para calcular ROI sofisticado considerando:
        - Ganho de estabilidade (FSRS)
        - Importância estratégica da matéria
        - Padrões de erro e eficiência
        - Tendências de melhoria
        - Fatores cognitivos do aluno

        Returns: Lista de dicionários com análise por matéria
        """
        if not history:
            return []

        # Calcular ROI por matéria usando o engine avançado
        roi_scores = self.intelligence_engine.calculate_roi_per_subject(student, history)

        # Agrupar eventos por matéria para análise detalhada
        subject_events = self._group_events_by_subject(history)

        analysis_report = []

        for subject, events in subject_events.items():
            roi_score = roi_scores.get(subject, 0.5)

            # Calcular métricas detalhadas
            metrics = self._calculate_detailed_metrics(events)

            # Gerar recomendações baseadas no ROI e métricas
            recommendations = self._generate_recommendations(subject, roi_score, metrics, student)

            # Determinar status do ROI
            roi_status = self._determine_roi_status(roi_score)

            analysis_report.append({
                "subject": subject,
                "roi_score": round(roi_score, 3),
                "roi_status": roi_status.value,
                "metrics": metrics,
                "recommendations": recommendations,
                "event_count": len(events),
                "last_activity": self._get_last_activity_date(events),
                "trend_analysis": self._analyze_performance_trend(events)
            })

        # Ordenar por ROI score (maior primeiro)
        analysis_report.sort(key=lambda x: x["roi_score"], reverse=True)

        return analysis_report

    def _group_events_by_subject(self, history: List[object]) -> Dict[str, List]:
        """Agrupa eventos por matéria."""
        from brain.domain.entities.performance_event import PerformanceEvent

        subject_events = {}
        for event in history:
            if isinstance(event, PerformanceEvent) and event.topic:
                if event.topic not in subject_events:
                    subject_events[event.topic] = []
                subject_events[event.topic].append(event)
        return subject_events

    def _calculate_detailed_metrics(self, events: List) -> Dict[str, float]:
        """Calcula métricas detalhadas para uma matéria."""
        from brain.domain.entities.performance_event import PerformanceMetric

        accuracy_events = [e for e in events if hasattr(e, 'metric') and e.metric == PerformanceMetric.ACCURACY]
        error_events = [e for e in events if hasattr(e, 'metric') and e.metric == PerformanceMetric.ERROR_RATE]

        metrics = {
            "avg_accuracy": 0.0,
            "avg_error_rate": 0.0,
            "total_events": len(events),
            "accuracy_events": len(accuracy_events),
            "error_events": len(error_events),
            "consistency_score": 0.0,
            "improvement_rate": 0.0
        }

        if accuracy_events:
            accuracy_values = [e.value for e in accuracy_events]
            metrics["avg_accuracy"] = sum(accuracy_values) / len(accuracy_values)

            # Calcular consistência (inverso da variabilidade)
            if len(accuracy_values) > 1:
                mean_acc = metrics["avg_accuracy"]
                variance = sum((x - mean_acc) ** 2 for x in accuracy_values) / len(accuracy_values)
                metrics["consistency_score"] = max(0.0, 1.0 - variance * 4)  # Normalizar variabilidade

        if error_events:
            error_values = [e.value for e in error_events]
            metrics["avg_error_rate"] = sum(error_values) / len(error_values)

        # Calcular taxa de melhoria (comparando primeiros vs últimos eventos)
        if len(accuracy_events) >= 6:
            first_half = accuracy_events[:len(accuracy_events)//2]
            second_half = accuracy_events[len(accuracy_events)//2:]

            first_avg = sum(e.value for e in first_half) / len(first_half)
            second_avg = sum(e.value for e in second_half) / len(second_half)

            metrics["improvement_rate"] = second_avg - first_avg

        return metrics

    def _generate_recommendations(self, subject: str, roi_score: float,
                                metrics: Dict[str, float], student) -> List[str]:
        """Gera recomendações personalizadas baseadas na análise."""
        recommendations = []

        # Recomendações baseadas no ROI
        if roi_score > 1.5:
            recommendations.append(f"🎯 Excelente investimento! Continue priorizando {subject}.")
        elif roi_score > 1.0:
            recommendations.append(f"✅ Bom ROI em {subject}. Mantenha o ritmo atual.")
        elif roi_score > 0.7:
            recommendations.append(f"⚠️ ROI moderado em {subject}. Considere aumentar foco.")
        else:
            recommendations.append(f"🔴 ROI baixo em {subject}. Necessita atenção urgente.")

        # Recomendações baseadas em métricas
        if metrics["avg_accuracy"] < 0.6:
            recommendations.append("📚 Acurácia baixa detectada. Reveja conceitos fundamentais.")

        if metrics["consistency_score"] < 0.5:
            recommendations.append("📊 Performance inconsistente. Foque em prática regular.")

        if metrics["improvement_rate"] > 0.1:
            recommendations.append("📈 Melhoria consistente! Continue com essa estratégia.")
        elif metrics["improvement_rate"] < -0.1:
            recommendations.append("📉 Performance declinante. Reavalie método de estudo.")

        if metrics["avg_error_rate"] > 0.3:
            recommendations.append("🐛 Alta taxa de erros. Identifique padrões de erro recorrentes.")

        # Recomendações baseadas no perfil do estudante
        try:
            if hasattr(student, 'goal'):
                goal_name = student.goal.value if hasattr(student.goal, 'value') else str(student.goal)
                recommendations.append(f"🎯 Alinhado com objetivo: {goal_name}")
        except:
            pass

        return recommendations

    def _determine_roi_status(self, roi_score: float) -> ROIStatus:
        """Determina o status do ROI baseado no score."""
        if roi_score >= 1.5:
            return ROIStatus.EXCELLENT
        elif roi_score >= 1.0:
            return ROIStatus.GOOD
        elif roi_score >= 0.7:
            return ROIStatus.MODERATE
        else:
            return ROIStatus.NEEDS_ATTENTION

    def _get_last_activity_date(self, events: List) -> Optional[str]:
        """Retorna a data da última atividade."""
        if not events:
            return None

        try:
            last_event = max(events, key=lambda e: e.occurred_at if hasattr(e, 'occurred_at') else datetime.min.replace(tzinfo=timezone.utc))
            return last_event.occurred_at.isoformat() if hasattr(last_event, 'occurred_at') else None
        except:
            return None

    def _analyze_performance_trend(self, events: List) -> Dict[str, any]:
        """Analisa tendência de performance."""
        from brain.domain.entities.performance_event import PerformanceMetric

        accuracy_events = sorted(
            [e for e in events if hasattr(e, 'metric') and e.metric == PerformanceMetric.ACCURACY],
            key=lambda e: e.occurred_at if hasattr(e, 'occurred_at') else datetime.min.replace(tzinfo=timezone.utc)
        )

        if len(accuracy_events) < 3:
            return {"trend": "insufficient_data", "description": "Dados insuficientes para análise de tendência"}

        # Calcular tendência linear
        values = [e.value for e in accuracy_events]
        n = len(values)

        # Slope da regressão linear
        x = list(range(n))
        slope = self._calculate_linear_slope(x, values)

        if slope > 0.01:
            trend = "improving"
            description = "Performance melhorando consistentemente"
        elif slope < -0.01:
            trend = "declining"
            description = "Performance em declínio"
        else:
            trend = "stable"
            description = "Performance estável"

        return {
            "trend": trend,
            "description": description,
            "slope": round(slope, 4),
            "data_points": n
        }

    def _calculate_linear_slope(self, x: List[float], y: List[float]) -> float:
        """Calcula o slope de uma regressão linear simples."""
        n = len(x)
        if n < 2:
            return 0.0

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi ** 2 for xi in x)

        denominator = n * sum_xx - sum_x ** 2
        if denominator == 0:
            return 0.0

        return (n * sum_xy - sum_x * sum_y) / denominator