"""
Module-level configuration settings adapter.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class AppSettings(BaseSettings):
    """
    Enterprise App Configuration Settings.
    """
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = Field(min_length=32, validation_alias="SECRET_KEY")
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AppSettings()
