from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar, Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding='utf-8')

    ENVIRONMENT: Literal["dev", "prod", "test"] = "dev"

    # sql config
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: ClassVar[str] = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Neo4j config
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    NEO4J_initial_dbms_default__database: str

    # course map
    COURSE_TO_NEO4J_DB: dict = {
        # course_name -> db_name
        "g11phys": "g11phys",
        "g11chem": "g11chem",
    }

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"


settings = Settings()  # type: ignore
