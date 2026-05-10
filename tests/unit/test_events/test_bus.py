"""Tests for galaxy.events.bus (EventBus)."""

import asyncio

import pytest

from galaxy.events import Event
from galaxy.events.bus import EventBus


@pytest.fixture
def bus() -> EventBus:
    """Create a fresh EventBus for each test."""
    return EventBus(history_size=100)


class TestPublishSubscribe:
    """Test basic pub/sub functionality."""

    @pytest.mark.asyncio
    async def test_publish_subscribe(self, bus: EventBus) -> None:
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("test.event", handler)
        await bus.publish(Event(type="test.event", payload={"msg": "hello"}))

        assert len(received) == 1
        assert received[0].payload["msg"] == "hello"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus: EventBus) -> None:
        count = {"a": 0, "b": 0}

        async def handler_a(event: Event) -> None:
            count["a"] += 1

        async def handler_b(event: Event) -> None:
            count["b"] += 1

        bus.subscribe("test.event", handler_a)
        bus.subscribe("test.event", handler_b)
        await bus.publish(Event(type="test.event"))

        assert count["a"] == 1
        assert count["b"] == 1

    @pytest.mark.asyncio
    async def test_no_cross_topic_delivery(self, bus: EventBus) -> None:
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("topic.a", handler)
        await bus.publish(Event(type="topic.b"))

        assert len(received) == 0


class TestUnsubscribe:
    """Test unsubscribe functionality."""

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus: EventBus) -> None:
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("test.event", handler)
        await bus.publish(Event(type="test.event"))
        assert len(received) == 1

        result = bus.unsubscribe("test.event", handler)
        assert result is True

        await bus.publish(Event(type="test.event"))
        assert len(received) == 1  # still 1, handler removed

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, bus: EventBus) -> None:
        async def handler(event: Event) -> None:
            pass

        result = bus.unsubscribe("no.topic", handler)
        assert result is False


class TestTopicFiltering:
    """Test wildcard topic matching."""

    @pytest.mark.asyncio
    async def test_wildcard_match(self, bus: EventBus) -> None:
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("task.*", handler)
        await bus.publish(Event(type="task.completed"))
        await bus.publish(Event(type="task.failed"))
        await bus.publish(Event(type="agent.spawned"))  # should NOT match

        assert len(received) == 2
        assert received[0].type == "task.completed"
        assert received[1].type == "task.failed"

    @pytest.mark.asyncio
    async def test_catch_all_wildcard(self, bus: EventBus) -> None:
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("*", handler)
        await bus.publish(Event(type="anything"))
        await bus.publish(Event(type="whatever.topic"))

        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_nested_wildcard(self, bus: EventBus) -> None:
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("agent.task.*", handler)
        await bus.publish(Event(type="agent.task.completed"))
        await bus.publish(Event(type="agent.spawned"))  # should NOT match

        assert len(received) == 1


class TestRequestReply:
    """Test request/reply pattern."""

    @pytest.mark.asyncio
    async def test_request_reply(self, bus: EventBus) -> None:
        async def responder(event: Event) -> None:
            response = Event(
                type="response.topic",
                payload={"answer": event.payload.get("question", "") + " replied"},
            )
            await bus.publish(response)

        bus.subscribe("request.topic", responder)

        response = await bus.request(
            Event(type="request.topic", payload={"question": "hello"}),
            response_topic="response.topic",
            timeout=5.0,
        )

        assert response.type == "response.topic"
        assert response.payload["answer"] == "hello replied"

    @pytest.mark.asyncio
    async def test_request_timeout(self, bus: EventBus) -> None:
        with pytest.raises(asyncio.TimeoutError):
            await bus.request(
                Event(type="no.responder"),
                response_topic="no.response",
                timeout=0.1,
            )


class TestHistory:
    """Test event history tracking."""

    @pytest.mark.asyncio
    async def test_history_records_events(self, bus: EventBus) -> None:
        await bus.publish(Event(type="event.1"))
        await bus.publish(Event(type="event.2"))
        await bus.publish(Event(type="event.3"))

        history = bus.get_history()
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_history_filter(self, bus: EventBus) -> None:
        await bus.publish(Event(type="task.completed"))
        await bus.publish(Event(type="task.failed"))
        await bus.publish(Event(type="agent.spawned"))

        task_events = bus.get_history(topic_filter="task.*")
        assert len(task_events) == 2

    @pytest.mark.asyncio
    async def test_history_limit(self, bus: EventBus) -> None:
        for i in range(50):
            await bus.publish(Event(type=f"event.{i}"))

        history = bus.get_history(limit=5)
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_history_max_size(self) -> None:
        bus = EventBus(history_size=5)
        for i in range(10):
            await bus.publish(Event(type=f"event.{i}"))

        history = bus.get_history()
        assert len(history) == 5

    def test_clear_history(self, bus: EventBus) -> None:
        bus.clear_history()
        assert bus.get_history() == []


class TestSubscriberCount:
    """Test subscriber counting."""

    def test_count_empty(self, bus: EventBus) -> None:
        assert bus.subscriber_count() == 0

    def test_count_by_topic(self, bus: EventBus) -> None:
        async def h1(e: Event) -> None: pass
        async def h2(e: Event) -> None: pass

        bus.subscribe("topic.a", h1)
        bus.subscribe("topic.a", h2)
        bus.subscribe("topic.b", h1)

        assert bus.subscriber_count("topic.a") == 2
        assert bus.subscriber_count("topic.b") == 1
        assert bus.subscriber_count() == 3


class TestBusLifecycle:
    """Test start/stop behavior."""

    @pytest.mark.asyncio
    async def test_stopped_bus_drops_events(self, bus: EventBus) -> None:
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("test", handler)
        await bus.stop()
        await bus.publish(Event(type="test"))

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_restart_bus(self, bus: EventBus) -> None:
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("test", handler)
        await bus.stop()
        await bus.start()
        await bus.publish(Event(type="test"))

        assert len(received) == 1


class TestErrorHandling:
    """Test that handler errors don't crash the bus."""

    @pytest.mark.asyncio
    async def test_handler_error_doesnt_crash(self, bus: EventBus) -> None:
        results: list[str] = []

        async def bad_handler(event: Event) -> None:
            raise RuntimeError("I broke!")

        async def good_handler(event: Event) -> None:
            results.append("ok")

        bus.subscribe("test", bad_handler)
        bus.subscribe("test", good_handler)

        # Should not raise — error is logged and isolated
        await bus.publish(Event(type="test"))
        assert results == ["ok"]
