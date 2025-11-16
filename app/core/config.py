from typing import ClassVar, Literal
from pydantic import Field
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Docker/local development: use .env.local
        # Testing: use .env.test (set ENVIRONMENT=test)
        # Production: use environment variables directly
        env_file=f".env.{os.getenv('ENVIRONMENT', 'local')}",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: Literal["local", "prod", "test"] = "local"

    # sql config
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: ClassVar[str] = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # redis config
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # Email config (Resend)
    RESEND_API_KEY: str
    FRONTEND_URL: str = Field(default="http://localhost:3000")  # Default for local dev
    EMAIL_FROM: str

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"


settings = Settings()  # type: ignore
import logging

logging.basicConfig(level=logging.INFO)
logging.info(f"Settings loaded for ENVIRONMENT: {settings.ENVIRONMENT}")
logging.info(f"Database URL: {settings.DATABASE_URL}")
