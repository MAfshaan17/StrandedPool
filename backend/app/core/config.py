import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_FRONTEND_ORIGINS = (
    "http://localhost:3000,"
    "http://127.0.0.1:3000,"
    "http://localhost:3001,"
    "http://127.0.0.1:3001,"
    "http://localhost:3002,"
    "http://127.0.0.1:3002"
)


class Settings(BaseSettings):
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    frontend_origin: str = Field(
        default=DEFAULT_FRONTEND_ORIGINS,
        validation_alias="FRONTEND_ORIGIN",
    )
    database_url: str = Field(
        default="sqlite+aiosqlite:///./strandedpool.db",
        validation_alias="DATABASE_URL",
    )

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, value: str) -> str:
        if value not in {"development", "production", "test"}:
            raise ValueError("APP_ENV must be one of development, production, test")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=os.getenv("ENV_FILE", str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
