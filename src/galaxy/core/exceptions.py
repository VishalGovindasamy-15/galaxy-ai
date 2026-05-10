"""Galaxy custom exceptions.

Every exception Galaxy can raise is defined here. Organized by subsystem.
All exceptions inherit from GalaxyError for catch-all handling.
"""

from __future__ import annotations


# ─── Base ────────────────────────────────────────────────────────────────────


class GalaxyError(Exception):
    """Base exception for all Galaxy errors."""

    def __init__(self, message: str = "", *, details: str = "") -> None:
        self.details = details
        super().__init__(message)


# ─── Configuration ───────────────────────────────────────────────────────────


class ConfigError(GalaxyError):
    """Invalid or missing configuration."""


class ConfigNotFoundError(ConfigError):
    """Configuration file not found."""


class ConfigValidationError(ConfigError):
    """Configuration values failed validation."""


# ─── Kernel / Lifecycle ──────────────────────────────────────────────────────


class KernelError(GalaxyError):
    """Error during kernel boot or shutdown."""


class BootError(KernelError):
    """Failed to boot Galaxy kernel."""


class ShutdownError(KernelError):
    """Error during graceful shutdown."""


class SubsystemInitError(KernelError):
    """A subsystem failed to initialize during boot."""

    def __init__(self, subsystem: str, message: str = "") -> None:
        self.subsystem = subsystem
        super().__init__(message or f"Failed to initialize subsystem: {subsystem}")


# ─── Agent ───────────────────────────────────────────────────────────────────


class AgentError(GalaxyError):
    """Base error for agent operations."""


class AgentSpawnError(AgentError):
    """Failed to spawn an agent."""


class AgentLimitError(AgentError):
    """Agent limit exceeded (max domain agents or workers per domain)."""


class AgentTimeoutError(AgentError):
    """Agent operation timed out."""


# ─── Model / LLM ────────────────────────────────────────────────────────────


class ModelError(GalaxyError):
    """Base error for model operations."""


class ModelNotAvailableError(ModelError):
    """Requested model is not available (not pulled, provider down)."""

    def __init__(self, model: str, provider: str = "", message: str = "") -> None:
        self.model = model
        self.provider = provider
        super().__init__(message or f"Model not available: {model} (provider: {provider})")


class ModelInferenceError(ModelError):
    """Model inference call failed."""


class ModelRateLimitError(ModelError):
    """Model provider rate limit exceeded."""


class VRAMExhaustedError(ModelError):
    """Not enough VRAM to load the requested model."""


# ─── Tool ────────────────────────────────────────────────────────────────────


class ToolError(GalaxyError):
    """Base error for tool operations."""


class ToolNotFoundError(ToolError):
    """Requested tool not found in registry."""


class ToolPermissionError(ToolError):
    """Agent doesn't have permission to use this tool."""


class ToolExecutionError(ToolError):
    """Tool execution failed."""


class ToolTimeoutError(ToolError):
    """Tool execution timed out."""


# ─── Orchestrator ────────────────────────────────────────────────────────────


class OrchestratorError(GalaxyError):
    """Base error for orchestration."""


class TaskGraphError(OrchestratorError):
    """Error in task graph (circular dependency, invalid state)."""


class CircularDependencyError(TaskGraphError):
    """Circular dependency detected in task graph."""


class EscalationError(OrchestratorError):
    """Error during escalation chain."""


class MaxEscalationReachedError(EscalationError):
    """All escalation levels exhausted — requires user intervention."""


# ─── Vault / Persistence ────────────────────────────────────────────────────


class VaultError(GalaxyError):
    """Base error for vault operations."""


class CheckpointError(VaultError):
    """Failed to create or load checkpoint."""


class RecoveryError(VaultError):
    """Failed to recover from crash."""


class SnapshotCorruptedError(VaultError):
    """Checkpoint snapshot data is corrupted."""


# ─── Terminal ────────────────────────────────────────────────────────────────


class TerminalError(GalaxyError):
    """Base error for terminal operations."""


class TmuxNotInstalledError(TerminalError):
    """tmux is not installed on the system."""


class SessionCreationError(TerminalError):
    """Failed to create tmux session."""


# ─── Workspace ───────────────────────────────────────────────────────────────


class WorkspaceError(GalaxyError):
    """Base error for workspace operations."""


class PathOutsideWorkspaceError(WorkspaceError):
    """Operation attempted outside the allowed workspace directory."""

    def __init__(self, path: str, workspace: str) -> None:
        self.path = path
        self.workspace = workspace
        super().__init__(f"Path '{path}' is outside workspace '{workspace}'")


# ─── Validation / Forge ──────────────────────────────────────────────────────


class ValidationError(GalaxyError):
    """Base error for validation pipeline."""


class SyntaxCheckError(ValidationError):
    """Generated code has syntax errors."""


class ImportCheckError(ValidationError):
    """Generated code has import errors."""


class LintError(ValidationError):
    """Generated code failed linting."""


class TestFailedError(ValidationError):
    """Generated test failed to pass."""
