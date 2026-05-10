"""Pytest configuration and shared fixtures for Galaxy tests."""

import pytest


@pytest.fixture
def tmp_workspace(tmp_path):
    """Create a temporary workspace directory for tests."""
    workspace = tmp_path / "test_project"
    workspace.mkdir()
    return workspace


@pytest.fixture
def galaxy_dir(tmp_workspace):
    """Create a .galaxy directory in the temp workspace."""
    gdir = tmp_workspace / ".galaxy"
    gdir.mkdir()
    return gdir
