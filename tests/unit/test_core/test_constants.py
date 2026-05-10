"""Tests for galaxy.core.constants."""

from pathlib import Path

from galaxy.core.constants import (
    CHECKPOINT_INTERVAL_MINUTES,
    CRASH_MARKER_FILENAME,
    DEFAULT_DATABASE_URL,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_MASTER_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_SCHEDULER_MODE,
    DEFAULT_STUDIO_PORT,
    ESCALATION_LEVEL_DOMAIN,
    ESCALATION_LEVEL_MASTER,
    ESCALATION_LEVEL_MODEL_FALLBACK,
    ESCALATION_LEVEL_USER,
    ESCALATION_LEVEL_WORKER_RETRY,
    GALAXY_DIR_NAME,
    MAX_DOMAIN_AGENTS,
    MAX_RETRY_LOOPS,
    MAX_WORKERS_PER_DOMAIN,
    SCHEDULER_MODE_BALANCED,
    VALIDATION_STEPS,
    VRAM_RESERVE_MB,
    VRAM_TIER_HIGH,
    VRAM_TIER_LOW,
    VRAM_TIER_MEDIUM,
    get_checkpoints_dir,
    get_config_path,
    get_galaxy_dir,
    get_logs_dir,
    get_memory_dir,
)


class TestSystemConstants:
    """Test system-wide constants have correct values."""

    def test_galaxy_dir_name(self) -> None:
        assert GALAXY_DIR_NAME == ".galaxy"

    def test_studio_port(self) -> None:
        assert DEFAULT_STUDIO_PORT == 8420

    def test_database_url_is_sqlite(self) -> None:
        assert "sqlite" in DEFAULT_DATABASE_URL

    def test_ollama_host(self) -> None:
        assert DEFAULT_OLLAMA_HOST == "http://localhost:11434"

    def test_default_models_are_set(self) -> None:
        assert DEFAULT_MASTER_MODEL
        assert DEFAULT_EMBEDDING_MODEL


class TestVRAMThresholds:
    """Test VRAM tier thresholds are ordered correctly."""

    def test_tiers_ordered(self) -> None:
        assert VRAM_TIER_HIGH > VRAM_TIER_MEDIUM > VRAM_TIER_LOW

    def test_reserve_is_reasonable(self) -> None:
        assert 256 <= VRAM_RESERVE_MB <= 2048


class TestAgentLimits:
    """Test agent limit constants."""

    def test_domain_limit_positive(self) -> None:
        assert MAX_DOMAIN_AGENTS > 0

    def test_worker_limit_positive(self) -> None:
        assert MAX_WORKERS_PER_DOMAIN > 0

    def test_retry_limit_positive(self) -> None:
        assert MAX_RETRY_LOOPS > 0


class TestEscalationLevels:
    """Test escalation chain constants are ordered 1-5."""

    def test_escalation_order(self) -> None:
        assert ESCALATION_LEVEL_WORKER_RETRY == 1
        assert ESCALATION_LEVEL_DOMAIN == 2
        assert ESCALATION_LEVEL_MASTER == 3
        assert ESCALATION_LEVEL_MODEL_FALLBACK == 4
        assert ESCALATION_LEVEL_USER == 5


class TestScheduler:
    """Test scheduler constants."""

    def test_default_mode(self) -> None:
        assert DEFAULT_SCHEDULER_MODE == SCHEDULER_MODE_BALANCED


class TestCheckpointing:
    """Test vault/checkpoint constants."""

    def test_interval_positive(self) -> None:
        assert CHECKPOINT_INTERVAL_MINUTES > 0

    def test_crash_marker_filename(self) -> None:
        assert CRASH_MARKER_FILENAME.startswith(".")


class TestValidationPipeline:
    """Test validation step list."""

    def test_steps_not_empty(self) -> None:
        assert len(VALIDATION_STEPS) > 0

    def test_syntax_is_first(self) -> None:
        assert VALIDATION_STEPS[0] == "syntax"

    def test_no_duplicates(self) -> None:
        assert len(VALIDATION_STEPS) == len(set(VALIDATION_STEPS))


class TestPathHelpers:
    """Test path utility functions."""

    def test_get_galaxy_dir(self) -> None:
        result = get_galaxy_dir("/tmp/project")
        assert result == Path("/tmp/project/.galaxy")

    def test_get_config_path(self) -> None:
        result = get_config_path("/tmp/project")
        assert result.name == "galaxy.config.yaml"

    def test_get_memory_dir(self) -> None:
        result = get_memory_dir("/tmp/project")
        assert result.name == "memory"

    def test_get_checkpoints_dir(self) -> None:
        result = get_checkpoints_dir("/tmp/project")
        assert result.name == "checkpoints"

    def test_get_logs_dir(self) -> None:
        result = get_logs_dir("/tmp/project")
        assert result.name == "logs"

    def test_default_workspace(self) -> None:
        result = get_galaxy_dir()
        assert result == Path(".galaxy")
