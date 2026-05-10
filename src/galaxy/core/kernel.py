"""Galaxy Kernel — the main entry point and lifecycle manager.

The kernel boots all subsystems, wires them together via the event bus,
and manages the full Galaxy lifecycle from boot to shutdown.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from galaxy.core.config import GalaxyConfig, load_config
from galaxy.core.constants import CRASH_MARKER_FILENAME, get_galaxy_dir
from galaxy.core.exceptions import BootError, ShutdownError, SubsystemInitError
from galaxy.events import GALAXY_BOOTED, GALAXY_BOOTING, GALAXY_SHUTDOWN, GALAXY_SHUTTING_DOWN, Event
from galaxy.events.bus import EventBus

logger = logging.getLogger(__name__)


class GalaxyKernel:
    """The brain of Galaxy. Boots all subsystems, manages lifecycle.

    Boot sequence:
    1. Load configuration
    2. Initialize event bus
    3. Create .galaxy directory
    4. Set crash marker
    5. Initialize all subsystems (in dependency order)
    6. Remove crash marker (clean boot)
    7. Emit galaxy.booted event

    Shutdown sequence:
    1. Emit galaxy.shutting_down event
    2. Stop all subsystems (reverse order)
    3. Stop event bus
    4. Remove crash marker
    5. Emit galaxy.shutdown event
    """

    def __init__(self) -> None:
        self.config: GalaxyConfig | None = None
        self.event_bus: EventBus = EventBus()
        self._booted: bool = False
        self._subsystems: dict[str, Any] = {}

    @property
    def is_booted(self) -> bool:
        """Whether the kernel has completed boot sequence."""
        return self._booted

    async def boot(
        self,
        workspace: str | Path = ".",
        config_path: str | Path | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> None:
        """Boot the Galaxy kernel.

        Args:
            workspace: Project workspace path.
            config_path: Explicit config file path (optional).
            overrides: Config override dict (optional).

        Raises:
            BootError: If boot fails.
            SubsystemInitError: If a subsystem fails to initialize.
        """
        if self._booted:
            raise BootError("Kernel is already booted")

        try:
            # 1. Load configuration
            logger.info("Loading configuration...")
            self.config = load_config(
                workspace=workspace,
                config_path=config_path,
                overrides=overrides,
            )

            # 2. Start event bus
            await self.event_bus.start()
            await self.event_bus.publish(Event(
                type=GALAXY_BOOTING,
                source="kernel",
                payload={"workspace": str(workspace)},
            ))

            # 3. Create .galaxy directory
            galaxy_dir = get_galaxy_dir(self.config.workspace)
            galaxy_dir.mkdir(parents=True, exist_ok=True)

            # 4. Set crash marker
            self._set_crash_marker()

            # 5. Initialize subsystems (placeholder — subsystems added in later phases)
            await self._init_subsystems()

            # 6. Remove crash marker (clean boot completed)
            self._remove_crash_marker()

            # 7. Mark as booted
            self._booted = True
            await self.event_bus.publish(Event(
                type=GALAXY_BOOTED,
                source="kernel",
                payload={"subsystems": list(self._subsystems.keys())},
            ))
            logger.info("Galaxy kernel booted successfully")

        except (BootError, SubsystemInitError):
            raise
        except Exception as e:
            raise BootError(f"Kernel boot failed: {e}") from e

    async def shutdown(self) -> None:
        """Gracefully shut down the Galaxy kernel.

        Raises:
            ShutdownError: If shutdown encounters errors.
        """
        if not self._booted:
            logger.warning("Kernel is not booted, nothing to shut down")
            return

        try:
            await self.event_bus.publish(Event(
                type=GALAXY_SHUTTING_DOWN,
                source="kernel",
            ))

            # Stop subsystems in reverse initialization order
            await self._shutdown_subsystems()

            # Remove crash marker
            self._remove_crash_marker()

            # Stop event bus
            await self.event_bus.stop()

            self._booted = False
            logger.info("Galaxy kernel shut down cleanly")

        except Exception as e:
            raise ShutdownError(f"Shutdown error: {e}") from e

    def has_crash_marker(self) -> bool:
        """Check if a crash marker exists (indicates previous unclean shutdown)."""
        if not self.config:
            return False
        marker = get_galaxy_dir(self.config.workspace) / CRASH_MARKER_FILENAME
        return marker.exists()

    def register_subsystem(self, name: str, instance: Any) -> None:
        """Register a subsystem instance.

        Args:
            name: Subsystem identifier (e.g. 'memory', 'cortex').
            instance: The subsystem instance.
        """
        self._subsystems[name] = instance
        logger.debug("Registered subsystem: %s", name)

    def get_subsystem(self, name: str) -> Any:
        """Get a registered subsystem by name.

        Args:
            name: Subsystem identifier.

        Returns:
            The subsystem instance, or None if not found.
        """
        return self._subsystems.get(name)

    async def _init_subsystems(self) -> None:
        """Initialize all subsystems in dependency order.

        This is a skeleton — each phase adds subsystem initialization here.
        """
        # Phase 1: Core subsystems initialized during boot
        # Phase 2+: Memory, Cortex, Vault, etc. will be added here
        logger.debug("Subsystem initialization complete (Phase 1 skeleton)")

    async def _shutdown_subsystems(self) -> None:
        """Shut down all subsystems in reverse order."""
        for name in reversed(list(self._subsystems.keys())):
            subsystem = self._subsystems[name]
            if hasattr(subsystem, "shutdown"):
                try:
                    await subsystem.shutdown()
                    logger.debug("Shut down subsystem: %s", name)
                except Exception:
                    logger.exception("Error shutting down subsystem: %s", name)
        self._subsystems.clear()

    def _set_crash_marker(self) -> None:
        """Create crash marker file."""
        if self.config:
            marker = get_galaxy_dir(self.config.workspace) / CRASH_MARKER_FILENAME
            marker.touch()

    def _remove_crash_marker(self) -> None:
        """Remove crash marker file."""
        if self.config:
            marker = get_galaxy_dir(self.config.workspace) / CRASH_MARKER_FILENAME
            if marker.exists():
                marker.unlink()
