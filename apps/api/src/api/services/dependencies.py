"""
Service Layer Dependency Injection.
"""

from typing import Generator


def get_base_service() -> Generator[None, None, None]:
    yield None
