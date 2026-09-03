from functools import cached_property
from pathlib import Path

from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "myapp"

    APP_NAME: str = "alix"

    # RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672//"
    # QUEUE_NAME: str

    DEBUG: bool = True

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    SECRET_KEY: str = "12345"
    ALGORITHM: str = "HS256"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "<PASSWORD>"

    # Text Manipulation
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Embeddings / RAG providers
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL_NAME: str = "gemini-embedding-2"
    EMBEDDING_DIMENSION: int = 3072
    LLM_MODEL_NAME: str = "gemini-3.5-flash"
    CURRENT_VECTORSTORE: str = "pgvector"
    CURRENT_EMBEDDING: str = "gemini"
    CURRENT_LLM: str = "gemini"

    def _create_database_url(self, drivername: str) -> str:
        url = URL.create(
            drivername=drivername,
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )
        return url.render_as_string(hide_password=False)

    @cached_property
    def DATABASE_URL(self) -> str:
        return self._create_database_url("postgresql")

    @cached_property
    def ASYNC_DATABASE_URL(self) -> str:
        return self._create_database_url("postgresql+asyncpg")

    @cached_property
    def PSYCOPG_DATABASE_URL(self) -> str:
        return self._create_database_url("postgresql+psycopg")

    class Config:
        env_file = BACKEND_DIR / ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
