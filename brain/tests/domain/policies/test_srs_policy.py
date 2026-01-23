from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Assumindo que SRSPolicy e KnowledgeNode estão em caminhos como estes:
# Você precisará ajustar os imports conforme a estrutura exata do seu projeto
from brain.domain.policies.srs_policy import SRSPolicy
from brain.domain.entities.knowledge_node import ReviewGrade
# from brain.domain.entities.knowledge_node import KnowledgeNode # Se você tiver uma classe KnowledgeNode real e quiser usá-la em vez de MagicMock


# Helper para criar um KnowledgeNode mockado com valores iniciais
def create_mock_knowledge_node(
    stability=1.0, difficulty=0.5, next_review=None, repetitions=0, elapsed_days=0
):
    """Cria um objeto KnowledgeNode mockado para testes."""
    mock_node = MagicMock()
    mock_node.stability = stability
    mock_node.difficulty = difficulty
    mock_node.reps = repetitions
    mock_node.elapsed_days = elapsed_days
    mock_node.last_review = next_review - timedelta(days=elapsed_days) if next_review else datetime.now() - timedelta(days=elapsed_days)

    if next_review is None:
        mock_node.next_review = datetime.now()
    else:
        mock_node.next_review = next_review
    return mock_node


@patch('brain.domain.policies.srs_policy.datetime')
def test_srs_policy_apply_grade_good(mock_datetime):
    """
    Testa a aplicação da SRSPolicy com uma nota 'Good' (3).
    Espera-se que a estabilidade aumente e a próxima revisão seja no futuro.
    """
    # Fixa a data atual para garantir testes determinísticos
    fixed_now = datetime(2026, 1, 22, 10, 0, 0)
    mock_datetime.now.return_value = fixed_now
    # Permite que outras chamadas a datetime funcionem normalmente (ex: datetime.timedelta)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)


    # Cria um KnowledgeNode mockado com estado inicial
    initial_stability = 1.0
    initial_difficulty = 1.0
    initial_next_review = fixed_now - timedelta(days=1) # Estaria atrasado por 1 dia
    initial_elapsed_days = 1 # Passou 1 dia desde a última revisão

    mock_node = create_mock_knowledge_node(
        stability=initial_stability,
        difficulty=initial_difficulty,
        next_review=initial_next_review,
        elapsed_days=initial_elapsed_days
    )

    srs_policy = SRSPolicy()
    grade = ReviewGrade.GOOD

    # Aplica a política
    updated_node = srs_policy.apply_policy(mock_node, grade)

    # Verifica se o método apply_policy retornou o nó atualizado
    assert updated_node is mock_node

    # Assegura que a estabilidade aumentou (para 'Good', deve aumentar)
    assert updated_node.stability > initial_stability

    # Assegura que a dificuldade diminuiu ou permaneceu a mesma (para 'Good', geralmente diminui um pouco ou se mantém)
    # Aqui estamos fazendo uma suposição, o cálculo exato dependerá da sua implementação FSRS
    assert updated_node.difficulty <= initial_difficulty

    # Assegura que a próxima data de revisão é no futuro em relação à data fixa
    # E que o intervalo é maior do que o tempo passado
    expected_interval = updated_node.stability
    assert updated_node.next_review > fixed_now
    assert updated_node.next_review.date() == (fixed_now + timedelta(days=round(expected_interval))).date()
    assert updated_node.reps == 1 # Aumenta a contagem de repetições

    print(f"\n--- Teste 'Good' Concluído ---")
    print(f"Estabilidade Inicial: {initial_stability}, Final: {updated_node.stability}")
    print(f"Dificuldade Inicial: {initial_difficulty}, Final: {updated_node.difficulty}")
    print(f"Próxima Revisão Esperada: {(fixed_now + timedelta(days=round(expected_interval))).date()}, Calculada: {updated_node.next_review.date()}")
    print(f"Repetições: {updated_node.repetitions}")

