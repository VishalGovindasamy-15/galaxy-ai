"""MODULE GATE: Core + Events integration test.

This test validates that all Week 1-2 modules work together:
- Kernel boots with default config
- Event bus is functional after boot
- Full boot → subscribe → publish → shutdown lifecycle works
"""

import pytest

from galaxy.core.kernel import GalaxyKernel
from galaxy.core.config import GalaxyConfig, load_config
from galaxy.events import Event, GALAXY_BOOTED
from galaxy.events.bus import EventBus


class TestKernelBootsWithDefaultConfig:
    """Test that kernel boots cleanly with zero config."""

    @pytest.mark.asyncio
    async def test_kernel_boots_with_default_config(self, tmp_path) -> None:
        kernel = GalaxyKernel()
        await kernel.boot(workspace=tmp_path)

        assert kernel.is_booted
        assert kernel.config is not None
        assert kernel.config.models.master.provider == "ollama"
        assert kernel.config.scheduler.mode == "balanced"
        assert (tmp_path / ".galaxy").exists()

        await kernel.shutdown()
        assert not kernel.is_booted


class TestEventBusWorksAfterBoot:
    """Test that events flow correctly through a booted kernel."""

    @pytest.mark.asyncio
    async def test_event_bus_works_after_boot(self, tmp_path) -> None:
        kernel = GalaxyKernel()
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        # Subscribe before boot
        kernel.event_bus.subscribe("custom.test", handler)
        await kernel.boot(workspace=tmp_path)

        # Publish a custom event through the kernel's bus
        await kernel.event_bus.publish(
            Event(type="custom.test", payload={"from": "integration_test"})
        )

        assert len(received) == 1
        assert received[0].payload["from"] == "integration_test"

        await kernel.shutdown()

    @pytest.mark.asyncio
    async def test_bus_captures_boot_events(self, tmp_path) -> None:
        kernel = GalaxyKernel()
        await kernel.boot(workspace=tmp_path)

        # Check history for boot events
        history = kernel.event_bus.get_history(topic_filter="galaxy.*")
        event_types = [e.type for e in history]

        assert "galaxy.booting" in event_types
        assert "galaxy.booted" in event_types

        await kernel.shutdown()


class TestKernelBootAndShutdownLifecycle:
    """Full lifecycle integration test."""

    @pytest.mark.asyncio
    async def test_kernel_boot_and_shutdown_lifecycle(self, tmp_path) -> None:
        lifecycle_events: list[str] = []

        kernel = GalaxyKernel()

        async def on_booting(event: Event) -> None:
            lifecycle_events.append("booting")

        async def on_booted(event: Event) -> None:
            lifecycle_events.append("booted")

        async def on_shutting_down(event: Event) -> None:
            lifecycle_events.append("shutting_down")

        kernel.event_bus.subscribe("galaxy.booting", on_booting)
        kernel.event_bus.subscribe("galaxy.booted", on_booted)
        kernel.event_bus.subscribe("galaxy.shutting_down", on_shutting_down)

        # Boot
        await kernel.boot(workspace=tmp_path)
        assert "booting" in lifecycle_events
        assert "booted" in lifecycle_events
        assert kernel.is_booted

        # Register and verify subsystem
        class FakeSubsystem:
            shutdown_called = False
            async def shutdown(self):
                self.shutdown_called = True

        sub = FakeSubsystem()
        kernel.register_subsystem("test_sub", sub)

        # Shutdown
        await kernel.shutdown()
        assert "shutting_down" in lifecycle_events
        assert not kernel.is_booted
        assert sub.shutdown_called
        assert not kernel.has_crash_marker()

    @pytest.mark.asyncio
    async def test_config_flows_to_kernel(self, tmp_path) -> None:
        """Verify config resolution chain works end-to-end."""
        kernel = GalaxyKernel()
        await kernel.boot(
            workspace=tmp_path,
            overrides={
                "project_name": "integration-test",
                "log_level": "DEBUG",
            },
        )

        assert kernel.config is not None
        assert kernel.config.project_name == "integration-test"
        assert kernel.config.log_level == "DEBUG"
        assert str(tmp_path) in kernel.config.workspace

        await kernel.shutdown()
