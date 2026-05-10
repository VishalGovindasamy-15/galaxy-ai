"""Tests for galaxy.events.events (Event data model)."""

from datetime import datetime, timezone

from galaxy.events import (
    AGENT_SPAWNED,
    GALAXY_BOOTED,
    GALAXY_BOOTING,
    TASK_COMPLETED,
    Event,
)


class TestEventCreation:
    """Test Event dataclass creation."""

    def test_basic_event(self) -> None:
        event = Event(type="test.event")
        assert event.type == "test.event"
        assert event.payload == {}
        assert event.source == ""
        assert event.event_id  # auto-generated
        assert event.timestamp  # auto-generated

    def test_event_with_payload(self) -> None:
        event = Event(type="task.done", payload={"file": "main.py", "lines": 42})
        assert event.payload["file"] == "main.py"
        assert event.payload["lines"] == 42

    def test_event_with_source(self) -> None:
        event = Event(type="agent.spawned", source="orchestrator")
        assert event.source == "orchestrator"

    def test_unique_ids(self) -> None:
        e1 = Event(type="test")
        e2 = Event(type="test")
        assert e1.event_id != e2.event_id

    def test_timestamp_is_utc(self) -> None:
        event = Event(type="test")
        assert event.timestamp.tzinfo == timezone.utc

    def test_event_is_frozen(self) -> None:
        event = Event(type="test")
        try:
            event.type = "changed"  # type: ignore[misc]
            assert False, "Should have raised"
        except AttributeError:
            pass  # Expected — frozen dataclass


class TestEventSerialization:
    """Test Event to_dict / from_dict."""

    def test_to_dict(self) -> None:
        event = Event(type="test.event", payload={"key": "value"}, source="kernel")
        data = event.to_dict()
        assert data["type"] == "test.event"
        assert data["payload"] == {"key": "value"}
        assert data["source"] == "kernel"
        assert "event_id" in data
        assert "timestamp" in data

    def test_from_dict(self) -> None:
        data = {
            "type": "task.completed",
            "payload": {"file": "main.py"},
            "source": "worker_01",
            "event_id": "abc123",
            "timestamp": "2025-01-01T00:00:00+00:00",
        }
        event = Event.from_dict(data)
        assert event.type == "task.completed"
        assert event.payload["file"] == "main.py"
        assert event.source == "worker_01"
        assert event.event_id == "abc123"

    def test_roundtrip(self) -> None:
        original = Event(
            type="agent.task.completed",
            payload={"status": "success", "lines": 150},
            source="worker_03",
        )
        data = original.to_dict()
        restored = Event.from_dict(data)
        assert restored.type == original.type
        assert restored.payload == original.payload
        assert restored.source == original.source
        assert restored.event_id == original.event_id

    def test_from_dict_minimal(self) -> None:
        data = {"type": "minimal.event"}
        event = Event.from_dict(data)
        assert event.type == "minimal.event"
        assert event.payload == {}


class TestEventTypeConstants:
    """Test that event type constants are properly defined."""

    def test_galaxy_events(self) -> None:
        assert GALAXY_BOOTING == "galaxy.booting"
        assert GALAXY_BOOTED == "galaxy.booted"

    def test_agent_events(self) -> None:
        assert AGENT_SPAWNED == "agent.spawned"

    def test_task_events(self) -> None:
        assert TASK_COMPLETED == "task.completed"
