from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    DATABASE_HOSTNAME: str
    DATABASE_PORT: int
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_USER: str

    SECRET_KEY: str
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOSTNAME}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

settings = Settings()


# DB_SETTINGS = {
#     'dbname': 'learning_graph_db',
#     'user': 'learning_user',      # 你的 PostgreSQL 用户名
#     'password': 'd1997225',  # 你的 PostgreSQL 密码
#     'host': 'localhost',          # 通常是 localhost
#     'port': '5432'                # 默认端口
# }