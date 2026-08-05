"""
Module-level configuration settings adapter.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """
    Enterprise App Configuration Settings.
    """
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "eaimos_super_secret_key_change_in_production"
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AppSettings()
