"""VRAM detection and monitoring.

Detects available GPUs, measures free VRAM, and estimates model memory requirements.
Works with NVIDIA GPUs via nvidia-smi. Gracefully handles no-GPU systems.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Approximate VRAM requirements per model size (in GB)
MODEL_VRAM_ESTIMATES: dict[str, float] = {
    "1b": 1.5,
    "3b": 3.0,
    "7b": 5.5,
    "8b": 6.0,
    "13b": 9.0,
    "14b": 10.0,
    "32b": 20.0,
    "70b": 42.0,
}


@dataclass
class GPUInfo:
    """Information about a single GPU."""

    index: int
    name: str
    total_mb: int
    used_mb: int
    free_mb: int
    temperature: int = 0

    @property
    def total_gb(self) -> float:
        return self.total_mb / 1024

    @property
    def used_gb(self) -> float:
        return self.used_mb / 1024

    @property
    def free_gb(self) -> float:
        return self.free_mb / 1024

    @property
    def utilization(self) -> float:
        """Usage percentage (0-100)."""
        return (self.used_mb / self.total_mb * 100) if self.total_mb > 0 else 0


@dataclass
class VRAMStatus:
    """Aggregated VRAM status across all GPUs."""

    gpus: list[GPUInfo] = field(default_factory=list)
    nvidia_smi_available: bool = False

    @property
    def gpu_count(self) -> int:
        return len(self.gpus)

    @property
    def total_vram_mb(self) -> int:
        return sum(g.total_mb for g in self.gpus)

    @property
    def free_vram_mb(self) -> int:
        return sum(g.free_mb for g in self.gpus)

    @property
    def total_vram_gb(self) -> float:
        return self.total_vram_mb / 1024

    @property
    def free_vram_gb(self) -> float:
        return self.free_vram_mb / 1024

    @property
    def has_gpu(self) -> bool:
        return self.gpu_count > 0


def detect_gpus() -> VRAMStatus:
    """Detect all available NVIDIA GPUs and their VRAM.

    Returns:
        VRAMStatus with GPU information, or empty if no GPUs found.
    """
    if not shutil.which("nvidia-smi"):
        logger.info("nvidia-smi not found — no NVIDIA GPU detected")
        return VRAMStatus(nvidia_smi_available=False)

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            logger.warning("nvidia-smi failed: %s", result.stderr.strip())
            return VRAMStatus(nvidia_smi_available=True)

        gpus: list[GPUInfo] = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpus.append(GPUInfo(
                    index=int(parts[0]),
                    name=parts[1],
                    total_mb=int(parts[2]),
                    used_mb=int(parts[3]),
                    free_mb=int(parts[4]),
                    temperature=int(parts[5]) if len(parts) > 5 else 0,
                ))

        logger.info("Detected %d GPU(s): %s", len(gpus), ", ".join(g.name for g in gpus))
        return VRAMStatus(gpus=gpus, nvidia_smi_available=True)

    except subprocess.TimeoutExpired:
        logger.warning("nvidia-smi timed out")
        return VRAMStatus(nvidia_smi_available=True)
    except Exception as e:
        logger.warning("GPU detection failed: %s", e)
        return VRAMStatus(nvidia_smi_available=False)


def get_free_vram() -> float:
    """Get total free VRAM across all GPUs in GB.

    Returns:
        Free VRAM in GB, or 0.0 if no GPU.
    """
    status = detect_gpus()
    return status.free_vram_gb


def estimate_model_vram(model_name: str) -> float:
    """Estimate VRAM required for a model based on its name.

    Parses model size from name (e.g., 'qwen2.5-coder:7b' → 5.5 GB).

    Args:
        model_name: Model name string.

    Returns:
        Estimated VRAM in GB.
    """
    model_lower = model_name.lower()

    # Try to extract size from model name
    for size_key, vram_gb in sorted(
        MODEL_VRAM_ESTIMATES.items(),
        key=lambda x: float(x[0].rstrip("b")),
        reverse=True,
    ):
        if size_key in model_lower:
            return vram_gb

    # Default estimate for unknown models
    return 4.0


def select_models_for_vram(available_vram_gb: float) -> dict[str, str]:
    """Auto-select best models based on available VRAM.

    Args:
        available_vram_gb: Available VRAM in GB.

    Returns:
        Dict with keys 'master', 'domain', 'worker', 'embedding' mapping to model names.
    """
    if available_vram_gb >= 24.0:
        return {
            "master": "qwen2.5-coder:14b",
            "domain": "qwen2.5-coder:7b",
            "worker": "qwen2.5-coder:7b",
            "embedding": "nomic-embed-text",
        }
    elif available_vram_gb >= 12.0:
        return {
            "master": "qwen2.5-coder:7b",
            "domain": "qwen2.5-coder:7b",
            "worker": "qwen2.5-coder:7b",
            "embedding": "nomic-embed-text",
        }
    elif available_vram_gb >= 8.0:
        return {
            "master": "qwen2.5-coder:3b",
            "domain": "qwen2.5-coder:3b",
            "worker": "qwen2.5-coder:3b",
            "embedding": "nomic-embed-text",
        }
    else:
        # No GPU or very low VRAM — suggest cloud or CPU
        return {
            "master": "qwen2.5-coder:1.5b",
            "domain": "qwen2.5-coder:1.5b",
            "worker": "qwen2.5-coder:1.5b",
            "embedding": "nomic-embed-text",
        }
