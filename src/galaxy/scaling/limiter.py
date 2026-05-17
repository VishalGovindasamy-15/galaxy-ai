"""Rate limiter and resource limits for agent scaling.

Manages concurrency, VRAM budgets, and scaling policies
for local and cloud-based agent deployments.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ScalingMode(str, Enum):
    """Agent scaling mode."""
    LOCAL = "local"      # Single machine, GPU-constrained
    CLOUD = "cloud"      # Cloud providers, API-based
    HYBRID = "hybrid"    # Mix of local and cloud


@dataclass
class ResourceLimit:
    """Resource limits for agent execution."""
    max_concurrent_agents: int = 3
    max_vram_mb: int = 4096
    max_tokens_per_minute: int = 10000
    max_requests_per_minute: int = 60
    timeout_seconds: int = 300

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_concurrent_agents": self.max_concurrent_agents,
            "max_vram_mb": self.max_vram_mb,
            "max_tokens_per_minute": self.max_tokens_per_minute,
            "max_requests_per_minute": self.max_requests_per_minute,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceLimit:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def for_gpu(cls, vram_gb: float) -> ResourceLimit:
        """Create limits based on GPU VRAM."""
        if vram_gb >= 24:
            return cls(max_concurrent_agents=8, max_vram_mb=int(vram_gb * 1024 * 0.8))
        elif vram_gb >= 12:
            return cls(max_concurrent_agents=5, max_vram_mb=int(vram_gb * 1024 * 0.8))
        elif vram_gb >= 6:
            return cls(max_concurrent_agents=3, max_vram_mb=int(vram_gb * 1024 * 0.8))
        else:
            return cls(max_concurrent_agents=2, max_vram_mb=int(vram_gb * 1024 * 0.8))


@dataclass
class ScalingConfig:
    """Configuration for agent scaling."""
    mode: ScalingMode = ScalingMode.LOCAL
    limits: ResourceLimit = field(default_factory=ResourceLimit)
    auto_scale: bool = False
    prefer_local: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "limits": self.limits.to_dict(),
            "auto_scale": self.auto_scale,
            "prefer_local": self.prefer_local,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScalingConfig:
        return cls(
            mode=ScalingMode(data.get("mode", "local")),
            limits=ResourceLimit.from_dict(data.get("limits", {})),
            auto_scale=data.get("auto_scale", False),
            prefer_local=data.get("prefer_local", True),
        )


class RateLimiter:
    """Token-bucket rate limiter for agent requests.

    Enforces limits on concurrent agents, tokens/min, and requests/min.

    Usage:
        limiter = RateLimiter(ResourceLimit())
        if limiter.can_proceed():
            limiter.acquire()
            # ... do work ...
            limiter.release()
    """

    def __init__(self, limits: ResourceLimit | None = None) -> None:
        self._limits = limits or ResourceLimit()
        self._active_agents: int = 0
        self._tokens_used: int = 0
        self._requests_made: int = 0
        self._window_start: float = time.monotonic()
        self._window_duration: float = 60.0  # 1 minute window

    @property
    def active_agents(self) -> int:
        return self._active_agents

    @property
    def available_slots(self) -> int:
        return max(0, self._limits.max_concurrent_agents - self._active_agents)

    @property
    def utilization(self) -> float:
        """Current utilization as a percentage (0.0 to 1.0)."""
        if self._limits.max_concurrent_agents == 0:
            return 1.0
        return self._active_agents / self._limits.max_concurrent_agents

    def can_proceed(self) -> bool:
        """Check if a new request can proceed within limits."""
        self._maybe_reset_window()

        if self._active_agents >= self._limits.max_concurrent_agents:
            return False
        if self._requests_made >= self._limits.max_requests_per_minute:
            return False
        if self._tokens_used >= self._limits.max_tokens_per_minute:
            return False
        return True

    def acquire(self, estimated_tokens: int = 0) -> bool:
        """Acquire a slot for an agent.

        Args:
            estimated_tokens: Estimated tokens for this request.

        Returns:
            True if acquired, False if limits exceeded.
        """
        if not self.can_proceed():
            return False

        self._active_agents += 1
        self._requests_made += 1
        self._tokens_used += estimated_tokens
        return True

    def release(self) -> None:
        """Release an agent slot."""
        if self._active_agents > 0:
            self._active_agents -= 1

    def record_tokens(self, tokens: int) -> None:
        """Record actual token usage after completion."""
        self._tokens_used += tokens

    def get_stats(self) -> dict[str, Any]:
        """Get current rate limiter stats."""
        return {
            "active_agents": self._active_agents,
            "available_slots": self.available_slots,
            "utilization": f"{self.utilization:.0%}",
            "requests_this_window": self._requests_made,
            "tokens_this_window": self._tokens_used,
            "limits": self._limits.to_dict(),
        }

    def _maybe_reset_window(self) -> None:
        """Reset counters if the time window has passed."""
        now = time.monotonic()
        if now - self._window_start >= self._window_duration:
            self._tokens_used = 0
            self._requests_made = 0
            self._window_start = now
