import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ----------------------
# Configuração da DB
# ----------------------
POSTGRES_USER = os.getenv("POSTGRES_USER", "utilizador")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "senha")
POSTGRES_DB = os.getenv("POSTGRES_DB", "athena_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ----------------------
# Context manager da sessão
# ----------------------
@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Fornece uma sessão de banco de dados SQLAlchemy.
    Garante fechamento da sessão após uso.
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()  # garante commit automático ao sair
    except Exception:
        db.rollback()  # rollback em caso de erro
        raise
    finally:
        db.close()
