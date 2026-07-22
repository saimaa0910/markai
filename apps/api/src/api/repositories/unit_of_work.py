"""
EAIMOS Unit of Work (UoW) Pattern
==================================
Coordinates repository operations within an explicit transaction boundary.
Guarantees transaction integrity (ACID):
- No repository commits directly unless UoW finishes successfully.
- Auto-rollbacks on unhandled exceptions or error conditions.
- Supports nested savepoints and nested transaction blocks.
"""

import inspect
from typing import Any, Callable, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.session import SessionLocal
from api.repositories.base import BaseRepository
from api.repositories.tenant import TenantRepository


class UnitOfWork:
    """
    Async/Sync context manager encapsulating database transactions and repository instantiation.
    """

    def __init__(self, session_factory: Optional[Callable[[], Any]] = None, session: Optional[Any] = None) -> None:
        self.session_factory = session_factory or SessionLocal
        self._external_session = session
        self.session: Optional[Any] = None
        self._is_nested = False

    async def __aenter__(self) -> "UnitOfWork":
        if self._external_session:
            self.session = self._external_session
            self._is_nested = True
        else:
            self.session = self.session_factory()

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            if not self._is_nested:
                await self.commit()

        if not self._is_nested and self.session:
            close_res = self.session.close()
            if inspect.isawaitable(close_res):
                await close_res

    def __enter__(self) -> "UnitOfWork":
        if self._external_session:
            self.session = self._external_session
            self._is_nested = True
        else:
            self.session = self.session_factory()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.session.rollback()
        else:
            if not self._is_nested:
                self.session.commit()

        if not self._is_nested and self.session:
            self.session.close()

    async def commit(self) -> None:
        """Explicit transaction commit."""
        if self.session:
            res = self.session.commit()
            if inspect.isawaitable(res):
                await res

    async def rollback(self) -> None:
        """Explicit transaction rollback."""
        if self.session:
            res = self.session.rollback()
            if inspect.isawaitable(res):
                await res

    async def savepoint(self) -> Any:
        """Create a nested savepoint."""
        if self.session:
            return self.session.begin_nested()
        return None

    def get_repository(self, repo_cls: Type[BaseRepository]) -> Any:
        """Instantiate a repository class sharing the current UoW session."""
        return repo_cls(self.session)
