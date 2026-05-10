"""Tests for galaxy.core.exceptions."""

import pytest

from galaxy.core.exceptions import (
    AgentError,
    AgentLimitError,
    AgentSpawnError,
    BootError,
    CheckpointError,
    CircularDependencyError,
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError,
    EscalationError,
    GalaxyError,
    KernelError,
    MaxEscalationReachedError,
    ModelError,
    ModelInferenceError,
    ModelNotAvailableError,
    ModelRateLimitError,
    OrchestratorError,
    PathOutsideWorkspaceError,
    RecoveryError,
    SessionCreationError,
    ShutdownError,
    SubsystemInitError,
    TaskGraphError,
    TerminalError,
    TmuxNotInstalledError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolPermissionError,
    ValidationError,
    VRAMExhaustedError,
    VaultError,
    WorkspaceError,
)


class TestGalaxyErrorBase:
    """Test the base GalaxyError class."""

    def test_empty_message(self) -> None:
        err = GalaxyError()
        assert str(err) == ""

    def test_with_message(self) -> None:
        err = GalaxyError("something broke")
        assert str(err) == "something broke"

    def test_with_details(self) -> None:
        err = GalaxyError("failed", details="stack trace here")
        assert err.details == "stack trace here"

    def test_is_exception(self) -> None:
        assert issubclass(GalaxyError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(GalaxyError, match="test"):
            raise GalaxyError("test")


class TestExceptionHierarchy:
    """Test that all exceptions inherit from GalaxyError."""

    EXCEPTION_CLASSES = [
        ConfigError, ConfigNotFoundError, ConfigValidationError,
        KernelError, BootError, ShutdownError, SubsystemInitError,
        AgentError, AgentSpawnError, AgentLimitError,
        ModelError, ModelNotAvailableError, ModelInferenceError,
        ModelRateLimitError, VRAMExhaustedError,
        ToolError, ToolNotFoundError, ToolPermissionError, ToolExecutionError,
        OrchestratorError, TaskGraphError, CircularDependencyError,
        EscalationError, MaxEscalationReachedError,
        VaultError, CheckpointError, RecoveryError,
        TerminalError, TmuxNotInstalledError, SessionCreationError,
        WorkspaceError, PathOutsideWorkspaceError,
        ValidationError,
    ]

    @pytest.mark.parametrize("exc_class", EXCEPTION_CLASSES)
    def test_inherits_from_galaxy_error(self, exc_class: type) -> None:
        assert issubclass(exc_class, GalaxyError)

    @pytest.mark.parametrize("exc_class", EXCEPTION_CLASSES)
    def test_all_exceptions_have_messages(self, exc_class: type) -> None:
        """Every exception class should have a docstring."""
        assert exc_class.__doc__ is not None
        assert len(exc_class.__doc__.strip()) > 0


class TestSpecializedExceptions:
    """Test exceptions with extra attributes."""

    def test_subsystem_init_error(self) -> None:
        err = SubsystemInitError("memory")
        assert err.subsystem == "memory"
        assert "memory" in str(err)

    def test_subsystem_init_error_custom_msg(self) -> None:
        err = SubsystemInitError("vault", "disk full")
        assert str(err) == "disk full"

    def test_model_not_available(self) -> None:
        err = ModelNotAvailableError("gpt-4o", provider="openai")
        assert err.model == "gpt-4o"
        assert err.provider == "openai"
        assert "gpt-4o" in str(err)

    def test_path_outside_workspace(self) -> None:
        err = PathOutsideWorkspaceError("/etc/passwd", "/home/user/project")
        assert err.path == "/etc/passwd"
        assert err.workspace == "/home/user/project"
        assert "outside workspace" in str(err)


class TestExceptionChaining:
    """Test that exceptions chain correctly through the hierarchy."""

    def test_config_not_found_is_config_error(self) -> None:
        with pytest.raises(ConfigError):
            raise ConfigNotFoundError("missing")

    def test_boot_error_is_kernel_error(self) -> None:
        with pytest.raises(KernelError):
            raise BootError("failed")

    def test_circular_dep_is_task_graph_error(self) -> None:
        with pytest.raises(TaskGraphError):
            raise CircularDependencyError("A → B → A")

    def test_tmux_not_installed_is_terminal_error(self) -> None:
        with pytest.raises(TerminalError):
            raise TmuxNotInstalledError("install tmux")

    def test_catch_all_galaxy_error(self) -> None:
        """Any Galaxy exception can be caught with GalaxyError."""
        exceptions = [
            ConfigNotFoundError("x"),
            BootError("x"),
            AgentSpawnError("x"),
            ModelInferenceError("x"),
            ToolExecutionError("x"),
            CircularDependencyError("x"),
            CheckpointError("x"),
            TmuxNotInstalledError("x"),
        ]
        for exc in exceptions:
            with pytest.raises(GalaxyError):
                raise exc
