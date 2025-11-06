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
        extra="ignore"
    )

    ENVIRONMENT: Literal["local", "prod", "test"] = "local"

    # sql config
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: ClassVar[str] = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # redis config
    REDIS_URL: str = Field(
        default="redis://redis:6379/0"
    )

    # Neo4j config
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"

    @property
    def NEOMODEL_NEO4J_URI(self) -> str:
        from urllib.parse import urlparse, urlunparse

        parsed_uri = urlparse(self.NEO4J_URI)

        netloc_with_auth = f"{self.NEO4J_USER}:{self.NEO4J_PASSWORD}@{parsed_uri.hostname}"
        if parsed_uri.port:
            netloc_with_auth += f":{parsed_uri.port}"

        db_name = self.NEO4J_DATABASE or parsed_uri.path.lstrip('/')
        path = f"/{db_name}" if db_name else "/"

        return urlunparse(
            (parsed_uri.scheme, netloc_with_auth, path, "", "", "")
        )


settings = Settings()  # type: ignore
import logging
logging.basicConfig(level=logging.INFO)
logging.info(f"Settings loaded for ENVIRONMENT: {settings.ENVIRONMENT}")
logging.info(f"Database URL: {settings.DATABASE_URL}")
