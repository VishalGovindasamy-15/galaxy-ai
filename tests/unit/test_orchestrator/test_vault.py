"""Tests for galaxy.vault.checkpoint."""

import pytest
from pathlib import Path

from galaxy.vault.checkpoint import Checkpoint


class TestCreateCheckpoint:
    """Test checkpoint creation."""

    def test_create_checkpoint(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        state = {"tasks": {"t1": "completed"}, "progress": 0.5}
        path = cp.create(state, label="milestone_1")
        assert path.exists()
        assert "milestone_1" in path.name

    def test_create_without_label(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        path = cp.create({"key": "value"})
        assert path.exists()


class TestLoadCheckpoint:
    """Test checkpoint loading."""

    def test_load_checkpoint(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        original = {"tasks": {"t1": "done"}, "agents": 3}
        cp.create(original, label="test")

        loaded = cp.load_latest()
        assert loaded == original

    def test_load_latest_empty(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        assert cp.load_latest() is None

    def test_list_checkpoints(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        cp.create({"a": 1}, label="first")
        cp.create({"b": 2}, label="second")

        cps = cp.list_checkpoints()
        assert len(cps) == 2
        assert cps[0]["label"] == "first"


class TestCrashMarker:
    """Test crash detection."""

    def test_no_crash_initially(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        assert not cp.has_crash_marker()

    def test_create_and_remove_crash_marker(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        cp.create_crash_marker()
        assert cp.has_crash_marker()
        cp.remove_crash_marker()
        assert not cp.has_crash_marker()


class TestRecoverFromCrash:
    """Test crash recovery."""

    def test_recover_with_marker_and_checkpoint(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        cp.create({"state": "saved"}, label="pre_crash")
        cp.create_crash_marker()

        recovered = cp.recover_from_crash()
        assert recovered == {"state": "saved"}
        assert not cp.has_crash_marker()  # Cleaned up

    def test_recover_no_marker(self, tmp_path: Path) -> None:
        cp = Checkpoint(workspace=str(tmp_path))
        assert cp.recover_from_crash() is None
