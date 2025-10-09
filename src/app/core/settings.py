from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding='utf-8')

    DATABASE_URL: str
    SECRET_KEY: str

    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    NEO4J_initial_dbms_default__database: str

    COURSE_TO_NEO4J_DB: dict = {
        # course_name -> db_name
        "g11phys": "g11phys",
        "g11chem": "g11chem",
    }

    ALGORITHM: ClassVar[str] = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()
