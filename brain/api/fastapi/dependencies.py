from uuid import uuid4, UUID
from typing import Tuple, List
from brain.domain.entities.student import Student, StudentGoal
from brain.domain.entities.cognitive_profile import CognitiveProfile
from brain.domain.entities.knowledge_node import KnowledgeNode


SEED_SUCCESS_MESSAGE = "\n🚀 Sistema populado com sucesso"

MATERIA_DIREITO_ADMINISTRATIVO = "Direito Administrativo"
MATERIA_INFORMATICA = "Informática"
MATERIA_DIREITO_CONSTITUCIONAL = "Direito Constitucional"
MATERIA_LINGUA_PORTUGUESA = "Língua Portuguesa"
TEST_STUDENT_NAME = "Jose Alcionis"
TOPICO_REDES_DE_COMPUTADORES = "Redes de Computadores"



def seed_repositories(student_repo, know_repo) -> UUID:
    """
    Popula os repositórios com dados de teste.
    
    Args:
        student_repo: Repositório de estudantes
        know_repo: Repositório de conhecimento
        
    Returns:
        UUID: ID do estudante criado para testes
    """
    # 1. Criar um Aluno de Teste
    student_id = uuid4()
    # Este profile foi movido para dentro da criação do Student
    # profile = CognitiveProfile(retention_rate=0.7, learning_speed=1.0) 
    test_student = Student(
        id=student_id, 
        name=TEST_STUDENT_NAME, 
        goal=StudentGoal.POLICIA_FEDERAL, 
        # cognitive_profile=profile # O profile agora é um ID
    )
    student_repo.save(test_student)
    
    # 2. Criar um pequeno Grafo de Conhecimento
    nodes = [
        KnowledgeNode(
            id=uuid4(), 
            title=MATERIA_DIREITO_ADMINISTRATIVO, 
            content="Atos Administrativos", 
            difficulty=0.8, 
            impact=1.0
        ),
        KnowledgeNode(
            id=uuid4(), 
            title=MATERIA_INFORMATICA, 
            content=TOPICO_REDES_DE_COMPUTADORES, 
            difficulty=0.6, 
            impact=0.9
        ),
    ]
    know_repo.set_graph(nodes)
    
    print(f"{SEED_SUCCESS_MESSAGE}!")
    print(f"📚 Estudante criado: {test_student.name}")
    print(f"🎯 Objetivo: {test_student.goal.value if hasattr(test_student.goal, 'value') else test_student.goal}")
    print(f"🆔 ID do aluno para testes: {student_id}")
    print(f"📊 Nós de conhecimento criados: {len(nodes)}\n")
    
    return student_id


def seed_repositories_extended(student_repo, know_repo, performance_repo=None) -> Tuple[UUID, List[UUID]]:
    """
    Versão estendida com mais dados de teste, incluindo múltiplos alunos e grafo maior.
    
    Args:
        student_repo: Repositório de estudantes
        know_repo: Repositório de conhecimento
        performance_repo: Repositório de performance (opcional)
        
    Returns:
        Tuple[UUID, List[UUID]]: ID do aluno principal e lista de IDs de nós de conhecimento
    """
    # 1. Criar múltiplos alunos de teste
    students_data = [
        {
            "name": TEST_STUDENT_NAME,
            "goal": StudentGoal.POLICIA_FEDERAL,
            "retention": 0.7,
            "speed": 1.0
        },
        {
            "name": "Maria Silva",
            "goal": StudentGoal.INSS,
            "retention": 0.8,
            "speed": 1.2
        },
        {
            "name": "João Santos",
            "goal": StudentGoal.RECEITA_FEDERAL,
            "retention": 0.6,
            "speed": 0.9
        }
    ]
    
    created_students = []
    for data in students_data:
        student_id = uuid4()
        # profile = CognitiveProfile(
        #     retention_rate=data["retention"], 
        #     learning_speed=data["speed"]
        # )
        student = Student(
            id=student_id,
            name=data["name"],
            goal=data["goal"],
            # cognitive_profile=profile
        )
        student_repo.save(student)
        created_students.append((student_id, data["name"]))
    
    # 2. Criar um grafo de conhecimento mais completo
    knowledge_data = [
        # Direito Administrativo
        {
            "title": MATERIA_DIREITO_ADMINISTRATIVO,
            "content": "Atos Administrativos",
            "difficulty": 0.8,
            "impact": 1.0
        },
        {
            "title": MATERIA_DIREITO_ADMINISTRATIVO,
            "content": "Princípios da Administração Pública",
            "difficulty": 0.6,
            "impact": 0.9
        },
        {
            "title": MATERIA_DIREITO_ADMINISTRATIVO,
            "content": "Licitações e Contratos",
            "difficulty": 0.7,
            "impact": 0.85
        },
        
        # Informática
        {
            "title": MATERIA_INFORMATICA,
            "content": TOPICO_REDES_DE_COMPUTADORES,
            "difficulty": 0.6,
            "impact": 0.9
        },
        {
            "title": MATERIA_INFORMATICA,
            "content": "Segurança da Informação",
            "difficulty": 0.7,
            "impact": 0.95
        },
        {
            "title": MATERIA_INFORMATICA,
            "content": "Sistemas Operacionais",
            "difficulty": 0.5,
            "impact": 0.8
        },
        
        # Direito Constitucional
        {
            "title": MATERIA_DIREITO_CONSTITUCIONAL,
            "content": "Direitos Fundamentais",
            "difficulty": 0.7,
            "impact": 1.0
        },
        {
            "title": MATERIA_DIREITO_CONSTITUCIONAL,
            "content": "Organização do Estado",
            "difficulty": 0.6,
            "impact": 0.85
        },
        
        # Português
        {
            "title": MATERIA_LINGUA_PORTUGUESA,
            "content": "Sintaxe e Semântica",
            "difficulty": 0.5,
            "impact": 0.9
        },
        {
            "title": MATERIA_LINGUA_PORTUGUESA,
            "content": "Interpretação de Textos",
            "difficulty": 0.6,
            "impact": 1.0
        },
    ]
    
    nodes = []
    node_ids = []
    for data in knowledge_data:
        node_id = uuid4()
        node = KnowledgeNode(
            id=node_id,
            name=data["content"],
            subject=data["title"],
            weight_in_exam=data["impact"],
            difficulty=data["difficulty"]
        )
        nodes.append(node)
        node_ids.append(node_id)
    
    know_repo.set_graph(nodes)
    
    # 3. Adicionar eventos de performance se o repositório foi fornecido
    if performance_repo:
        from brain.domain.entities.PerformanceEvent import PerformanceEvent, PerformanceEventType, PerformanceMetric
        from datetime import datetime, timedelta
        
        # Adicionar alguns eventos de exemplo para o primeiro aluno
        main_student_id = created_students[0][0]
        base_date = datetime.now() - timedelta(days=7)
        
        sample_events = [
            PerformanceEvent(
                id=uuid4(),
                student_id=main_student_id,
                event_type=PerformanceEventType.QUIZ,
                occurred_at=base_date + timedelta(days=1),
                topic=MATERIA_DIREITO_ADMINISTRATIVO,
                metric=PerformanceMetric.ACCURACY,
                value=1.0,
                baseline=0.5
            ),
            PerformanceEvent(
                id=uuid4(),
                student_id=main_student_id,
                event_type=PerformanceEventType.QUIZ,
                occurred_at=base_date + timedelta(days=2),
                topic=MATERIA_INFORMATICA,
                metric=PerformanceMetric.ACCURACY,
                value=0.0,
                baseline=0.5
            ),
            PerformanceEvent(
                id=uuid4(),
                student_id=main_student_id,
                event_type=PerformanceEventType.QUIZ,
                occurred_at=base_date + timedelta(days=3),
                topic=MATERIA_DIREITO_CONSTITUCIONAL,
                metric=PerformanceMetric.ACCURACY,
                value=1.0,
                baseline=0.5
            ),
        ]
        
        for event in sample_events:
            performance_repo.add_event(event)
    
    # Relatório de criação
    print(f"{SEED_SUCCESS_MESSAGE} (modo estendido)!")
    print(f"\n👥 Estudantes criados ({len(created_students)}):")
    for idx, (sid, name) in enumerate(created_students, 1):
        print(f"  {idx}. {name} - ID: {sid}")
    
    print(f"\n📚 Nós de conhecimento criados: {len(nodes)}")
    
    # Agrupar por disciplina
    topics = {}
    for node in nodes:
        if node.subject not in topics:
            topics[node.subject] = 0
        topics[node.subject] += 1
    
    print("\n📊 Distribuição por disciplina:")
    for topic, count in topics.items():
        print(f"  • {topic}: {count} tópicos")
    
    if performance_repo:
        print(f"\n✅ Eventos de performance adicionados: {len(sample_events)}")
    
    print(f"\n🎯 ID do aluno principal para testes: {created_students[0][0]}\n")
    
    return created_students[0][0], node_ids


# Função auxiliar para limpar os repositórios
def clear_repositories(student_repo, know_repo, performance_repo=None, study_plan_repo=None):
    """
    Limpa todos os dados dos repositórios.
    Útil para resetar o ambiente de testes.
    """
    if hasattr(student_repo, 'students'):
        student_repo.students.clear()
    
    if hasattr(know_repo, 'nodes'):
        know_repo.nodes.clear()
    
    if performance_repo and hasattr(performance_repo, 'events'):
        performance_repo.events.clear()
    
    if study_plan_repo and hasattr(study_plan_repo, 'plans'):
        study_plan_repo.plans.clear()
    
    print("🧹 Repositórios limpos com sucesso!\n")
