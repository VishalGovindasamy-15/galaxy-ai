"""Tests for galaxy.orchestrator.escalation."""

import pytest

from galaxy.core.exceptions import MaxEscalationReachedError
from galaxy.events.bus import EventBus
from galaxy.orchestrator.escalation import EscalationManager


@pytest.fixture
def escalation() -> EscalationManager:
    return EscalationManager(EventBus(), max_retries=2)


class TestWorkerRetry:
    """Test Level 1: Worker retry."""

    @pytest.mark.asyncio
    async def test_worker_retry(self, escalation) -> None:
        record = await escalation.handle_failure("t1", "syntax error", current_level=0)
        assert record.level == 1
        assert "retry" in record.action.lower()
        assert escalation.get_retry_count("t1") == 1

    @pytest.mark.asyncio
    async def test_multiple_retries(self, escalation) -> None:
        await escalation.handle_failure("t1", "err", current_level=0)
        await escalation.handle_failure("t1", "err", current_level=0)
        assert escalation.get_retry_count("t1") == 2


class TestDomainIntervention:
    """Test Level 2: Domain agent intervention."""

    @pytest.mark.asyncio
    async def test_domain_intervention(self, escalation) -> None:
        record = await escalation.handle_failure("t1", "complex error", current_level=1)
        assert record.level == 2
        assert "domain" in record.action.lower()


class TestMasterRestructure:
    """Test Level 3: Master restructure."""

    @pytest.mark.asyncio
    async def test_master_restructure(self, escalation) -> None:
        record = await escalation.handle_failure("t1", "design flaw", current_level=2)
        assert record.level == 3
        assert "master" in record.action.lower()


class TestModelFallback:
    """Test Level 4: Model fallback."""

    @pytest.mark.asyncio
    async def test_model_fallback(self, escalation) -> None:
        record = await escalation.handle_failure("t1", "model too weak", current_level=3)
        assert record.level == 4
        assert "model" in record.action.lower()


class TestUserEscalation:
    """Test Level 5: User intervention."""

    @pytest.mark.asyncio
    async def test_user_escalation(self, escalation) -> None:
        record = await escalation.handle_failure("t1", "unrecoverable", current_level=4)
        assert record.level == 5
        assert "user" in record.action.lower()

    @pytest.mark.asyncio
    async def test_max_escalation_raises(self, escalation) -> None:
        with pytest.raises(MaxEscalationReachedError):
            await escalation.handle_failure("t1", "final", current_level=5)


class TestEscalationHistory:
    """Test history tracking."""

    @pytest.mark.asyncio
    async def test_history_recorded(self, escalation) -> None:
        await escalation.handle_failure("t1", "err1", current_level=0)
        await escalation.handle_failure("t2", "err2", current_level=1)
        assert len(escalation.history) == 2

    @pytest.mark.asyncio
    async def test_reset_retries(self, escalation) -> None:
        await escalation.handle_failure("t1", "err", current_level=0)
        assert escalation.get_retry_count("t1") == 1
        escalation.reset_retries("t1")
        assert escalation.get_retry_count("t1") == 0
