# brain/tests/application/services/test_roi_analysis_service.py

from unittest.mock import MagicMock
import uuid

from brain.application.services.roi_analysis_service import ROIAnalysisService
from brain.domain.entities.knowledge_node import KnowledgeNode


def test_classify_high_roi_as_veio_de_ouro():
    """
    Garante que um nó com baixa proficiência e alta importância receba score alto de ROI.
    """
    mock_knowledge_repo = MagicMock()
    mock_performance_repo = MagicMock()

    service = ROIAnalysisService(
        knowledge_repo=mock_knowledge_repo,
        performance_repo=mock_performance_repo,
    )

    # Nó fácil (difficulty=1), importante (weight_in_exam=0.9), proficiência baixa
    node = KnowledgeNode(
        id=uuid.uuid4(),
        name="Direito Constitucional",
        subject="Direito",
        difficulty=1.0,
        weight_in_exam=0.9,
    )

    # ROI alto: gap_opportunity=0.9*0.9=0.81, roi=0.81/1.1≈0.736
    roi_score = service.calculate_priority_score(node, current_proficiency=0.1)
    assert roi_score > 0.7, f"ROI esperado > 0.7, obteve {roi_score}"

    label = service.get_roi_label(roi_score)
    assert label == "ALTO IMPACTO: Ganho Rápido"


def test_dominated_node_has_zero_roi():
    """
    Garante que um nó com proficiência >= 0.9 tenha ROI zero.
    """
    mock_knowledge_repo = MagicMock()
    mock_performance_repo = MagicMock()

    service = ROIAnalysisService(
        knowledge_repo=mock_knowledge_repo,
        performance_repo=mock_performance_repo,
    )

    node = KnowledgeNode(
        id=uuid.uuid4(),
        name="Tópico Dominado",
        subject="Math",
        difficulty=5.0,
    )

    roi_score = service.calculate_priority_score(node, current_proficiency=0.95)
    assert roi_score == 0.0

