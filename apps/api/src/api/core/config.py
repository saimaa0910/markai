import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional

# Load appropriate .env file manually into os.environ if it exists
try:
    env_type = os.environ.get("ENVIRONMENT")
    if env_type == "test":
        files_to_try = [".env.test", ".env"]
    elif env_type == "production":
        files_to_try = [".env.production", ".env"]
    else:
        files_to_try = [".env.local", ".env"]

    dir_to_check = os.path.dirname(os.path.abspath(__file__))
    env_path = None
    
    # Search upwards for the first matching env file
    for filename in files_to_try:
        curr_dir = dir_to_check
        found = False
        for _ in range(6):
            possible_path = os.path.join(curr_dir, filename)
            if os.path.exists(possible_path):
                env_path = possible_path
                found = True
                break
            parent = os.path.dirname(curr_dir)
            if parent == curr_dir:
                break
            curr_dir = parent
        if found:
            break

    if env_path:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip("'\"")
                    # Set in environ if not already set externally
                    os.environ.setdefault(key.strip(), val)
except Exception:
    pass



class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise AI Marketing Operating System (EAIMOS)"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/eaimos",
        validation_alias="DATABASE_URL",
    )

    # Optional explicit async DSN (P2-9). When omitted, DATABASE_URL is derived
    # by swapping the driver to asyncpg.
    ASYNC_DATABASE_URL: Optional[str] = Field(
        default=None, validation_alias="ASYNC_DATABASE_URL"
    )

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", validation_alias="REDIS_URL"
    )

    # JWT Secrets
    SECRET_KEY: str = Field(
        validation_alias="SECRET_KEY",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Dedicated Fernet master key for encrypting stored provider secrets.
    # MUST be a separate secret from SECRET_KEY.
    ENCRYPTION_KEY: str = Field(default="", validation_alias="ENCRYPTION_KEY")

    # MinIO / S3 configuration
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "eaimos-storage"

    # Email configuration — Resend (primary) + SMTP (dev fallback)
    RESEND_API_KEY: str = Field(default="", validation_alias="RESEND_API_KEY")
    EMAIL_FROM: str = Field(default="noreply@eaimos.ai", validation_alias="EMAIL_FROM")
    EMAIL_FROM_NAME: str = Field(default="EAIMOS Platform", validation_alias="EMAIL_FROM_NAME")
    # Legacy SMTP fields kept for dev fallback (not used when RESEND_API_KEY is set)
    SMTP_HOST: str = Field(default="", validation_alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, validation_alias="SMTP_PORT")
    SMTP_USER: str = Field(default="", validation_alias="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", validation_alias="SMTP_PASSWORD")
    SMTP_TIMEOUT: int = Field(default=30, validation_alias="SMTP_TIMEOUT")
    ALERT_EMAIL_RECIPIENT: str = Field(default="alerts@eaimos.ai", validation_alias="ALERT_EMAIL_RECIPIENT")

    # Frontend URL (used in email links)
    FRONTEND_URL: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")

    # MFA settings
    MFA_ISSUER: str = Field(default="EAIMOS", validation_alias="MFA_ISSUER")
    MFA_RECOVERY_CODE_COUNT: int = 10

    # Rate limiting
    RATE_LIMIT_LOGIN: str = Field(default="5/minute", validation_alias="RATE_LIMIT_LOGIN")
    RATE_LIMIT_REGISTER: str = Field(default="3/minute", validation_alias="RATE_LIMIT_REGISTER")
    RATE_LIMIT_FORGOT_PASSWORD: str = Field(default="3/minute", validation_alias="RATE_LIMIT_FORGOT_PASSWORD")

    # Account lockout
    MAX_FAILED_LOGIN_ATTEMPTS: int = Field(default=5, validation_alias="MAX_FAILED_LOGIN_ATTEMPTS")
    LOCKOUT_DURATION_MINUTES: int = Field(default=30, validation_alias="LOCKOUT_DURATION_MINUTES")

    # External integrations
    SLACK_BOT_TOKEN: str = Field(default="", validation_alias="SLACK_BOT_TOKEN")
    GOOGLE_CLIENT_ID: str = Field(default="", validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", validation_alias="GOOGLE_CLIENT_SECRET")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
