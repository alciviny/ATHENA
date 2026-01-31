import sys
import os

# Ajusta PYTHONPATH para importar o pacote `brain` quando executado como script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import text
from brain.infrastructure.persistence.database import engine, SYNC_DATABASE_URL, Base


def ensure_schema():
    print("Verificando schema do banco de dados...")

    if "postgresql" in (SYNC_DATABASE_URL or ""):
        with engine.begin() as conn:
            print("Banco PostgreSQL detectado — aplicando alterações seguras...")
            # Adiciona a coluna se não existir
            conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS cognitive_profile_id uuid;"))

            # Popula cognitive_profile_id a partir da tabela cognitive_profiles quando possível
            conn.execute(text(
                """
                UPDATE students
                SET cognitive_profile_id = cp.id
                FROM cognitive_profiles cp
                WHERE cp.student_id = students.id AND students.cognitive_profile_id IS NULL;
                """
            ))

            # Garantir colunas adicionais em knowledge_nodes usadas pelos modelos
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS description text;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS importance_weight double precision DEFAULT 1.0;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS estimated_study_time double precision DEFAULT 30.0;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS weight_in_exam double precision DEFAULT 0.0;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS weight double precision DEFAULT 1.0;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS stability double precision DEFAULT 1.0;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS reps integer DEFAULT 0;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS lapses integer DEFAULT 0;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS last_reviewed_at timestamp;"))
            conn.execute(text("ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS next_review_at timestamp;"))

            # Adiciona constraint FK somente se não existir
            conn.execute(text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'students_cognitive_profile_id_fkey'
                    ) THEN
                        ALTER TABLE students
                        ADD CONSTRAINT students_cognitive_profile_id_fkey
                        FOREIGN KEY (cognitive_profile_id) REFERENCES cognitive_profiles(id)
                        ON DELETE SET NULL;
                    END IF;
                END
                $$;
                """
            ))
        print("Alterações aplicadas (Postgres).")
    else:
        # Para outros bancos (ex: sqlite) usamos create_all para alinhar o schema local
        print("Banco não-Postgres detectado — executando create_all para sincronizar modelos locais.")
        Base.metadata.create_all(bind=engine)
        print("create_all finalizado.")


if __name__ == '__main__':
    ensure_schema()
