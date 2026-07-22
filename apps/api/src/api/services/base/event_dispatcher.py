"""
EAIMOS Event Dispatcher Module
==============================
Provides high-performance asynchronous event publishing, handler subscription,
exponential backoff retries, and Dead Letter Queue (DLQ) isolation for failure resilience.
"""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Sequence, Type, Union

from api.services.base.events import DomainEvent

logger = logging.getLogger("eaimos.event_dispatcher")

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventDispatcher:
    """
    In-memory async domain event bus supporting retries, subscribers, and dead letter queueing.
    Can be hooked into external message brokers (RabbitMQ / Kafka) as an event adapter.
    """

    def __init__(self, max_retries: int = 3, initial_backoff_sec: float = 0.1) -> None:
        self.max_retries = max_retries
        self.initial_backoff_sec = initial_backoff_sec
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._dlq: List[Dict[str, Any]] = []
        self._published_history: List[DomainEvent] = []

    def subscribe(
        self,
        event_type_or_cls: Union[str, Type[DomainEvent]],
        handler: EventHandler,
    ) -> None:
        """Subscribe an async handler function to an event type string or DomainEvent subclass."""
        if isinstance(event_type_or_cls, type) and issubclass(event_type_or_cls, DomainEvent):
            key = event_type_or_cls.__name__
        else:
            key = str(event_type_or_cls)

        if key not in self._handlers:
            self._handlers[key] = []
        if handler not in self._handlers[key]:
            self._handlers[key].append(handler)

    async def _execute_handler_with_retry(self, handler: EventHandler, event: DomainEvent) -> None:
        """Execute handler with exponential backoff retries."""
        attempt = 0
        backoff = self.initial_backoff_sec
        last_exception: Optional[Exception] = None

        while attempt <= self.max_retries:
            try:
                await handler(event)
                return
            except Exception as exc:
                attempt += 1
                last_exception = exc
                logger.warning(
                    f"Handler {handler.__name__} failed on event {event.event_type} "
                    f"(attempt {attempt}/{self.max_retries + 1}): {exc}"
                )
                if attempt <= self.max_retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

        # Send to Dead Letter Queue (DLQ) after retries exhausted
        self._dlq.append(
            {
                "event": event.model_dump() if hasattr(event, "model_dump") else event.__dict__,
                "handler": getattr(handler, "__name__", str(handler)),
                "exception": str(last_exception),
                "attempts": attempt,
            }
        )
        logger.error(f"Event {event.event_id} added to Dead Letter Queue after max retries.")

    async def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event asynchronously to all registered handlers."""
        self._published_history.append(event)
        target_keys = [event.event_type, event.__class__.__name__, "*"]
        handlers_to_call: List[EventHandler] = []

        for key in target_keys:
            if key in self._handlers:
                handlers_to_call.extend(self._handlers[key])

        if not handlers_to_call:
            return

        tasks = [
            self._execute_handler_with_retry(handler, event)
            for handler in set(handlers_to_call)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def publish_many(self, events: Sequence[DomainEvent]) -> None:
        """Publish multiple domain events in sequence."""
        for event in events:
            await self.publish(event)

    def get_dlq(self) -> List[Dict[str, Any]]:
        """Retrieve collected dead-letter queue records."""
        return list(self._dlq)

    def clear_dlq(self) -> None:
        """Purge dead-letter queue records."""
        self._dlq.clear()

    def get_history(self) -> List[DomainEvent]:
        """Retrieve published event history."""
        return list(self._published_history)
