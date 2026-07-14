import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

# Load root .env file manually into os.environ if it exists
try:
    dir_to_check = os.path.dirname(os.path.abspath(__file__))
    env_path = None
    for _ in range(6):
        possible_path = os.path.join(dir_to_check, ".env")
        if os.path.exists(possible_path):
            env_path = possible_path
            break
        parent = os.path.dirname(dir_to_check)
        if parent == dir_to_check:
            break
        dir_to_check = parent

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

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", validation_alias="REDIS_URL"
    )

    # JWT Secrets
    SECRET_KEY: str = Field(
        default="SUPER_SECRET_JWT_KEY_MIN_32_CHARS_LONG_PLEASE_REPLACE_IN_PRODUCTION",
        validation_alias="SECRET_KEY",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # MinIO / S3 configuration
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "eaimos-storage"

    # Email configuration (SMTP)
    SMTP_HOST: str = Field(default="smtp.sendgrid.net", validation_alias="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, validation_alias="SMTP_PORT")
    SMTP_USER: str = Field(default="apikey", validation_alias="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", validation_alias="SMTP_PASSWORD")
    EMAIL_FROM: str = Field(default="noreply@viptant.ai", validation_alias="EMAIL_FROM")

    # External integrations
    SLACK_BOT_TOKEN: str = Field(default="", validation_alias="SLACK_BOT_TOKEN")
    GOOGLE_CLIENT_ID: str = Field(default="", validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", validation_alias="GOOGLE_CLIENT_SECRET")

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
