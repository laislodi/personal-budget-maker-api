from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./budget.db"
    """Pydantic BaseSettings maps env vars to fields by name. The hardcoded string is just the fallback default for local dev so you don't need to set anything to run locally"""
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    # Comma-separated list of allowed CORS origins.
    # Default allows the Vite dev server; override in production.
    allowed_origins: str = "http://localhost:5173"

    @field_validator("database_url")
    @classmethod
    def fix_async_driver(cls, v: str) -> str:
        """Render provides postgres:// — convert to the asyncpg driver URL."""
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
