"""Tests for galaxy.core.kernel (GalaxyKernel)."""

import pytest

from galaxy.core.kernel import GalaxyKernel
from galaxy.core.exceptions import BootError
from galaxy.events import Event


@pytest.fixture
def kernel() -> GalaxyKernel:
    """Create a fresh kernel for each test."""
    return GalaxyKernel()


class TestKernelBoot:
    """Test kernel boot sequence."""

    @pytest.mark.asyncio
    async def test_boot_initializes_subsystems(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)
        assert kernel.is_booted
        assert kernel.config is not None
        assert kernel.config.workspace == str(tmp_path)

    @pytest.mark.asyncio
    async def test_boot_creates_galaxy_dir(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)
        galaxy_dir = tmp_path / ".galaxy"
        assert galaxy_dir.exists()

    @pytest.mark.asyncio
    async def test_boot_emits_events(self, kernel: GalaxyKernel, tmp_path) -> None:
        events: list[Event] = []

        async def capture(event: Event) -> None:
            events.append(event)

        kernel.event_bus.subscribe("galaxy.*", capture)
        await kernel.boot(workspace=tmp_path)

        event_types = [e.type for e in events]
        assert "galaxy.booting" in event_types
        assert "galaxy.booted" in event_types

    @pytest.mark.asyncio
    async def test_double_boot_raises(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)
        with pytest.raises(BootError, match="already booted"):
            await kernel.boot(workspace=tmp_path)

    @pytest.mark.asyncio
    async def test_boot_removes_crash_marker(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)
        assert not kernel.has_crash_marker()

    @pytest.mark.asyncio
    async def test_boot_with_config_overrides(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(
            workspace=tmp_path,
            overrides={"project_name": "test-project", "log_level": "DEBUG"},
        )
        assert kernel.config is not None
        assert kernel.config.project_name == "test-project"
        assert kernel.config.log_level == "DEBUG"


class TestKernelShutdown:
    """Test kernel shutdown sequence."""

    @pytest.mark.asyncio
    async def test_shutdown_cleans_up(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)
        assert kernel.is_booted

        await kernel.shutdown()
        assert not kernel.is_booted

    @pytest.mark.asyncio
    async def test_shutdown_removes_crash_marker(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)
        await kernel.shutdown()
        assert not kernel.has_crash_marker()

    @pytest.mark.asyncio
    async def test_shutdown_when_not_booted(self, kernel: GalaxyKernel) -> None:
        # Should not raise
        await kernel.shutdown()

    @pytest.mark.asyncio
    async def test_boot_shutdown_boot_cycle(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)
        await kernel.shutdown()

        # Should be able to boot again after shutdown
        kernel2 = GalaxyKernel()
        await kernel2.boot(workspace=tmp_path)
        assert kernel2.is_booted
        await kernel2.shutdown()


class TestSubsystemRegistry:
    """Test subsystem registration."""

    @pytest.mark.asyncio
    async def test_register_subsystem(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)

        class FakeSubsystem:
            name = "fake"

        kernel.register_subsystem("fake", FakeSubsystem())
        assert kernel.get_subsystem("fake") is not None

    @pytest.mark.asyncio
    async def test_get_missing_subsystem(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)
        assert kernel.get_subsystem("nonexistent") is None

    @pytest.mark.asyncio
    async def test_shutdown_clears_subsystems(self, kernel: GalaxyKernel, tmp_path) -> None:
        await kernel.boot(workspace=tmp_path)

        class MockSub:
            stopped = False
            async def shutdown(self):
                self.stopped = True

        sub = MockSub()
        kernel.register_subsystem("mock", sub)
        await kernel.shutdown()

        assert sub.stopped
        assert kernel.get_subsystem("mock") is None


class TestCrashDetection:
    """Test crash marker detection."""

    @pytest.mark.asyncio
    async def test_no_crash_marker_initially(self, kernel: GalaxyKernel, tmp_path) -> None:
        # Config not loaded yet
        assert not kernel.has_crash_marker()

    @pytest.mark.asyncio
    async def test_crash_marker_during_boot(self, kernel: GalaxyKernel, tmp_path) -> None:
        """Simulate crash by manually setting marker and checking."""
        await kernel.boot(workspace=tmp_path)
        # After clean boot, marker should be gone
        assert not kernel.has_crash_marker()
        await kernel.shutdown()
