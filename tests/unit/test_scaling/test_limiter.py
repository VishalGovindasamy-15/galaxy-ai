"""Tests for galaxy.scaling.limiter."""

from galaxy.scaling.limiter import (
    RateLimiter,
    ResourceLimit,
    ScalingConfig,
    ScalingMode,
)


class TestResourceLimit:
    def test_default(self) -> None:
        lim = ResourceLimit()
        assert lim.max_concurrent_agents == 3
        assert lim.timeout_seconds == 300

    def test_for_gpu_small(self) -> None:
        lim = ResourceLimit.for_gpu(4.0)
        assert lim.max_concurrent_agents == 2

    def test_for_gpu_medium(self) -> None:
        lim = ResourceLimit.for_gpu(6.0)
        assert lim.max_concurrent_agents == 3

    def test_for_gpu_large(self) -> None:
        lim = ResourceLimit.for_gpu(12.0)
        assert lim.max_concurrent_agents == 5

    def test_for_gpu_xlarge(self) -> None:
        lim = ResourceLimit.for_gpu(24.0)
        assert lim.max_concurrent_agents == 8

    def test_roundtrip(self) -> None:
        original = ResourceLimit(max_concurrent_agents=5, max_vram_mb=8192)
        restored = ResourceLimit.from_dict(original.to_dict())
        assert restored.max_concurrent_agents == 5
        assert restored.max_vram_mb == 8192


class TestScalingConfig:
    def test_default(self) -> None:
        cfg = ScalingConfig()
        assert cfg.mode == ScalingMode.LOCAL
        assert cfg.prefer_local

    def test_roundtrip(self) -> None:
        original = ScalingConfig(mode=ScalingMode.CLOUD, auto_scale=True)
        restored = ScalingConfig.from_dict(original.to_dict())
        assert restored.mode == ScalingMode.CLOUD
        assert restored.auto_scale


class TestRateLimiter:
    def test_initial_state(self) -> None:
        limiter = RateLimiter()
        assert limiter.active_agents == 0
        assert limiter.available_slots == 3
        assert limiter.utilization == 0.0

    def test_acquire_and_release(self) -> None:
        limiter = RateLimiter(ResourceLimit(max_concurrent_agents=2))
        assert limiter.acquire()
        assert limiter.active_agents == 1
        assert limiter.acquire()
        assert limiter.active_agents == 2
        assert not limiter.can_proceed()  # At limit
        assert not limiter.acquire()

        limiter.release()
        assert limiter.active_agents == 1
        assert limiter.can_proceed()

    def test_utilization(self) -> None:
        limiter = RateLimiter(ResourceLimit(max_concurrent_agents=4))
        limiter.acquire()
        limiter.acquire()
        assert limiter.utilization == 0.5

    def test_request_rate_limit(self) -> None:
        limiter = RateLimiter(ResourceLimit(max_requests_per_minute=2, max_concurrent_agents=10))
        assert limiter.acquire()
        assert limiter.acquire()
        limiter.release()
        limiter.release()
        assert not limiter.can_proceed()  # Hit request limit

    def test_token_rate_limit(self) -> None:
        limiter = RateLimiter(ResourceLimit(max_tokens_per_minute=100, max_concurrent_agents=10))
        assert limiter.acquire(estimated_tokens=50)
        assert limiter.acquire(estimated_tokens=50)
        limiter.release()
        limiter.release()
        assert not limiter.can_proceed()  # Hit token limit

    def test_stats(self) -> None:
        limiter = RateLimiter()
        limiter.acquire(estimated_tokens=100)
        stats = limiter.get_stats()
        assert stats["active_agents"] == 1
        assert stats["tokens_this_window"] == 100

    def test_release_floor(self) -> None:
        limiter = RateLimiter()
        limiter.release()  # Should not go negative
        assert limiter.active_agents == 0
