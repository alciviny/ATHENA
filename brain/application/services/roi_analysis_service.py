from typing import List, Dict
from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.domain.value_objects.roi_status import ROIStatus

class ROIAnalysisService:
    def __init__(self, engine: IntelligenceEngine):
        self.engine = engine

    def analyze(self, student, history) -> List[Dict]:
        roi_data = self.engine.calculate_roi_per_subject(student, history)
        report = []
        for subject_name, score in roi_data.items():
            subject_id = None
            if hasattr(student, 'subjects'):
                for subject in student.subjects:
                    if subject.name == subject_name:
                        subject_id = subject.id
                        break
            
            report.append({
                "subject_id": str(subject_id) if subject_id else None,
                "subject_name": subject_name,
                "roi_score": score,
                "status": self._classify(score),
                "recommendation": self._recommend(score)
            })
        return report

    def _classify(self, score: float) -> ROIStatus:
        if score >= 0.08: return ROIStatus.VEIO_DE_OURO
        if score <= 0.01: return ROIStatus.PANTANO
        return ROIStatus.ESTAGNACAO

    def _recommend(self, score: float) -> str:
        if score >= 0.08: return "Prioridade máxima. Alto retorno cognitivo por hora."
        if score <= 0.01: return "Baixo retorno. Verificar pré-requisitos ou trocar abordagem."
        return "Evolução consistente. Manter ritmo atual."
