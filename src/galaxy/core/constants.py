"""Galaxy system constants and defaults.

All magic numbers, default values, and system-wide constants live here.
No other module should hardcode these values.
"""

from __future__ import annotations

from pathlib import Path

# ─── Project Structure ───────────────────────────────────────────────────────

GALAXY_DIR_NAME = ".galaxy"
"""Name of the Galaxy workspace directory created in every project."""

CONFIG_FILENAME = "galaxy.config.yaml"
"""Default configuration file name."""

DEFAULT_WORKSPACE = "."
"""Default workspace path (current directory)."""

# ─── Networking ──────────────────────────────────────────────────────────────

DEFAULT_STUDIO_PORT = 8420
"""Default port for Galaxy Studio web dashboard."""

DEFAULT_STUDIO_HOST = "127.0.0.1"
"""Default host for Galaxy Studio (localhost only by default)."""

# ─── Database ────────────────────────────────────────────────────────────────

DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{GALAXY_DIR_NAME}/galaxy.db"
"""Default SQLite database URL (no external DB required)."""

# ─── Models ──────────────────────────────────────────────────────────────────

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
"""Default Ollama API endpoint."""

DEFAULT_MASTER_MODEL = "qwen2.5-coder:14b"
"""Default model for master agent (architecture, reasoning)."""

DEFAULT_DOMAIN_MODEL = "qwen2.5-coder:7b"
"""Default model for domain agents (planning, coordination)."""

DEFAULT_WORKER_MODEL = "qwen2.5-coder:7b"
"""Default model for worker agents (code generation)."""

DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
"""Default embedding model for memory/vector search."""

# ─── VRAM Thresholds (GB) ────────────────────────────────────────────────────

VRAM_TIER_HIGH = 24.0
"""24GB+ VRAM: use 14b master + 7b workers."""

VRAM_TIER_MEDIUM = 12.0
"""12-24GB VRAM: use 7b for all tiers."""

VRAM_TIER_LOW = 8.0
"""8-12GB VRAM: use 3b for all tiers."""

VRAM_RESERVE_MB = 512
"""MB of VRAM to keep reserved (don't allocate to models)."""

# ─── Agent Limits ────────────────────────────────────────────────────────────

MAX_DOMAIN_AGENTS = 10
"""Maximum number of concurrent domain agents."""

MAX_WORKERS_PER_DOMAIN = 50
"""Maximum workers a single domain agent can spawn."""

MAX_RETRY_LOOPS = 5
"""Maximum retry attempts before escalating to next level."""

MAX_RECURSION_DEPTH = 3
"""Maximum depth for recursive agent task decomposition."""

IDLE_TIMEOUT_SECONDS = 300
"""Seconds before an idle agent is cleaned up."""

# ─── Escalation Chain ────────────────────────────────────────────────────────

ESCALATION_LEVEL_WORKER_RETRY = 1
"""Level 1: Worker retries the task with error context."""

ESCALATION_LEVEL_DOMAIN = 2
"""Level 2: Domain agent intervenes (restructure, reassign)."""

ESCALATION_LEVEL_MASTER = 3
"""Level 3: Master agent restructures the approach."""

ESCALATION_LEVEL_MODEL_FALLBACK = 4
"""Level 4: Switch to a more capable model."""

ESCALATION_LEVEL_USER = 5
"""Level 5: Pause and ask the user for help."""

# ─── Vault / Checkpointing ──────────────────────────────────────────────────

CHECKPOINT_INTERVAL_MINUTES = 5
"""Auto-checkpoint interval during execution."""

MAX_SNAPSHOTS = 10
"""Maximum number of checkpoints to retain."""

CRASH_MARKER_FILENAME = ".galaxy_crash_marker"
"""File created on boot, removed on clean shutdown. Presence = crash."""

# ─── Scheduler ───────────────────────────────────────────────────────────────

SCHEDULER_MODE_SPEED = "speed"
"""Maximize parallelism, use all available VRAM."""

SCHEDULER_MODE_BALANCED = "balanced"
"""Balance between parallelism and resource usage."""

SCHEDULER_MODE_QUALITY = "quality"
"""Minimize parallelism, maximize per-task resources."""

DEFAULT_SCHEDULER_MODE = SCHEDULER_MODE_BALANCED
"""Default scheduling mode."""

# ─── Validation Pipeline ────────────────────────────────────────────────────

VALIDATION_STEPS = [
    "syntax",
    "imports",
    "lint",
    "type_check",
    "build",
    "test",
    "security",
    "doc_coverage",
]
"""Ordered validation steps for the Forge pipeline."""

# ─── Paths ───────────────────────────────────────────────────────────────────


def get_galaxy_dir(workspace: str | Path = ".") -> Path:
    """Get the .galaxy directory path for a workspace."""
    return Path(workspace) / GALAXY_DIR_NAME


def get_config_path(workspace: str | Path = ".") -> Path:
    """Get the galaxy.config.yaml path for a workspace."""
    return get_galaxy_dir(workspace) / CONFIG_FILENAME


def get_memory_dir(workspace: str | Path = ".") -> Path:
    """Get the memory storage directory."""
    return get_galaxy_dir(workspace) / "memory"


def get_checkpoints_dir(workspace: str | Path = ".") -> Path:
    """Get the checkpoints directory."""
    return get_galaxy_dir(workspace) / "checkpoints"


def get_logs_dir(workspace: str | Path = ".") -> Path:
    """Get the logs directory."""
    return get_galaxy_dir(workspace) / "logs"
