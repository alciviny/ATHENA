from dataclasses import dataclass
from typing import Callable, Dict, Any


RuleCondition = Callable[[Dict[str, Any]], bool]
RuleAction = Callable[[Dict[str, Any]], None]


@dataclass(frozen=True)
class AdaptiveRule:
    """
    Regra adaptativa do sistema.

    Uma regra avalia um contexto (estado atual do aluno, eventos recentes,
    perfil cognitivo, plano ativo, etc.) e executa uma ação se aplicável.
    """
    name: str
    description: str

    condition: RuleCondition
    action: RuleAction

    def should_apply(self, context: Dict[str, Any]) -> bool:
        """
        Avalia se a regra deve ser aplicada dado o contexto atual.
        """
        try:
            return self.condition(context)
        except Exception:
            # Regra nunca deve quebrar o fluxo do sistema
            return False

    def apply(self, context: Dict[str, Any]) -> bool:
        """
        Aplica a regra se a condição for satisfeita.

        Retorna True se a regra foi aplicada.
        """
        if not self.should_apply(context):
            return False

        self.action(context)
        return True
