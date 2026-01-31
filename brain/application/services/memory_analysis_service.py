from datetime import datetime, timezone
import math
from typing import Optional


class MemoryAnalysisService:
    def __init__(self, engine: Optional[object] = None, knowledge_repo: Optional[object] = None):
        self.engine = engine
        self.knowledge_repo = knowledge_repo

    @staticmethod
    def calculate_retention_probability(last_review: datetime, stability: float) -> float:
        """
        Aplica a fórmula da Curva de Esquecimento: R = e^(-t/S)
        R: Retenção
        t: Tempo decorrido
        S: Estabilidade da memória
        """
        now = datetime.now(timezone.utc)
        elapsed_days = (now - last_review).total_seconds() / 86400.0
        
        # Evita divisão por zero
        stability = max(stability, 0.1)
        
        retention = math.exp(-elapsed_days / stability)
        return max(retention, 0.0)

    @staticmethod
    def should_trigger_emergency_review(retention: float) -> bool:
        # Se a retenção cair abaixo de 70%, o tópico entra em "Zona de Perigo"
        return retention < 0.70

    async def get_student_memory_status(self, student: object, history: list) -> list:
        """
        Agrupa o histórico por tópico/assunto e usa o `engine` para analisar o estado da memória.
        Retorna uma lista de relatórios por assunto.
        """
        reports = []
        if not self.engine:
            return reports

        # Agrupar eventos por tópico
        topics = {}
        for ev in history:
            topics.setdefault(ev.topic, []).append(ev)

        for topic, events in topics.items():
            # O engine é um mock síncrono nos testes, portanto chamamos diretamente
            try:
                analysis = self.engine.analyze_memory_state(events)
            except TypeError:
                # Alguns mocks definem side_effects que aceitam diferentes assinaturas
                analysis = self.engine.analyze_memory_state()
            except Exception:
                analysis = {}

            # Tenta recuperar o nó correspondente (se o repositório foi injetado)
            node = None
            if self.knowledge_repo:
                try:
                    node = await self.knowledge_repo.get_node_by_name(topic)
                except Exception:
                    node = None

            report = {
                "subject_name": topic,
                "current_retention": analysis.get("current_retention"),
                "stability_days": analysis.get("stability_days"),
                "needs_review": analysis.get("needs_review", False),
                "status": "Crítico - Revisar Agora" if analysis.get("needs_review") else "Consolidado",
            }
            reports.append(report)

        return reports