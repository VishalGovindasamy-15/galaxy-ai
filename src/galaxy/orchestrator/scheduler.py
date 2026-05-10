"""VRAM-aware scheduler — determines parallelism based on available resources.

Decides how many workers can run simultaneously based on VRAM, model sizes,
and the configured scheduling mode.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from galaxy.core.constants import (
    DEFAULT_SCHEDULER_MODE,
    SCHEDULER_MODE_QUALITY,
    SCHEDULER_MODE_SPEED,
    VRAM_RESERVE_MB,
)
from galaxy.models.vram import detect_gpus, estimate_model_vram

logger = logging.getLogger(__name__)


@dataclass
class SchedulerPlan:
    """Result of scheduler calculation."""

    max_parallel_workers: int
    model_name: str
    estimated_vram_per_worker_gb: float
    total_free_vram_gb: float
    mode: str


class Scheduler:
    """VRAM-aware task scheduler."""

    def __init__(self, mode: str = DEFAULT_SCHEDULER_MODE) -> None:
        self.mode = mode

    def calculate_parallelism(self, model_name: str) -> SchedulerPlan:
        """Calculate how many workers can run in parallel.

        Args:
            model_name: Model each worker will use.

        Returns:
            SchedulerPlan with max_parallel_workers and details.
        """
        status = detect_gpus()
        free_vram_gb = status.free_vram_gb
        vram_per_worker = estimate_model_vram(model_name)

        # Reserve some VRAM for system
        usable_vram = max(0.0, free_vram_gb - (VRAM_RESERVE_MB / 1024))

        if vram_per_worker <= 0 or usable_vram <= 0:
            max_workers = 1  # CPU mode — single worker
        else:
            # Mode adjustments
            if self.mode == SCHEDULER_MODE_SPEED:
                # Ollama shares model weights — multiple workers share VRAM
                max_workers = max(1, int(usable_vram / (vram_per_worker * 0.3)))
            elif self.mode == SCHEDULER_MODE_QUALITY:
                max_workers = 1
            else:  # balanced
                max_workers = max(1, int(usable_vram / (vram_per_worker * 0.5)))

        logger.info(
            "Scheduler: mode=%s, free_vram=%.1fGB, per_worker=%.1fGB, max_parallel=%d",
            self.mode, free_vram_gb, vram_per_worker, max_workers,
        )

        return SchedulerPlan(
            max_parallel_workers=max_workers,
            model_name=model_name,
            estimated_vram_per_worker_gb=vram_per_worker,
            total_free_vram_gb=free_vram_gb,
            mode=self.mode,
        )
