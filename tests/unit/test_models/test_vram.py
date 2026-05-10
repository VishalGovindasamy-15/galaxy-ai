"""Tests for galaxy.models.vram."""

from galaxy.models.vram import (
    GPUInfo,
    VRAMStatus,
    detect_gpus,
    estimate_model_vram,
    get_free_vram,
    select_models_for_vram,
)


class TestGPUInfo:
    """Test GPUInfo dataclass."""

    def test_properties(self) -> None:
        gpu = GPUInfo(index=0, name="RTX 4090", total_mb=24576, used_mb=4096, free_mb=20480)
        assert gpu.total_gb == 24.0
        assert gpu.used_gb == 4.0
        assert gpu.free_gb == 20.0

    def test_utilization(self) -> None:
        gpu = GPUInfo(index=0, name="Test", total_mb=1000, used_mb=500, free_mb=500)
        assert gpu.utilization == 50.0

    def test_zero_total(self) -> None:
        gpu = GPUInfo(index=0, name="Test", total_mb=0, used_mb=0, free_mb=0)
        assert gpu.utilization == 0


class TestVRAMStatus:
    """Test VRAMStatus aggregation."""

    def test_empty_status(self) -> None:
        status = VRAMStatus()
        assert status.gpu_count == 0
        assert not status.has_gpu
        assert status.total_vram_gb == 0.0
        assert status.free_vram_gb == 0.0

    def test_single_gpu(self) -> None:
        gpu = GPUInfo(index=0, name="RTX 4090", total_mb=24576, used_mb=4096, free_mb=20480)
        status = VRAMStatus(gpus=[gpu], nvidia_smi_available=True)
        assert status.gpu_count == 1
        assert status.has_gpu
        assert status.total_vram_gb == 24.0

    def test_multi_gpu(self) -> None:
        gpus = [
            GPUInfo(index=0, name="GPU0", total_mb=8192, used_mb=1024, free_mb=7168),
            GPUInfo(index=1, name="GPU1", total_mb=8192, used_mb=2048, free_mb=6144),
        ]
        status = VRAMStatus(gpus=gpus, nvidia_smi_available=True)
        assert status.gpu_count == 2
        assert status.total_vram_mb == 16384
        assert status.free_vram_mb == 13312


class TestDetectGpus:
    """Test GPU detection (graceful handling)."""

    def test_detect_returns_status(self) -> None:
        status = detect_gpus()
        assert isinstance(status, VRAMStatus)

    def test_no_gpu_returns_zero(self) -> None:
        # On systems without nvidia-smi, should return 0
        vram = get_free_vram()
        assert isinstance(vram, float)
        assert vram >= 0.0


class TestEstimateModelVram:
    """Test VRAM estimation from model names."""

    def test_7b_model(self) -> None:
        assert estimate_model_vram("qwen2.5-coder:7b") == 5.5

    def test_14b_model(self) -> None:
        assert estimate_model_vram("qwen2.5-coder:14b") == 10.0

    def test_3b_model(self) -> None:
        assert estimate_model_vram("qwen2.5-coder:3b") == 3.0

    def test_unknown_model(self) -> None:
        assert estimate_model_vram("custom-model") == 4.0

    def test_70b_model(self) -> None:
        assert estimate_model_vram("llama3:70b") == 42.0


class TestSelectModels:
    """Test auto-model selection by VRAM."""

    def test_high_vram(self) -> None:
        models = select_models_for_vram(24.0)
        assert "14b" in models["master"]
        assert "7b" in models["domain"]
        assert "7b" in models["worker"]

    def test_medium_vram(self) -> None:
        models = select_models_for_vram(12.0)
        assert "7b" in models["master"]
        assert "7b" in models["domain"]

    def test_moderate_vram(self) -> None:
        """6GB GPU like RTX 3050 — 7b master, 3b domain/worker."""
        models = select_models_for_vram(6.0)
        assert "7b" in models["master"]
        assert "3b" in models["domain"]
        assert "3b" in models["worker"]

    def test_low_vram(self) -> None:
        models = select_models_for_vram(3.0)
        assert "3b" in models["master"]
        assert "3b" in models["domain"]

    def test_no_vram(self) -> None:
        models = select_models_for_vram(0.0)
        assert "3b" in models["master"]  # Never falls to 1.5b now
        assert "domain" in models  # Domain model always present

