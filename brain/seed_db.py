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
from brain.api.fastapi.auth.security import get_password_hash

# O ID do estudante que o frontend espera
STUDENT_ID = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
COGNITIVE_PROFILE_ID = uuid.uuid4()
STUDENT_NAME = "Aluno Teste"
STUDENT_EMAIL = "aluno@teste.com"
STUDENT_PASSWORD = "teste123"
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
            # Update missing fields if needed
            updated = False
            if not hasattr(existing_student, 'email') or not existing_student.email:
                existing_student.email = STUDENT_EMAIL
                updated = True
            if not hasattr(existing_student, 'password_hash') or not existing_student.password_hash:
                existing_student.password_hash = get_password_hash(STUDENT_PASSWORD)
                updated = True
            if updated:
                db.commit()
                print(f"Estudante existente atualizado com campos de autenticação.")

            if not existing_student.cognitive_profile:
                print(f"Estudante existe mas não tem perfil cognitivo. Criando...")
                new_profile = CognitiveProfileModel(
                    id=uuid.uuid4(),
                    retention_rate=0.8,
                    learning_speed=0.6,
                    stress_sensitivity=0.2,
                    error_patterns={}
                )
                existing_student.cognitive_profile = new_profile
                db.add(existing_student)
                db.commit()
                print("Perfil cognitivo criado para o estudante existente.")
            else:
                print(f"Estudante '{STUDENT_NAME}' com ID {STUDENT_ID} já existe e possui perfil cognitivo. Nada a fazer.")
            return

        print(f"Criando estudante de teste: {STUDENT_NAME}...")

        # 1. Cria as instâncias do estudante e do perfil
        new_student = StudentModel(
            id=STUDENT_ID,
            name=STUDENT_NAME,
            email=STUDENT_EMAIL,
            password_hash=get_password_hash(STUDENT_PASSWORD),
            goal=STUDENT_GOAL,
        )

        new_profile = CognitiveProfileModel(
            id=COGNITIVE_PROFILE_ID,
            retention_rate=0.8,
            learning_speed=0.6,
            stress_sensitivity=0.2,
            error_patterns={}
        )

        # 2. Associa o perfil ao estudante usando o relacionamento
        new_student.cognitive_profile = new_profile

        # 3. Adiciona o estudante à sessão (o perfil vai junto por causa do relacionamento)
        db.add(new_student)

        # 4. Commita a transação. O SQLAlchemy resolve a ordem de inserção.
        db.commit()

        print("Estudante e perfil cognitivo criados com sucesso!")

    finally:
        db.close()

if __name__ == "__main__":
    print("Iniciando o processo de seeding do banco de dados...")
    seed_database()
    print("Processo de seeding concluído.")
