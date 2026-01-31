from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Banco de Dados ---
    # Default para Postgres (Docker)
    DATABASE_URL: str = "postgresql+asyncpg://athena_user:athena_password@db:5432/athena_db"
    USE_IN_MEMORY_DB: bool = False

    # --- Qdrant (Memória Vetorial) ---
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: Optional[str] = None

    # --- IA: Google Gemini (Embeddings & Backup) ---
    GEMINI_API_KEY: Optional[str] = None
    # Usamos o 2.0 Flash como default seguro se o 1.5 não existir
    GEMINI_MODEL: str = "models/gemini-2.0-flash" 

    # --- IA: Groq (Texto Rápido - Llama 3) ---
    # ADICIONADO AGORA:
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # --- Feature flag: permite usar fallbacks "falsos" em ambientes de teste
    # Em produção, recomenda-se manter como False para evitar mascarar falhas de IA.
    ALLOW_FAKE_FALLBACK: bool = False

    # Configuração para ler do arquivo .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignora variáveis extras no .env para não dar erro
    )


settings = Settings()