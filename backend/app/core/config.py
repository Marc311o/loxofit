from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Loxofit API"
    VERSION: str = "0.0.1"
    API_V1_STR: str = "/api/v1"

    # DB
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    SQL_ECHO: bool = False

    # AUTH
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    COOKIE_SECURE: bool = False
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_SAMESITE: str = "lax"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REFRESH_COOKIE_PATH(self) -> str:
        return f"{self.API_V1_STR}/auth"

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", BASE_DIR / ".env", ".env", "../.env"),
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
