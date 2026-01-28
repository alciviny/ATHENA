import sys
import os

# Adiciona o diretório pai (raiz do projeto) ao caminho do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from brain.infrastructure.persistence.models import KnowledgeNodeModel, node_dependencies
from brain.config.settings import Settings
# etc...
NODES = {
    "aritmetica": {
        "name": "Aritmética Básica",
        "subject": "Matemática",
        "weight_in_exam": 0.10,
        "difficulty": 1.0,
        "weight": 1.0,
    },
    "algebra": {
        "name": "Álgebra Fundamental",
        "subject": "Matemática",
        "weight_in_exam": 0.25,
        "difficulty": 3.0,
        "weight": 1.2,
        "depends_on": ["aritmetica"],
    },
    "funcoes": {
        "name": "Funções e Gráficos",
        "subject": "Matemática",
        "weight_in_exam": 0.30,
        "difficulty": 5.0,
        "weight": 1.5,
        "depends_on": ["algebra"],
    },
    "cinematica": {
        "name": "Cinemática (MRU/MRUV)",
        "subject": "Física",
        "weight_in_exam": 0.20,
        "difficulty": 4.0,
        "weight": 1.1,
        "depends_on": ["algebra"],
    },
    "dinamica": {
        "name": "Leis de Newton (Dinâmica)",
        "subject": "Física",
        "weight_in_exam": 0.35,
        "difficulty": 6.0,
        "weight": 1.3,
        "depends_on": ["cinematica"],
    },
}


def seed_knowledge_graph(reset: bool = False):
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)

    print("(+) Seeding Knowledge Graph...")

    with Session.begin() as session:

        if reset:
            print("(!) RESET ATIVADO: apagando TUDO e recomeçando...")
            # Truncate tables to reset IDs and clear all data
            session.execute(text("TRUNCATE TABLE public.node_dependencies RESTART IDENTITY CASCADE"))
            session.execute(text("TRUNCATE TABLE public.knowledge_nodes RESTART IDENTITY CASCADE"))

        existing_nodes = {
            node.name: node
            for node in session.execute(
                select(KnowledgeNodeModel)
            ).scalars()
        }

        created_nodes = {}

        # 1. Criar nós
        for key, data in NODES.items():
            if data["name"] in existing_nodes:
                created_nodes[key] = existing_nodes[data["name"]]
                continue

            node = KnowledgeNodeModel(
                name=data["name"],
                subject=data["subject"],
                weight_in_exam=data["weight_in_exam"],
                difficulty=data["difficulty"],
                weight=data["weight"],
            )

            session.add(node)
            created_nodes[key] = node

        session.flush()  # garante IDs

        # 2. Criar dependências
        for key, data in NODES.items():
            if "depends_on" not in data:
                continue

            node = created_nodes[key]

            for dep_key in data["depends_on"]:
                dependency = created_nodes[dep_key]
                if dependency not in node.dependencies:
                    node.dependencies.append(dependency)

    print(">> Knowledge Graph pronto!")
    print("   Matemática: Aritmética > Álgebra > Funções")
    print("   Física: Álgebra > Cinemática > Dinâmica")  


if __name__ == "__main__":
    seed_knowledge_graph(reset=True)
