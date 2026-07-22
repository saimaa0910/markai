"""
EAIMOS Dependency Injection Provider & Container
================================================
Central service locator / DI container supplying singletons and factory instances for Repositories,
UnitOfWork, Cache Managers, Authorization Services, and Event Dispatchers across all 15 sprints.
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar
from api.repositories.base import BaseRepository
from api.repositories.unit_of_work import UnitOfWork
from api.services.base.authorization import AuthorizationService
from api.services.base.cache import ICacheManager, RedisCacheManager
from api.services.base.event_dispatcher import EventDispatcher
from api.services.base.unit_of_work_service import UnitOfWorkService

R = TypeVar("R", bound=BaseRepository)


class ServiceContainer:
    """
    Central Dependency Injection container managing singleton and request-scoped services.
    """

    def __init__(self) -> None:
        self._cache_manager: Optional[ICacheManager] = None
        self._auth_service: Optional[AuthorizationService] = None
        self._event_dispatcher: Optional[EventDispatcher] = None
        self._custom_providers: Dict[str, Any] = {}

    @property
    def cache(self) -> ICacheManager:
        """Lazy-loaded or configured Cache Manager singleton."""
        if self._cache_manager is None:
            self._cache_manager = RedisCacheManager()
        return self._cache_manager

    def set_cache_manager(self, cache_manager: ICacheManager) -> None:
        """Override Cache Manager instance."""
        self._cache_manager = cache_manager

    @property
    def authorizer(self) -> AuthorizationService:
        """Lazy-loaded Authorization Service singleton."""
        if self._auth_service is None:
            self._auth_service = AuthorizationService()
        return self._auth_service

    def set_authorizer(self, auth_service: AuthorizationService) -> None:
        """Override Authorization Service instance."""
        self._auth_service = auth_service

    @property
    def dispatcher(self) -> EventDispatcher:
        """Lazy-loaded Event Dispatcher singleton."""
        if self._event_dispatcher is None:
            self._event_dispatcher = EventDispatcher()
        return self._event_dispatcher

    def set_dispatcher(self, dispatcher: EventDispatcher) -> None:
        """Override Event Dispatcher instance."""
        self._event_dispatcher = dispatcher

    def create_uow_service(self, session: Optional[Any] = None) -> UnitOfWorkService:
        """Factory method to construct a fresh UnitOfWorkService instance."""
        uow = UnitOfWork(session=session)
        return UnitOfWorkService(uow=uow, dispatcher=self.dispatcher)

    def get_repository(self, repo_cls: Type[R], session: Optional[Any] = None) -> R:
        """Instantiate a repository using session or fresh UoW session."""
        return repo_cls(session=session)

    def register(self, key: str, provider: Any) -> None:
        """Register a custom dependency instance or factory."""
        self._custom_providers[key] = provider

    def resolve(self, key: str) -> Any:
        """Resolve a custom registered dependency."""
        if key not in self._custom_providers:
            raise KeyError(f"Dependency '{key}' has not been registered in ServiceContainer.")
        provider = self._custom_providers[key]
        if callable(provider):
            return provider()
        return provider


# Global default DI container instance
container = ServiceContainer()
