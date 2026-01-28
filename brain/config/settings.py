from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./athena.db"
    USE_IN_MEMORY_DB: bool = False
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "athena_knowledge"

    GEMINI_API_KEY: str | None = None
    # OPENAI_API_KEY: str | None = None  # Deprecated


settings = Settings()
