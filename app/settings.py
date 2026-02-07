"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import field_validator, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/skills_marketplace"

    # Admin Auth
    admin_username: str = "admin"
    admin_password_hash: str = "$2b$12$hLswkuEVcK3pHzkOacog1er9oqZkB.8pJhCKyCf9Ru03K6FqpwEPi" # Hardcoded fallback for safety
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # GitHub
    github_token: str = ""
    github_api_base: str = "https://api.github.com"

    # GLM (optional)
    glm_api_key: str = Field(default="", validation_alias=AliasChoices("GLM_API_KEY"))
    glm_api_base: str = Field(default="", validation_alias=AliasChoices("GLM_API_BASE", "GLM_BASE_URL"))
    # Optional override for providers that require a specific path (e.g. .../chat/completions).
    glm_chat_completions_url: str = Field(default="", validation_alias=AliasChoices("GLM_CHAT_COMPLETIONS_URL"))
    glm_model: str = Field(default="glm-4", validation_alias=AliasChoices("GLM_MODEL"))
    glm_temperature: float = Field(default=0.2, validation_alias=AliasChoices("GLM_TEMPERATURE"))
    glm_timeout_seconds: int = Field(default=30, validation_alias=AliasChoices("GLM_TIMEOUT_SECONDS"))

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Logging
    log_level: str = "INFO"

    @field_validator("admin_password_hash", mode="before")
    @classmethod
    def normalize_admin_hash(cls, value: str) -> str:
        """Normalize escaped dollar signs from docker-compose env interpolation."""
        if isinstance(value, str):
            return value.replace("$$", "$")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
