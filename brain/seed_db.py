import sys
import os
import uuid

# Adiciona a raiz do projeto ao PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from brain.infrastructure.persistence.database import SessionLocal, engine, Base
from brain.infrastructure.persistence.models import StudentModel, CognitiveProfileModel

# O ID do estudante que o frontend espera
STUDENT_ID = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
COGNITIVE_PROFILE_ID = uuid.uuid4()
STUDENT_NAME = "Aluno Teste"
STUDENT_GOAL = "Polícia Federal"

def seed_database():
    """
    Popula o banco de dados com dados iniciais se ele estiver vazio.
    """
    # Cria todas as tabelas no engine.
    # Equivalente a "CREATE TABLE IF NOT EXISTS ..."
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Verifica se o estudante já existe
        existing_student = db.query(StudentModel).filter(StudentModel.id == STUDENT_ID).first()
        if existing_student:
            # Verifica se ele tem um perfil cognitivo, se não, cria um
            existing_profile = db.query(CognitiveProfileModel).filter(CognitiveProfileModel.student_id == STUDENT_ID).first()
            if not existing_profile:
                print(f"Estudante existe mas não tem perfil cognitivo. Criando...")
                new_profile = CognitiveProfileModel(
                    id=uuid.uuid4(),
                    student_id=STUDENT_ID,
                    retention_rate=0.8,
                    learning_speed=0.6,
                    stress_sensitivity=0.2,
                    error_patterns={}
                )
                db.add(new_profile)
                existing_student.cognitive_profile_id = new_profile.id
                db.commit()
                print("Perfil cognitivo criado para o estudante existente.")
            else:
                print(f"Estudante '{STUDENT_NAME}' com ID {STUDENT_ID} já existe e possui perfil cognitivo. Nada a fazer.")
            return

        print(f"Criando estudante de teste: {STUDENT_NAME}...")

        # Primeiro cria o perfil cognitivo
        new_profile = CognitiveProfileModel(
            id=COGNITIVE_PROFILE_ID,
            student_id=STUDENT_ID,
            retention_rate=0.8,
            learning_speed=0.6,
            stress_sensitivity=0.2,
            error_patterns={}
        )
        db.add(new_profile)

        # Cria a instância do modelo SQLAlchemy
        new_student = StudentModel(
            id=STUDENT_ID,
            name=STUDENT_NAME,
            goal=STUDENT_GOAL,
            cognitive_profile_id=new_profile.id
        )

        # Adiciona à sessão e commita
        db.add(new_student)
        db.commit()

        print("Estudante e perfil cognitivo criados com sucesso!")

    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando o processo de seeding do banco de dados...")
    seed_database()
    print("Processo de seeding concluído.")
