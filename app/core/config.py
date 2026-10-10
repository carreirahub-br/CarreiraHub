from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Aceita URLs do Render (`postgres://` / `postgresql://`) e força o driver psycopg 3."""
    value = url.strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        value = "postgresql+psycopg://" + value[len("postgresql://") :]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CarreiraHub"
    app_env: str = "development"
    app_debug: bool = False
    app_base_url: str = "http://localhost:8000"
    render_external_url: str = Field(default="")
    secret_key: str = "dev-only-change-me"
    database_url: str = "sqlite+pysqlite:///./carreirahub.db"
    auto_create_tables: bool = True
    adsense_enabled: bool = False
    adsense_client_id: str = ""
    social_linkedin_url: str = ""
    social_instagram_url: str = ""
    social_youtube_url: str = ""
    contact_email: str = "contato@carreirahub.com.br"

    @field_validator("database_url", mode="before")
    @classmethod
    def _database_url(cls, value: str) -> str:
        return normalize_database_url(value) if isinstance(value, str) else value

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local", "test"}

    @property
    def base_url(self) -> str:
        custom = self.app_base_url.rstrip("/")
        if custom and "localhost" not in custom and "127.0.0.1" not in custom:
            return custom
        if self.render_external_url:
            return self.render_external_url.rstrip("/")
        return custom or "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
