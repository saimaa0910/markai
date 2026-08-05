"""
Auth Domain Abstract Interfaces.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class IAuthRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        pass


class IAuthService(ABC):
    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        pass
