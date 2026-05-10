"""Tests for galaxy.core.config."""

import os
from pathlib import Path

import pytest
import yaml

from galaxy.core.config import (
    GalaxyConfig,
    ModelConfig,
    ModelsConfig,
    SchedulerConfig,
    generate_default_config,
    load_config,
    load_config_from_yaml,
)
from galaxy.core.exceptions import ConfigNotFoundError, ConfigValidationError


class TestModelConfig:
    """Test ModelConfig model."""

    def test_defaults(self) -> None:
        mc = ModelConfig()
        assert mc.provider == "ollama"
        assert mc.temperature == 0.1

    def test_resolve_api_key_empty(self) -> None:
        mc = ModelConfig()
        assert mc.resolve_api_key() is None

    def test_resolve_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_API_KEY", "sk-12345")
        mc = ModelConfig(api_key_env="TEST_API_KEY")
        assert mc.resolve_api_key() == "sk-12345"

    def test_resolve_api_key_missing_env(self) -> None:
        mc = ModelConfig(api_key_env="NONEXISTENT_KEY_12345")
        assert mc.resolve_api_key() is None


class TestSchedulerConfig:
    """Test SchedulerConfig validation."""

    def test_valid_modes(self) -> None:
        for mode in ("speed", "balanced", "quality"):
            sc = SchedulerConfig(mode=mode)
            assert sc.mode == mode

    def test_invalid_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="must be one of"):
            SchedulerConfig(mode="turbo")


class TestGalaxyConfig:
    """Test root GalaxyConfig."""

    def test_load_default_config(self) -> None:
        config = GalaxyConfig()
        assert config.workspace == "."
        assert config.log_level == "INFO"
        assert config.models.master.provider == "ollama"
        assert config.scheduler.mode == "balanced"

    def test_get_galaxy_dir(self) -> None:
        config = GalaxyConfig(workspace="/tmp/test")
        assert config.get_galaxy_dir() == Path("/tmp/test/.galaxy")

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GALAXY_LOG_LEVEL", "DEBUG")
        config = GalaxyConfig()
        assert config.log_level == "DEBUG"


class TestLoadConfigFromYaml:
    """Test YAML loading function."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"project_name": "test", "log_level": "DEBUG"}))
        data = load_config_from_yaml(config_file)
        assert data["project_name"] == "test"
        assert data["log_level"] == "DEBUG"

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(ConfigNotFoundError):
            load_config_from_yaml("/nonexistent/config.yaml")

    def test_load_empty_yaml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        data = load_config_from_yaml(config_file)
        assert data == {}

    def test_load_invalid_yaml_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.yaml"
        config_file.write_text(":\n  - :\n    invalid: [")
        with pytest.raises(ConfigValidationError, match="Invalid YAML"):
            load_config_from_yaml(config_file)

    def test_load_non_dict_yaml_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / "list.yaml"
        config_file.write_text("- item1\n- item2")
        with pytest.raises(ConfigValidationError, match="YAML mapping"):
            load_config_from_yaml(config_file)


class TestLoadConfig:
    """Test the full config loading chain."""

    def test_load_from_yaml(self, tmp_path: Path) -> None:
        galaxy_dir = tmp_path / ".galaxy"
        galaxy_dir.mkdir()
        config_file = galaxy_dir / "galaxy.config.yaml"
        config_file.write_text(yaml.dump({
            "project_name": "my-api",
            "log_level": "DEBUG",
        }))
        config = load_config(workspace=tmp_path)
        assert config.project_name == "my-api"
        assert config.log_level == "DEBUG"

    def test_load_with_overrides(self, tmp_path: Path) -> None:
        config = load_config(
            workspace=tmp_path,
            overrides={"project_name": "override-project", "log_level": "WARNING"},
        )
        assert config.project_name == "override-project"
        assert config.log_level == "WARNING"

    def test_load_with_explicit_path(self, tmp_path: Path) -> None:
        config_file = tmp_path / "custom.yaml"
        config_file.write_text(yaml.dump({"project_name": "custom"}))
        config = load_config(workspace=tmp_path, config_path=config_file)
        assert config.project_name == "custom"

    def test_invalid_config_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigValidationError):
            load_config(
                workspace=tmp_path,
                overrides={"scheduler": {"mode": "invalid_mode"}},
            )


class TestGenerateDefaultConfig:
    """Test default config generation."""

    def test_generates_yaml_file(self, tmp_path: Path) -> None:
        path = generate_default_config(tmp_path)
        assert path.exists()
        assert path.name == "galaxy.config.yaml"

    def test_creates_galaxy_dir(self, tmp_path: Path) -> None:
        generate_default_config(tmp_path)
        assert (tmp_path / ".galaxy").is_dir()

    def test_generated_config_is_valid(self, tmp_path: Path) -> None:
        path = generate_default_config(tmp_path)
        data = load_config_from_yaml(path)
        assert "models" in data
        assert "scheduler" in data

    def test_generated_config_loadable(self, tmp_path: Path) -> None:
        generate_default_config(tmp_path)
        config = load_config(workspace=tmp_path)
        assert config.models.master.provider == "ollama"
