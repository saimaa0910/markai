import json
import logging
import random
import time
import zlib
from typing import Any, Dict, Optional
from contextlib import contextmanager
from api.core.redis_manager import RedisConnectionManager

logger = logging.getLogger("api.services.cache_service")

class CacheService:
    _instance: Optional["CacheService"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "CacheService":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.redis_manager = RedisConnectionManager()
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # In-memory metrics counter
        self.hits_count = 0
        self.misses_count = 0
        self.evictions_count = 0
        
        self._initialized = True

    def _get_key(self, namespace: str, org_id: Optional[str], key: str) -> str:
        """Create namespace & organization isolated cache key."""
        org_prefix = f"org:{org_id}" if org_id else "global"
        return f"eaimos:cache:{org_prefix}:{namespace}:{key}"

    def get(self, namespace: str, key: str, org_id: Optional[str] = None) -> Optional[Any]:
        """Fetch item from cache. Automates json parsing and decompression."""
        cache_key = self._get_key(namespace, org_id, key)
        
        try:
            client = self.redis_manager.get_client()
            val = client.get(cache_key)
            if val is None:
                # Check memory fallback
                mem_item = self._memory_cache.get(cache_key)
                if mem_item and mem_item.get("expires_at", float("inf")) > time.time():
                    self.hits_count += 1
                    return mem_item.get("value")
                self.misses_count += 1
                return None
            
            self.hits_count += 1
            
            # Check if value is compressed (binary format or starts with zlib compression header)
            if isinstance(val, bytes) or (isinstance(val, str) and val.startswith("zlib:")):
                compressed_bytes = val
                if isinstance(val, str):
                    compressed_bytes = bytes.fromhex(val[5:])
                decompressed = zlib.decompress(compressed_bytes).decode("utf-8")
                return json.loads(decompressed)
            
            return json.loads(val)
        except Exception as e:
            # Memory fallback on Redis error
            mem_item = self._memory_cache.get(cache_key)
            if mem_item and mem_item.get("expires_at", float("inf")) > time.time():
                self.hits_count += 1
                return mem_item.get("value")
            logger.debug(f"Cache get error for {cache_key}: {e}")
            return None

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        org_id: Optional[str] = None,
        ttl: Optional[int] = 3600,
        compress: bool = False,
        jitter: bool = True,
    ) -> bool:
        """Save item to cache with jittered TTL to prevent cache stampedes."""
        cache_key = self._get_key(namespace, org_id, key)
        
        # Apply jitter (random offset +- 10%) to prevent synchronized expiry stampedes
        effective_ttl = ttl
        if ttl and jitter:
            jitter_offset = random.randint(-int(ttl * 0.1), int(ttl * 0.1))
            effective_ttl = max(1, ttl + jitter_offset)

        try:
            serialized = json.dumps(value)
            
            if compress:
                compressed = zlib.compress(serialized.encode("utf-8"))
                serialized = "zlib:" + compressed.hex()
                
            client = self.redis_manager.get_client()
            if effective_ttl:
                client.setex(cache_key, effective_ttl, serialized)
            else:
                client.set(cache_key, serialized)
                
            # Store in local memory cache as warm backup
            self._memory_cache[cache_key] = {
                "value": value,
                "expires_at": time.time() + (effective_ttl if effective_ttl else 86400)
            }
            return True
        except Exception as e:
            # Save to memory fallback
            self._memory_cache[cache_key] = {
                "value": value,
                "expires_at": time.time() + (effective_ttl if effective_ttl else 3600)
            }
            logger.debug(f"Cache set fallback to memory for {cache_key}: {e}")
            return True

    @contextmanager
    def with_lock(self, lock_name: str, timeout_seconds: int = 10):
        """Distributed lock context manager with Redis and in-memory fallback."""
        lock_key = f"eaimos:lock:{lock_name}"
        acquired = False
        client = None
        try:
            client = self.redis_manager.get_client()
            acquired = client.set(lock_key, "locked", nx=True, ex=timeout_seconds)
        except Exception:
            acquired = True  # fallback: allow execution

        try:
            yield acquired
        finally:
            if acquired and client:
                try:
                    client.delete(lock_key)
                except Exception:
                    pass

    def delete(self, namespace: str, key: str, org_id: Optional[str] = None) -> bool:
        """Manually invalidate/delete item from cache."""
        client = self.redis_manager.get_client()
        cache_key = self._get_key(namespace, org_id, key)
        self._memory_cache.pop(cache_key, None)
        try:
            res = client.delete(cache_key)
            if res > 0:
                self.evictions_count += 1
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache key {cache_key}: {e}")
            return False

    def clear_namespace(self, namespace: str, org_id: Optional[str] = None) -> int:
        """Invalidate all keys inside a specific namespace (optionally for one organization)."""
        client = self.redis_manager.get_client()
        org_pattern = f"org:{org_id}" if org_id else "*"
        pattern = f"eaimos:cache:{org_pattern}:{namespace}:*"
        
        # Purge matching keys from memory cache
        mem_keys = [k for k in self._memory_cache.keys() if f":{namespace}:" in k]
        for mk in mem_keys:
            self._memory_cache.pop(mk, None)

        try:
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
                self.evictions_count += len(keys)
                return len(keys)
            return len(mem_keys)
        except Exception as e:
            logger.error(f"Failed to clear namespace pattern {pattern}: {e}")
            return len(mem_keys)

    def clear_org(self, org_id: str) -> int:
        """Invalidate all cached items for a specific organization."""
        client = self.redis_manager.get_client()
        pattern = f"eaimos:cache:org:{org_id}:*:*"
        
        mem_keys = [k for k in self._memory_cache.keys() if f":org:{org_id}:" in k]
        for mk in mem_keys:
            self._memory_cache.pop(mk, None)

        try:
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
                self.evictions_count += len(keys)
                return len(keys)
            return len(mem_keys)
        except Exception as e:
            logger.error(f"Failed to clear org cache pattern {pattern}: {e}")
            return len(mem_keys)

    def clear_all(self) -> int:
        """Purge all application cache keys."""
        client = self.redis_manager.get_client()
        pattern = "eaimos:cache:*"
        self._memory_cache.clear()
        try:
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
                self.evictions_count += len(keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear all cache: {e}")
            return 0

    def get_metrics(self) -> Dict[str, Any]:
        """Retrieve cache hit/miss statistics and calculate ratios."""
        total = self.hits_count + self.misses_count
        hit_ratio = round((self.hits_count / total) * 100, 2) if total > 0 else 0.0
        miss_ratio = round((self.misses_count / total) * 100, 2) if total > 0 else 0.0
        
        client = self.redis_manager.get_client()
        keys_count = 0
        try:
            keys_count = len(client.keys("eaimos:cache:*"))
        except Exception:
            pass

        return {
            "hits": self.hits_count,
            "misses": self.misses_count,
            "hit_ratio": hit_ratio,
            "miss_ratio": miss_ratio,
            "evictions": self.evictions_count,
            "cached_keys_count": keys_count,
        }
