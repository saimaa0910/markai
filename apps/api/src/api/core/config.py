from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise AI Marketing Operating System (EAIMOS)"
    API_V1_STR: str = "/api/v1"

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

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
