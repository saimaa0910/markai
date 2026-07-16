import json
import logging
from typing import Any, Dict, Optional
from api.core.redis_manager import RedisConnectionManager

logger = logging.getLogger("api.services.queue_service")

class QueueService:
    _instance: Optional["QueueService"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "QueueService":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        
        self.redis_manager = RedisConnectionManager()
        self.processed_counts: Dict[str, int] = {}
        
        self._initialized = True

    def _get_queue_key(self, queue_name: str, priority: bool = False) -> str:
        suffix = "priority" if priority else "fifo"
        return f"eaimos:queue:{queue_name}:{suffix}"

    def enqueue(self, queue_name: str, payload: Any, priority: int = 0) -> bool:
        """Enqueue payload into a FIFO or Priority queue."""
        client = self.redis_manager.get_client()
        try:
            serialized = json.dumps(payload)
            if priority > 0:
                # Use Sorted Set for priority queue (score is -priority so higher priority pops first in ZPOPMIN)
                key = self._get_queue_key(queue_name, priority=True)
                client.zadd(key, {serialized: -priority})
            else:
                # Use List for FIFO queue
                key = self._get_queue_key(queue_name, priority=False)
                client.rpush(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue into {queue_name}: {e}")
            return False

    def dequeue(self, queue_name: str) -> Optional[Any]:
        """Dequeue payload (priority queue gets popped first, then FIFO queue)."""
        client = self.redis_manager.get_client()
        
        # 1. Try to pop from Priority Queue
        priority_key = self._get_queue_key(queue_name, priority=True)
        try:
            items = client.zpopmin(priority_key, count=1)
            if items:
                serialized, score = items[0]
                self.processed_counts[queue_name] = self.processed_counts.get(queue_name, 0) + 1
                return json.loads(serialized)
        except Exception as e:
            logger.error(f"Failed to dequeue priority from {queue_name}: {e}")

        # 2. Try to pop from FIFO List
        fifo_key = self._get_queue_key(queue_name, priority=False)
        try:
            val = client.lpop(fifo_key)
            if val:
                self.processed_counts[queue_name] = self.processed_counts.get(queue_name, 0) + 1
                return json.loads(val)
        except Exception as e:
            logger.error(f"Failed to dequeue FIFO from {queue_name}: {e}")

        return None

    def get_size(self, queue_name: str) -> int:
        """Get the total size of a queue (Priority size + FIFO size)."""
        client = self.redis_manager.get_client()
        total_size = 0
        try:
            priority_key = self._get_queue_key(queue_name, priority=True)
            total_size += client.zcard(priority_key)
        except Exception:
            pass

        try:
            fifo_key = self._get_queue_key(queue_name, priority=False)
            total_size += client.llen(fifo_key)
        except Exception:
            pass

        return total_size

    def clear(self, queue_name: str) -> bool:
        """Clear all messages from a queue."""
        client = self.redis_manager.get_client()
        try:
            client.delete(
                self._get_queue_key(queue_name, priority=True),
                self._get_queue_key(queue_name, priority=False)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue {queue_name}: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Aggregate queue statistics and processed counts."""
        queues = [
            "ai_requests", "streaming", "notifications", "analytics", 
            "cost", "usage", "model_sync", "provider_sync", 
            "retry_queue", "dead_letter"
        ]
        
        metrics = {}
        total_size = 0
        
        for q in queues:
            size = self.get_size(q)
            total_size += size
            metrics[q] = {
                "size": size,
                "processed_count": self.processed_counts.get(q, 0),
            }
            
        metrics["total_size"] = total_size
        return metrics
