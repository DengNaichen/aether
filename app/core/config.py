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

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"


settings = Settings()  # type: ignore

logging.basicConfig(level=logging.INFO)
logging.info(f"Settings loaded for ENVIRONMENT: {settings.ENVIRONMENT}")
logging.info(f"Database URL: {settings.DATABASE_URL}")
