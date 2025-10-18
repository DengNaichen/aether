from typing import ClassVar, Literal
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: Literal["dev", "prod", "test"] = "dev"

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


settings = Settings()  # type: ignore
