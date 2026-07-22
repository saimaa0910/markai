"""
EAIMOS Cache Abstraction & Redis Ready Cache Manager
====================================================
Provides unified async caching abstractions, Redis integration with automatic in-memory fallback,
TTL management, pattern invalidation, and declarative caching decorators.
"""

import asyncio
from datetime import timedelta
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Protocol, Union, runtime_checkable

logger = logging.getLogger("eaimos.cache")


@runtime_checkable
class ICacheManager(Protocol):
    """Abstract interface defining standard async cache operations."""

    async def get(self, key: str) -> Optional[Any]:
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        ...

    async def delete(self, key: str) -> bool:
        ...

    async def delete_pattern(self, pattern: str) -> int:
        ...

    async def exists(self, key: str) -> bool:
        ...

    async def clear(self) -> bool:
        ...


class InMemoryCacheManager:
    """Thread-safe in-memory async cache manager used for tests, local execution, or fallback."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}
        self._expires: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _is_expired(self, key: str) -> bool:
        if key not in self._expires:
            return False
        now = asyncio.get_event_loop().time()
        return now > self._expires[key]

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._store:
                return None
            if self._is_expired(key):
                del self._store[key]
                del self._expires[key]
                return None
            return self._store[key]

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        async with self._lock:
            self._store[key] = value
            if ttl is not None:
                seconds = ttl.total_seconds() if isinstance(ttl, timedelta) else float(ttl)
                self._expires[key] = asyncio.get_event_loop().time() + seconds
            elif key in self._expires:
                del self._expires[key]
            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            removed = key in self._store
            self._store.pop(key, None)
            self._expires.pop(key, None)
            return removed

    async def delete_pattern(self, pattern: str) -> int:
        import fnmatch
        async with self._lock:
            keys_to_delete = [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]
            for k in keys_to_delete:
                self._store.pop(k, None)
                self._expires.pop(k, None)
            return len(keys_to_delete)

    async def exists(self, key: str) -> bool:
        async with self._lock:
            if key not in self._store:
                return False
            if self._is_expired(key):
                del self._store[key]
                del self._expires[key]
                return False
            return True

    async def clear(self) -> bool:
        async with self._lock:
            self._store.clear()
            self._expires.clear()
            return True


class RedisCacheManager:
    """
    Distributed Redis-ready Cache Manager supporting automatic JSON serialization,
    TTL management, pattern invalidation, and seamless in-memory fallback.
    """

    def __init__(self, redis_client: Optional[Any] = None) -> None:
        self.redis = redis_client
        self._fallback = InMemoryCacheManager()

    def _normalize_ttl(self, ttl: Optional[Union[int, timedelta]]) -> Optional[int]:
        if ttl is None:
            return None
        if isinstance(ttl, timedelta):
            return int(ttl.total_seconds())
        return int(ttl)

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return await self._fallback.get(key)
        try:
            res = await self.redis.get(key)
            if res is None:
                return None
            if isinstance(res, (bytes, str)):
                try:
                    return json.loads(res)
                except Exception:
                    return res.decode("utf-8") if isinstance(res, bytes) else res
            return res
        except Exception as exc:
            logger.warning(f"Redis get failed for key {key}, falling back: {exc}")
            return await self._fallback.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        if not self.redis:
            return await self._fallback.set(key, value, ttl)
        try:
            ttl_sec = self._normalize_ttl(ttl)
            serialized = json.dumps(value) if not isinstance(value, (str, int, float, bool)) else value
            if ttl_sec:
                await self.redis.setex(key, ttl_sec, serialized)
            else:
                await self.redis.set(key, serialized)
            return True
        except Exception as exc:
            logger.warning(f"Redis set failed for key {key}, falling back: {exc}")
            return await self._fallback.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        if not self.redis:
            return await self._fallback.delete(key)
        try:
            res = await self.redis.delete(key)
            return bool(res)
        except Exception as exc:
            logger.warning(f"Redis delete failed for key {key}, falling back: {exc}")
            return await self._fallback.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        if not self.redis:
            return await self._fallback.delete_pattern(pattern)
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                count = await self.redis.delete(*keys)
                return int(count)
            return 0
        except Exception as exc:
            logger.warning(f"Redis delete_pattern failed for pattern {pattern}, falling back: {exc}")
            return await self._fallback.delete_pattern(pattern)

    async def exists(self, key: str) -> bool:
        if not self.redis:
            return await self._fallback.exists(key)
        try:
            res = await self.redis.exists(key)
            return bool(res)
        except Exception as exc:
            logger.warning(f"Redis exists failed for key {key}, falling back: {exc}")
            return await self._fallback.exists(key)

    async def clear(self) -> bool:
        if not self.redis:
            return await self._fallback.clear()
        try:
            await self.redis.flushdb()
            return True
        except Exception as exc:
            logger.warning(f"Redis flushdb failed, falling back: {exc}")
            return await self._fallback.clear()
