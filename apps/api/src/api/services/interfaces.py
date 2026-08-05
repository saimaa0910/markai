"""
Service Layer Interfaces.
"""

from abc import ABC, abstractmethod


class IBaseService(ABC):
    @abstractmethod
    async def execute(self) -> None:
        pass
