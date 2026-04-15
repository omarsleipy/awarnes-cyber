"""Application configuration from environment."""
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings loaded from env and .env file."""

    # Database (accept DB_URL or DATABASE_URL from env)
    DB_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/cyberaware",
        validation_alias=AliasChoices("DB_URL", "DATABASE_URL"),
    )

    # JWT
    JWT_SECRET: str = "change-me-in-production-use-long-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS (React frontend)
    CORS_ORIGINS: str = "http://localhost:8080,http://127.0.0.1:8080"

    # SMTP (for exam passwords & notifications)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@corp.com"
    SMTP_FROM_NAME: str = "CyberAware Platform"
    SMTP_USE_TLS: bool = True
    SMTP_MOCK_MODE: bool = True

    # App URLs used in notification/tracking emails
    APP_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:8080"

    # LDAP (stub integration)
    LDAP_SERVER: str = ""
    LDAP_PORT: int = 389
    LDAP_BASE_DN: str = ""
    LDAP_BIND_DN: str = ""
    LDAP_BIND_PASSWORD: str = ""
    LDAP_USER_FILTER: str = "(objectClass=person)"
    LDAP_USE_SSL: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
