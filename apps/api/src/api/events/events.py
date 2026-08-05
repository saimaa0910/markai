"""
Domain Event Publisher & Listener Subsystem.
"""

from typing import Dict, Any, Callable, List
from pydantic import BaseModel


class DomainEvent(BaseModel):
    """
    Base class for domain events.
    """
    event_id: str
    event_type: str
    payload: Dict[str, Any]


class EventBus:
    """
    In-memory or Distributed Event Bus Publisher.
    """
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable[[DomainEvent], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        """
        Subscribe a handler to an event type.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribed handlers.
        """
        # TODO: Dispatch to handlers or publish to Redis Pub/Sub topic
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)


event_bus = EventBus()
