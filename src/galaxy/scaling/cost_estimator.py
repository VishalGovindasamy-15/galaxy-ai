"""Cost estimator — estimates compute cost for project generation.

Provides cost estimation before the user confirms project generation,
helping them understand resource usage and expected time.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from galaxy.cognitive.types import ExecutionPlan

logger = logging.getLogger(__name__)

# Cost constants (relative units for local GPU)
COST_PER_CHUNK = 0.5  # Minutes per chunk on average
TOKENS_PER_CHUNK = 800  # Average tokens per chunk
VRAM_PER_AGENT_MB = 1500  # VRAM per active agent (3B model)


@dataclass
class CostEstimate:
    """Estimated cost for a project generation run."""
    total_chunks: int = 0
    total_domains: int = 0
    estimated_tokens: int = 0
    estimated_time_minutes: float = 0.0
    estimated_vram_mb: int = 0
    max_concurrent_agents: int = 1
    warnings: list[str] = field(default_factory=list)

    @property
    def estimated_time_display(self) -> str:
        """Human-readable time estimate."""
        minutes = self.estimated_time_minutes
        if minutes < 1:
            return f"{minutes * 60:.0f} seconds"
        elif minutes < 60:
            return f"{minutes:.0f} minutes"
        else:
            hours = minutes / 60
            return f"{hours:.1f} hours"

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_chunks": self.total_chunks,
            "total_domains": self.total_domains,
            "estimated_tokens": self.estimated_tokens,
            "estimated_time_minutes": self.estimated_time_minutes,
            "estimated_vram_mb": self.estimated_vram_mb,
            "max_concurrent_agents": self.max_concurrent_agents,
            "warnings": self.warnings,
        }


class CostEstimator:
    """Estimates compute cost for project generation.

    Usage:
        estimator = CostEstimator(vram_gb=6.0)
        estimate = estimator.estimate_from_plan(plan)
        print(estimate.estimated_time_display)
    """

    def __init__(
        self,
        vram_gb: float = 6.0,
        cost_per_chunk: float = COST_PER_CHUNK,
        tokens_per_chunk: int = TOKENS_PER_CHUNK,
    ) -> None:
        self._vram_gb = vram_gb
        self._cost_per_chunk = cost_per_chunk
        self._tokens_per_chunk = tokens_per_chunk
        self._vram_per_agent = VRAM_PER_AGENT_MB

    def estimate_from_plan(self, plan: ExecutionPlan) -> CostEstimate:
        """Estimate cost from an execution plan.

        Args:
            plan: The execution plan to estimate.

        Returns:
            CostEstimate with all estimates.
        """
        total_chunks = plan.estimated_total_chunks or sum(
            n.estimated_chunks for n in plan.nodes
        )
        total_domains = len(plan.domains)

        # Max concurrent agents = 1 master + N domain agents (limited by VRAM)
        max_agents = self._calculate_max_agents(total_domains)

        # Time estimate: total chunks / parallelism factor
        parallelism = min(max_agents, total_domains) if total_domains > 0 else 1
        estimated_time = (total_chunks * self._cost_per_chunk) / parallelism

        estimate = CostEstimate(
            total_chunks=total_chunks,
            total_domains=total_domains,
            estimated_tokens=total_chunks * self._tokens_per_chunk,
            estimated_time_minutes=estimated_time,
            estimated_vram_mb=max_agents * self._vram_per_agent,
            max_concurrent_agents=max_agents,
        )

        # Add warnings
        if estimate.estimated_vram_mb > self._vram_gb * 1024:
            estimate.warnings.append(
                f"Estimated VRAM ({estimate.estimated_vram_mb}MB) exceeds "
                f"available ({self._vram_gb * 1024:.0f}MB)"
            )

        if estimated_time > 30:
            estimate.warnings.append(
                f"Estimated time ({estimate.estimated_time_display}) is significant"
            )

        return estimate

    def estimate_from_chunks(self, num_chunks: int, num_domains: int = 1) -> CostEstimate:
        """Simple estimate from chunk and domain counts."""
        max_agents = self._calculate_max_agents(num_domains)
        parallelism = min(max_agents, num_domains) if num_domains > 0 else 1

        return CostEstimate(
            total_chunks=num_chunks,
            total_domains=num_domains,
            estimated_tokens=num_chunks * self._tokens_per_chunk,
            estimated_time_minutes=(num_chunks * self._cost_per_chunk) / parallelism,
            estimated_vram_mb=max_agents * self._vram_per_agent,
            max_concurrent_agents=max_agents,
        )

    def _calculate_max_agents(self, num_domains: int) -> int:
        """Calculate max concurrent agents based on VRAM."""
        vram_mb = self._vram_gb * 1024
        max_by_vram = max(1, int(vram_mb / self._vram_per_agent))
        # 1 master + domain agents, capped by VRAM
        desired = 1 + num_domains
        return min(desired, max_by_vram)
