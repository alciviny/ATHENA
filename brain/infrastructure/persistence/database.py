from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from brain.config.settings import settings

# ----------------------
# Configuração da DB Async
# ----------------------
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()

# ----------------------
# Context manager da sessão async
# ----------------------
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Fornece uma sessão de banco de dados SQLAlchemy assíncrona.
    Garante fechamento da sessão após uso.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise