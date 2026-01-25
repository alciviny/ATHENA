from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from brain.config.settings import settings

# ----------------------
# Configuração da DB Sync (para scripts e ferramentas Legadas)
# ----------------------
SYNC_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ----------------------
# Configuração da DB Async
# ----------------------
ASYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
if "postgresql" in ASYNC_DATABASE_URL:
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
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
