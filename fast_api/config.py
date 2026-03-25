from __future__ import annotations

import sys
import logging
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator
from functools import lru_cache

logger = logging.getLogger(__name__)


class Settings(BaseSettings):

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/reconix"
    DATABASE_READ_REPLICA_URL: str = ""
    DATABASE_DRIVER: str = "postgresql"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO_SQL: bool = False
    DATABASE_STATEMENT_TIMEOUT_MS: int = 30000

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

    API_RATE_LIMIT_PER_MINUTE: int = 100
    AUTH_RATE_LIMIT_PER_MINUTE: int = 5
    MAX_REQUEST_SIZE_MB: int = 10
    MAX_BULK_UPLOAD_RECORDS: int = 10000

    PAGINATION_MAX_LIMIT: int = 100
    PAGINATION_DEFAULT_LIMIT: int = 50

    NIMC_API_URL: str = "https://api.nimc.gov.ng"
    NIBSS_API_URL: str = "https://api.nibss.gov.ng"
    BANK_API_TIMEOUT: int = 30

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    NOTIFICATION_FROM_EMAIL: str = "no-reply@reconix.ng"
    ENABLE_EMAIL_NOTIFICATIONS: bool = False

    AUDIT_LOG_RETENTION_DAYS: int = 365

    ENFORCE_HTTPS: bool = True

    FIELD_ENCRYPTION_KEY: str = ""
    ENABLE_JSON_LOGGING: bool = True
    ENABLE_METRICS: bool = True
    ENABLE_IDEMPOTENCY: bool = True
    ENABLE_TRACING: bool = True

    SENTRY_DSN: str = ""
    SENTRY_RELEASE: str = "1.0.0"

    REDIS_URL: str = ""

    VAULT_URL: str = ""
    VAULT_TOKEN: str = ""

    ENABLE_WEBSOCKET: bool = True

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.JWT_ALGORITHM not in ("HS256", "HS384", "HS512"):
            logger.critical(f"CONFIG ERROR: JWT_ALGORITHM must be HS256, HS384, or HS512 (got {self.JWT_ALGORITHM})")
            sys.exit(1)

        if self.ENVIRONMENT == "production":
            fatal_errors: list[str] = []

            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == "your-super-secret-key-change-in-production":
                fatal_errors.append("JWT_SECRET_KEY must be set to a strong, unique value")

            if len(self.JWT_SECRET_KEY) < 32:
                fatal_errors.append("JWT_SECRET_KEY must be at least 32 characters")

            if "user:password" in self.DATABASE_URL:
                fatal_errors.append("DATABASE_URL contains default credentials")

            if any(origin.startswith("http://") for origin in self.CORS_ORIGINS):
                fatal_errors.append("CORS_ORIGINS must use HTTPS in production")

            if self.DATABASE_ECHO_SQL:
                fatal_errors.append("DATABASE_ECHO_SQL must be False in production")

            if self.DEBUG:
                fatal_errors.append("DEBUG must be False in production")

            if not self.FIELD_ENCRYPTION_KEY or len(self.FIELD_ENCRYPTION_KEY) < 32:
                fatal_errors.append("FIELD_ENCRYPTION_KEY must be at least 32 characters in production")

            if fatal_errors:
                for err in fatal_errors:
                    logger.critical(f"CONFIG ERROR: {err}")
                sys.exit(1)

        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()
