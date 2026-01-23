import sys
import os

# Adiciona a raiz do projeto ao PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from brain.infrastructure.persistence.database import Base, engine
from brain.infrastructure.persistence import models

def create_database():
    """
    Cria o banco de dados e as tabelas se eles não existirem.
    """
    print("Criando banco de dados e tabelas...")
    Base.metadata.create_all(bind=engine)
    print("Banco de dados e tabelas criados com sucesso.")

if __name__ == "__main__":
    create_database()
