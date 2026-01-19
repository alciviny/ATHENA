# brain/tests/application/services/test_roi_analysis_service.py

from unittest.mock import MagicMock
import uuid

from brain.application.services.roi_analysis_service import ROIAnalysisService
from brain.domain.services.intelligence_engine import IntelligenceEngine
from brain.domain.value_objects.roi_status import ROIStatus


def test_classify_high_roi_as_veio_de_ouro():
    """
    Garante que um score de ROI de 0.10 seja classificado como VEIO_DE_OURO.
    """
    # Arrange
    mock_engine = MagicMock(spec=IntelligenceEngine)
    subject_id = uuid.uuid4()
    
    # Configura o motor para retornar um score de ROI alto para uma matéria
    mock_engine.calculate_roi_per_subject.return_value = {
        str(subject_id): 0.10
    }

    # Cria um mock para o estudante com a matéria correspondente
    mock_student = MagicMock()
    mock_subject = MagicMock()
    mock_subject.id = subject_id
    mock_subject.name = "Direito Constitucional"
    mock_student.subjects = [mock_subject]

    # Instancia o serviço com o motor mockado
    service = ROIAnalysisService(engine=mock_engine)

    # Act
    # O histórico pode ser vazio, pois o cálculo do motor já está mockado
    report = service.analyze(student=mock_student, history=[])

    # Assert
    assert len(report) == 1
    assert report[0]["subject_id"] == str(subject_id)
    assert report[0]["roi_score"] == 0.10
    assert report[0]["status"] == ROIStatus.VEIO_DE_OURO
    assert "Prioridade máxima" in report[0]["recommendation"]

