"""
EAIMOS Unit of Work Service Module
===================================
Integrates database transaction management with domain event collection & dispatching.
Ensures ACID guarantees and postpones event publication until database commit succeeds.
"""

from functools import wraps
import inspect
from typing import Any, Callable, List, Optional, Type, TypeVar
from api.repositories.base import BaseRepository
from api.repositories.unit_of_work import UnitOfWork
from api.services.base.event_dispatcher import EventDispatcher
from api.services.base.events import DomainEvent

T = TypeVar("T")


class UnitOfWorkService:
    """
    Service Layer UnitOfWork coordinator wrapping lower-level DB UnitOfWork with domain event buffers.
    Events added during a transactional block are held until commit() succeeds.
    """

    def __init__(
        self,
        uow: Optional[UnitOfWork] = None,
        dispatcher: Optional[EventDispatcher] = None,
    ) -> None:
        self.uow = uow or UnitOfWork()
        self.dispatcher = dispatcher or EventDispatcher()
        self._pending_events: List[DomainEvent] = []

    async def __aenter__(self) -> "UnitOfWorkService":
        await self.uow.__aenter__()
        self._pending_events = []
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self._pending_events.clear()
            await self.uow.__aexit__(exc_type, exc_val, exc_tb)
        else:
            await self.uow.__aexit__(None, None, None)
            # Dispatch events only after database commit succeeds
            if self._pending_events and self.dispatcher:
                events_to_dispatch = list(self._pending_events)
                self._pending_events.clear()
                await self.dispatcher.publish_many(events_to_dispatch)

    def add_event(self, event: DomainEvent) -> None:
        """Buffer a domain event to be published upon successful transaction commit."""
        self._pending_events.append(event)

    def get_repository(self, repo_cls: Type[BaseRepository]) -> Any:
        """Instantiate a repository class for database interaction."""
        try:
            return repo_cls()
        except TypeError:
            return repo_cls(self.session)

    @property
    def session(self) -> Any:
        """Return active database session."""
        return self.uow.session


def transactional(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator wrapping async service methods with automated UnitOfWorkService transaction boundaries.
    """
    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Check if service has a uow_factory or uow attribute
        uow_service = getattr(self, "uow_service", None)
        if uow_service and isinstance(uow_service, UnitOfWorkService):
            async with uow_service:
                return await func(self, *args, **kwargs)
        
        # Fallback to direct call if no UoW configured
        return await func(self, *args, **kwargs)

    return wrapper
