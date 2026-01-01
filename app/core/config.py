import logging
import os
from typing import ClassVar, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('ENVIRONMENT', 'local')}",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: Literal["local", "prod", "test"] = "local"

    # sql config
    DATABASE_URL: str
    SUPABASE_JWT_SECRET: str
    ALGORITHM: ClassVar[str] = "HS256"

    # redis config
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # AI API key
    GOOGLE_API_KEY: str

    # AI model defaults
    GEMINI_GRAPH_MODEL: str = "gemini-3-flash-preview"
    GEMINI_GRAPH_TEMPERATURE: float = 0.0
    GEMINI_GRAPH_MAX_RETRY_ATTEMPTS: int = 3
    GEMINI_GRAPH_CHUNK_SIZE: int = 300000
    GEMINI_GRAPH_CHUNK_OVERLAP: int = 10000

    GEMINI_QUESTION_MODEL: str = "gemini-3-pro-preview"
    GEMINI_QUESTION_TEMPERATURE: float = 0.7
    GEMINI_QUESTION_MAX_RETRY_ATTEMPTS: int = 3

    PDF_GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    PDF_GEMINI_TEMPERATURE: float = 0.0
    PDF_GEMINI_TOP_P: float = 0.95
    PDF_CHUNK_SIZE: int = 20
    PDF_PROCESSING_TIMEOUT_SECONDS: int = 60
    PDF_POLL_INTERVAL_SECONDS: int = 2
    PDF_MAX_CONCURRENCY: int = 2

    # Pipeline storage paths
    PIPELINE_STORAGE_PATH: str = Field(default="temp/pipeline_storage")
    PIPELINE_RESULTS_PATH: str = Field(default="temp/results")

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"


settings = Settings()  # type: ignore

logging.basicConfig(level=logging.INFO)
logging.info(f"Settings loaded for ENVIRONMENT: {settings.ENVIRONMENT}")
logging.info(f"Database URL: {settings.DATABASE_URL}")
