from dataclasses import dataclass, field
from typing import Dict
from uuid import UUID


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Garante que um valor esteja dentro de um intervalo seguro.
    """
    return max(min_value, min(max_value, value))


@dataclass
class CognitiveProfile:
    """
    Perfil cognitivo do aluno.

    Representa métricas comportamentais e cognitivas aprendidas ao longo do tempo,
    utilizadas para personalização de planos de estudo e decisões adaptativas.
    """
    id: UUID
    student_id: UUID

    # Scores normalizados (0.0 - 1.0)
    retention_rate: float
    learning_speed: float
    stress_sensitivity: float

    # Mapeia tipo de erro → frequência acumulada
    error_patterns: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Normaliza automaticamente os scores na criação.
        """
        self.retention_rate = _clamp(self.retention_rate)
        self.learning_speed = _clamp(self.learning_speed)
        self.stress_sensitivity = _clamp(self.stress_sensitivity)

    # ==============================
    # Domain Behaviors
    # ==============================

    def update_retention(self, delta: float) -> None:
        """
        Atualiza a taxa de retenção de forma incremental.
        """
        self.retention_rate = _clamp(self.retention_rate + delta)

    def update_learning_speed(self, delta: float) -> None:
        """
        Atualiza a velocidade de aprendizado.
        """
        self.learning_speed = _clamp(self.learning_speed + delta)

    def update_stress_sensitivity(self, delta: float) -> None:
        """
        Ajusta sensibilidade ao estresse conforme comportamento observado.
        """
        self.stress_sensitivity = _clamp(self.stress_sensitivity + delta)

    def register_error_event(self, error_type: str, weight: float = 1.0) -> None:
        """
        Registra um padrão de erro observado durante estudos ou avaliações.

        Ex:
        - "falta_atencao"
        - "erro_conceitual"
        - "gestao_tempo"
        """
        self.error_patterns[error_type] = (
            self.error_patterns.get(error_type, 0.0) + max(weight, 0.0)
        )

    # ==============================
    # Domain Insights
    # ==============================

    def dominant_error_pattern(self) -> str | None:
        """
        Retorna o padrão de erro mais frequente, se existir.
        """
        if not self.error_patterns:
            return None
        return max(self.error_patterns, key=self.error_patterns.get)
