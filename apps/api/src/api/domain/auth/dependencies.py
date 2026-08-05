"""
Auth Domain Dependency Injection Providers.
"""

from typing import Generator
from fastapi import Depends


def get_auth_service() -> Generator[None, None, None]:
    """
    FastAPI dependency injection provider for AuthService.
    """
    # TODO: Yield instantiated AuthService
    yield None
