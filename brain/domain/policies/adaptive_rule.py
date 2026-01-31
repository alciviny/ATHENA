from abc import ABC
from typing import List, Callable, Any, Optional
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.performance_event import PerformanceEvent


class AdaptiveRule(ABC):
    """
    Classe base para regras adaptativas.

    Pode ser usada de duas formas:
    1) Subclassing: criar uma subclasse e sobrescrever `apply`.
    2) Instantiation: fornecer `condition` e `action` callables ao criar a regra.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        condition: Optional[Callable[[dict], bool]] = None,
        action: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.name = name
        self.description = description
        self._condition = condition
        self._action = action

    def apply(self, cognitive_profile: Any, performance_events: Optional[List[PerformanceEvent]] = None) -> None:
        # Comportamento flexível:
        # - Se chamado com um dicionário (ctx), trata como contexto direto das regras.
        # - Caso contrário, monta um ctx a partir de cognitive_profile e performance_events.
        try:
            # Caso 1: chamado como apply(ctx: dict)
            if isinstance(cognitive_profile, dict):
                ctx = cognitive_profile
                if self._condition and self._action and self._condition(ctx):
                    self._action(ctx)
                return
        except Exception:
            pass

        # Caso 2: assinatura clássica: (cognitive_profile, performance_events)
        if self._condition and self._action:
            ctx = {
                "cognitive_profile": cognitive_profile,
                "performance_events": performance_events,
            }
            try:
                if self._condition(ctx):
                    self._action(ctx)
            except Exception:
                return
        else:
            # Se a subclasse implementou seu próprio comportamento, permita que sobrescreva
            return

    def should_apply(self, ctx: dict) -> bool:
        """Avalia a condição com um contexto de dicionário (compatibilidade com testes)."""
        if not self._condition:
            return False
        try:
            return bool(self._condition(ctx))
        except Exception:
            return False
