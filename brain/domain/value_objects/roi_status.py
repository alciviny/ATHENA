from enum import Enum

class ROIStatus(str, Enum):
    VEIO_DE_OURO = "high_efficiency"
    ESTAGNACAO = "plateau"
    PANTANO = "low_efficiency"