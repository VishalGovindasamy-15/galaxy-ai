"""Checkpoint engine — saves and restores Galaxy state.

Creates checkpoint snapshots at milestones for crash recovery and pause/resume.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from galaxy.core.constants import CRASH_MARKER_FILENAME, MAX_SNAPSHOTS, get_checkpoints_dir
from galaxy.core.exceptions import CheckpointError

logger = logging.getLogger(__name__)


class Checkpoint:
    """Manages checkpoint creation, loading, and cleanup."""

    def __init__(self, workspace: str = ".") -> None:
        self.workspace = Path(workspace)
        self._checkpoint_dir = get_checkpoints_dir(workspace)

    def create(self, state: dict[str, Any], label: str = "") -> Path:
        """Create a checkpoint snapshot.

        Args:
            state: Dictionary of serializable state data.
            label: Optional human-readable label.

        Returns:
            Path to the created checkpoint file.
        """
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        filename = f"checkpoint_{timestamp}.json"
        if label:
            safe_label = label.replace(" ", "_")[:30]
            filename = f"checkpoint_{timestamp}_{safe_label}.json"

        checkpoint_path = self._checkpoint_dir / filename

        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "label": label,
            "state": state,
        }

        try:
            checkpoint_path.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            )
            logger.info("Checkpoint created: %s", checkpoint_path.name)
        except Exception as e:
            raise CheckpointError(f"Failed to create checkpoint: {e}") from e

        # Cleanup old checkpoints
        self._cleanup_old()

        return checkpoint_path

    def load_latest(self) -> dict[str, Any] | None:
        """Load the most recent checkpoint.

        Returns:
            Checkpoint state dict, or None if no checkpoints exist.
        """
        checkpoints = self._list_checkpoints()
        if not checkpoints:
            return None

        latest = checkpoints[-1]
        return self._load_file(latest)

    def load(self, path: Path) -> dict[str, Any]:
        """Load a specific checkpoint file."""
        return self._load_file(path)

    def list_checkpoints(self) -> list[dict[str, Any]]:
        """List all available checkpoints with metadata."""
        result = []
        for cp_path in self._list_checkpoints():
            try:
                data = json.loads(cp_path.read_text(encoding="utf-8"))
                result.append({
                    "path": str(cp_path),
                    "filename": cp_path.name,
                    "timestamp": data.get("timestamp", ""),
                    "label": data.get("label", ""),
                })
            except Exception:
                continue
        return result

    def has_crash_marker(self) -> bool:
        """Check if a crash marker exists (indicates unclean shutdown)."""
        marker = self.workspace / ".galaxy" / CRASH_MARKER_FILENAME
        return marker.exists()

    def create_crash_marker(self) -> None:
        """Create crash marker on boot."""
        marker_dir = self.workspace / ".galaxy"
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker = marker_dir / CRASH_MARKER_FILENAME
        marker.write_text(
            datetime.now(timezone.utc).isoformat(), encoding="utf-8",
        )

    def remove_crash_marker(self) -> None:
        """Remove crash marker on clean shutdown."""
        marker = self.workspace / ".galaxy" / CRASH_MARKER_FILENAME
        if marker.exists():
            marker.unlink()

    def recover_from_crash(self) -> dict[str, Any] | None:
        """Attempt crash recovery: load latest checkpoint if crash marker exists.

        Returns:
            Recovered state dict, or None if no crash detected.
        """
        if not self.has_crash_marker():
            return None

        logger.warning("Crash marker detected — attempting recovery")
        state = self.load_latest()

        if state:
            logger.info("Recovered from checkpoint: %s", state.get("label", "unknown"))
            self.remove_crash_marker()

        return state

    def _list_checkpoints(self) -> list[Path]:
        """List checkpoint files sorted by name (oldest first)."""
        if not self._checkpoint_dir.exists():
            return []
        return sorted(self._checkpoint_dir.glob("checkpoint_*.json"))

    def _load_file(self, path: Path) -> dict[str, Any]:
        """Load and parse a checkpoint file."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("state", {})
        except Exception as e:
            raise CheckpointError(f"Failed to load checkpoint: {e}") from e

    def _cleanup_old(self) -> None:
        """Remove old checkpoints beyond MAX_SNAPSHOTS."""
        checkpoints = self._list_checkpoints()
        while len(checkpoints) > MAX_SNAPSHOTS:
            old = checkpoints.pop(0)
            try:
                old.unlink()
                logger.debug("Removed old checkpoint: %s", old.name)
            except Exception:
                pass
