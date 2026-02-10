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
    glm_timeout_seconds: int = Field(default=60, validation_alias=AliasChoices("GLM_TIMEOUT_SECONDS"))

    # Security scan (SKILL.md content)
    # - enabled: run scan during parsing
    # - enforce: block/quarantine when flagged
    security_scan_enabled: bool = Field(default=True, validation_alias=AliasChoices("SECURITY_SCAN_ENABLED"))
    security_scan_enforce: bool = Field(default=True, validation_alias=AliasChoices("SECURITY_SCAN_ENFORCE"))
    # Run GLM security classification only when heuristic scan finds suspicious signals.
    security_scan_glm_on_suspicion_only: bool = Field(
        default=True, validation_alias=AliasChoices("SECURITY_SCAN_GLM_ON_SUSPICION_ONLY")
    )
    security_scan_confidence_threshold: float = Field(
        default=0.7, validation_alias=AliasChoices("SECURITY_SCAN_CONFIDENCE_THRESHOLD")
    )
    security_scan_max_chars: int = Field(default=6000, validation_alias=AliasChoices("SECURITY_SCAN_MAX_CHARS"))

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Logging
    log_level: str = "INFO"

    # Skill validation/enforcement (ingest pipeline)
    # - profile: "lax" (default) logs warnings but only hard failures become errors
    # - profile: "strict" elevates more spec issues to errors
    skill_validation_profile: str = "lax"
    skill_validation_enforce: bool = True

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
