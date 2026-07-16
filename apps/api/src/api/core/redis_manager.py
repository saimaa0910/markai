import logging
import os
import time
from typing import Any, Dict, Optional
import redis
from redis.sentinel import Sentinel
from redis.cluster import RedisCluster
from api.core.config import settings

logger = logging.getLogger("api.core.redis_manager")

class RedisConnectionManager:
    _instance: Optional["RedisConnectionManager"] = None
    
    def __new__(cls, *args: Any, **kwargs: Any) -> "RedisConnectionManager":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.redis_url = settings.REDIS_URL
        self.redis_client: Optional[Any] = None
        self.is_cluster = False
        self.is_sentinel = False
        self.pool: Optional[redis.ConnectionPool] = None
        
        # Stats tracking
        self.connects_count = 0
        self.errors_count = 0
        
        self.connect()
        self._initialized = True

    def connect(self) -> None:
        """Initialize connection to Redis (supporting Standard, Sentinel, or Cluster)."""
        try:
            # 1. Check Sentinel Configuration
            sentinel_hosts = os.getenv("REDIS_SENTINEL_HOSTS")
            sentinel_master = os.getenv("REDIS_SENTINEL_MASTER", "mymaster")
            
            if sentinel_hosts:
                self.is_sentinel = True
                logger.info("Initializing Redis Sentinel connection manager")
                hosts = []
                for h in sentinel_hosts.split(","):
                    parts = h.split(":")
                    hosts.append((parts[0], int(parts[1])))
                
                sentinel = Sentinel(
                    hosts,
                    socket_timeout=float(os.getenv("REDIS_TIMEOUT", "2.0")),
                    sentinel_kwargs={"ssl": self.redis_url.startswith("rediss://")},
                )
                self.redis_client = sentinel.master_for(sentinel_master, decode_responses=True)
                self.connects_count += 1
                return
            
            # 2. Check Cluster Configuration
            cluster_nodes = os.getenv("REDIS_CLUSTER_NODES")
            if cluster_nodes:
                self.is_cluster = True
                logger.info("Initializing Redis Cluster connection manager")
                startup_nodes = []
                for node in cluster_nodes.split(","):
                    parts = node.split(":")
                    startup_nodes.append({"host": parts[0], "port": int(parts[1])})
                
                self.redis_client = RedisCluster(
                    startup_nodes=startup_nodes,
                    decode_responses=True,
                    ssl=self.redis_url.startswith("rediss://"),
                )
                self.connects_count += 1
                return

            # 3. Standard Connection (with pool)
            logger.info(f"Initializing standard Redis connection pool: {self.redis_url}")
            
            # Use connection pool for auto reconnection and pooling
            self.pool = redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
                socket_timeout=float(os.getenv("REDIS_TIMEOUT", "2.0")),
                retry_on_timeout=True,
            )
            self.redis_client = redis.Redis(connection_pool=self.pool)
            self.connects_count += 1
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)

    def get_client(self) -> Any:
        """Get active Redis client instance."""
        if self.redis_client is None:
            self.connect()
        return self.redis_client

    def get_metrics(self) -> Dict[str, Any]:
        """Perform ping to calculate latency and retrieve client connection statistics."""
        client = self.get_client()
        metrics = {
            "status": "disconnected",
            "latency_ms": 0.0,
            "connected_clients": 0,
            "used_memory_human": "0B",
            "cluster_enabled": self.is_cluster,
            "sentinel_enabled": self.is_sentinel,
            "connects_count": self.connects_count,
            "errors_count": self.errors_count,
        }
        
        try:
            start_time = time.time()
            client.ping()
            metrics["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            metrics["status"] = "connected"
            
            # Get info from server
            info = client.info()
            metrics["connected_clients"] = info.get("connected_clients", 0)
            metrics["used_memory_human"] = info.get("used_memory_human", "N/A")
        except Exception as e:
            self.errors_count += 1
            logger.warning(f"Redis ping or info command failed: {e}")
            metrics["status"] = "error"
            metrics["error_msg"] = str(e)
            
        return metrics

    def disconnect(self) -> None:
        """Gracefully close all connections in pool."""
        logger.info("Closing Redis connection manager")
        if self.pool:
            try:
                self.pool.disconnect()
            except Exception:
                pass
        if self.redis_client:
            try:
                self.redis_client.close()
            except Exception:
                pass
