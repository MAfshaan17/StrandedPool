import os
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_FRONTEND_ORIGINS = (
    "http://localhost:3000,"
    "http://127.0.0.1:3000,"
    "http://localhost:3001,"
    "http://127.0.0.1:3001,"
    "http://localhost:3002,"
    "http://127.0.0.1:3002,"
    "http://localhost:3003,"
    "http://127.0.0.1:3003"
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
    auth_secret_key: str = Field(default="", validation_alias="AUTH_SECRET_KEY")
    cost_score_weight: float = Field(default=0.40, validation_alias="COST_SCORE_WEIGHT")
    time_score_weight: float = Field(default=0.35, validation_alias="TIME_SCORE_WEIGHT")
    reliability_score_weight: float = Field(default=0.15, validation_alias="RELIABILITY_SCORE_WEIGHT")
    convenience_score_weight: float = Field(default=0.10, validation_alias="CONVENIENCE_SCORE_WEIGHT")

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, value: str) -> str:
        if value not in {"development", "production", "test"}:
            raise ValueError("APP_ENV must be one of development, production, test")
        return value

    @model_validator(mode="after")
    def require_production_auth_secret(self):
        placeholder_secret = self.auth_secret_key.startswith("replace-with-")
        if self.app_env == "production" and (
            len(self.auth_secret_key) < 32 or placeholder_secret
        ):
            raise ValueError(
                "Set AUTH_SECRET_KEY to a non-placeholder secret of at least 32 characters in production"
            )
        if placeholder_secret:
            self.auth_secret_key = ""
        weights = (
            self.cost_score_weight,
            self.time_score_weight,
            self.reliability_score_weight,
            self.convenience_score_weight,
        )
        if any(weight < 0 or weight > 1 for weight in weights):
            raise ValueError("Scoring weights must each be between 0 and 1")
        if abs(sum(weights) - 1.0) > 1e-6:
            raise ValueError("Scoring weights must sum to 1")
        return self

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
