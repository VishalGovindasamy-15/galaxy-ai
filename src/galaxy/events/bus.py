"""Galaxy in-memory async event bus.

Provides publish/subscribe messaging between all Galaxy subsystems.
This is the default event bus — no Redis or external dependency required.

Features:
- Async publish/subscribe with topic filtering
- Wildcard subscriptions (e.g. 'agent.*')
- Request/reply pattern for synchronous-style communication
- Event history for replay/debugging
- Thread-safe via asyncio locks
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from galaxy.events import Event

logger = logging.getLogger(__name__)

# Type alias for event handler callbacks
EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """In-memory async event bus for Galaxy subsystem communication.

    Usage:
        bus = EventBus()

        async def on_task_completed(event: Event):
            print(f"Task done: {event.payload}")

        bus.subscribe("task.completed", on_task_completed)
        await bus.publish(Event(type="task.completed", payload={"file": "main.py"}))
    """

    def __init__(self, history_size: int = 1000) -> None:
        """Initialize the event bus.

        Args:
            history_size: Maximum number of events to retain in history.
        """
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []
        self._history_size = history_size
        self._lock = asyncio.Lock()
        self._running = True

    async def publish(self, event: Event) -> None:
        """Publish an event to all matching subscribers.

        Matches exact topic names and wildcard patterns (e.g. 'agent.*').

        Args:
            event: The event to publish.
        """
        if not self._running:
            logger.warning("Event bus is stopped, dropping event: %s", event.type)
            return

        # Store in history
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._history_size:
                self._history = self._history[-self._history_size :]

        # Find matching handlers
        handlers = self._get_matching_handlers(event.type)

        if not handlers:
            logger.debug("No handlers for event: %s", event.type)
            return

        # Execute all handlers concurrently
        tasks = [self._safe_call(handler, event) for handler in handlers]
        await asyncio.gather(*tasks)

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Subscribe a handler to a topic pattern.

        Supports exact matches and glob patterns:
        - 'task.completed' — exact match
        - 'task.*' — matches task.completed, task.failed, etc.
        - '*' — matches everything

        Args:
            topic: Topic pattern to subscribe to.
            handler: Async callback function.
        """
        self._subscribers[topic].append(handler)
        logger.debug("Subscribed handler to topic: %s", topic)

    def unsubscribe(self, topic: str, handler: EventHandler) -> bool:
        """Remove a handler from a topic.

        Args:
            topic: Topic pattern the handler was subscribed to.
            handler: The handler to remove.

        Returns:
            True if the handler was found and removed, False otherwise.
        """
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(handler)
                logger.debug("Unsubscribed handler from topic: %s", topic)
                return True
            except ValueError:
                return False
        return False

    async def request(
        self,
        event: Event,
        response_topic: str,
        timeout: float = 30.0,
    ) -> Event:
        """Publish an event and wait for a response on a specific topic.

        This implements request/reply pattern over the event bus.

        Args:
            event: The request event to publish.
            response_topic: Topic to listen on for the response.
            timeout: Maximum seconds to wait for response.

        Returns:
            The response event.

        Raises:
            asyncio.TimeoutError: If no response within timeout.
        """
        response_future: asyncio.Future[Event] = asyncio.get_event_loop().create_future()

        async def _capture_response(resp_event: Event) -> None:
            if not response_future.done():
                response_future.set_result(resp_event)

        self.subscribe(response_topic, _capture_response)
        try:
            await self.publish(event)
            return await asyncio.wait_for(response_future, timeout=timeout)
        finally:
            self.unsubscribe(response_topic, _capture_response)

    def get_history(
        self,
        topic_filter: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """Get recent events from history.

        Args:
            topic_filter: Optional glob pattern to filter events.
            limit: Maximum number of events to return.

        Returns:
            List of matching events, most recent last.
        """
        if topic_filter:
            filtered = [
                e for e in self._history if fnmatch.fnmatch(e.type, topic_filter)
            ]
        else:
            filtered = list(self._history)
        return filtered[-limit:]

    def subscriber_count(self, topic: str | None = None) -> int:
        """Get the number of subscribers.

        Args:
            topic: If provided, count only subscribers for this exact topic.
                   If None, count all subscribers across all topics.

        Returns:
            Number of subscriber handlers.
        """
        if topic:
            return len(self._subscribers.get(topic, []))
        return sum(len(handlers) for handlers in self._subscribers.values())

    async def stop(self) -> None:
        """Stop the event bus. No more events will be processed."""
        self._running = False
        logger.info("Event bus stopped")

    async def start(self) -> None:
        """Start (or restart) the event bus."""
        self._running = True
        logger.info("Event bus started")

    def clear_history(self) -> None:
        """Clear the event history."""
        self._history.clear()

    def _get_matching_handlers(self, event_type: str) -> list[EventHandler]:
        """Get all handlers matching an event type (exact + wildcard)."""
        handlers: list[EventHandler] = []
        for pattern, pattern_handlers in self._subscribers.items():
            if fnmatch.fnmatch(event_type, pattern):
                handlers.extend(pattern_handlers)
        return handlers

    @staticmethod
    async def _safe_call(handler: EventHandler, event: Event) -> None:
        """Call a handler with error protection."""
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "Error in event handler %s for event %s",
                handler.__name__,
                event.type,
            )
