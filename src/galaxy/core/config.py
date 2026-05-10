"""Galaxy configuration system.

Loads configuration from YAML files, environment variables, and defaults.
Uses Pydantic for validation and type safety.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from galaxy.core.constants import (
    CHECKPOINT_INTERVAL_MINUTES,
    DEFAULT_DATABASE_URL,
    DEFAULT_DOMAIN_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MASTER_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_SCHEDULER_MODE,
    DEFAULT_STUDIO_HOST,
    DEFAULT_STUDIO_PORT,
    DEFAULT_WORKER_MODEL,
    GALAXY_DIR_NAME,
    IDLE_TIMEOUT_SECONDS,
    MAX_DOMAIN_AGENTS,
    MAX_RETRY_LOOPS,
    MAX_SNAPSHOTS,
    MAX_WORKERS_PER_DOMAIN,
    VRAM_RESERVE_MB,
)
from galaxy.core.exceptions import ConfigNotFoundError, ConfigValidationError


# ─── Model Configuration ────────────────────────────────────────────────────


class ModelConfig(BaseModel):
    """Configuration for a single LLM model."""

    provider: str = "ollama"
    model: str = ""
    api_key_env: str = ""
    base_url: str = ""
    temperature: float = 0.1
    max_tokens: int = 8192
    timeout_seconds: int = 300

    def resolve_api_key(self) -> str | None:
        """Resolve API key from environment variable name."""
        if not self.api_key_env:
            return None
        return os.environ.get(self.api_key_env)


class FallbackConfig(BaseModel):
    """Fallback model configuration when primary fails."""

    enabled: bool = False
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key_env: str = "OPENAI_API_KEY"
    trigger_after_failures: int = 2
    base_url: str = ""


class ModelsConfig(BaseModel):
    """Complete model configuration for all agent tiers."""

    master: ModelConfig = ModelConfig(provider="ollama", model=DEFAULT_MASTER_MODEL)
    domain: ModelConfig = ModelConfig(provider="ollama", model=DEFAULT_DOMAIN_MODEL)
    worker: ModelConfig = ModelConfig(provider="ollama", model=DEFAULT_WORKER_MODEL)
    embedding: ModelConfig = ModelConfig(provider="ollama", model=DEFAULT_EMBEDDING_MODEL)
    fallback: FallbackConfig = FallbackConfig()


# ─── Subsystem Configurations ───────────────────────────────────────────────


class AgentLimits(BaseModel):
    """Agent spawn and resource limits."""

    max_domain_agents: int = MAX_DOMAIN_AGENTS
    max_workers_per_domain: int = MAX_WORKERS_PER_DOMAIN
    max_retry_loops: int = MAX_RETRY_LOOPS
    max_recursion_depth: int = 3
    idle_timeout_seconds: int = IDLE_TIMEOUT_SECONDS


class SchedulerConfig(BaseModel):
    """VRAM-aware scheduler configuration."""

    mode: str = DEFAULT_SCHEDULER_MODE
    max_parallel_workers: int | str = "auto"
    vram_reserve_mb: int = VRAM_RESERVE_MB

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        valid = {"speed", "balanced", "quality"}
        if v not in valid:
            raise ValueError(f"Scheduler mode must be one of {valid}, got '{v}'")
        return v


class VaultConfig(BaseModel):
    """Checkpoint and recovery configuration."""

    checkpoint_interval_minutes: int = CHECKPOINT_INTERVAL_MINUTES
    crash_recovery: bool = True
    max_snapshots: int = MAX_SNAPSHOTS


class StudioConfig(BaseModel):
    """Galaxy Studio web dashboard configuration."""

    enabled: bool = True
    host: str = DEFAULT_STUDIO_HOST
    port: int = DEFAULT_STUDIO_PORT
    auto_open_browser: bool = True


# ─── Root Configuration ─────────────────────────────────────────────────────


class GalaxyConfig(BaseSettings):
    """Root Galaxy configuration.

    Loads from:
    1. Default values (defined here)
    2. galaxy.config.yaml (if exists)
    3. Environment variables (GALAXY_ prefix)
    """

    project_name: str = ""
    workspace: str = "."
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    agents: AgentLimits = Field(default_factory=AgentLimits)
    vault: VaultConfig = Field(default_factory=VaultConfig)
    studio: StudioConfig = Field(default_factory=StudioConfig)
    database_url: str = DEFAULT_DATABASE_URL
    log_level: str = "INFO"

    model_config = {"env_prefix": "GALAXY_", "env_nested_delimiter": "__"}

    def get_galaxy_dir(self) -> Path:
        """Get the .galaxy directory path for this workspace."""
        return Path(self.workspace) / GALAXY_DIR_NAME


# ─── Config Loading Functions ────────────────────────────────────────────────


def load_config_from_yaml(path: str | Path) -> dict[str, Any]:
    """Load configuration dictionary from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        ConfigNotFoundError: If the file doesn't exist.
        ConfigValidationError: If the YAML is malformed.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"Invalid YAML in {config_path}: {e}") from e

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigValidationError(f"Config file must contain a YAML mapping, got {type(data)}")

    return data


def load_config(
    workspace: str | Path = ".",
    config_path: str | Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> GalaxyConfig:
    """Load Galaxy configuration with full resolution chain.

    Resolution order (later overrides earlier):
    1. Built-in defaults
    2. galaxy.config.yaml (if found)
    3. Environment variables (GALAXY_ prefix)
    4. Explicit overrides dict

    Args:
        workspace: Project workspace path.
        config_path: Explicit config file path (optional).
        overrides: Dict of config overrides (optional).

    Returns:
        Fully resolved GalaxyConfig instance.
    """
    config_data: dict[str, Any] = {"workspace": str(workspace)}

    # Try loading YAML config
    if config_path:
        yaml_data = load_config_from_yaml(config_path)
        config_data.update(yaml_data)
    else:
        default_path = Path(workspace) / GALAXY_DIR_NAME / "galaxy.config.yaml"
        if default_path.exists():
            yaml_data = load_config_from_yaml(default_path)
            config_data.update(yaml_data)

    # Apply explicit overrides
    if overrides:
        config_data.update(overrides)

    try:
        return GalaxyConfig(**config_data)
    except Exception as e:
        raise ConfigValidationError(f"Configuration validation failed: {e}") from e


def generate_default_config(workspace: str | Path = ".") -> Path:
    """Generate a default galaxy.config.yaml in the workspace.

    Args:
        workspace: Project workspace path.

    Returns:
        Path to the generated config file.
    """
    galaxy_dir = Path(workspace) / GALAXY_DIR_NAME
    galaxy_dir.mkdir(parents=True, exist_ok=True)

    config = GalaxyConfig(workspace=str(workspace))
    config_path = galaxy_dir / "galaxy.config.yaml"

    config_dict = {
        "project_name": "",
        "log_level": config.log_level,
        "models": {
            "master": {"provider": "ollama", "model": config.models.master.model},
            "domain": {"provider": "ollama", "model": config.models.domain.model},
            "worker": {"provider": "ollama", "model": config.models.worker.model},
            "embedding": {"provider": "ollama", "model": config.models.embedding.model},
            "fallback": {"enabled": False, "provider": "openai", "model": "gpt-4o"},
        },
        "scheduler": {"mode": config.scheduler.mode},
        "studio": {"enabled": True, "port": config.studio.port},
    }

    with open(config_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    return config_path
